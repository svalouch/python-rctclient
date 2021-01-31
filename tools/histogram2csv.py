#!/usr/bin/env python3

'''
Import a days worth of "minute" histogram data and outputs a CSV file with the results
'''

# Copyright 2020, Stefan Valouch (svalouch)
# SPDX-License-Identifier: GPL-3.0-only

import csv
import os
import select
import socket
import struct
import sys
from datetime import datetime, timedelta
from tempfile import mkstemp
from typing import Dict, Optional

import click
import pytz

from rctclient.exceptions import FrameCRCMismatch
from rctclient.frame import ReceiveFrame, make_frame
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


be_quiet: bool = False


def cprint(text: str) -> None:
    '''
    Custom print to output to stderr if quiet is not set.
    '''
    if not be_quiet:
        click.echo(text, err=True)


@click.command()
@click.option('-h', '--host', type=str, required=True, help='Host to query')
@click.option('-p', '--port', type=int, default=8899, help='Port on the host to query [8899]')
@click.option('-o', '--output', type=click.Path(writable=True, dir_okay=False, allow_dash=True), required=False,
              help='Output file (use "-" for standard output), omit for "data_<date>.csv"')
@click.option('-H', '--no-headers', type=bool, is_flag=True, default=False, help='When specified, does not output the '
                                                                                 'column names as first row')
@click.option('--time-zone', type=str, default='Europe/Berlin', help='Timezone of the device (not the host running the'
                                                                     ' script) [Europe/Berlin]')
@click.option('-q', '--quiet', type=bool, is_flag=True, default=False, help='Supress output')
@click.argument('DAY_BEFORE_TODAY', type=int)
def histogram2csv(host: str, port: int, output: Optional[str], no_headers: bool, time_zone: str, quiet: bool,
                  day_before_today: int) -> None:

    '''
    Extract a day of history data from the RCT device. This tool connects to a device and reads the fine-grained
    "minute" values of a day which is DAY_BEFORE_TODAY number of days before the current day.

    The output format is CSV. If --output is not given, then a name is constructed from the current date. Specify "-"
    to have the tool print the table to standard output, for use with other tools.
    '''
    global be_quiet
    be_quiet = quiet

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
        cprint('DAYS_BEFORE_TODAY must be a positive number')
        sys.exit(1)
    if day_before_today > 365:
        cprint('DAYS_BEFORE_TODAY must be less than a year ago')
        sys.exit(1)

    oids = [x for x in R.all() if x.name in oid_names]

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except ConnectionRefusedError:
        cprint('Device refused connection')
        sys.exit(2)

    ts_start = (datetime.now() - timedelta(days=day_before_today)).replace(hour=0, minute=0, second=0, microsecond=0)
    ts_end = ts_start.replace(hour=23, minute=59, second=59, microsecond=0)

    datetable: Dict[datetime, Dict[str, int]] = {dt: dict() for dt in datetime_range(ts_start, ts_end,
                                                                                     timedelta(minutes=5))}

    for oid in oids:
        name = oid.name.replace('logger.minutes_', '').replace('_log_ts', '')
        cprint(f'Requesting {name}')

        highest_ts = ts_end

        while highest_ts > ts_start:
            cprint(f'\ttimestamp: {highest_ts}')
            sock.send(make_frame(command=Command.WRITE, id=oid.object_id,
                                 payload=encode_value(DataType.INT32, int(highest_ts.timestamp()))))

            rframe = ReceiveFrame()
            while True:
                try:
                    rread, _, _ = select.select([sock], [], [], 2)
                except select.error as exc:
                    cprint(f'Select error: {str(exc)}')
                    raise

                if rread:
                    buf = sock.recv(1024)
                    if len(buf) > 0:
                        try:
                            rframe.consume(buf)
                        except FrameCRCMismatch:
                            cprint('\tCRC error')
                            break
                        if rframe.complete():
                            break
                    else:
                        cprint('Device closed connection')
                        sys.exit(2)
                else:
                    cprint('\tTimeout, retrying')
                    break

            if not rframe.complete():
                cprint('\tIncomplete frame, retrying')
                continue

            # in case something (such as a "net.package") slips in, make sure to ignore all irelevant responses
            if rframe.id != oid.object_id:
                cprint(f'\tGot unexpected frame oid 0x{rframe.id:08X}')
                continue

            try:
                _, table = decode_value(DataType.TIMESERIES, rframe.data)
            except (AssertionError, struct.error):
                # the device sent invalid data with the correct CRC
                cprint('\tInvalid data received, retrying')
                continue

            # work with the data
            for t_ts, t_val in table.items():

                # set the "highest" point in time to know what to request next when the day is not complete
                if t_ts < highest_ts:
                    highest_ts = t_ts

                # break if we reached the end of the day
                if t_ts < ts_start:
                    cprint('\tReached limit')
                    break

                # Check if the timestamp fits the raster, adjust up to one minute in both directions
                if t_ts not in datetable:
                    nt_ts = t_ts.replace(second=0)
                    if nt_ts not in datetable:
                        nt_ts = t_ts.replace(second=0, minute=t_ts.minute + 1)
                        if nt_ts not in datetable:
                            cprint(f'\t{t_ts} does not fit raster, skipped')
                            continue
                    t_ts = nt_ts
                datetable[t_ts][name] = t_val

    if output is None:
        output = f'data_{ts_start.isoformat("T")}.csv'

    if output == '-':
        fd = sys.stdout
    else:
        filedes, filepath = mkstemp(dir=os.path.dirname(output), text=True)
        fd = open(filedes, 'wt')

    writer = csv.writer(fd)

    names = [oid.name.replace('logger.minutes_', '').replace('_log_ts', '') for oid in oids]

    if not no_headers:
        writer.writerow(['timestamp'] + names)

    for bts, btval in datetable.items():
        if btval:  # there may be holes in the data
            writer.writerow([timezone.localize(bts).isoformat('T')] + [str(btval[name]) for name in names])

    if output != '-':
        fd.flush()
        os.fsync(fd.fileno())
        try:
            os.rename(filepath, output)
        except OSError as exc:
            cprint(f'Could not move destination file: {str(exc)}')
            try:
                os.unlink(filepath)
            except Exception:
                cprint(f'Could not remove temporary file {filepath}')
            sys.exit(1)


if __name__ == '__main__':
    histogram2csv()
