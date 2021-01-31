
'''
Tests the bytecode generator.
Identical tests are done for the SendFrame class in test_sendframe.py.
'''

import struct
import pytest
from rctclient.frame import make_frame
from rctclient.types import Command

# pylint: disable=no-self-use
# TODO: escape sequences


class TestBytecodeGenerator:
    '''
    Tests for the bytecode generator.
    '''

    @pytest.mark.parametrize('id_in,data_out', [(0x0, '2b0204000000000c56'), (0xc0de, '2b02040000c0de30b1'),
                                                (0xffffffff, '2b0204ffffffff9599')])
    def test_write_standard_nopayload(self, id_in: int, data_out: str) -> None:
        '''
        Tests the encoding of various write commands without payload.
        '''
        assert make_frame(Command.WRITE, id_in) == bytearray.fromhex(data_out)

    @pytest.mark.parametrize('id_in,data_out', [(0x00, '2b010400000000c2b6'), (0xc0de, '2b01040000c0defe51'),
                                                (0xffffffff, '2b0104ffffffff5b79')])
    def test_read_standard_nopayload(self, id_in: int, data_out: str) -> None:
        '''
        Create a SendFrame and encode various read commands without payload.
        '''
        assert make_frame(Command.READ, id_in) == bytearray.fromhex(data_out)

    @pytest.mark.parametrize('id_in,data_out', [(0x00, '2b06000400000000b754'), (0xc0de, '2b0600040000c0dea78b'),
                                                (0xffffffff, '2b060004ffffffff6ac4')])
    def test_longresponse_standard_nopayload(self, id_in: int, data_out: str) -> None:
        '''
        Create a SendFrame and encode various long response commands without payload.
        '''
        assert make_frame(Command.LONG_RESPONSE, id_in) == bytearray.fromhex(data_out)

    @pytest.mark.parametrize('id_in,data_out', [(0x00, '2b050400000000c417'), (0xc0de, '2b05040000c0def8f0'),
                                                (0xffffffff, '2b0504ffffffff5dd8')])
    def test_response_standard_nopayload(self, id_in: int, data_out: str) -> None:
        '''
        Create a SendFrame and encode various response commands without payload.
        '''
        assert make_frame(Command.RESPONSE, id_in) == bytearray.fromhex(data_out)

    def test_invalid_id_too_big(self):
        '''
        Passing in an ID that is too big (more than 4 bytes) should result in an error.
        '''
        with pytest.raises(struct.error):
            make_frame(Command.READ, 0xfffffffff)
