
# Copyright 2020, Peter Oberhofer (pob90)
# Copyright 2020-2021, Stefan Valouch (svalouch)
# SPDX-License-Identifier: GPL-3.0-only

'''
Exceptions used by the module.
'''


class RctClientException(Exception):
    '''
    Base exception for this Python module.
    '''


class FrameError(RctClientException):
    '''
    Base exception for frame handling code.
    '''


class ReceiveFrameError(FrameError):
    '''
    Base exception for errors happening in  ReceiveFrame.

    :param message: A message describing the error.
    :param consumed_bytes: How many bytes were consumed.
    '''
    def __init__(self, message: str, consumed_bytes: int = 0) -> None:
        super().__init__(message)
        self.consumed_bytes = consumed_bytes


class FrameCRCMismatch(ReceiveFrameError):
    '''
    Indicates that the CRC that was received did not match with the computed value.

    :param received_crc: The CRC that was received with the frame.
    :param calculated_crc: The CRC that was calculated based on the received data.
    '''
    def __init__(self, message: str, received_crc: int, calculated_crc: int, consumed_bytes: int = 0) -> None:
        super().__init__(message)
        self.received_crc = received_crc
        self.calculated_crc = calculated_crc
        self.consumed_bytes = consumed_bytes


class InvalidCommand(ReceiveFrameError):
    '''
    Indicates that the command is not supported. This means that ``Command`` does not contain a field for it, or that
    it is the EXTENSION command that cannot be handled.

    :param command: The command byte.
    '''
    def __init__(self, message: str, command: int, consumed_bytes: int = 0) -> None:
        super().__init__(message)
        self.command = command
        self.consumed_bytes = consumed_bytes


class FrameLengthExceeded(ReceiveFrameError):
    '''
    Indicates that more data was consumed by ReceiveFrame than it should have. This usually indicates a bug in the
    parser code and should be reported.
    '''
