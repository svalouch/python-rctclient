
# Copyright 2020, Peter Oberhofer (pob90)
# Copyright 2020-2021, Stefan Valouch (svalouch)
# SPDX-License-Identifier: GPL-3.0-only

'''
Type declarations.
'''

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
    #: Long write command (use for variables > 251 bytes)
    LONG_WRITE = 0x03
    #: Response to a read or write command
    RESPONSE = 0x05
    #: Long response (for variables > 251 bytes)
    LONG_RESPONSE = 0x06
    # Periodic reading
    # READ_PERIODICALLY = 0x08

    #: Plant: Read command
    PLANT_READ = READ | 0x40
    #: Plant: Write command
    PLANT_WRITE = WRITE | 0x40
    #: Plant: Long write
    PLANT_LONG_WRITE = LONG_WRITE | 0x40

    #: Extension
    EXTENSION = 0x3c

    #: Sentinel, do not use
    _NONE = 0xff

    @staticmethod
    def is_plant(command: 'Command') -> bool:
        '''
        Returns whether a command is for plant communication by checking if bit 6 is set.
        '''
        return bool(command & 0x40)

    @staticmethod
    def is_long(command: 'Command') -> bool:
        '''
        Returns whether a command is a long command.
        '''
        return command in (Command.LONG_WRITE, Command.LONG_RESPONSE, Command.PLANT_LONG_WRITE)


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
    SWITCH_ON_COND = 20
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
    FRT = 35
    PARTITION = 36


class FrameType(IntEnum):
    '''
    Enumeration of supported frame types.
    '''
    #: Standard frame with an ID
    STANDARD = 4
    #: Plant frame with ID and address
    PLANT = 8

    #: Sentinel value, denotes unknown type.
    _NONE = 0


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

    # user defined, usually composite datatypes follow:

    #: Non-native type: Timeseries data consisting of a tuple of a timestamp for the record (usually the day) and a
    #: dict mapping values to timestamps. Can not be used for encoding.
    TIMESERIES = 20  # timestamp, [(timestamp, value), ...]
    #: Non-native: Event table entries consisting of a tuple of a timestamp for the record (usually the day) and a dict
    #: mapping values to timestamps. Can not be used for encoding.
    EVENT_TABLE = 21


class EventEntry:
    '''
    A single entry in the event table. An entry consists of a type, which controls the meaning of the other fields.

    .. note::

       Not a whole lot is known about the entries. Information (and this structure) may change in the future. The
       payload fields are stored as-is for now, as the information known to this date is too limited. Refer to the
       documentation for more information about the event table.

       Furthermore, the entry type is believed to be a single byte, so unless more information is known that changes
       this, the type is validated to be in the range 0-255.

    Each entry has a timestamp field that, depending on the type, either denotes the start time for a ranged event
    (such as the start of an error condition) or the precise time when the event occured (such as for a parameter
    change).

    The element-fields contain the raw value from the device. Use :func:`~rctclient.utils.decode_value` to decode them
    if the data type is known.

    :param entry_type: The type of the entry.
    :param timestamp: Timestamp of the entry (element1).
    :param element2: The second element of the entry.
    :param element3: The third element of the entry.
    :param element4: The fourth element of the entry.
    '''
    entry_type: int
    timestamp: datetime
    element2: Optional[bytes]
    element3: Optional[bytes]
    element4: Optional[bytes]

    def __init__(self, entry_type: int, timestamp: datetime, element2: Optional[bytes] = None,
                 element3: Optional[bytes] = None, element4: Optional[bytes] = None) -> None:
        if entry_type < 0 or entry_type > 0xff:
            raise ValueError(f'Entry type {entry_type} outside of range 0-255')
        self.entry_type = entry_type
        self.timestamp = timestamp
        self.element2 = element2
        self.element3 = element3
        self.element4 = element4

    def __repr__(self) -> str:
        return f'<EventEntry(type=0x{self.entry_type:x}, ts={self.timestamp})>'
