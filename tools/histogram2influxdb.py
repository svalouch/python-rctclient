#!/usr/bin/env python3

'''
Import a days worth of "minute" histogram data and push it to an influxdb.
'''

# Copyright 2020, Stefan Valouch (svalouch)
# SPDX-License-Identifier: GPL-3.0-only

import select
import socket
import struct
import sys
from datetime import datetime, timedelta
from typing import Dict

import click
import pytz
import requests
import yaml
from influxdb import InfluxDBClient  # type: ignore

from rctclient.exceptions import FrameCRCMismatch
from rctclient.frame import ReceiveFrame, SendFrame
from rctclient.registry import REGISTRY as R
from rctclient.types import Command, DataType
from rctclient.utils import decode_value, encode_value

# pylint: disable=too-many-arguments,too-many-locals


def datetime_range(start: datetime, end: datetime, delta: timedelta):
    '''
    Generator yielding datetime objects between `start` and `end` with `delta` increments.
    '''
    current = start
    while current < end:
        yield current
        current += delta


@click.command()
@click.option('--host', type=str, required=True, help='Host to query')
@click.option('--port', type=int, default=8899, help='Port on the host to query [8899]')
@click.option('--device-name', type=str, default='rct1', help='Name of the device [rct1]')
@click.option('--influx-host', type=str, default='localhost', help='InfluxDB hostname [localhost]')
@click.option('--influx-port', type=int, default=8086, help='InfluxDB port [8086]')
@click.option('--influx-db', type=str, default='rct', help='InfluxDB database name [rct]')
@click.option('--influx-user', type=str, default='rct', help='InfluxDB user name [rct]')
@click.option('--influx-pass', type=str, default='rct', help='InfluxDB password [rct]')
@click.option('--dump', is_flag=True, default=False, help='If set, dumps data to the CWD in a file '
                                                          '"device-name.data.yml')
@click.option('--time-zone', type=str, default='Europe/Berlin', help='Timezone of the device (not the host running the'
                                                                     ' script) [Europe/Berlin]')
@click.argument('DAY_BEFORE_TODAY', type=int)
def histogram2influxdb(host: str, port: int, device_name: str, influx_host: str, influx_port: int, influx_db: str,
                       influx_user: str, influx_pass: str, dump: bool, time_zone: str, day_before_today: int) -> None:

    timezone = pytz.timezone(time_zone)
    oid_names = ['logger.minutes_ubat_log_ts', 'logger.minutes_ul3_log_ts', 'logger.minutes_ub_log_ts',
                 'logger.minutes_temp2_log_ts', 'logger.minutes_eb_log_ts', 'logger.minutes_eac1_log_ts',
                 'logger.minutes_eext_log_ts', 'logger.minutes_ul2_log_ts', 'logger.minutes_ea_log_ts',
                 'logger.minutes_soc_log_ts', 'logger.minutes_ul1_log_ts', 'logger.minutes_eac2_log_ts',
                 'logger.minutes_eac_log_ts', 'logger.minutes_ua_log_ts', 'logger.minutes_soc_targ_log_ts',
                 'logger.minutes_egrid_load_log_ts', 'logger.minutes_egrid_feed_log_ts',
                 'logger.minutes_eload_log_ts', 'logger.minutes_ebat_log_ts', 'logger.minutes_temp_bat_log_ts',
                 'logger.minutes_eac3_log_ts', 'logger.minutes_temp_log_ts']

    if day_before_today < 0:
        click.echo('DAYS_BEFORE_TODAY must be a positive number')
        sys.exit(1)
    if day_before_today > 365:
        click.echo('DAYS_BEFORE_TODAY must be less than a year ago')
        sys.exit(1)

    oids = [x for x in R.all() if x.name in oid_names]

    influx = InfluxDBClient(host=influx_host, port=influx_port, username=influx_user, password=influx_pass,
                            database=influx_db)

    try:
        influx.ping()
    except requests.exceptions.ConnectionError as exc:
        click.echo(f'InfluxDB refused connection: {str(exc)}')
        sys.exit(2)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except ConnectionRefusedError:
        click.echo('Device refused connection')
        sys.exit(2)

    ts_start = (datetime.now() - timedelta(days=day_before_today)).replace(hour=0, minute=0, second=0, microsecond=0)
    ts_end = ts_start.replace(hour=23, minute=59, second=59, microsecond=0)

    datetable: Dict[datetime, Dict[str, int]] = {dt: dict() for dt in datetime_range(ts_start, ts_end,
                                                                                     timedelta(minutes=5))}

    for oid in oids:
        name = oid.name.replace('logger.minutes_', '').replace('_log_ts', '')
        print(f'Requesting {name}')

        highest_ts = ts_end

        while highest_ts > ts_start:
            print(f'\ttimestamp: {highest_ts}')
            sframe = SendFrame(command=Command.WRITE, id=oid.object_id,
                               payload=encode_value(DataType.INT32, int(highest_ts.timestamp())))
            sock.send(sframe.data)

            rframe = ReceiveFrame()
            while True:
                try:
                    rread, _, _ = select.select([sock], [], [], 2)
                except select.error as exc:
                    click.echo(f'Select error: {str(exc)}')
                    raise

                if rread:
                    buf = sock.recv(1024)
                    if len(buf) > 0:
                        try:
                            rframe.consume(buf)
                        except FrameCRCMismatch:
                            click.echo('\tCRC error')
                            break
                        if rframe.complete():
                            break
                    else:
                        click.echo('Device closed connection')
                        sys.exit(2)
                else:
                    click.echo('\tTimeout, retrying')
                    break

            if not rframe.complete():
                click.echo('\tIncomplete frame, retrying')
                continue

            # in case something (such as a "net.package") slips in, make sure to ignore all irelevant responses
            if rframe.id != oid.object_id:
                click.echo(f'\tGot unexpected frame oid 0x{rframe.id:08X}')
                continue

            try:
                _, table = decode_value(DataType.TIMESERIES, rframe.data)
            except (AssertionError, struct.error):
                # the device sent invalid data with the correct CRC
                click.echo('\tInvalid data received, retrying')
                continue

            # work with the data
            for t_ts, t_val in table.items():

                # set the "highest" point in time to know what to request next when the day is not complete
                if t_ts < highest_ts:
                    highest_ts = t_ts

                # break if we reached the end of the day
                if t_ts < ts_start:
                    click.echo('\tReached limit')
                    break

                # Check if the timestamp fits the raster, adjust up to one minute in both directions
                if t_ts not in datetable:
                    nt_ts = t_ts.replace(second=0)
                    if nt_ts not in datetable:
                        nt_ts = t_ts.replace(second=0, minute=t_ts.minute + 1)
                        if nt_ts not in datetable:
                            print(f'\t{t_ts} does not fit raster, skipped')
                            continue
                    t_ts = nt_ts
                datetable[t_ts][name] = t_val

    if dump:
        with open(f'data_{device_name}_{ts_start.isoformat("T")}.yml', 'wt') as out:
            yaml.dump(datetable, out)

    points = []
    for bts, btval in datetable.items():
        if btval:  # there may be holes in the data
            points.append({
                'measurement': 'history',
                'tags': {
                    'rct': device_name,
                },
                'time': timezone.localize(bts).isoformat('T'),
                'fields': btval,
            })
    if points:
        click.echo(f'Writing {len(points)} points')
        influx.write_points(time_precision='s', points=points)


if __name__ == '__main__':
    histogram2influxdb()
