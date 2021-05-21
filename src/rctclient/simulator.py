
# Copyright 2020, Peter Oberhofer (pob90)
# Copyright 2020, Stefan Valouch (svalouch)
# SPDX-License-Identifier: GPL-3.0-only

import logging
import select
import socket
import threading

from .exceptions import FrameCRCMismatch
from .frame import ReceiveFrame, SendFrame
from .registry import REGISTRY as R
from .types import Command
from .utils import decode_value, encode_value


def run_simulator(host: str, port: int, verbose: bool) -> None:
    '''
    Starts the simulator. The simulator will bind to `host:port` and allow up to 5 concurrent clients to connect. Each
    client connection is handled in a thread. The function is intended to be run from a terminal and stopped by sending
    a keyboard interrupt (Ctrl+c). It runs forever until interrupted.
    '''

    log = logging.getLogger('rctclient.simulator')
    try:
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind((host, port))
        serversocket.listen(5)
    except socket.error as e:
        log.error(f'Unable to bind to {host}:{port}: {str(e)}')
        serversocket.close()
        raise

    log.info('Waiting for client connections')
    try:
        while True:
            connection, address = serversocket.accept()
            msg = f'connection accepted: {connection} {address}'
            if verbose:
                log.info(msg)
            else:
                log.debug(msg)

            # Start a new thread and return its identifier
            threading.Thread(target=socket_thread, args=(connection, address), daemon=True).start()
    except KeyboardInterrupt:
        msg = 'Keyboard interrupt, shutting down'
        if verbose:
            log.info(msg)
        else:
            log.debug(msg)

    serversocket.close()


def socket_thread(connection, address) -> None:
    log = logging.getLogger(f'rctclient.simulator.socket_thread.{address[1]}')
    frame = ReceiveFrame()
    while True:
        try:
            ready_read, _, _ = select.select([connection], [], [], 1000.0)
        except select.error as e:
            log.error(f'Error during select call: {str(e)}')
            break

        if ready_read:
            # read up to 4k bytes in one chunk
            buf = connection.recv(4096)
            if len(buf) > 0:
                log.debug(f'Read {len(buf)} bytes: {buf.hex()}')
                consumed = 0
                while consumed < len(buf):
                    try:
                        i = frame.consume(buf)
                    except FrameCRCMismatch as exc:
                        log.warning(f'Discard frame with wrong CRC checksum. Got 0x{exc.received_crc:x}, calculated '
                                    f'0x{exc.calculated_crc:x}, consumed {exc.consumed_bytes} bytes')
                        log.warning(f'Frame data: {frame.data.hex()}')
                        consumed += exc.consumed_bytes
                        frame = ReceiveFrame()
                    else:
                        log.debug(f'Frame consumed {i} bytes')
                        consumed += i
                        if frame.complete():
                            log.debug(f'Complete frame: {frame}')
                            try:
                                send_sim_response(connection, frame, log)
                            except Exception as exc:
                                log.warning(f'Caught {type(exc)} during send_sim_response: {str(exc)}')

                            frame = ReceiveFrame()
                    buf = buf[consumed:]
            else:
                break

    connection.close()
    log.debug(f'Closing connection {connection}')


def send_sim_response(connection, frame: ReceiveFrame, log: logging.Logger) -> None:
    oinfo = R.get_by_id(frame.id)

    if frame.command == Command.READ:
        payload = encode_value(oinfo.response_data_type, oinfo.sim_data)
        sframe = SendFrame(command=Command.RESPONSE, id=frame.id, address=frame.address, payload=payload)
        log.info(f'Read   : 0x{oinfo.object_id:08X} {oinfo.name:{R.name_max_length()}} -> {sframe.data.hex()}')
        log.debug(f'Sending frame {sframe} with {len(sframe.data)} bytes 0x{sframe.data.hex()}')
        connection.send(sframe.data)

    elif frame.command == Command.WRITE:
        value = decode_value(oinfo.request_data_type, frame.data)
        log.info(f'Write  : #{oinfo.index:3} 0x{oinfo.object_id:08X} {oinfo.name:{R.name_max_length()}} '
                 f'-> {value}')

        # TODO send response

    elif frame.command == Command.LONG_WRITE:
        value = decode_value(oinfo.request_data_type, frame.data)
        log.info(f'Write L: #{oinfo.index:3} 0x{oinfo.object_id:08X} {oinfo.name:{R.name_max_length()}} '
                 f'-> {value}')

        # TODO send response
