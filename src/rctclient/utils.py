
# Copyright 2020, Peter Oberhofer (pob90)
# Copyright 2020-2021, Stefan Valouch (svalouch)
# SPDX-License-Identifier: GPL-3.0-only

import struct
from datetime import datetime
from typing import overload, Dict, Tuple, Union

try:
    # Python 3.8+
    from typing import Literal
except ImportError:
    # Python < 3.8
    from typing_extensions import Literal

from .types import DataType, EventEntry


# pylint: disable=invalid-name
def CRC16(data: Union[bytes, bytearray]) -> int:
    '''
    Calculates the CRC16 checksum of data. Note that this automatically skips the first byte (start token) if the
    length is uneven.
    '''
    crcsum = 0xFFFF
    polynom = 0x1021  # CCITT Polynom
    buffer = bytearray(data)

    # skip start token
    if len(data) & 0x01:
        buffer.append(0)

    for byte in buffer:
        crcsum ^= byte << 8
        for _bit in range(8):
            crcsum <<= 1
            if crcsum & 0x7FFF0000:
                # ~~ overflow in bit 16
                crcsum = (crcsum & 0x0000FFFF) ^ polynom
    return crcsum


@overload
def encode_value(data_type: Literal[DataType.BOOL], value: bool) -> bytes:
    ...


@overload
def encode_value(data_type: Union[Literal[DataType.INT8], Literal[DataType.UINT8], Literal[DataType.INT16],
                                  Literal[DataType.UINT16], Literal[DataType.INT32], Literal[DataType.UINT32],
                                  Literal[DataType.ENUM]], value: int) -> bytes:
    ...


@overload
def encode_value(data_type: Literal[DataType.FLOAT], value: float) -> bytes:
    ...


@overload
def encode_value(data_type: Literal[DataType.STRING], value: Union[str, bytes]) -> bytes:
    ...


# pylint: disable=too-many-branches,too-many-return-statements
def encode_value(data_type: DataType, value: Union[bool, bytes, float, int, str]) -> bytes:
    '''
    Encodes a value suitable for transmitting as payload to the device. The actual encoding depends on the `data_type`.

    :param data_type: Data type of the `value` to be encoded. This selects the encoding mechanism.
    :param value: Data to be encoded according to the `data_type`.
    :return: The encoded value.
    :raises struct.error: If the packing failed, usually when the input value can't be encoded using the selected type.
    :raises ValueError: For string values, if the data type is not ``str`` or ``bytes``.
    '''
    if data_type == DataType.BOOL:
        return struct.pack('>B', bool(value))
    if data_type in (DataType.UINT8, DataType.ENUM):
        value = struct.unpack('<B', struct.pack('<b', value))[0]
        return struct.pack(">B", value)
    if data_type == DataType.INT8:
        return struct.pack(">b", value)
    if data_type == DataType.UINT16:
        value = struct.unpack('<H', struct.pack('<h', value))[0]
        return struct.pack(">H", value)
    if data_type == DataType.INT16:
        return struct.pack(">h", value)
    if data_type == DataType.UINT32:
        value = struct.unpack('<I', struct.pack('<i', value))[0]
        return struct.pack(">I", value)
    if data_type == DataType.INT32:
        return struct.pack(">i", value)
    if data_type == DataType.FLOAT:
        return struct.pack(">f", value)
    if data_type == DataType.STRING:
        if isinstance(value, str):
            return value.encode('utf-8')
        if isinstance(value, bytes):
            return value
        raise ValueError(f'Invalid value of type {type(value)} for string type encoding')
        # return struct.pack("s", value)
    raise KeyError('Undefinded or unknown type')


@overload
def decode_value(data_type: Literal[DataType.BOOL], data: bytes) -> bool:
    ...


@overload
def decode_value(data_type: Union[Literal[DataType.INT8], Literal[DataType.UINT8], Literal[DataType.INT16],
                                  Literal[DataType.UINT16], Literal[DataType.INT32], Literal[DataType.UINT32],
                                  Literal[DataType.ENUM]], data: bytes) -> int:
    ...


@overload
def decode_value(data_type: Literal[DataType.FLOAT], data: bytes) -> float:
    ...


@overload
def decode_value(data_type: Literal[DataType.STRING], data: bytes) -> str:
    ...


@overload
def decode_value(data_type: Literal[DataType.TIMESERIES], data: bytes) -> Tuple[datetime, Dict[datetime, int]]:
    ...


@overload
def decode_value(data_type: Literal[DataType.EVENT_TABLE], data: bytes) -> Tuple[datetime, Dict[datetime, EventEntry]]:
    ...


