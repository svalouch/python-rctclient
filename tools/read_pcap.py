#!/usr/bin/env python3

'''
PCAP reader. This tool reads a pcap file (first and only argument) and parses the payload and presents the result. This
is a debugging tool. As with the rest of the software, this tool comes with no warranty etc. whatsoever, use at your
own risk.
'''

import struct
import sys
from scapy.utils import rdpcap  # type: ignore
from scapy.layers.inet import TCP  # type: ignore
from rctclient.frame import ReceiveFrame, FrameCRCMismatch
from rctclient.registry import REGISTRY as R
from rctclient.types import Command
from rctclient.utils import decode_value


def main():
    packets = rdpcap(sys.argv[1])

    streams = dict()

    i = 0
    pl = b''
    for name, stream in packets.sessions().items():
        print(f'Stream {i:4} {name} {stream} ', end='')
        length = 0
        streams[i] = dict()
        for k in stream:
            if TCP in k:
                if len(k[TCP].payload) > 0:
                    if k[TCP].sport == 8899 or k[TCP].dport == 8899:
                        payload = bytes(k[TCP].payload)

                        # skip AT+ keepalive and app serial "protocol switch"
                        if payload == b'AT+\r' or payload == bytearray.fromhex('2b3ce1'):
                            continue
                        ptime = float(k.time)
                        if ptime not in streams[i]:
                            streams[i][ptime] = b''
                        streams[i][ptime] += payload
                        length += len(payload)
        print(f'{length} bytes')
        i += 1

    frame = None
    for _, data in streams.items():

        for ts, pl in data.items():

            while len(pl) > 0:
                if not frame:
                    frame = ReceiveFrame()
                try:
                    i = frame.consume(pl)
                except FrameCRCMismatch as exc:
                    if frame.command == Command.EXTENSION:
                        print('Frame is an extension frame and we don\'t know how to parse it')
                    else:
                        print(f'Frame {frame.id} CRC mismatch, got 0x{exc.received_crc:X} but calculated '
                              f'0x{exc.calculated_crc:X}. Buffer: {frame._buffer.hex()}')
                    print(pl[0:2].hex())
                    if pl[0:2] == bytearray.fromhex('002b'):
                        i = 2
                    else:
                        i = exc.consumed_bytes
                pl = pl[i:]
                print(f'frame consumed {i} bytes, {len(pl)} remaining')
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
                            print(f'Received read : {rid.index:4} {rid.name:40}')
                        else:
                            if frame.command in [Command.RESPONSE, Command.LONG_RESPONSE]:
                                dtype = rid.response_data_type
                            else:
                                dtype = rid.request_data_type
                            try:
                                value = decode_value(dtype, frame.data)
                            except struct.error as exc:
                                print(f'Could not decode value: {str(exc)}')
                                print(f'Received reply: {rid.index:4} {rid.name:40} type: {dtype.name:17} value: '
                                      'UNKNOWN')
                            except UnicodeDecodeError as exc:
                                print(f'Could not decode value: {str(exc)}')
                                print(f'Received reply: {rid.index:4} {rid.name:40} type: {dtype.name:17} value: '
                                      'UNKNOWN')
                            else:
                                print(f'Received reply: {rid.index:4} {rid.name:40} type: {dtype.name:17} value: '
                                      f'{value}')
                    frame = None


if __name__ == '__main__':
    main()
