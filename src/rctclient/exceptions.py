
# Copyright 2020, Peter Oberhofer (pob90)
# Copyright 2020, Stefan Valouch (svalouch)
# SPDX-License-Identifier: GPL-3.0-only

class RctClientException(Exception):
    '''
    Base exception for this Python module.
    '''


class FrameError(RctClientException):
    '''
    Base exception for frame handling code.
    '''


class FrameCRCMismatch(FrameError):
    '''
    Indicates that the CRC that was received did not match with the computed value.

    :param message: A message.
    :param received_crc: The CRC that was received with the frame.
    :param calculated_crc: The CRC that was calculated based on the received data.
    :param consumed_bytes: How many bytes were consumed.
    '''
    def __init__(self, message: str, received_crc: int, calculated_crc: int, consumed_bytes: int = 0) -> None:
        super().__init__(message)
        self.received_crc = received_crc
        self.calculated_crc = calculated_crc
        self.consumed_bytes = consumed_bytes


class InvalidCommand(FrameError):
    '''
    Indicates that the command is not supported. This means that ``Command`` does not contain a field for it, or that
    it is the EXTENSION command that cannot be handled.
    '''
    def __init__(self, message: str, command: int, consumed_bytes: int = 0) -> None:
        super().__init__(message)
        self.command = command
        self.consumed_bytes = consumed_bytes
