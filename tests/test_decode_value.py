
'''
Tests for decode_value.
'''

from datetime import UTC, datetime

import pytest
from rctclient.registry import REGISTRY as R
from rctclient.types import BatteryModuleResistance, BatteryModuleStatistics, BatteryModuleStatus, DataType
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

    def test_BATTERY_MODULE_STATUS_happy(self) -> None:
        '''
        Tests decoding of the battery module status payload.
        '''
        data = bytes.fromhex(
            '19 f6 0c 00 19 f6 0c 00 1a f6 0c 00 1a f7 0c 00 '
            '1a f6 0c 00 1a f6 0c 00 1b f6 0c 00 1a f7 0c 00 '
            '1b f7 0c 00 1b f6 0c 00 1b f6 0c 00 1b f6 0c 00 '
            '1c fd 0c 00 1b fd 0c 00 1c fd 0c 00 1b ff 0c 00 '
            '1b fd 0c 00 1b fd 0c 00 1b fd 0c 00 1a fd 0c 00 '
            '1a fd 0c 00 1a fd 0c 00 1a ff 0c 00 19 fd 0c 00'
        )

        result = decode_value(data_type=DataType.BATTERY_MODULE_STATUS, data=data)

        assert isinstance(result, BatteryModuleStatus)
        assert isinstance(result.cells, dict)
        assert set(result.cells.keys()) == set(range(24))
        assert len(result) == 24
        assert result[0].temperature_c == 25
        assert result[0].voltage_mv == 3318
        assert result[0].voltage_v == pytest.approx(3.318)
        assert result[0].status == 0
        assert result[15].temperature_c == 27
        assert result[15].voltage_mv == 3327
        assert result[23].temperature_c == 25
        assert result[23].voltage_mv == 3325

    def test_BATTERY_MODULE_STATUS_invalid_length(self) -> None:
        '''
        Tests that invalid battery module payload lengths are rejected.
        '''
        with pytest.raises(ValueError):
            decode_value(data_type=DataType.BATTERY_MODULE_STATUS, data=b'\x00' * 4)

    def test_BATTERY_MODULE_STATISTICS_happy(self) -> None:
        '''
        Tests decoding of the battery module statistics payload.
        '''
        data = bytes.fromhex('0000000046d25b6223db414000000000f163ab6619045e4000000000baeea065000090410e0000001ba4e26000002442')

        result = decode_value(data_type=DataType.BATTERY_MODULE_STATISTICS, data=data)

        assert isinstance(result, BatteryModuleStatistics)
        assert result.u_min.cell == 0
        assert result.u_min.timestamp == datetime.fromtimestamp(1650184774, UTC)
        assert result.u_min.value == pytest.approx(3.029)
        assert result.u_max.cell == 0
        assert result.u_max.timestamp == datetime.fromtimestamp(1722508273, UTC)
        assert result.u_max.value == pytest.approx(3.469)
        assert result.t_min.cell == 0
        assert result.t_min.timestamp == datetime.fromtimestamp(1705045690, UTC)
        assert result.t_min.value == pytest.approx(18.0)
        assert result.t_max.cell == 14
        assert result.t_max.timestamp == datetime.fromtimestamp(1625465883, UTC)
        assert result.t_max.value == pytest.approx(41.0)

    def test_BATTERY_MODULE_STATISTICS_invalid_length(self) -> None:
        '''
        Tests that invalid battery module statistics payload lengths are rejected.
        '''
        with pytest.raises(ValueError):
            decode_value(data_type=DataType.BATTERY_MODULE_STATISTICS, data=b'\x00' * 4)

    def test_BATTERY_MODULE_RESISTANCE_happy(self) -> None:
        '''
        Tests decoding of the battery module resistance payload.
        '''
        # payload from battery.cells_resist[0] with known correct values 1.3-2.4 mOhm
        data = bytes.fromhex(
            '01 fb 00 00 01 52 00 00 01 fb 00 00 01 fb 00 00 '
            '01 8a 00 00 01 fb 00 00 01 8a 00 00 01 8a 00 00 '
            '01 8a 00 00 01 fb 00 00 01 8a 00 00 01 c2 00 00 '
            '01 c2 00 00 01 52 00 00 02 6b 00 00 02 6b 00 00 '
            '01 8a 00 00 01 fb 00 00 01 fb 00 00 01 8a 00 00 '
            '01 c2 00 00 01 c2 00 00 01 fb 00 00 01 c2 00 00'
        )

        result = decode_value(data_type=DataType.BATTERY_MODULE_RESISTANCE, data=data)

        assert isinstance(result, BatteryModuleResistance)
        assert isinstance(result.cells, dict)
        assert set(result.cells.keys()) == set(range(24))
        assert len(result) == 24
        # cell 1: 0x0152 = 338 → 338/256 = 1.3203 mOhm
        assert result[1].raw_value == 0x0152
        assert result[1].resistance_mohm == pytest.approx(1.3203, abs=1e-4)
        # cell 0: 0x01FB = 507 → 507/256 = 1.9805 mOhm
        assert result[0].raw_value == 0x01FB
        assert result[0].resistance_mohm == pytest.approx(1.9805, abs=1e-4)
        # cell 14: 0x026B = 619 → 619/256 = 2.4180 mOhm
        assert result[14].raw_value == 0x026B
        assert result[14].resistance_mohm == pytest.approx(2.4180, abs=1e-4)

    def test_BATTERY_MODULE_RESISTANCE_invalid_length(self) -> None:
        '''
        Tests that invalid battery module resistance payload lengths are rejected.
        '''
        with pytest.raises(ValueError):
            decode_value(data_type=DataType.BATTERY_MODULE_RESISTANCE, data=b'\x00' * 4)

    @pytest.mark.parametrize(
        'name',
        [
            'battery.cells[0]',
            'battery.cells[1]',
            'battery.cells[2]',
            'battery.cells[3]',
            'battery.cells[4]',
            'battery.cells[5]',
            'battery.cells[6]',
        ],
    )
    def test_battery_cells_registry_uses_battery_module_status(self, name: str) -> None:
        '''
        Tests that battery.cells objects use the structured battery module status type.
        '''
        assert R.get_by_name(name).response_data_type == DataType.BATTERY_MODULE_STATUS

    @pytest.mark.parametrize(
        'name',
        [
            'battery.cells_stat[0]',
            'battery.cells_stat[1]',
            'battery.cells_stat[2]',
            'battery.cells_stat[3]',
            'battery.cells_stat[4]',
            'battery.cells_stat[5]',
            'battery.cells_stat[6]',
        ],
    )
    def test_battery_cells_stat_registry_uses_battery_module_statistics(self, name: str) -> None:
        '''
        Tests that battery.cells_stat objects use the structured battery module statistics type.
        '''
        assert R.get_by_name(name).response_data_type == DataType.BATTERY_MODULE_STATISTICS

    @pytest.mark.parametrize(
        'name',
        [
            'battery.cells_resist[0]',
            'battery.cells_resist[1]',
            'battery.cells_resist[2]',
            'battery.cells_resist[3]',
            'battery.cells_resist[4]',
            'battery.cells_resist[5]',
            'battery.cells_resist[6]',
        ],
    )
    def test_battery_cells_resist_registry_uses_battery_module_resistance(self, name: str) -> None:
        '''
        Tests that battery.cells_resist objects use the structured battery module resistance type.
        '''
        assert R.get_by_name(name).response_data_type == DataType.BATTERY_MODULE_RESISTANCE
