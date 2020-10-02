
# Copyright 2020, Peter Oberhofer (pob90)
# Copyright 2020, Stefan Valouch (svalouch)
# SPDX-License-Identifier: GPL-3.0-only

class RctClientException(Exception):
    '''
    Base exception for this Python module.
    '''
    pass


class FrameError(RctClientException):
    '''
    Base exception for frame handling code.
    '''
    pass


class FrameNotComplete(FrameError):
    '''
    Used to denote that data was requested before the frame was completly received / parsed.
    '''
    pass


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
