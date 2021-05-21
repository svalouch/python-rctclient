
'''
Command line interface implementation.
'''

# Copyright 2020, Peter Oberhofer (pob90)
# Copyright 2020-2021, Stefan Valouch (svalouch)
# SPDX-License-Identifier: GPL-3.0-only

import logging
import select
import socket
import sys
from datetime import datetime
from typing import List, Optional

try:
    import click
except ImportError:
    print('"click" not found, commands unavailable', file=sys.stderr)
    sys.exit(1)

from .exceptions import FrameCRCMismatch, FrameLengthExceeded, InvalidCommand
from .frame import ReceiveFrame, make_frame
from .registry import REGISTRY as R
from .simulator import run_simulator
from .types import Command, DataType
from .utils import decode_value, encode_value

log = logging.getLogger('rctclient.cli')


@click.group()
@click.pass_context
@click.version_option()
@click.option('-d', '--debug', is_flag=True, default=False, help='Enable debug output')
@click.option('--frame-debug', is_flag=True, default=False, help='Enables frame debugging (requires --debug)')
def cli(ctx, debug: bool, frame_debug: bool) -> None:
    '''
    rctclient toolbox. Please help yourself with the subcommands.
    '''
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug

    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        )
        if not frame_debug:
            logging.getLogger('rctclient.frame.ReceiveFrame').setLevel(logging.INFO)
    log.info('rctclient CLI starting')


def autocomplete_registry_name(_ctx, _args: List, incomplete: str) -> List[str]:
    '''
    Provides autocompletion for the object IDs name parameter.

    :param _ctx: Click context (ignored).
    :param _args: Arguments (ignored).
    :param incomplete: Incomplete (or empty) string from the user.
    :return: A list of names that either start with `incomplete` or all if `incomplete` is empty.
    '''
    return R.prefix_complete_name(incomplete)


def receive_frame(sock: socket.socket, timeout: int = 2) -> ReceiveFrame:
    '''
    Receives a frame from a socket.

    :param sock: The socket to receive from.
    :param timeout: Receive timeout in seconds.
    :returns: The received frame.
    :raises TimeoutError: If the timeout expired.
    '''
    frame = ReceiveFrame()
    while True:
        try:
            ready_read, _, _ = select.select([sock], [], [], timeout)
        except select.error as exc:
            log.error('Error during receive: select returned an error: %s', str(exc))
            raise

        if ready_read:
            buf = sock.recv(1024)
            if len(buf) > 0:
                log.debug('Received %d bytes: %s', len(buf), buf.hex())
                i = frame.consume(buf)
                log.debug('Frame consumed %d bytes', i)
                if frame.complete():
                    if len(buf) > i:
                        log.warning('Frame complete, but buffer still contains %d bytes', len(buf) - i)
                        log.debug('Leftover bytes: %s', buf[i:].hex())
                    return frame
    raise TimeoutError


@cli.command('read-value')
@click.pass_context
@click.option('-p', '--port', default=8899, type=click.INT, help='Port at which the device listens, default 8899',
              metavar='<port>')
@click.option('-h', '--host', required=True, type=click.STRING, help='Host address or IP of the device',
              metavar='<host>')
@click.option('-i', '--id', type=click.STRING, help='Object ID to query, of the form "0xXXXX"', metavar='<ID>')
@click.option('-n', '--name', help='Object name to query', type=click.STRING, metavar='<name>',
              autocompletion=autocomplete_registry_name)
