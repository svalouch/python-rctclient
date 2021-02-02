#!/usr/bin/env python3

'''
Imports CSV histogram data from file to influxdb. Intended to be used on the output of timeseries2csv.py.
'''

# Copyright 2020-2021, Stefan Valouch (svalouch)
# SPDX-License-Identifier: GPL-3.0-only

import csv
import sys
from datetime import datetime, timedelta

import click
import requests
from influxdb import InfluxDBClient  # type: ignore

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
@click.option('-i', '--input', type=click.Path(readable=True, dir_okay=False, allow_dash=True), required=True,
              help='Input CSV file (with headers). Supply "-" to read from standard input')
@click.option('-n', '--device-name', type=str, default='rct1', help='Name of the device [rct1]')
@click.option('-h', '--influx-host', type=str, default='localhost', help='InfluxDB hostname [localhost]')
@click.option('-p', '--influx-port', type=int, default=8086, help='InfluxDB port [8086]')
@click.option('-d', '--influx-db', type=str, default='rct', help='InfluxDB database name [rct]')
@click.option('-u', '--influx-user', type=str, default='rct', help='InfluxDB user name [rct]')
@click.option('-P', '--influx-pass', type=str, default='rct', help='InfluxDB password [rct]')
@click.option('-r', '--resolution', type=click.Choice(['day', 'week', 'month', 'year']), default='day')
def csv2influxdb(input: str, device_name: str, influx_host: str, influx_port: int, influx_db: str,
                 influx_user: str, influx_pass: str, resolution: str) -> None:

    '''
    Reads a CSV file produced by `timeseries2csv.py` (requires headers) and pushes it to an InfluxDB database. This
    tool is intended to get you started and not a complete solution. It blindly trusts the timestamps and headers in
    the file.
    '''
    if input == '-':
        fin = sys.stdin
    else:
        fin = open(input, 'rt')
    reader = csv.DictReader(fin)

    influx = InfluxDBClient(host=influx_host, port=influx_port, username=influx_user, password=influx_pass,
                            database=influx_db)

    try:
        influx.ping()
    except requests.exceptions.ConnectionError as exc:
        click.echo(f'InfluxDB refused connection: {str(exc)}')
        sys.exit(2)

    points = []
    for row in reader:
        points.append({
            'measurement': f'history_{resolution}',
            'tags': {
                'rct': device_name,
            },
            'time': row.pop('timestamp'),
            'fields': {k: float(v) for k, v in row.items()},
        })

    if points:
        click.echo(f'Writing {len(points)} points')
        influx.write_points(time_precision='s', points=points)

    if input != '-':
        fin.close()


if __name__ == '__main__':
    csv2influxdb()
