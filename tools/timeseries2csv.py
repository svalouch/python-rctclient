#!/usr/bin/env python3

'''
Retrieves time series data from the device and converts it to CSV.
'''

# Copyright 2020-2021, Stefan Valouch (svalouch)
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
from dateutil.relativedelta import relativedelta

from rctclient.exceptions import FrameCRCMismatch
from rctclient.frame import ReceiveFrame, make_frame
from rctclient.registry import REGISTRY as R
from rctclient.types import Command, DataType
from rctclient.utils import decode_value, encode_value

# pylint: disable=too-many-arguments,too-many-locals


def datetime_range(start: datetime, end: datetime, delta: relativedelta):
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
              help='Output file (use "-" for standard output), omit for "data_<resolution>_<date>.csv"')
@click.option('-H', '--no-headers', type=bool, is_flag=True, default=False, help='When specified, does not output the '
                                                                                 'column names as first row')
@click.option('--time-zone', type=str, default='Europe/Berlin', help='Timezone of the device (not the host running the'
                                                                     ' script) [Europe/Berlin].')
@click.option('-q', '--quiet', type=bool, is_flag=True, default=False, help='Supress output.')
@click.option('-r', '--resolution', type=click.Choice(['minutes', 'day', 'month', 'year'], case_sensitive=False),
              default='day', help='Resolution to query [minutes].')
@click.option('-c', '--count', type=int, default=1, help='Amount of time to go back, depends on --resolution, see '
              '--help.')
