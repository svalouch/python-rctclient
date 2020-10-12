
'''
Tests for decode_value.
'''

import pytest
from rctclient.types import DataType
from rctclient.utils import decode_value

# pylint: disable=invalid-name,no-self-use


class TestDecodeValue:
    '''
    Tests for decode_value.
    '''

    @pytest.mark.parametrize('data_in,data_out', [(b'\x00', False), (b'\x01', True), (b'\x02', True),
                                                  (b'\xff', True)])
    def test_BOOL_happy(self, data_in: bytes, data_out: bool) -> None:
        '''
        Tests the boolean happy path.
        '''
        assert decode_value(data_type=DataType.BOOL, data=data_in) == data_out

    @pytest.mark.parametrize('data_in,data_out', [(b'\x00', 0), (b'\x01', 1), (b'\x02', 2), (b'\xff', 255)])
    def test_UINT8_happy(self, data_in: bytes, data_out: int) -> None:
        '''
        Tests the uint8 happy path.
        '''
        assert decode_value(data_type=DataType.UINT8, data=data_in) == data_out

    def test_STRING_happy_null(self) -> None:
        '''
        Tests that a NULL terminated string can be decoded.
        '''
        data = bytearray.fromhex('505320362e30204241334c00000000000000000000000000000000000000000000000000000000000000'
                                 '00000000000000000000000000000000000000000000')
        plain = 'PS 6.0 BA3L'
        result = decode_value(data_type=DataType.STRING, data=data)
        assert isinstance(result, str), 'The resulting type should be a string'
        assert result == plain

    def test_STRING_happy_nonull(self) -> None:
        '''
        Tests that a not NULL terminated string can be decoded.
        '''
        data = bytearray.fromhex('505320362e30204241334c')
        plain = 'PS 6.0 BA3L'
        result = decode_value(data_type=DataType.STRING, data=data)
        assert isinstance(result, str), 'The resulting type should be a string'
        assert result == plain
