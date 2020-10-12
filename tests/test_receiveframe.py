
'''
Tests the ReceiveFrame class.
'''

import pytest
from rctclient.frame import ReceiveFrame
from rctclient.types import Command

# pylint: disable=no-self-use
# TODO: escape sequences


class TestReceiveFrame:
    '''
    Tests for ReceiveFrame.
    '''

    @pytest.mark.parametrize('data_in,result', [('2b0204000000000c56', {'cmd': Command.WRITE, 'id': 0x0}),
                                                ('2b02040000c0de30b1', {'cmd': Command.WRITE, 'id': 0xc0de}),
                                                ('2b0204ffffffff9599', {'cmd': Command.WRITE, 'id': 0xffffffff}),
                                                ('2b010400000000c2b6', {'cmd': Command.READ, 'id': 0x0}),
                                                ('2b01040000c0defe51', {'cmd': Command.READ, 'id': 0xc0de}),
                                                ('2b0104ffffffff5b79', {'cmd': Command.READ, 'id': 0xffffffff}),
                                                ('2b06000400000000b754', {'cmd': Command.LONG_RESPONSE, 'id': 0x0}),
                                                ('2b0600040000c0dea78b', {'cmd': Command.LONG_RESPONSE, 'id': 0xc0de}),
                                                ('2b060004ffffffff6ac4', {'cmd': Command.LONG_RESPONSE,
                                                                          'id': 0xffffffff}),
                                                ('2b050400000000c417', {'cmd': Command.RESPONSE, 'id': 0x0}),
                                                ('2b05040000c0def8f0', {'cmd': Command.RESPONSE, 'id': 0xc0de}),
                                                ('2b0504ffffffff5dd8', {'cmd': Command.RESPONSE, 'id': 0xffffffff}),
                                                ])
    def test_read_standard_nopayload(self, data_in: str, result: dict) -> None:
        '''
        Tests that payloadless data can be read.
        '''
        data = bytearray.fromhex(data_in)
        frame = ReceiveFrame()
        assert frame.consume(data) == len(data), 'The frame should consume all the data'
        assert frame.complete(), 'The frame should be complete'
        assert frame.command == result['cmd']
        assert frame.id == result['id']
        assert frame.address == 0, 'Standard frames have no address'
        assert frame.data == b'', 'No data was attached, so the shouldn\'t be any'

    def test_read_standard_int(self) -> None:
        '''
        Tests that a integer payload can be read. The data has a leading NULL byte, too. Response for
        `display_struct.brightness` from a real device.
        '''
        data = bytearray.fromhex('002b050529bda75fffb8d2')
        frame = ReceiveFrame()
        assert frame.consume(data) == len(data), 'The frame should consume all the data'
        assert frame.complete(), 'The frame should be complete'
        assert frame.command == Command.RESPONSE
        assert frame.id == 0x29bda75f
        assert frame.address == 0, 'Standard frames have no address'
        assert frame.data == b'\xff'

    def test_read_standard_string(self) -> None:
        '''
        Tests that a larger string can be read. Response for `android_name` from a real device.
        '''
        data = bytearray.fromhex('002b0544ebc62737505320362e30204241334c0000000000000000000000000000000000000000000000'
                                 '000000000000000000000000000000000000000000000000000000000000476c')
        frame = ReceiveFrame()
        assert frame.consume(data) == len(data), 'The frame should consume all the data'
        assert frame.complete(), 'The frame should be complete'
        assert frame.command == Command.RESPONSE
        assert frame.id == 0xebc62737
        assert frame.address == 0, 'Standard frames have no address'
        assert frame.data == bytearray.fromhex('505320362e30204241334c000000000000000000000000000000000000000000000000'
                                               '0000000000000000000000000000000000000000000000000000000000')
