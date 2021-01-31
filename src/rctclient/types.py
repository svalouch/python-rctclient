
# Copyright 2020, Peter Oberhofer (pob90)
# Copyright 2020, Stefan Valouch (svalouch)
# SPDX-License-Identifier: GPL-3.0-only

# pylint: disable=too-many-arguments,too-few-public-methods

from datetime import datetime
from enum import IntEnum
from typing import Optional


class Command(IntEnum):
    '''
    Commands that can be used with :class:`~rctclient.frame.ReceiveFrame`, :func:`~rctclient.frame.make_frame` as well
    as :class:`~rctclient.frame.SendFrame`.
    '''
    #: Read command
    READ = 0x01
    #: Write command
    WRITE = 0x02
    #: Long write command
    LONG_WRITE = 0x03
    #: Response to a read or write command
    RESPONSE = 0x05
    #: Long response
    LONG_RESPONSE = 0x06
    #: Extension
    EXTENSION = 0x3c

    #: Sentinel, do not use
    _NONE = 0xff


class ObjectGroup(IntEnum):
    '''
    Grouping information for object IDs. The information is not used by the protocol and only provided to aid the user
    in using the software.
    '''
    RB485 = 0
    ENERGY = 1
    GRID_MON = 2
    TEMPERATURE = 3
    BATTERY = 4
    CS_NEG = 5
    HW_TEST = 6
    G_SYNC = 7
    LOGGER = 8
    WIFI = 9
    ADC = 10
    NET = 11
    ACC_CONV = 12
    DC_CONV = 13
    NSM = 14
    IO_BOARD = 15
    FLASH_RTC = 16
    POWER_MNG = 17
    BUF_V_CONTROL = 18
    DB = 19
    SWITCH_ON_BOARD = 20
    P_REC = 21
    MODBUS = 22
    BAT_MNG_STRUCT = 23
    ISO_STRUCT = 24
    GRID_LT = 25
    CAN_BUS = 26
    DISPLAY_STRUCT = 27
    FLASH_PARAM = 28
    FAULT = 29
    PRIM_SM = 30
    CS_MAP = 31
    LINE_MON = 32
    OTHERS = 33
    BATTERY_PLACEHOLDER = 34


class FrameType(IntEnum):
    '''
    Enumeration of supported frame types.
    '''
    #: Standard frame with an ID
    STANDARD = 4
    #: Plant frame with ID and address
    PLANT = 8


class DataType(IntEnum):
    '''
    Enumeration of types, used to select the correct structure when encoding for sending or decoding received data. See
    :func:`~rctclient.utils.decode_value` and :func:`~rctclient.utils.encode_value`.
    '''

    #: Unknown type, default. Do not use for encoding or decoding.
    UNKNOWN = 0
    #: Boolean data (true or false)
    BOOL = 1
    #: 8-bit unsigned integer
    UINT8 = 2
    #: 8-bit signed integer
    INT8 = 3
    #: 16-bit unsigned integer
    UINT16 = 4
    #: 16-bit signed integer
    INT16 = 5
    #: 32-bit unsigned integer
    UINT32 = 6
    #: 32-bit signed integer
    INT32 = 7
    #: Enum, will be handled like a 16-bit unsigned integer
    ENUM = 8
    #: Floating point number
    FLOAT = 9
    #: String (may contain `\0` padding).
    STRING = 10

    # user defined, usually composite datatypes

    #: Non-native type: Timeseries data consisting of a tuple of a timestamp for the record (usually the day) and a
    #: dict mapping values to timestamps. Can not be used for encoding.
    TIMESERIES = 20  # timestamp, [(timestamp, value), ...]
    #: Non-native: Event table entries consisting of a tuple of a timestamp for the record (usually the day) and a dict
    #: mapping values to timestamps. Can not be used for encoding.
    EVENT_TABLE = 21


class EventEntry:
    '''
    Entry in the error log table. The table consists of an `entry_type` that controls the rest of the structure.

    Not all of the entry types are known yet. Of the known ones:

    * ``s`` and ``w`` are single events, such as changing a value. The fields `value_old` and `value_new` contain the
      old and new value, specific to the ID of the data. Additionally, they contain the `object_id` of the object they
      describe. They do not contain a end timestamp.
    * All other types observed so far are ranges of events. In addition to the `timestamp` signaling the start of the
      event, they also set `timestamp_end` to signal the end of the event. They do not set `value_old`, `value_new` or
      `object_id` as they are not describing a object but an event. Some contain additional payload that is not yet
      extracted.

    :param entry_type: The type of the entry (see above).
    :param timestamp: Timestamp of the entry (start time unless ``s`` entry type).
    :param object_id: The ID of the object, for lookup in the registry.
    :param timestamp_end: For entry types ``R`` and ``T``, the end of the event, forming a time range.
    :param value_old: Old value before the event, for event type ``s``. Raw value, interpretation via the registry
       required.
    :param value_new: New value after the event, for event type ``s``.
    '''
    entry_type: str
    timestamp: datetime
    timestamp_end: Optional[datetime]
    object_id: int
    value_old: Optional[int]
    value_new: Optional[int]

    def __init__(self, entry_type: str, timestamp: datetime, object_id: int, timestamp_end: Optional[datetime] = None,
                 value_old: Optional[int] = None, value_new: Optional[int] = None) -> None:
        if entry_type not in ['c', 'd', 'k', 'O', 'P', 'r', 'R', 's', 'S', 'T', 'v', 'w', 'W', 'x', 'X', 'y', 'Y', 'Z']:
            raise ValueError(f'Entry type {entry_type} invalid')
        self.entry_type = entry_type
        self.timestamp = timestamp
        self.object_id = object_id

        self.value_old = value_old
        self.value_new = value_new
        self.timestamp_end = timestamp_end

        if entry_type in ['s', 'w']:
            if value_old is None or value_new is None:
                raise ValueError('old or new value must be set for entry type s')
            if timestamp_end is not None:
                raise ValueError('timestamp_end must not be set for entry type s')
        else:
            if value_old is not None or value_new is not None:
                raise ValueError(f'values old or new must not be set for entry type {entry_type}')
            if timestamp_end is None:
                raise ValueError(f'end timestamp must be set for entry type {entry_type}')

    def __repr__(self) -> str:
        return f'<EventEntry(type={self.entry_type}, ts={self.timestamp}, object_id={self.object_id:x})>'