@click.argument('DAY_BEFORE_TODAY', type=int)
def timeseries2csv(host: str, port: int, output: Optional[str], no_headers: bool, time_zone: str, quiet: bool,
                   resolution: str, count: int, day_before_today: int) -> None:

    '''
    Extract time series data from an RCT device. The tool works similar to the official App, but can be run
    independantly, it is designed to be run from a cronjob or as part of a script.

    The output format is CSV.  If --output is not given, then a name is constructed from the resolution and the current
    date.  Specify "-" to have the tool print the table to standard output, for use with other tools.  Unless
    --no-headers is set, the first line contains the column headers.

    Data is queried into the past, by specifying the latest point in time for which data should be queried.  Thus,
    DAYS_BEFORE_TODAY selects the last second of the day that is the given amount in the past.  0 therefor is the
    incomplete current day, 1 is the end of yesterday etc.

    The device has multiple sampling memories at varying sampling intervals.  The resolution can be selected using
    --resolution, which supports "minutes" (which is at 5 minute intervals), day, month and year.  The amount of time
    to cover (back from the end of DAY_BEFORE_TODAY) can be selected using --count:

    * For --resolution=minute, if DAY_BEFORE_TODAY is 0 it selects the last --count hours up to the current time.

    * For --resolution=minute, if DAY_BEFORE_TODAY is greater than 0, it selects --count days back.

    * For all the other resolutions, --count selects the amount of days, months and years to go back, respectively.

    Note that the tool does not remove extra information: If the device sends more data than was requested, that extra
    data is included.

    Examples:

    * The previous 3 hours at finest resolution: --resolution=minutes --count=3 0

    * A whole day, 3 days ago, at finest resolution: --resolution=minutes --count=24 3

    * 4 Months back, at 1 month resolution: --resolution=month --count=4 0
    '''
    global be_quiet
    be_quiet = quiet

    if count < 1:
        cprint('Error: --count must be a positive integer')
        sys.exit(1)

    timezone = pytz.timezone(time_zone)
    now = datetime.now()

    if resolution == 'minutes':
        oid_names = ['logger.minutes_ubat_log_ts', 'logger.minutes_ul3_log_ts', 'logger.minutes_ub_log_ts',
                     'logger.minutes_temp2_log_ts', 'logger.minutes_eb_log_ts', 'logger.minutes_eac1_log_ts',
                     'logger.minutes_eext_log_ts', 'logger.minutes_ul2_log_ts', 'logger.minutes_ea_log_ts',
                     'logger.minutes_soc_log_ts', 'logger.minutes_ul1_log_ts', 'logger.minutes_eac2_log_ts',
                     'logger.minutes_eac_log_ts', 'logger.minutes_ua_log_ts', 'logger.minutes_soc_targ_log_ts',
                     'logger.minutes_egrid_load_log_ts', 'logger.minutes_egrid_feed_log_ts',
                     'logger.minutes_eload_log_ts', 'logger.minutes_ebat_log_ts', 'logger.minutes_temp_bat_log_ts',
                     'logger.minutes_eac3_log_ts', 'logger.minutes_temp_log_ts']
        # the prefix is cut from the front of individual oid_names to produce the name (the end is cut off, too)
        name_prefix = 'logger.minutes_'
        # one sample every 5 minutes
        timediff = relativedelta(minutes=5)
        # select whole days when not querying the current day
        if day_before_today > 0:
            # lowest timestamp that's of interest
            ts_start = (now - timedelta(days=day_before_today)).replace(hour=0, minute=0, second=0, microsecond=0)
            # highest timestamp, we stop when this is reached
            ts_end = ts_start.replace(hour=23, minute=59, second=59, microsecond=0)
        else:
            ts_start = ((now - (now - datetime.min) % timedelta(minutes=30)) - timedelta(hours=count)) \
                .replace(second=0, microsecond=0)
            ts_end = now.replace(second=59, microsecond=0)

    elif resolution == 'day':
        oid_names = ['logger.day_ea_log_ts', 'logger.day_eac_log_ts', 'logger.day_eb_log_ts',
                     'logger.day_eext_log_ts', 'logger.day_egrid_feed_log_ts', 'logger.day_egrid_load_log_ts',
                     'logger.day_eload_log_ts']
        name_prefix = 'logger.day_'
        # one sample every day
        timediff = relativedelta(days=1)
        # <count> days
        ts_start = (now - timedelta(days=day_before_today + count)) \
            .replace(hour=0, minute=59, second=59, microsecond=0)
        ts_end = (now - timedelta(days=day_before_today)).replace(hour=23, minute=59, second=59, microsecond=0)
    elif resolution == 'month':
        oid_names = ['logger.month_ea_log_ts', 'logger.month_eac_log_ts', 'logger.month_eb_log_ts',
                     'logger.month_eext_log_ts', 'logger.month_egrid_feed_log_ts', 'logger.month_egrid_load_log_ts',
                     'logger.month_eload_log_ts']
        name_prefix = 'logger.month_'
        # one sample per month
        timediff = relativedelta(months=1)
        # <count> months
        ts_start = (now - timedelta(days=day_before_today) - relativedelta(months=count)) \
            .replace(day=2, hour=0, minute=59, second=59, microsecond=0)
        if ts_start.year < 2000:
            ts_start = ts_start.replace(year=2000)
        ts_end = (now - timedelta(days=day_before_today)).replace(day=2, hour=23, minute=59, second=59, microsecond=0)
    elif resolution == 'year':
        oid_names = ['logger.year_ea_log_ts', 'logger.year_eac_log_ts', 'logger.year_eb_log_ts',
                     'logger.year_eext_log_ts', 'logger.year_egrid_feed_log_ts', 'logger.year_egrid_load_log_ts',
                     'logger.year_eload_log_ts']  # , 'logger.year_log_ts']
        name_prefix = 'logger.year_'
        # one sample per year
        timediff = relativedelta(years=1)
        # <count> years
        ts_start = (now - timedelta(days=day_before_today) - relativedelta(years=count)) \
            .replace(month=1, day=2, hour=0, minute=59, second=59, microsecond=0)
        ts_end = (now - timedelta(days=day_before_today)) \
            .replace(month=1, day=2, hour=23, minute=59, second=59, microsecond=0)
    else:
        cprint('Unsupported resolution')
        sys.exit(1)

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

    datetable: Dict[datetime, Dict[str, int]] = {dt: dict() for dt in datetime_range(ts_start, ts_end, timediff)}

    for oid in oids:
        name = oid.name.replace(name_prefix, '').replace('_log_ts', '')
        cprint(f'Requesting {name}')

        # set to true if the current time series reached its end, e.g. year 2000 for "year" resolution
        iter_end = False
        highest_ts = ts_end

        while highest_ts > ts_start and not iter_end:
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

                # Check if the timestamp fits the raster, adjust depending on the resolution
                if t_ts not in datetable:
                    if resolution == 'minutes':
                        # correct up to one full minute
                        nt_ts = t_ts.replace(second=0)
                        if nt_ts not in datetable:
                            nt_ts = t_ts.replace(second=0, minute=t_ts.minute + 1)
                            if nt_ts not in datetable:
                                cprint(f'\t{t_ts} does not fit raster, skipped')
                                continue
                        t_ts = nt_ts
                    elif resolution in ['day', 'month']:
                        # correct up to one hour
                        nt_ts = t_ts.replace(hour=0)
                        if nt_ts not in datetable:
                            nt_ts = t_ts.replace(hour=t_ts.hour + 1)
                            if nt_ts not in datetable:
                                cprint(f'\t{t_ts} does not fit raster, skipped')
                                continue
                        t_ts = nt_ts
                datetable[t_ts][name] = t_val

                # year statistics stop at 2000-01-02 00:59:59, so if the year hits 2000 we know we're done
                if resolution == 'year' and t_ts.year == 2000:
                    iter_end = True

    if output is None:
        output = f'data_{resolution}_{ts_start.isoformat("T")}.csv'

    if output == '-':
        fd = sys.stdout
    else:
        filedes, filepath = mkstemp(dir=os.path.dirname(output), text=True)
        fd = open(filedes, 'wt')

    writer = csv.writer(fd)

    names = [oid.name.replace(name_prefix, '').replace('_log_ts', '') for oid in oids]

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
    timeseries2csv()
