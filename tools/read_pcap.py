#!/usr/bin/env python3

'''
PCAP reader. This tool reads a pcap file (first and only argument) and parses the payload and presents the result. This
is a debugging tool. As with the rest of the software, this tool comes with no warranty etc. whatsoever, use at your
own risk.
'''

# the ugly truth about debugging tools:
# pylint: disable=too-many-statements,too-many-nested-blocks,too-many-branches,too-many-locals

import struct
import sys
from datetime import datetime
from scapy.utils import rdpcap  # type: ignore
from scapy.layers.inet import TCP  # type: ignore
from rctclient.exceptions import RctClientException, FrameCRCMismatch, InvalidCommand
from rctclient.frame import ReceiveFrame
from rctclient.registry import REGISTRY as R
from rctclient.types import Command, DataType
from rctclient.utils import decode_value


def main():
    ''' Main program '''
    packets = rdpcap(sys.argv[1])

    streams = dict()

    i = 0
    for name, stream in packets.sessions().items():
        print(f'Stream {i:4} {name} {stream} ', end='')
        length = 0
        streams[i] = dict()
        for k in stream:
            if TCP in k:
                if len(k[TCP].payload) > 0:
                    if k[TCP].sport == 8899 or k[TCP].dport == 8899:
                        payload = bytes(k[TCP].payload)

                        # skip AT+ keepalive and app serial "protocol switch" '2b3ce1'
                        if payload in [b'AT+\r', b'+<\xe1']:
                            continue
                        ptime = float(k.time)
                        if ptime not in streams[i]:
                            streams[i][ptime] = b''
                        streams[i][ptime] += payload
                        length += len(payload)
        print(f'{length} bytes')
        i += 1

    frame = None
    sid = 0
    for _, data in streams.items():
        print(f'\nNEW STREAM #{sid}\n')

        for timestamp, data_item in data.items():
            print(f'NEW INPUT: {datetime.fromtimestamp(timestamp):%Y-%m-%d %H:%M:%S.%f} | {data_item.hex()}')

            # frames should not cross segments (though it may be valid, but the devices haven't been observed doing
            # that). Sometimes, the device sends invalid data with a very high length field, causing the code to read
            # way byond the end of the actual data, causing it to miss frames until its length is satisfied. This way,
            # if the next segment starts with the typical 0x002b used by the devices, the current frame is dropped.
            # This way only on segment is lost.
            if frame and data_item[0:2] == b'\0+':
                print('Frame not complete at segment start, starting new frame.')
                print(f'command: {frame.command}, length: {frame.frame_length}, oid: 0x{frame.id:X}')
                frame = None

            while len(data_item) > 0:
                if not frame:
                    frame = ReceiveFrame()
                try:
                    i = frame.consume(data_item)
                except InvalidCommand as exc:
                    if frame.command == Command.EXTENSION:
                        print('Frame is an extension frame and we don\'t know how to parse it')
                    else:
                        print(f'Invalid command 0x{exc.command:x} received after consuming {exc.consumed_bytes} bytes')
                    i = exc.consumed_bytes
                except FrameCRCMismatch as exc:
                    print(f'CRC mismatch, got 0x{exc.received_crc:X} but calculated '
                          f'0x{exc.calculated_crc:X}. Buffer: {frame._buffer.hex()}')
                    i = exc.consumed_bytes
                except struct.error as exc:
                    print(f'skipping 2 bytes ahead as struct could not unpack: {str(exc)}')
                    i = 2
                    frame = ReceiveFrame()

                data_item = data_item[i:]
                print(f'frame consumed {i} bytes, {len(data_item)} remaining')
                if frame.complete():
                    if frame.id == 0:
                        print(f'Frame complete: {frame} Buffer: {frame._buffer.hex()}')
                    else:
                        print(f'Frame complete: {frame}')
                    try:
                        rid = R.get_by_id(frame.id)
                    except KeyError:
                        print('Could not find ID in registry')
                    else:
                        if frame.command == Command.READ:
                            print(f'Received read : {rid.name:40}')
                        else:
                            if frame.command in [Command.RESPONSE, Command.LONG_RESPONSE]:
                                dtype = rid.response_data_type
                            else:
                                dtype = rid.request_data_type
                            is_write = frame.command in [Command.WRITE, Command.LONG_WRITE]

                            try:
                                value = decode_value(dtype, frame.data)
                            except (struct.error, UnicodeDecodeError) as exc:
                                print(f'Could not decode value: {str(exc)}')
                                if is_write:
                                    print(f'Received write : {rid.name:40} type: {dtype.name:17} value: UNKNOWN')
                                else:
                                    print(f'Received reply : {rid.name:40} type: {dtype.name:17} value: UNKNOWN')
                            except KeyError:
                                print('Could not decode unknown type')
                                if is_write:
                                    print(f'Received write : {rid.name:40} value: 0x{frame.data.hex()}')
                                else:
                                    print(f'Received reply : {rid.name:40} value: 0x{frame.data.hex()}')
                            else:
                                if dtype == DataType.ENUM:
                                    try:
                                        value = rid.enum_str(value)
                                    except RctClientException as exc:
                                        print(f'ENUM mapping failed: {str(exc)}')
                                    except KeyError:
                                        print('ENUM value out of bounds')
                                if is_write:
                                    print(f'Received write : {rid.name:40} type: {dtype.name:17} value: {value}')
                                else:
                                    print(f'Received reply : {rid.name:40} type: {dtype.name:17} value: {value}')
                    frame = None
                    print()
            print('END OF INPUT-SEGMENT')
        sid += 1


if __name__ == '__main__':
    main()