# pylint: disable=too-many-branches,too-many-return-statements
def decode_value(data_type: DataType, data: bytes) -> Union[bool, bytes, float, int, str,
                                                            Tuple[datetime, Dict[datetime, int]],
                                                            Tuple[datetime, Dict[datetime, EventEntry]]]:
    '''
    Decodes a value received from the device.

    .. note::

       Values for a message id may be decoded using a different type than was used for encoding. For example, the
       logger history writes a unix timestamp and receives a timeseries data structure.

    :param data_type: Data type of the `value` to be decoded. This selects the decoding mechanism.
    :param value: The value to be decoded.
    :return: The decoded value, depending on the `data_type`.
    :raises struct.error: If decoding of native types failed.
    '''
    if data_type == DataType.BOOL:
        value = struct.unpack(">B", data)[0]
        if value != 0:
            return True
        return False
    if data_type in (DataType.UINT8, DataType.ENUM):
        return struct.unpack(">B", data)[0]
    if data_type == DataType.INT8:
        return struct.unpack(">b", data)[0]
    if data_type == DataType.UINT16:
        return struct.unpack(">H", data)[0]
    if data_type == DataType.INT16:
        return struct.unpack(">h", data)[0]
    if data_type == DataType.UINT32:
        return struct.unpack(">I", data)[0]
    if data_type == DataType.INT32:
        return struct.unpack(">i", data)[0]
    if data_type == DataType.FLOAT:
        return struct.unpack(">f", data)[0]
    if data_type == DataType.STRING:
        pos = data.find(0x00)
        if pos == -1:
            return data.decode('ascii')
        return data[0:pos].decode('ascii')
    if data_type == DataType.TIMESERIES:
        return _decode_timeseries(data)
    if data_type == DataType.EVENT_TABLE:
        return _decode_event_table(data)
    raise KeyError(f'Undefined or unknown type {data_type}')


def _decode_timeseries(data: bytes) -> Tuple[datetime, Dict[datetime, int]]:
    '''
    Helper function to decode the timeseries type.
    '''
    timestamp = datetime.fromtimestamp(struct.unpack('>I', data[0:4])[0])
    tsval: Dict[datetime, int] = dict()
    assert len(data) % 4 == 0, 'Data should be divisible by 4'
    assert int(len(data) / 4 % 2) == 1, 'Data should be an even number of 4-byte pairs plus the starting timestamp'
    for pair in range(0, int(len(data) / 4 - 1), 2):
        pair_ts = datetime.fromtimestamp(struct.unpack('>I', data[4 + pair * 4:4 + pair * 4 + 4])[0])
        pair_val = struct.unpack('>f', data[4 + pair * 4 + 4:4 + pair * 4 + 4 + 4])[0]
        tsval[pair_ts] = pair_val
    return timestamp, tsval


def _decode_event_table(data: bytes) -> Tuple[datetime, Dict[datetime, EventEntry]]:
    '''
    Helper function to decode the event table type.
    '''
    timestamp = datetime.fromtimestamp(struct.unpack('>I', data[0:4])[0])
    tabval: Dict[datetime, EventEntry] = dict()
    assert len(data) % 4 == 0
    assert (len(data) - 4) % 20 == 0
    for pair in range(0, int(len(data) / 4 - 1), 5):
        # this is most likely a single byte of information, but this is not sure yet
        # entry_type = bytes([struct.unpack('>I', data[4 + pair * 4:4 + pair * 4 + 4])[0]]).decode('ascii')
        entry_type = struct.unpack('>I', data[4 + pair * 4:4 + pair * 4 + 4])[0]
        timestamp = datetime.fromtimestamp(struct.unpack('>I', data[4 + pair * 4 + 4:4 + pair * 4 + 8])[0])
        element2 = struct.unpack('>I', data[4 + pair * 4 + 8:4 + pair * 4 + 12])[0]
        element3 = struct.unpack('>I', data[4 + pair * 4 + 12:4 + pair * 4 + 16])[0]
        element4 = struct.unpack('>I', data[4 + pair * 4 + 16:4 + pair * 4 + 20])[0]
        tabval[timestamp] = EventEntry(entry_type=entry_type, timestamp=timestamp, element2=element2, element3=element3,
                                       element4=element4)
        # these two are known to contain object IDs
        # if entry_type in ['s', 'w']:
        #     object_id = struct.unpack('>I', data[4 + pair * 4 + 8:4 + pair * 4 + 12])[0]
        #     value_old = struct.unpack('>I', data[4 + pair * 4 + 12:4 + pair * 4 + 16])[0]
        #     value_new = struct.unpack('>I', data[4 + pair * 4 + 16:4 + pair * 4 + 20])[0]
        #     tabval[timestamp] = EventEntry(timestamp=timestamp, object_id=object_id, entry_type=entry_type,
        #                                    value_old=value_old, value_new=value_new)
        # the rest is assumed to be range-based events
        # else:
        #     timestamp_end = datetime.fromtimestamp(
        #         struct.unpack('>I', data[4 + pair * 4 + 12:4 + pair * 4 + 16])[0])
        #     object_id = struct.unpack('>I', data[4 + pair * 4 + 16:4 + pair * 4 + 20])[0]
        #     tabval[timestamp] = EventEntry(timestamp=timestamp, object_id=object_id, entry_type=entry_type,
        #                                    timestamp_end=timestamp_end)
    return timestamp, tabval