@click.option('-v', '--verbose', is_flag=True, default=False, help='Enable verbose output')
def read_value(ctx, port: int, host: str, id: Optional[str], name: Optional[str], verbose: bool) -> None:
    '''
    Sends a read request. The request is sent to the target "<host>" on the given "<port>" (default: 8899), the
    response is returned on stdout. Without "verbose" set, the value is returned on standard out, otherwise more
    information about the object is printed with the value.

    Specify either "--id <id>" or "--name <name>". The ID must be in th decimal notation, such as "0x959930BF", the
    name must exactly match the name of a known object ID such as "battery.soc".

    The "<name>" option supports shell autocompletion (if installed).

    If "--debug" is set, log output is sent to stderr, so the value can be read from stdout while still catching
    everything else on stderr.

    Timeseries data and the event table will be queried using the current time. Note that the device may send an
    arbitrary amount of data. For time series data, The output will be a list of "timestamp=value" pairs separated by a
    comma, the timestamps are in isoformat, and they are not altered or timezone-corrected but passed from the device
    as-is. Likewise for event table entries, but their values are printed in hexadecimal.

    Examples:

    \b
    rctclient read-value --host 192.168.0.1 --name temperature.sink_temp_power_reduction
    rctclient read-value --host 192.168.0.1 --id 0x90B53336
    \f
    :param ctx: Click context
    :param port: The port number.
    :param host: The hostname or IP address, passed to ``socket.connect``.
    :param id: The ID to query. Mutually exclusive with `name`.
    :param name: The name to query. Mutually exclusive with `id`.
    :param verbose: Prints more information if `True`, or just the value if `False`.
    '''
    if (id is None and name is None) or (id is not None and name is not None):
        log.error('Please specify either --id or --name', err=True)
        sys.exit(1)

    try:
        if id:
            real_id = int(id[2:], 16)
            log.debug('Parsed ID: 0x%X', real_id)
            oinfo = R.get_by_id(real_id)
            log.debug('Object info by ID: %s', oinfo)
        elif name:
            oinfo = R.get_by_name(name)
            log.debug('Object info by name: %s', oinfo)
    except KeyError:
        log.error('Could not find requested id or name')
        sys.exit(1)
    except ValueError as exc:
        log.debug('Invalid --id parameter: %s', str(exc))
        log.error('Invalid --id parameter, can\'t parse', err=True)
        sys.exit(1)

    log.debug('Connecting to host')
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        log.debug('Connected to %s:%d', host, port)
    except socket.error as exc:
        log.error('Could not connect to host: %s', str(exc))
        sys.exit(1)

    is_ts = oinfo.response_data_type == DataType.TIMESERIES
    is_ev = oinfo.response_data_type == DataType.EVENT_TABLE
    if is_ts or is_ev:
        sock.send(make_frame(command=Command.WRITE, id=oinfo.object_id,
                             payload=encode_value(DataType.INT32, int(datetime.now().timestamp()))))
    else:
        sock.send(make_frame(command=Command.READ, id=oinfo.object_id))
    try:
        rframe = receive_frame(sock)
    except FrameCRCMismatch as exc:
        log.error('Received frame CRC mismatch: received 0x%X but calculated 0x%X',
                  exc.received_crc, exc.calculated_crc)
        sys.exit(1)
    except InvalidCommand:
        log.error('Received an unexpected/invalid command in response')
        sys.exit(1)
    except FrameLengthExceeded:
        log.error('Parser overshot, cannot recover frame')
        sys.exit(1)

    log.debug('Got frame: %s', rframe)
    if rframe.id != oinfo.object_id:
        log.error('Received unexpected frame, ID is 0x%X, expected 0x%X', rframe.id, oinfo.object_id)
        sys.exit(1)

    if is_ts or is_ev:
        _, table = decode_value(oinfo.response_data_type, rframe.data)
        if is_ts:
            value = ', '.join({f'{k:%Y-%m-%dT%H:%M:%S}={v:.4f}' for k, v in table.items()})
        else:
            value = ''
            for entry in table.values():
                e2 = f'0x{entry.element2:x}' if entry.element2 is not None else ''
                e3 = f'0x{entry.element3:x}' if entry.element3 is not None else ''
                e4 = f'0x{entry.element4:x}' if entry.element4 is not None else ''
                value += f'0x{entry.entry_type:x},{entry.timestamp:%Y-%m-%dT%H:%M:%S},{e2},{e3},{e4}\n'
    else:
        # hexdump if the data type is now known
        if oinfo.response_data_type == DataType.UNKNOWN:
            value = '0x' + rframe.data.hex()
        else:
            value = decode_value(oinfo.response_data_type, rframe.data)

    if verbose:
        description = oinfo.description if oinfo.description is not None else ''
        unit = oinfo.unit if oinfo.unit is not None else ''
        click.echo(f'#{oinfo.index:3} 0x{oinfo.object_id:8X} {oinfo.name:{R.name_max_length()}} '
                   f'{description:75} {value} {unit}')
    else:
        click.echo(f'{value}')

    try:
        sock.close()
    except Exception as exc:  # pylint: disable=broad-except
        log.error('Exception when disconnecting from the host: %s', str(exc))
    sys.exit(0)


@cli.command('simulator')
@click.pass_context
@click.option('-p', '--port', default=8899, type=click.INT, help='Port to bind the simulator to, defaults to 8899',
              metavar='<port>')
@click.option('-h', '--host', default='localhost', type=click.STRING, help='IP to bind the simulator to, defaults to '
              'localhost', metavar='<host>')
@click.option('-v', '--verbose', is_flag=True, default=False, help='Enable verbose output')
def simulator(ctx, port: int, host: str, verbose: bool) -> None:
    '''
    Starts the simulator. The simulator returns valid, but useless responses to queries. It binds to the address and
    port passed using "<host>" (default: localhost) and "<port>" (default: 8899) and allows up to five concurrent
    clients.

    The response values (for read queries) is read from the information associated with the queried object ID if set,
    else a sensible default value (such as 0, False or dummy strings) is computed based on the response data type of
    the object ID.
    \f
    :param port: The port to bind to, defaults to 8899.
    :param host: The address to bind to, defaults to localhost.
    :param verbose: Enables verbose output.
    '''
    if not ctx.obj['DEBUG'] and verbose:
        logging.basicConfig(level=logging.INFO)

    run_simulator(host=host, port=port, verbose=verbose)
