
# Copyright 2020, Peter Oberhofer (pob90)
# Copyright 2020-2021, Stefan Valouch (svalouch)
# SPDX-License-Identifier: GPL-3.0-only

# pylint: disable=line-too-long

'''
Dataset defining the values and names to conveniently use the system.
'''

from typing import Any, Dict, List, Optional

from .exceptions import RctClientException
from .types import ObjectGroup, DataType


class ObjectInfo:
    '''
    Information about an object that can be sent to or received from the device. It describes a single object ID and
    adds more information to it. Some of this information is required to interact with the device (receive and send
    data type), while other bits are purely to aid the user when using the structures.

    It is in concept similar to SNMP OIDs or their MIB information respectively, in that it describes an object ID.

    Each instance of this class describes a single object ID. When interacting with the device, the object ID is used
    to target the information that should be returned (read command) or changed (write command). Data received from or
    sent to the device needs to be decoded or encoded, and object IDs may respond with a different data type than the
    request for it uses (such as the logger-group). To facilitate this, a `request_data_type` tells the user how to
    encode a request to the device (for both read and write commands), while the `response_data_type` tells the user
    how to decode the response from the device (for both read and write commands). If the `response_data_type` is not
    set, the `request_data_type` is returned as a default fallback.

    While object IDs are grouped when looking at their name (such as ``rb485.version_boot`` in group ``rb485``), this
    information is not actually used by the protocol. Similarly, the index, name and description are not used by the
    protocol, but allow the user to quickly identify what they are dealing with.

    Refer to the :class:`~rctclient.registry.Registry` for information about how to handle the information.

    :param group: The group the ID belongs to.
    :param object_id: The unique message id.
    :param index: Numerical index.
    :param request_data_type: Data type used for encoding the payload of a :class:`~rctmon.rct_frame.RctSendFrame`.
    :param response_data_type: Data type used for decoding the response payload of a
       :class:`~rctmon.rct_frame.RctReceiveFrame`. If omitted, the value of `request_data_type` is used.
    :param description: Optional description.
    :param unit: Optional unit symbol.
    :param sim_data: Data used by the simulator.
    :param enum_values: Mapping of integer ID to string value.
    '''
    #: The group the ID belongs to
    group: ObjectGroup
    #: The unique message id that identifies it.
    object_id: int
    #: Numerical index.
    index: int
    #: Name internal to the device, may be found in the official app.
    name: str
    #: Data type for encoding the request
    request_data_type: DataType
    #: Data type for decoding the response
    response_data_type: DataType
    #: Optional description in English text.
    description: Optional[str]
    #: Optional unit.
    unit: Optional[str]
    #: Optional enum mapping
    enum_map: Optional[Dict[int, str]]

    sim_data: Any

    def __init__(self, group: ObjectGroup, object_id: int, index: int, name: str, request_data_type: DataType,
                 description: Optional[str] = None, unit: Optional[str] = None, sim_data: Any = None,
                 response_data_type: Optional[DataType] = None, enum_map: Optional[Dict[int, str]] = None) -> None:
        self.group = group
        self.object_id = object_id
        self.index = index
        self.name = name
        self.request_data_type = request_data_type
        self.enum_map = enum_map
        if response_data_type is None:
            self.response_data_type = request_data_type
        else:
            if request_data_type == DataType.ENUM and response_data_type != DataType.ENUM:
                raise RctClientException('ENUMs do not support non-ENUM response types')
            self.response_data_type = response_data_type
        self.description = description
        self.unit = unit

        if sim_data is None:
            if self.response_data_type == DataType.BOOL:
                self.sim_data = True
            elif self.response_data_type == DataType.STRING:
                self.sim_data = 'ABCDEFG'
            elif self.response_data_type == DataType.FLOAT:
                self.sim_data = 0.0
            else:
                self.sim_data = 0
        else:
            self.sim_data = sim_data

    def __repr__(self) -> str:
        return f'<ObjectInfo(id=0x{self.object_id:X}, name={self.name})>'

    def __lt__(self, other: 'ObjectInfo') -> bool:
        return self.object_id < other.object_id

    def enum_str(self, value: int) -> str:
        '''
        For DataType.ENUM: converts the integer value to the string. If there is no mapping or the type is not
        DataType.ENUM, raises an exception.

        :param value: The value to convert.
        :returns: The string key associated with the value.
        :raises RctClientException: If the type is not ENUM or no mapping is defined.
        :raises KeyError: If the value is not in the range of the enum mapping.
        '''
        if self.request_data_type == DataType.ENUM:
            if self.enum_map is not None:
                return self.enum_map[value]
            raise RctClientException('No ENUM mapping defined for this type')
        raise RctClientException('Not an ENUM type')


class Registry:
    '''
    Registry object maintaining all the :class:`~rctmon.registry.ObjectInfo` instances. Its main purpose is to provide
    functions to query for IDs by various means. As it contains the whole lot of IDs, loading it is slow. It should be
    kept around as a singleton.

    :param data: List of the IDs it should maintain.
    '''

    _ids: Dict[int, ObjectInfo]
    #: maximum length of names in _ids
    _name_max_len: int

    def __init__(self, data: List[ObjectInfo]) -> None:
        self._ids = dict()
        self._name_max_len = 0
        for elem in data:
            self._name_max_len = max(self._name_max_len, len(elem.name))
            self._ids[elem.object_id] = elem

    def type_by_id(self, id: int) -> DataType:
        '''
        Returns the request data type of an ID.

        :param id: The object_id to query for.
        :returns: The request data type.
        :raises KeyError: If the id is not in the registry.
        '''
        return self._ids[id].request_data_type

    def get_by_id(self, id: int) -> ObjectInfo:
        '''
        Returns a specific id.

        :param id: The object_id to query for.
        :returns: The id that was found.
        :raises KeyError: If the id is not in the registry.
        '''
        return self._ids[id]

    def get_by_name(self, name: str) -> ObjectInfo:
        '''
        Returns the id identified by its name field.

        :param name: The name to query for.
        :returns: The id.
        :raises KeyError: If no id with that `name` is in the registry.
        '''
        for id, elem in self._ids.items():
            if elem.name == name:
                return elem
        raise KeyError('Element not found')

    def all(self) -> List[ObjectInfo]:
        return list(self._ids.values())

    def prefix_complete_name(self, prefix: str) -> List[str]:
        '''
        To aid the CLI commands when autocompleting, this function returns a list of names that start with the given
        `prefix`, or all names if the prefix is empty.

        :param prefix: Prefix to match.
        :returns: A list of names that start with the given prefix, or all if the prefix is an empty string.
        '''
        if len(prefix) == 0:
            return sorted([x.name for x in self._ids.values()])
        else:
            return sorted([x.name for x in self._ids.values() if x.name.startswith(prefix)])

    def name_max_length(self) -> int:
        '''
        Returns the length of the longest name managed by this instance, primarily for improving user interface.
        '''
        return self._name_max_len


#: Registry singleton containing all known IDs
REGISTRY = Registry([
    ObjectInfo(group=ObjectGroup.RB485,           object_id=0x104EB6A,  index=0,   request_data_type=DataType.FLOAT,  unit='Hz',          name='rb485.f_grid[2]',                              description='Grid phase 3 frequency'),
    ObjectInfo(group=ObjectGroup.RB485,           object_id=0x7367B64,  index=24,  request_data_type=DataType.INT16,                      name='rb485.phase_marker',                           description='Next phase after phase 1 in Power Switch'),
    ObjectInfo(group=ObjectGroup.RB485,           object_id=0x173D81E4, index=82,  request_data_type=DataType.UINT32,                     name='rb485.version_boot',                           description='Power Switch bootloader version'),
    ObjectInfo(group=ObjectGroup.RB485,           object_id=0x21EE7CBB, index=115, request_data_type=DataType.FLOAT,  unit='V',           name='rb485.u_l_grid[2]',                            description='Grid phase 3 voltage'),
    ObjectInfo(group=ObjectGroup.RB485,           object_id=0x27650FE2, index=140, request_data_type=DataType.UINT32,                     name='rb485.version_main',                           description='Power Switch software version'),
    ObjectInfo(group=ObjectGroup.RB485,           object_id=0x3B5F6B9D, index=204, request_data_type=DataType.FLOAT,  unit='Hz',          name='rb485.f_wr[0]',                                description='Power Storage phase 1 frequency'),
    ObjectInfo(group=ObjectGroup.RB485,           object_id=0x437B8122, index=228, request_data_type=DataType.BOOL,                       name='rb485.available',                              description='Power Switch is available'),
    ObjectInfo(group=ObjectGroup.RB485,           object_id=0x6FD36B32, index=393, request_data_type=DataType.FLOAT,  unit='Hz',          name='rb485.f_wr[1]',                                description='Power Storage phase 2 frequency'),
    ObjectInfo(group=ObjectGroup.RB485,           object_id=0x7A9091EA, index=439, request_data_type=DataType.FLOAT,  unit='V',           name='rb485.u_l_grid[1]',                            description='Grid phase 2 voltage'),
    ObjectInfo(group=ObjectGroup.RB485,           object_id=0x905F707B, index=515, request_data_type=DataType.FLOAT,  unit='Hz',          name='rb485.f_wr[2]',                                description='Power Storage phase 3 frequency'),
    ObjectInfo(group=ObjectGroup.RB485,           object_id=0x93F976AB, index=540, request_data_type=DataType.FLOAT,  unit='V',           name='rb485.u_l_grid[0]',                            description='Grid phase 1 voltage'),
    ObjectInfo(group=ObjectGroup.RB485,           object_id=0x9558AD8A, index=544, request_data_type=DataType.FLOAT,  unit='Hz',          name='rb485.f_grid[0]',                              description='Grid phase1 frequency'),
    ObjectInfo(group=ObjectGroup.RB485,           object_id=0xFAE429C5, index=871, request_data_type=DataType.FLOAT,  unit='Hz',          name='rb485.f_grid[1]',                              description='Grid phase 2 frequency'),

    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x31A6110,  index=6,   request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_ext_month',                           description='External month energy'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xC588B75,  index=43,  request_data_type=DataType.FLOAT,                      name='energy.e_ext_day_sum'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xF28E2E1,  index=59,  request_data_type=DataType.FLOAT,                      name='energy.e_ext_total_sum'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x10970E9D, index=66,  request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_ac_month',                            description='Month energy'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x126ABC86, index=69,  request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_grid_load_month',                     description='Month energy grid load'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x1BFA5A33, index=95,  request_data_type=DataType.FLOAT,                      name='energy.e_grid_load_total_sum'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x21E1A802, index=114, request_data_type=DataType.FLOAT,                      name='energy.e_dc_month_sum[1]'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x241F1F98, index=129, request_data_type=DataType.FLOAT,                      name='energy.e_dc_day_sum[1]'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x26EFFC2F, index=137, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_grid_feed_year',                      description='Year energy grid feed-in'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x27C828F4, index=144, request_data_type=DataType.FLOAT,                      name='energy.e_grid_feed_total_sum'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x2AE703F2, index=152, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_dc_day[0]',                           description='Solar generator A day energy'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x2F3C1D7D, index=160, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_load_day',                            description='Household day energy'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x3A873343, index=199, request_data_type=DataType.FLOAT,                      name='energy.e_ac_day_sum'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x3A9D2680, index=200, request_data_type=DataType.FLOAT,                      name='energy.e_ext_year_sum'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x3C87C4F5, index=209, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_grid_feed_day',                       description='Day energy grid feed-in'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x44D4C533, index=235, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_grid_feed_total',                     description='Total energy grid feed-in'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x495BF0B6, index=249, request_data_type=DataType.FLOAT,                      name='energy.e_dc_year_sum[0]'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x4BE02BB7, index=256, request_data_type=DataType.FLOAT,                      name='energy.e_load_day_sum'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x4EE8DB78, index=274, request_data_type=DataType.FLOAT,                      name='energy.e_load_year_sum'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x62FBE7DC, index=341, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_grid_load_total',                     description='Total energy grid load'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x65B624AB, index=352, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_grid_feed_month',                     description='Month energy grid feed-in'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x6709A2F4, index=357, request_data_type=DataType.FLOAT,                      name='energy.e_ac_year_sum'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x68EEFD3D, index=367, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_dc_total[1]',                         description='Solar generator B total energy'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x6CFCD774, index=381, request_data_type=DataType.FLOAT,                      name='energy.e_dc_year_sum[1]'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x6FF4BD55, index=394, request_data_type=DataType.FLOAT,                      name='energy.e_ext_month_sum'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x79C0A724, index=434, request_data_type=DataType.FLOAT,                      name='energy.e_ac_total_sum'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x7AB9B045, index=440, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_dc_month[1]',                         description='Solar generator B month energy'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x7E096024, index=454, request_data_type=DataType.FLOAT,                      name='energy.e_load_total_sum'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x812E5ADD, index=463, request_data_type=DataType.FLOAT,                      name='energy.e_dc_total_sum[1]'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x81AE960B, index=465, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_dc_month[0]',                         description='Solar generator A month energy'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x84ABE3D8, index=474, request_data_type=DataType.FLOAT,                      name='energy.e_grid_feed_year_sum'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x867DEF7D, index=478, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_grid_load_day',                       description='Day energy grid load'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0x917E3622, index=525, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_ext_year',                            description='External year energy'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xA12BE39C, index=576, request_data_type=DataType.FLOAT,                      name='energy.e_load_month_sum'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xA5341F4A, index=587, request_data_type=DataType.FLOAT,                      name='energy.e_grid_feed_month_sum'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xA59C8428, index=589, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_ext_total',                           description='External total energy'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xAF64D0FE, index=618, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_dc_year[0]',                          description='Solar generator A year energy'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xB1EF67CE, index=627, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_ac_total',                            description='Total energy'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xB7B2967F, index=648, request_data_type=DataType.FLOAT,                      name='energy.e_dc_total_sum[0]'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xB9A026F9, index=658, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_ext_day',                             description='External day energy'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xBD55905F, index=670, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_ac_day',                              description='Day energy'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xBD55D796, index=671, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_dc_year[1]',                          description='Solar generator B year energy'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xC0CC81B6, index=683, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_ac_year',                             description='Year energy'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xC7D3B479, index=710, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_load_year',                           description='Household year energy'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xC9D76279, index=718, request_data_type=DataType.FLOAT,                      name='energy.e_dc_day_sum[0]'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xD9D66B76, index=760, request_data_type=DataType.FLOAT,                      name='energy.e_grid_load_year_sum'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xDA207111, index=763, request_data_type=DataType.FLOAT,                      name='energy.e_grid_load_month_sum'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xDE17F021, index=776, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_grid_load_year',                      description='Year energy grid load'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xEAEEB3CA, index=813, request_data_type=DataType.FLOAT,                      name='energy.e_dc_month_sum[0]'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xEFF4B537, index=826, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_load_total',                          description='Household total energy'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xF0BE6429, index=833, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_load_month',                          description='Household month energy'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xFBF3CE97, index=876, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_dc_day[1]',                           description='Solar generator B day energy'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xFBF8D63C, index=878, request_data_type=DataType.FLOAT,                      name='energy.e_grid_load_day_sum'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xFC1C614E, index=879, request_data_type=DataType.FLOAT,                      name='energy.e_ac_month_sum'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xFC724A9E, index=882, request_data_type=DataType.FLOAT,  unit='Wh',          name='energy.e_dc_total[0]',                         description='Solar generator A total energy'),
    ObjectInfo(group=ObjectGroup.ENERGY,          object_id=0xFDB81124, index=888, request_data_type=DataType.FLOAT,                      name='energy.e_grid_feed_day_sum'),

    ObjectInfo(group=ObjectGroup.GRID_MON,        object_id=0x16109E1,  index=2,   request_data_type=DataType.FLOAT,  unit='s',           name='grid_mon[0].u_over.time',                      description='Max. voltage switch-off time level 1'),
    ObjectInfo(group=ObjectGroup.GRID_MON,        object_id=0x3044195F, index=162, request_data_type=DataType.FLOAT,  unit='s',           name='grid_mon[1].u_under.time',                     description='Min. voltage switch-off time level 2'),
    ObjectInfo(group=ObjectGroup.GRID_MON,        object_id=0x3CB1EF01, index=211, request_data_type=DataType.FLOAT,  unit='V',           name='grid_mon[0].u_under.threshold',                description='Min. voltage level 1'),
    ObjectInfo(group=ObjectGroup.GRID_MON,        object_id=0x3E722B43, index=215, request_data_type=DataType.FLOAT,  unit='Hz',          name='grid_mon[1].f_under.threshold',                description='Min. frequency level 2'),
    ObjectInfo(group=ObjectGroup.GRID_MON,        object_id=0x5438B68E, index=293, request_data_type=DataType.FLOAT,  unit='V',           name='grid_mon[1].u_over.threshold',                 description='Max. voltage level 2'),
    ObjectInfo(group=ObjectGroup.GRID_MON,        object_id=0x70E28322, index=399, request_data_type=DataType.FLOAT,  unit='s',           name='grid_mon[0].f_under.time',                     description='Min. frequency switch-off time level 1'),
    ObjectInfo(group=ObjectGroup.GRID_MON,        object_id=0x82CD1525, index=468, request_data_type=DataType.FLOAT,  unit='V',           name='grid_mon[1].u_under.threshold',                description='Min. voltage level 2'),
    ObjectInfo(group=ObjectGroup.GRID_MON,        object_id=0x915CD4A4, index=523, request_data_type=DataType.FLOAT,  unit='Hz',          name='grid_mon[1].f_over.threshold',                 description='Max. frequency level 2'),
    ObjectInfo(group=ObjectGroup.GRID_MON,        object_id=0x933F9A24, index=534, request_data_type=DataType.FLOAT,  unit='s',           name='grid_mon[0].f_over.time',                      description='Max. frequency switch-off time level 1'),
    ObjectInfo(group=ObjectGroup.GRID_MON,        object_id=0xA6271C2E, index=592, request_data_type=DataType.FLOAT,  unit='V',           name='grid_mon[0].u_over.threshold',                 description='Max. voltage level 1'),
    ObjectInfo(group=ObjectGroup.GRID_MON,        object_id=0xA95AD038, index=606, request_data_type=DataType.FLOAT,  unit='Hz',          name='grid_mon[0].f_under.threshold',                description='Min. frequency level 1'),
    ObjectInfo(group=ObjectGroup.GRID_MON,        object_id=0xEBF7A4E8, index=818, request_data_type=DataType.FLOAT,  unit='Hz',          name='grid_mon[0].f_over.threshold',                 description='Max. frequency level 1'),
    ObjectInfo(group=ObjectGroup.GRID_MON,        object_id=0xEF89568B, index=824, request_data_type=DataType.FLOAT,  unit='s',           name='grid_mon[0].u_under.time',                     description='Min. voltage switch-off time level 1'),
    ObjectInfo(group=ObjectGroup.GRID_MON,        object_id=0xF09CC4A2, index=830, request_data_type=DataType.FLOAT,  unit='s',           name='grid_mon[1].u_over.time',                      description='Max. voltage switch-off time level 2'),
    ObjectInfo(group=ObjectGroup.GRID_MON,        object_id=0xF1FA5BB9, index=837, request_data_type=DataType.FLOAT,  unit='s',           name='grid_mon[1].f_under.time',                     description='Min. frequency switch-off time level 2'),
    ObjectInfo(group=ObjectGroup.GRID_MON,        object_id=0xFD4F17C4, index=886, request_data_type=DataType.FLOAT,  unit='s',           name='grid_mon[1].f_over.time',                      description='Max. frequency switch-off time level 2'),

    ObjectInfo(group=ObjectGroup.TEMPERATURE,     object_id=0x90B53336, index=520, request_data_type=DataType.FLOAT,  unit='°C',          name='temperature.sink_temp_power_reduction',        description='Heat sink temperature target'),
    ObjectInfo(group=ObjectGroup.TEMPERATURE,     object_id=0xA7447FC4, index=595, request_data_type=DataType.FLOAT,  unit='°C',          name='temperature.bat_temp_power_reduction',         description='Battery actuator temperature target'),

    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x1676FA6,  index=3,   request_data_type=DataType.UNKNOWN,                    name='battery.cells_stat[3]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x3D9C51F,  index=10,  request_data_type=DataType.FLOAT,                      name='battery.cells_stat[0].u_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x56162CA,  index=15,  request_data_type=DataType.UINT32,                     name='battery.cells_stat[4].u_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x56417DF,  index=16,  request_data_type=DataType.UINT8,                      name='battery.cells_stat[3].t_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x64A60FE,  index=19,  request_data_type=DataType.UINT8,                      name='battery.cells_stat[4].t_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x6A9FFA2,  index=21,  request_data_type=DataType.FLOAT,  unit='Ah',          name='battery.charged_amp_hours',                    description='Total charge flow into battery'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x77692DE,  index=27,  request_data_type=DataType.UINT8,                      name='battery.cells_stat[4].u_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x86C75B0,  index=30,  request_data_type=DataType.UINT32,                     name='battery.stack_software_version[3]',            description='Software version stack 3'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x9923C1E,  index=35,  request_data_type=DataType.UINT8,                      name='battery.cells_stat[3].t_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xCFA8BC4,  index=47,  request_data_type=DataType.UINT16,                     name='battery.stack_cycles[1]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xDACF21B,  index=49,  request_data_type=DataType.UNKNOWN,                    name='battery.cells_stat[4]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xDE3D20D,  index=51,  request_data_type=DataType.INT32,                      name='battery.status2',                              description='Battery extra status'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xEF60C7E,  index=58,  request_data_type=DataType.FLOAT,                      name='battery.cells_stat[3].u_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x120EC3B4, index=68,  request_data_type=DataType.UINT8,                      name='battery.cells_stat[4].u_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x1348AB07, index=71,  request_data_type=DataType.UNKNOWN,                    name='battery.cells[4]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x162491E8, index=76,  request_data_type=DataType.STRING,                     name='battery.module_sn[5]',                         description='Module 5 Serial Number'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x16A1F844, index=78,  request_data_type=DataType.STRING,                     name='battery.bms_sn',                               description='BMS Serial Number'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x18D1E9E0, index=87,  request_data_type=DataType.UINT8,                      name='battery.cells_stat[5].u_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x18F98B6D, index=88,  request_data_type=DataType.FLOAT,                      name='battery.cells_stat[3].u_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x1B39A3A3, index=93,  request_data_type=DataType.UINT32,                     name='battery.bms_power_version',                    description='Software version BMS Power'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x1E5FCA70, index=102, request_data_type=DataType.FLOAT,  unit='A',           name='battery.maximum_charge_current',               description='Max. charge current'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x1F73B6A4, index=104, request_data_type=DataType.UINT32,                     name='battery.cells_stat[3].t_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x21961B58, index=113, request_data_type=DataType.FLOAT,  unit='A',           name='battery.current',                              description='Battery current'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x23E55DA0, index=125, request_data_type=DataType.UNKNOWN,                    name='battery.cells_stat[5]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x257B5945, index=132, request_data_type=DataType.UINT8,                      name='battery.cells_stat[2].u_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x257B7612, index=133, request_data_type=DataType.STRING,                     name='battery.module_sn[3]',                         description='Module 3 Serial Number'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x26363AAE, index=135, request_data_type=DataType.UINT8,                      name='battery.cells_stat[1].t_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x265EACF6, index=136, request_data_type=DataType.UINT32,                     name='battery.cells_stat[2].t_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x27C39CEA, index=143, request_data_type=DataType.UINT16,                     name='battery.stack_cycles[6]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x2A30A97E, index=149, request_data_type=DataType.UINT16,                     name='battery.stack_cycles[5]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x2AACCAA7, index=151, request_data_type=DataType.FLOAT,                      name='battery.max_cell_voltage'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x2BC1E72B, index=153, request_data_type=DataType.FLOAT,  unit='Ah',          name='battery.discharged_amp_hours',                 description='Total charge flow from battery'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x331D0689, index=169, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[2].t_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x336415EA, index=170, request_data_type=DataType.UINT32,                     name='battery.cells_stat[0].t_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x34A164E7, index=173, request_data_type=DataType.UNKNOWN,                    name='battery.cells_stat[0]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x34E33726, index=174, request_data_type=DataType.UINT8,                      name='battery.cells_stat[2].u_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x3503B92D, index=177, request_data_type=DataType.UINT32,                     name='battery.cells_stat[3].u_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x381B8BF9, index=187, request_data_type=DataType.FLOAT,   unit='%',          name='battery.soh',                                  description='SOH (State of Health)'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x3A7D5F53, index=198, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[1].u_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x3BA1B77B, index=206, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[3].t_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x3F98F58A, index=218, request_data_type=DataType.UINT8,                      name='battery.cells_stat[5].t_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x40FF01B7, index=222, request_data_type=DataType.UNKNOWN,                    name='battery.cells[6]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x41B11ECF, index=224, request_data_type=DataType.UINT8,                      name='battery.cells_stat[3].u_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x428CCF46, index=225, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[5].u_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x442A3409, index=233, request_data_type=DataType.UINT32,                     name='battery.cells_stat[4].t_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x4443C661, index=234, request_data_type=DataType.UINT8,                      name='battery.cells_stat[0].t_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x4B51A539, index=254, request_data_type=DataType.STRING,                     name='battery.prog_sn'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x4CB7C0DC, index=261, request_data_type=DataType.FLOAT,                      name='battery.min_cell_voltage'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x4D985F33, index=263, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[5].u_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x4E699086, index=271, request_data_type=DataType.STRING,                     name='battery.module_sn[4]',                         description='Module 4 Serial Number'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x501A162D, index=280, request_data_type=DataType.STRING,                     name='battery.cells_resist[5]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x50514732, index=281, request_data_type=DataType.UINT8,                      name='battery.cells_stat[6].u_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x518C7BBE, index=285, request_data_type=DataType.UINT32,                     name='battery.cells_stat[5].u_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x537C719F, index=289, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[0].t_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x5570401B, index=298, request_data_type=DataType.FLOAT,  unit='Wh',          name='battery.stored_energy',                        description='Total energy flow into battery'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x55DDF7BA, index=300, request_data_type=DataType.FLOAT,                      name='battery.max_cell_temperature'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x5939EC5D, index=311, request_data_type=DataType.STRING,                     name='battery.module_sn[6]',                         description='Module 6 Serial Number'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x5A120CE4, index=313, request_data_type=DataType.UINT32,                     name='battery.cells_stat[1].t_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x5A9EEFF0, index=315, request_data_type=DataType.UINT16,                     name='battery.stack_cycles[4]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x5AF50FD7, index=316, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[4].t_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x5BA122A5, index=318, request_data_type=DataType.UINT16,                     name='battery.stack_cycles[2]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x60749E5E, index=333, request_data_type=DataType.UINT32,                     name='battery.cells_stat[6].u_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x61EAC702, index=336, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[0].t_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x6213589B, index=337, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[6].u_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x62D645D9, index=340, request_data_type=DataType.UNKNOWN,                    name='battery.cells[5]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x6388556C, index=344, request_data_type=DataType.UINT32,                     name='battery.stack_software_version[0]',            description='Software version stack 0'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x6445D856, index=345, request_data_type=DataType.UINT8,                      name='battery.cells_stat[1].u_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x649B10DA, index=347, request_data_type=DataType.STRING,                     name='battery.cells_resist[0]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x4E04DD55, index=266, request_data_type=DataType.FLOAT,                      name='battery.soc_update_since'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x65EED11B, index=353, request_data_type=DataType.FLOAT,  unit='V',           name='battery.voltage',                              description='Battery voltage'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x6974798A, index=369, request_data_type=DataType.UINT32,                     name='battery.stack_software_version[6]',            description='Software version stack 6'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x69B8FF28, index=371, request_data_type=DataType.UNKNOWN,                    name='battery.cells[2]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x6DB1FDDC, index=385, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[4].u_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x6E24632E, index=388, request_data_type=DataType.UINT32,                     name='battery.cells_stat[5].u_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x6E491B50, index=390, request_data_type=DataType.FLOAT,  unit='V',           name='battery.maximum_charge_voltage',               description='Max. charge voltage'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x70349444, index=396, request_data_type=DataType.UINT8,                      name='battery.cells_stat[1].t_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x70A2AF4F, index=397, request_data_type=DataType.INT32,                      name='battery.bat_status'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x5847E59E, index=306, request_data_type=DataType.FLOAT,  unit='V',           name='battery.maximum_charge_voltage_constant_u',    description='Max. charge voltage'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x71196579, index=400, request_data_type=DataType.UINT8,                      name='battery.cells_stat[5].t_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x71765BD8, index=404, request_data_type=DataType.INT32,                      name='battery.status',                               description='Battery status'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x71CB0B57, index=406, request_data_type=DataType.STRING,                     name='battery.cells_resist[1]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x7268CE4D, index=409, request_data_type=DataType.UINT32,                     name='battery.inv_cmd'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x73489528, index=412, request_data_type=DataType.STRING,                     name='battery.module_sn[2]',                         description='Module 2 Serial Number'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x74FD4609, index=415, request_data_type=DataType.UNKNOWN,                    name='battery.cells_stat[2]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x770A6E7C, index=422, request_data_type=DataType.UINT8,                      name='battery.cells_stat[0].u_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x7E590128, index=455, request_data_type=DataType.UINT32,                     name='battery.cells_stat[0].u_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x7F42BB82, index=457, request_data_type=DataType.UINT8,                      name='battery.cells_stat[6].u_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x7FF6252C, index=459, request_data_type=DataType.UINT32,                     name='battery.cells_stat[5].t_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x804A3266, index=460, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[6].u_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x8160539D, index=464, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[4].t_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x885BB57E, index=483, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[6].t_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x889DC27F, index=485, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[0].u_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x88BBF8CB, index=486, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[5].t_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x89B25F4B, index=492, request_data_type=DataType.UINT16,                     name='battery.stack_cycles[3]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x8B9FF008, index=497, request_data_type=DataType.FLOAT,  unit='%',           name='battery.soc_target',                           description='Target SOC'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x8BB08839, index=498, request_data_type=DataType.UINT32,                     name='battery.cells_stat[6].t_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x8DFFDD33, index=504, request_data_type=DataType.UINT32,                     name='battery.cells_stat[3].u_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x8EC23427, index=507, request_data_type=DataType.UINT32,                     name='battery.cells_stat[4].u_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x8EF6FBBD, index=509, request_data_type=DataType.UNKNOWN,                    name='battery.cells[1]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x8EF9C9B8, index=510, request_data_type=DataType.UINT32,                     name='battery.cells_stat[6].t_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x902AFAFB, index=513, request_data_type=DataType.FLOAT,  unit='°C',          name='battery.temperature',                          description='Battery temperature'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x90832471, index=518, request_data_type=DataType.UINT32,                     name='battery.cells_stat[1].u_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x91C325D9, index=526, request_data_type=DataType.UINT32,                     name='battery.cells_stat[0].t_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x91FB68CD, index=527, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[6].t_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x959930BF, index=545, request_data_type=DataType.FLOAT,  unit='%',           name='battery.soc',                                  description='SOC (State of charge)'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x99396810, index=558, request_data_type=DataType.STRING,                     name='battery.module_sn[1]',                         description='Module 1 Serial Number'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x993C06F6, index=559, request_data_type=DataType.STRING,                     name='battery.cells_resist[3]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x9D785E8C, index=569, request_data_type=DataType.UINT32,                     name='battery.bms_software_version',                 description='Software version BMS Master'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0x9E314430, index=572, request_data_type=DataType.UINT32,                     name='battery.cells_stat[2].u_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xA10D9A4B, index=574, request_data_type=DataType.FLOAT,                      name='battery.min_cell_temperature'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xA3E48B21, index=584, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[2].t_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xA40906BF, index=585, request_data_type=DataType.UINT32,                     name='battery.stack_software_version[4]',            description='Software version stack 4'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xA54C4685, index=588, request_data_type=DataType.UINT32,                     name='battery.stack_software_version[1]',            description='Software version stack 1'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xA616B022, index=591, request_data_type=DataType.FLOAT,                      name='battery.soc_target_low',                       description='SOC target low'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xA6871A4D, index=593, request_data_type=DataType.UINT8,                      name='battery.cells_stat[4].t_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xA6C4FD4A, index=594, request_data_type=DataType.UINT16,                     name='battery.stack_cycles[0]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xA7DBD28C, index=598, request_data_type=DataType.UINT8,                      name='battery.cells_stat[2].t_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xA7FE5C0C, index=601, request_data_type=DataType.UINT8,                      name='battery.cells_stat[2].t_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xA9033880, index=605, request_data_type=DataType.FLOAT,  unit='Wh',          name='battery.used_energy',                          description='Total energy flow from battery'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xAACAC898, index=611, request_data_type=DataType.UINT32,                     name='battery.cells_stat[4].t_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xACF7666B, index=615, request_data_type=DataType.FLOAT,                      name='battery.efficiency',                           description='Battery efficiency (used energy / stored energy)'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xB0EBE75A, index=622, request_data_type=DataType.FLOAT,  unit='V',           name='battery.minimum_discharge_voltage',            description='Min. discharge voltage'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xB4E053D4, index=639, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[1].u_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xB57B59BD, index=642, request_data_type=DataType.FLOAT,  unit='Ah',          name='battery.ah_capacity',                          description='Battery capacity'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xB81FB399, index=651, request_data_type=DataType.UINT32,                     name='battery.cells_stat[2].u_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xB84A38AB, index=653, request_data_type=DataType.FLOAT,                      name='battery.soc_target_high',                      description='SOC target high'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xB9E09F78, index=659, request_data_type=DataType.UINT8,                      name='battery.cells_stat[5].u_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xBB302278, index=662, request_data_type=DataType.UINT32,                     name='battery.cells_stat[1].t_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xBDE3BF0A, index=673, request_data_type=DataType.UINT8,                      name='battery.cells_stat[6].t_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xC0680302, index=679, request_data_type=DataType.UINT32,                     name='battery.cells_stat[2].t_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xC0DF2978, index=684, request_data_type=DataType.INT32,                      name='battery.cycles',                               description='Battery charge / discharge cycles'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xC42F5807, index=695, request_data_type=DataType.UINT8,                      name='battery.cells_stat[1].u_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xC6DA81A0, index=704, request_data_type=DataType.UINT32,                     name='battery.cells_stat[6].u_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xC8609C8E, index=712, request_data_type=DataType.UNKNOWN,                    name='battery.cells[3]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xC88EB032, index=713, request_data_type=DataType.UINT32,                     name='battery.cells_stat[0].u_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xC8BA1729, index=714, request_data_type=DataType.UINT32,                     name='battery.stack_software_version[2]',            description='Software version stack 2'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xD0C47326, index=736, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[1].t_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xD60E7A2F, index=754, request_data_type=DataType.UINT32,                     name='battery.cells_stat[1].u_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xDD5930A2, index=773, request_data_type=DataType.UINT8,                      name='battery.cells_stat[0].t_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xDE9CBCB0, index=778, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[5].t_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xDEE1957F, index=779, request_data_type=DataType.STRING,                     name='battery.cells_resist[4]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xDF0A735C, index=780, request_data_type=DataType.FLOAT,  unit='A',           name='battery.maximum_discharge_current',            description='Max. discharge current'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xDFF966E3, index=783, request_data_type=DataType.UINT8,                      name='battery.cells_stat[6].t_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xE7177DEE, index=804, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[2].u_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xEB4C2597, index=814, request_data_type=DataType.STRING,                     name='battery.cells_resist[6]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xEEA3F59B, index=821, request_data_type=DataType.UINT32,                     name='battery.stack_software_version[5]',            description='Software version stack 5'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xEECDFEFC, index=823, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[2].u_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xEFD3EC8A, index=825, request_data_type=DataType.UINT32,                     name='battery.cells_stat[5].t_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xF044EDA0, index=828, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[3].t_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xF257D342, index=842, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[1].t_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xF3FD8CE6, index=848, request_data_type=DataType.STRING,                     name='battery.cells_resist[2]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xF54BC06D, index=854, request_data_type=DataType.FLOAT,                      name='battery.cells_stat[4].u_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xF8C0D255, index=864, request_data_type=DataType.UNKNOWN,                    name='battery.cells[0]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xF99E8CC8, index=866, request_data_type=DataType.UNKNOWN,                    name='battery.cells_stat[6]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xFA3276DC, index=868, request_data_type=DataType.UINT32,                     name='battery.cells_stat[3].t_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xFB796780, index=874, request_data_type=DataType.UNKNOWN,                    name='battery.cells_stat[1]'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xFBF6D834, index=877, request_data_type=DataType.STRING,                     name='battery.module_sn[0]',                         description='Module 0 Serial Number'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xFDBD9EE9, index=889, request_data_type=DataType.UINT8,                      name='battery.cells_stat[3].u_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xFE44BA26, index=892, request_data_type=DataType.UINT8,                      name='battery.cells_stat[0].u_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xE7B0E692, index=805, request_data_type=DataType.FLOAT,                      name='battery.bat_impedance.impedance_fine',         description='Battery circuit impedance'),
    ObjectInfo(group=ObjectGroup.BATTERY,         object_id=0xEA77252E, index=812, request_data_type=DataType.FLOAT,  unit='V',           name='battery.minimum_discharge_voltage_constant_u', description='Min. discharge voltage'),

    ObjectInfo(group=ObjectGroup.CS_NEG,          object_id=0x19C0B60,  index=4,   request_data_type=DataType.FLOAT,                      name='cs_neg[2]',                                    description='Multiply value of the current sensor 2 by'),
    ObjectInfo(group=ObjectGroup.CS_NEG,          object_id=0x4C12C4C7, index=257, request_data_type=DataType.FLOAT,                      name='cs_neg[1]',                                    description='Multiply value of the current sensor 1 by'),
    ObjectInfo(group=ObjectGroup.CS_NEG,          object_id=0x82258C01, index=467, request_data_type=DataType.FLOAT,                      name='cs_neg[0]',                                    description='Multiply value of the current sensor 0 by'),

    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0x39BDE11,  index=8,   request_data_type=DataType.UINT8,                      name='hw_test.state'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0x58F1759,  index=17,  request_data_type=DataType.FLOAT,                      name='hw_test.bt_power[6]'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0x875C906,  index=31,  request_data_type=DataType.FLOAT,                      name='hw_test.bt_time[2]'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0x2082BFB6, index=109, request_data_type=DataType.FLOAT,                      name='hw_test.bt_time[9]'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0x3CA8E8D0, index=210, request_data_type=DataType.FLOAT,                      name='hw_test.bt_time[0]'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0x3D789979, index=212, request_data_type=DataType.FLOAT,                      name='hw_test.bt_power[7]'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0x4E2B42A4, index=268, request_data_type=DataType.FLOAT,                      name='hw_test.bt_power[0]'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0x4E77B2CE, index=272, request_data_type=DataType.UINT8,                      name='hw_test.bt_cycle'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0x58378BD0, index=305, request_data_type=DataType.FLOAT,                      name='hw_test.bt_time[3]'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0x6BFF1AF4, index=375, request_data_type=DataType.FLOAT,                      name='hw_test.bt_power[2]'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0x71B70DCE, index=405, request_data_type=DataType.FLOAT,                      name='hw_test.bt_power[4]'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0x75AE19ED, index=418, request_data_type=DataType.FLOAT,                      name='hw_test.hw_switch_time'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0x77DD4364, index=425, request_data_type=DataType.FLOAT,                      name='hw_test.bt_time[5]'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0x86782D58, index=477, request_data_type=DataType.FLOAT,                      name='hw_test.bt_power[9]'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0x903FE89E, index=514, request_data_type=DataType.FLOAT,                      name='hw_test.bt_time[8]'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0x9214A00C, index=529, request_data_type=DataType.UINT8,                      name='hw_test.booster_test_index'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0x940569AC, index=541, request_data_type=DataType.FLOAT,                      name='hw_test.bt_time[6]'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0xB082C4D7, index=621, request_data_type=DataType.FLOAT,                      name='hw_test.bt_power[5]'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0xC1C82889, index=686, request_data_type=DataType.FLOAT,                      name='hw_test.bt_power[1]'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0xC3C7325E, index=692, request_data_type=DataType.FLOAT,                      name='hw_test.bt_time[4]'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0xC66A522B, index=703, request_data_type=DataType.FLOAT,                      name='hw_test.bt_time[1]'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0xC707102E, index=705, request_data_type=DataType.FLOAT,                      name='hw_test.bt_power[3]'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0xCBEC8200, index=728, request_data_type=DataType.FLOAT,                      name='hw_test.timer2'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0xD4C4A941, index=748, request_data_type=DataType.FLOAT,                      name='hw_test.bt_time[7]'),
    ObjectInfo(group=ObjectGroup.HW_TEST,         object_id=0xE6248312, index=800, request_data_type=DataType.FLOAT,                      name='hw_test.bt_power[8]'),

    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x3A39CA2,  index=9,   request_data_type=DataType.FLOAT,  unit='W',           name='g_sync.p_ac_load[0]',                          description='Load household phase 1'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0xA04CA7F,  index=36,  request_data_type=DataType.FLOAT,  unit='V',           name='g_sync.u_zk_n_avg',                            description='Negative buffer capacitor voltage'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x147E8E26, index=72,  request_data_type=DataType.FLOAT,                      name='g_sync.p_ac[1]',                               description='AC2'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x1AC87AA0, index=92,  request_data_type=DataType.FLOAT,  unit='W',           name='g_sync.p_ac_load_sum_lp',                      description='Load household - external Power'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x24150B85, index=127, request_data_type=DataType.FLOAT,  unit='V',           name='g_sync.u_zk_sum_mov_avg',                      description='Actual DC link voltage'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x2545E22D, index=131, request_data_type=DataType.FLOAT,  unit='V',           name='g_sync.u_l_rms[2]',                            description='AC voltage phase 3'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x2788928C, index=141, request_data_type=DataType.FLOAT,  unit='W',           name='g_sync.p_ac_load[1]',                          description='Load household phase 2'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x27BE51D9, index=142, request_data_type=DataType.FLOAT,  unit='W',           name='g_sync.p_ac_sc[0]',                            description='Grid power phase 1'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x3A444FC6, index=197, request_data_type=DataType.FLOAT,  unit='VA',          name='g_sync.s_ac_lp[0]',                            description='Apparent power phase 1'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x400F015B, index=219, request_data_type=DataType.FLOAT,  unit='W',           name='g_sync.p_acc_lp',                              description='Battery power'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x4077335D, index=220, request_data_type=DataType.FLOAT,  unit='VA',          name='g_sync.s_ac_lp[1]',                            description='Apparent power phase 2'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x43257820, index=227, request_data_type=DataType.FLOAT,                      name='g_sync.p_ac[0]',                               description='AC1'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x485AD749, index=245, request_data_type=DataType.FLOAT,  unit='V',           name='g_sync.u_ptp_rms[1]',                          description='Phase to phase voltage 2'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x48D73FA5, index=247, request_data_type=DataType.FLOAT,  unit='A',           name='g_sync.i_dr_lp[2]',                            description='Current phase 3 (average)'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x4E49AEC5, index=270, request_data_type=DataType.FLOAT,  unit='W',           name='g_sync.p_ac_sum',                              description='Real power'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x54B4684E, index=295, request_data_type=DataType.FLOAT,  unit='V',           name='g_sync.u_l_rms[1]',                            description='AC voltage phase 2'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x55C22966, index=299, request_data_type=DataType.FLOAT,  unit='VA',          name='g_sync.s_ac[2]',                               description='Apparent power phase 3'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x6002891F, index=331, request_data_type=DataType.FLOAT,  unit='W',           name='g_sync.p_ac_sc_sum',                           description='Grid power (ext. sensors)'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x612F7EAB, index=335, request_data_type=DataType.FLOAT,  unit='VA',          name='g_sync.s_ac[1]',                               description='Apparent power phase 2'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x63476DBE, index=342, request_data_type=DataType.FLOAT,  unit='V',           name='g_sync.u_ptp_rms[0]',                          description='Phase to phase voltage 1'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x650C1ED7, index=348, request_data_type=DataType.FLOAT,  unit='A',           name='g_sync.i_dr_eff[1]',                           description='Current phase 2'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x6E1C5B78, index=387, request_data_type=DataType.FLOAT,  unit='W',           name='g_sync.p_ac_lp[1]',                            description='AC power phase 2'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x71E10B51, index=407, request_data_type=DataType.FLOAT,  unit='W',           name='g_sync.p_ac_lp[0]',                            description='AC power phase 1'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x7C78CBAC, index=449, request_data_type=DataType.FLOAT,  unit='var',         name='g_sync.q_ac_sum_lp',                           description='Reactive power'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x82E3C121, index=469, request_data_type=DataType.FLOAT,  unit='var',         name='g_sync.q_ac[1]',                               description='Reactive power phase 2'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x883DE9AB, index=482, request_data_type=DataType.FLOAT,  unit='VA',          name='g_sync.s_ac_lp[2]',                            description='Apparent power phase 3'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x887D43C4, index=484, request_data_type=DataType.FLOAT,  unit='A',           name='g_sync.i_dr_lp[0]',                            description='Current phase 1 (average)'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x89EE3EB5, index=493, request_data_type=DataType.FLOAT,  unit='A',           name='g_sync.i_dr_eff[0]',                           description='Current phase 1'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x8A18539B, index=494, request_data_type=DataType.FLOAT,  unit='V',           name='g_sync.u_zk_sum_avg',                          description='DC link voltage'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x91617C58, index=524, request_data_type=DataType.FLOAT,  unit='W',           name='g_sync.p_ac_grid_sum_lp',                      description='Total grid power'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0x92BC682B, index=533, request_data_type=DataType.FLOAT,  unit='A',           name='g_sync.i_dr_eff[2]',                           description='Current phase 3'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0xB0041187, index=619, request_data_type=DataType.FLOAT,  unit='V',           name='g_sync.u_sg_avg[1]',                           description='Solar generator B voltage'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0xB221BCFA, index=629, request_data_type=DataType.FLOAT,  unit='W',           name='g_sync.p_ac_sc[2]',                            description='Grid power phase 3'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0xB55BA2CE, index=641, request_data_type=DataType.FLOAT,  unit='V',           name='g_sync.u_sg_avg[0]',                           description='Solar generator A voltage'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0xB9928C51, index=657, request_data_type=DataType.FLOAT,  unit='W',           name='g_sync.p_ac_lp[2]',                            description='AC power phase 3'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0xBCA77559, index=665, request_data_type=DataType.FLOAT,  unit='var',         name='g_sync.q_ac[2]',                               description='Reactive power phase 3'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0xC03462F6, index=677, request_data_type=DataType.FLOAT,                      name='g_sync.p_ac[2]',                               description='AC3'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0xC198B25B, index=685, request_data_type=DataType.FLOAT,  unit='V',           name='g_sync.u_zk_p_avg',                            description='Positive buffer capacitor voltage'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0xCABC44CA, index=721, request_data_type=DataType.FLOAT,  unit='VA',          name='g_sync.s_ac[0]',                               description='Apparent power phase 1'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0xCF053085, index=734, request_data_type=DataType.FLOAT,  unit='V',           name='g_sync.u_l_rms[0]',                            description='AC voltage phase 1'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0xDB2D69AE, index=767, request_data_type=DataType.FLOAT,  unit='W',           name='g_sync.p_ac_sum_lp',                           description='AC power'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0xDCA1CF26, index=771, request_data_type=DataType.FLOAT,  unit='VA',          name='g_sync.s_ac_sum_lp',                           description='Apparent power'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0xDCAC0EA9, index=772, request_data_type=DataType.FLOAT,  unit='A',           name='g_sync.i_dr_lp[1]',                            description='Current phase 2 (average)'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0xE94C2EFC, index=807, request_data_type=DataType.FLOAT,  unit='var',         name='g_sync.q_ac[0]',                               description='Reactive power phase 1'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0xF0B436DD, index=832, request_data_type=DataType.FLOAT,  unit='W',           name='g_sync.p_ac_load[2]',                          description='Load household phase 3'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0xF25C339B, index=843, request_data_type=DataType.FLOAT,  unit='V',           name='g_sync.u_ptp_rms[2]',                          description='Phase to phase voltage 3'),
    ObjectInfo(group=ObjectGroup.G_SYNC,          object_id=0xF5584F90, index=855, request_data_type=DataType.FLOAT,  unit='W',           name='g_sync.p_ac_sc[1]',                            description='Grid power phase 2'),

    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x5C7CFB1,  index=18,  request_data_type=DataType.INT32,                      name='logger.day_egrid_load_log_ts',                 response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x64E4340,  index=20,  request_data_type=DataType.INT32,  unit='V',           name='logger.minutes_ubat_log_ts',                   response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x95AFAA8,  index=33,  request_data_type=DataType.INT32,  unit='V',           name='logger.minutes_ul3_log_ts',                    response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0xDF164DE,  index=52,  request_data_type=DataType.INT32,                      name='logger.day_eb_log_ts',                         response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0xFA29566,  index=60,  request_data_type=DataType.INT32,  unit='V',           name='logger.minutes_ub_log_ts',                     response_data_type=DataType.TIMESERIES, description='Histogram voltage generator B'),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x132AA71E, index=70,  request_data_type=DataType.INT32,  unit='°C',          name='logger.minutes_temp2_log_ts',                  response_data_type=DataType.TIMESERIES, description='Histogram heat sink (battery actuator) temperature'),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x19B814F2, index=90,  request_data_type=DataType.INT32,                      name='logger.year_egrid_feed_log_ts',                response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x1D49380A, index=99,  request_data_type=DataType.INT32,                      name='logger.minutes_eb_log_ts',                     response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x21879805, index=112, request_data_type=DataType.INT32,                      name='logger.minutes_eac1_log_ts',                   response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x2A449E89, index=150, request_data_type=DataType.INT32,                      name='logger.year_log_ts',                           response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x2F0A6B15, index=159, request_data_type=DataType.INT32,                      name='logger.month_ea_log_ts',                       response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x34ECA9CA, index=175, request_data_type=DataType.INT32,                      name='logger.year_eb_log_ts',                        response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x3906A1D0, index=191, request_data_type=DataType.INT32,                      name='logger.minutes_eext_log_ts',                   response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x431509D1, index=226, request_data_type=DataType.INT32,                      name='logger.month_eload_log_ts',                    response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x488052BA, index=246, request_data_type=DataType.INT32,  unit='V',           name='logger.minutes_ul2_log_ts',                    response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x4C14CC7C, index=258, request_data_type=DataType.INT32,                      name='logger.year_ea_log_ts',                        response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x4E9D95A6, index=273, request_data_type=DataType.INT32,                      name='logger.year_eext_log_ts',                      response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x50B441C1, index=283, request_data_type=DataType.INT32,                      name='logger.minutes_ea_log_ts',                     response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x5293B668, index=287, request_data_type=DataType.INT32,  unit='%',           name='logger.minutes_soc_log_ts',                    response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x5411CE1B, index=292, request_data_type=DataType.INT32,  unit='V',           name='logger.minutes_ul1_log_ts',                    response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x554D8FEE, index=297, request_data_type=DataType.INT32,                      name='logger.minutes_eac2_log_ts',                   response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x5D34D09D, index=325, request_data_type=DataType.INT32,                      name='logger.month_egrid_load_log_ts',               response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x60A9A532, index=334, request_data_type=DataType.INT32,                      name='logger.day_eext_log_ts',                       response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x669D02FE, index=356, request_data_type=DataType.INT32,                      name='logger.minutes_eac_log_ts',                    response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x6B5A56C2, index=372, request_data_type=DataType.INT32,                      name='logger.month_eb_log_ts',                       response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x6F3876BC, index=391, request_data_type=DataType.INT32,                      name='logger.error_log_time_stamp',                  response_data_type=DataType.EVENT_TABLE, description='Time stamp for error log reading'),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x70BD7C46, index=398, request_data_type=DataType.INT32,                      name='logger.year_eac_log_ts',                       response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x72ACC0BF, index=410, request_data_type=DataType.INT32,  unit='V',           name='logger.minutes_ua_log_ts',                     response_data_type=DataType.TIMESERIES, description='Histogram voltage generator A'),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x76C9A0BD, index=420, request_data_type=DataType.INT32,  unit='%',           name='logger.minutes_soc_targ_log_ts',               response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x921997EE, index=530, request_data_type=DataType.INT32,                      name='logger.month_egrid_feed_log_ts',               response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x9247DB99, index=531, request_data_type=DataType.INT32,                      name='logger.minutes_egrid_load_log_ts',             response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0x9A51A23B, index=563, request_data_type=DataType.UINT16, unit='s',           name='logger.log_rate',                              description='Data log resolution'),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0xA60082A9, index=590, request_data_type=DataType.INT32,  unit='W',           name='logger.minutes_egrid_feed_log_ts',             response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0xA7C708EB, index=597, request_data_type=DataType.INT32,                      name='logger.minutes_eload_log_ts',                  response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0xB20D1AD6, index=628, request_data_type=DataType.INT32,                      name='logger.day_egrid_feed_log_ts',                 response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0xC55EF32E, index=699, request_data_type=DataType.INT32,                      name='logger.year_egrid_load_log_ts',                response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0xCA6D6472, index=720, request_data_type=DataType.INT32,                      name='logger.day_eload_log_ts',                      response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0xCBDAD315, index=727, request_data_type=DataType.INT32,                      name='logger.minutes_ebat_log_ts',                   response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0xD3E94E6B, index=744, request_data_type=DataType.INT32,  unit='°C',          name='logger.minutes_temp_bat_log_ts',               response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0xE04C3900, index=784, request_data_type=DataType.INT32,                      name='logger.day_eac_log_ts',                        response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0xE29C24EB, index=792, request_data_type=DataType.INT32,                      name='logger.minutes_eac3_log_ts',                   response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0xE4DC040A, index=796, request_data_type=DataType.INT32,                      name='logger.month_eext_log_ts',                     response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0xE5FBCC6F, index=799, request_data_type=DataType.INT32,                      name='logger.year_eload_log_ts',                     response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0xF28341E2, index=844, request_data_type=DataType.INT32,                      name='logger.month_eac_log_ts',                      response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0xF76DE445, index=861, request_data_type=DataType.INT32,  unit='°C',          name='logger.minutes_temp_log_ts',                   response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0xFCF4E78D, index=885, request_data_type=DataType.INT32,                      name='logger.day_ea_log_ts',                         response_data_type=DataType.TIMESERIES),
    ObjectInfo(group=ObjectGroup.LOGGER,          object_id=0xA305214D, index=581, request_data_type=DataType.STRING,                     name='logger.buffer'),

    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0x6E03755,  index=22,  request_data_type=DataType.STRING,                     name='wifi.ip',                                      description='IP Address'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0xBA16A10,  index=40,  request_data_type=DataType.ENUM,                       name='wifi.sockb_protocol',                          description='Network mode'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0x14C0E627, index=73,  request_data_type=DataType.STRING,                     name='wifi.password',                                description='WiFi password'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0x1D0623D6, index=97,  request_data_type=DataType.STRING,                     name='wifi.dns_address',                             description='DNS address'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0x392D1BEE, index=192, request_data_type=DataType.UINT8,                      name='wifi.connect_to_server'),  # BOOL?
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0x5673D737, index=301, request_data_type=DataType.BOOL,                       name='wifi.connect_to_wifi'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0x57429627, index=302, request_data_type=DataType.STRING,                     name='wifi.authentication_method',                   description='WiFi authentication method'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0x5952E5E6, index=312, request_data_type=DataType.STRING,                     name='wifi.mask',                                    description='Netmask'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0x5A316247, index=314, request_data_type=DataType.STRING,                     name='wifi.mode',                                    description='WiFi mode'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0x6D7C0BF4, index=384, request_data_type=DataType.INT32,                      name='wifi.sockb_port',                              description='Port'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0x76CAA9BF, index=421, request_data_type=DataType.STRING,                     name='wifi.encryption_algorithm'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0x7B1F7FBE, index=444, request_data_type=DataType.STRING,                     name='wifi.gateway',                                 description='Gateway'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0x7DDE352B, index=453, request_data_type=DataType.STRING,                     name='wifi.sockb_ip'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0x8CA00014, index=500, request_data_type=DataType.INT8,                       name='wifi.result',                                  description='WiFi result'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0xB4222BDE, index=637, request_data_type=DataType.UINT8,                      name='wifi.state'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0xB7C85C51, index=649, request_data_type=DataType.BOOL,                       name='wifi.use_ethernet'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0xD5790CE1, index=752, request_data_type=DataType.BOOL,                       name='wifi.use_wifi',                                description='Enable Wi-Fi Access Point'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0xF8DECCE6, index=865, request_data_type=DataType.STRING,                     name='wifi.connected_ap_ssid',                       description='WiFi associated AP'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0xF9FD0D61, index=867, request_data_type=DataType.STRING,                     name='wifi.service_ip',                              description='Server to connect to to wait for commands, usually used by the vendor service personell'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0xFF2A258B, index=894, request_data_type=DataType.STRING,                     name='wifi.server_ip',                               description='Server to connect to to wait for commands, usually used by the vendor service personell'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0xA1D2B565, index=578, request_data_type=DataType.INT32,                      name='wifi.service_port'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0xB7FEA209, index=650, request_data_type=DataType.INT32,                      name='wifi.connect_service_timestamp',               description='Service auto disconnect time'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0xD83DC6AC, index=757, request_data_type=DataType.INT32,                      name='wifi.server_port'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0x53886C09, index=290, request_data_type=DataType.UINT8,                      name='wifi.connect_to_service'),
    ObjectInfo(group=ObjectGroup.WIFI,            object_id=0x907CD1DF, index=517, request_data_type=DataType.INT32,  unit='s',           name='wifi.connect_service_max_duration',            description='Service connection max duration'),

    ObjectInfo(group=ObjectGroup.ADC,             object_id=0x7C61FAD,  index=28,  request_data_type=DataType.UINT16, unit='V',           name='adc.u_ref_1_5v[0]',                            description='Reference voltage 1'),
    ObjectInfo(group=ObjectGroup.ADC,             object_id=0x16B28CCA, index=80,  request_data_type=DataType.UINT16, unit='V',           name='adc.u_ref_1_5v[1]',                            description='Reference voltage 2'),
    ObjectInfo(group=ObjectGroup.ADC,             object_id=0x508FCE78, index=282, request_data_type=DataType.UINT16, unit='V',           name='adc.u_ref_1_5v[3]',                            description='Reference voltage 4'),
    ObjectInfo(group=ObjectGroup.ADC,             object_id=0x715C84A1, index=403, request_data_type=DataType.UINT16, unit='V',           name='adc.u_ref_1_5v[2]',                            description='Reference voltage 3'),
    ObjectInfo(group=ObjectGroup.ADC,             object_id=0xB84FDCF9, index=654, request_data_type=DataType.FLOAT,  unit='V',           name='adc.u_acc',                                    description='Battery voltage (inverter)'),

    ObjectInfo(group=ObjectGroup.NET,             object_id=0x8679611,  index=29,  request_data_type=DataType.UINT32,                     name='net.id'),
    ObjectInfo(group=ObjectGroup.NET,             object_id=0xC3815C2,  index=42,  request_data_type=DataType.FLOAT,                      name='net.load_reduction'),
    ObjectInfo(group=ObjectGroup.NET,             object_id=0x23F525DE, index=126, request_data_type=DataType.UINT16,                     name='net.command'),
    ObjectInfo(group=ObjectGroup.NET,             object_id=0x2E06172D, index=154, request_data_type=DataType.UINT32,                     name='net.net_tunnel_id'),
    ObjectInfo(group=ObjectGroup.NET,             object_id=0x3500F1E8, index=176, request_data_type=DataType.INT8,                       name='net.index'),
    ObjectInfo(group=ObjectGroup.NET,             object_id=0x36214C57, index=180, request_data_type=DataType.FLOAT,                      name='net.prev_k'),
    ObjectInfo(group=ObjectGroup.NET,             object_id=0x3AA565FC, index=201, request_data_type=DataType.UNKNOWN,                    name='net.package'),
    ObjectInfo(group=ObjectGroup.NET,             object_id=0x46635546, index=238, request_data_type=DataType.INT8,                       name='net.n_descendants',                            description='Number of descendant slaves'),
    ObjectInfo(group=ObjectGroup.NET,             object_id=0x5D1B0835, index=324, request_data_type=DataType.BOOL,                       name='net.use_network_filter'),
    ObjectInfo(group=ObjectGroup.NET,             object_id=0x5E540FB2, index=326, request_data_type=DataType.BOOL,                       name='net.update_slaves',                            description='Activate aut. update slaves'),
    ObjectInfo(group=ObjectGroup.NET,             object_id=0x67C0A2F5, index=362, request_data_type=DataType.FLOAT,                      name='net.slave_p_total'),
    ObjectInfo(group=ObjectGroup.NET,             object_id=0x6DCC4097, index=386, request_data_type=DataType.FLOAT,                      name='net.master_timeout'),
    ObjectInfo(group=ObjectGroup.NET,             object_id=0xBFFF3CAD, index=676, request_data_type=DataType.UINT8,                      name='net.n_slaves'),
    ObjectInfo(group=ObjectGroup.NET,             object_id=0xC0A7074F, index=681, request_data_type=DataType.UNKNOWN,                    name='net.slave_data'),
    ObjectInfo(group=ObjectGroup.NET,             object_id=0xD3085D80, index=743, request_data_type=DataType.FLOAT,                      name='net.soc_av'),
    ObjectInfo(group=ObjectGroup.NET,             object_id=0xD5205A45, index=749, request_data_type=DataType.FLOAT,                      name='net.slave_timeout'),
    ObjectInfo(group=ObjectGroup.NET,             object_id=0xDB62DCB7, index=769, request_data_type=DataType.UINT8,                      name='net.n_devices'),

    ObjectInfo(group=ObjectGroup.ACC_CONV,        object_id=0xB0FA4D23, index=623, request_data_type=DataType.FLOAT,  unit='A',           name='acc_conv.i_charge_max',                        description='Max. battery converter charge current'),
    ObjectInfo(group=ObjectGroup.ACC_CONV,        object_id=0xB408E40A, index=636, request_data_type=DataType.FLOAT,                      name='acc_conv.i_acc_lp_slow'),
    ObjectInfo(group=ObjectGroup.ACC_CONV,        object_id=0xC642B9D6, index=701, request_data_type=DataType.FLOAT,  unit='A',           name='acc_conv.i_discharge_max',                     description='Max. battery converter discharge current'),
    ObjectInfo(group=ObjectGroup.ACC_CONV,        object_id=0xD9F9F35B, index=762, request_data_type=DataType.UINT8,                      name='acc_conv.state_slow'),
    ObjectInfo(group=ObjectGroup.ACC_CONV,        object_id=0xE3F4D1DF, index=794, request_data_type=DataType.FLOAT,  unit='A',           name='acc_conv.i_max',                               description='Max. battery converter current'),
    ObjectInfo(group=ObjectGroup.ACC_CONV,        object_id=0xAFDD6CF,  index=38,  request_data_type=DataType.FLOAT,  unit='A',           name='acc_conv.i_acc_lp_fast',                       description='Battery current'),

    ObjectInfo(group=ObjectGroup.DC_CONV,         object_id=0xCB5D21B,  index=44,  request_data_type=DataType.FLOAT,  unit='W',           name='dc_conv.dc_conv_struct[1].p_dc_lp',            description='Solar generator B power'),
    ObjectInfo(group=ObjectGroup.DC_CONV,         object_id=0x5BB8075A, index=319, request_data_type=DataType.FLOAT,  unit='V',           name='dc_conv.dc_conv_struct[1].u_sg_lp',            description='Solar generator B voltage'),
    ObjectInfo(group=ObjectGroup.DC_CONV,         object_id=0x5E942C62, index=327, request_data_type=DataType.FLOAT,  unit='V',           name='dc_conv.dc_conv_struct[1].mpp.fixed_voltage',  description='Fixed voltage Solar generator B'),
    ObjectInfo(group=ObjectGroup.DC_CONV,         object_id=0x62B8940B, index=339, request_data_type=DataType.FLOAT,  unit='V',           name='dc_conv.start_voltage',                        description='Inverter DC-voltage start value'),
    ObjectInfo(group=ObjectGroup.DC_CONV,         object_id=0x6476A836, index=346, request_data_type=DataType.BOOL,                       name='dc_conv.dc_conv_struct[0].mpp.enable_scan',    description='Enable rescan for global MPP on solar generator A'),
    ObjectInfo(group=ObjectGroup.DC_CONV,         object_id=0x701A0482, index=395, request_data_type=DataType.BOOL,                       name='dc_conv.dc_conv_struct[0].enabled',            description='Solar generator A connected'),
    ObjectInfo(group=ObjectGroup.DC_CONV,         object_id=0x8DD1C728, index=503, request_data_type=DataType.BOOL,                       name='dc_conv.dc_conv_struct[1].mpp.enable_scan',    description='Enable rescan for global MPP on solar generator B'),
    ObjectInfo(group=ObjectGroup.DC_CONV,         object_id=0x9E1A88F5, index=571, request_data_type=DataType.FLOAT,  unit='V',           name='dc_conv.dc_conv_struct[0].mpp.fixed_voltage',  description='Fixed voltage Solar generator A'),
    ObjectInfo(group=ObjectGroup.DC_CONV,         object_id=0xAA9AA253, index=610, request_data_type=DataType.FLOAT,  unit='W',           name='dc_conv.dc_conv_struct[1].p_dc',               description='Solar generator B power'),
    ObjectInfo(group=ObjectGroup.DC_CONV,         object_id=0xB298395D, index=632, request_data_type=DataType.FLOAT,  unit='V',           name='dc_conv.dc_conv_struct[0].u_sg_lp',            description='Solar generator A voltage'),
    ObjectInfo(group=ObjectGroup.DC_CONV,         object_id=0xB5317B78, index=640, request_data_type=DataType.FLOAT,  unit='W',           name='dc_conv.dc_conv_struct[0].p_dc',               description='Solar generator A power'),
    ObjectInfo(group=ObjectGroup.DC_CONV,         object_id=0xB836B50C, index=652, request_data_type=DataType.FLOAT,  unit='V',           name='dc_conv.dc_conv_struct[1].rescan_correction',  description='Last global rescan MPP correction on input B'),
    ObjectInfo(group=ObjectGroup.DC_CONV,         object_id=0xDB11855B, index=766, request_data_type=DataType.FLOAT,  unit='W',           name='dc_conv.dc_conv_struct[0].p_dc_lp',            description='Solar generator A power'),
    ObjectInfo(group=ObjectGroup.DC_CONV,         object_id=0xDB45ABD0, index=768, request_data_type=DataType.FLOAT,  unit='V',           name='dc_conv.dc_conv_struct[0].rescan_correction',  description='Last global rescan MPP correction on input A'),
    ObjectInfo(group=ObjectGroup.DC_CONV,         object_id=0xFED51BD2, index=893, request_data_type=DataType.BOOL,                       name='dc_conv.dc_conv_struct[1].enabled',            description='Solar generator B connected'),
    ObjectInfo(group=ObjectGroup.DC_CONV,         object_id=0x226A23A4, index=117, request_data_type=DataType.FLOAT,  unit='V',           name='dc_conv.dc_conv_struct[0].u_target',           description='MPP on input A'),
    ObjectInfo(group=ObjectGroup.DC_CONV,         object_id=0x675776B1, index=360, request_data_type=DataType.FLOAT,  unit='V',           name='dc_conv.dc_conv_struct[1].u_target',           description='MPP on input B'),
    ObjectInfo(group=ObjectGroup.DC_CONV,         object_id=0xF87A2A1E, index=863, request_data_type=DataType.UINT32,                     name='dc_conv.last_rescan',                          description='Last global rescan'),

    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xCBA34B9,  index=45,  request_data_type=DataType.FLOAT,  unit='V',           name='nsm.u_q_u[3]',                                 description='High voltage max. point'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x10842019, index=63,  request_data_type=DataType.FLOAT,  unit='cos(rct_db)', name='nsm.cos_phi_p[3][1]',                          description='Point 4 (positive = overexcited)'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x1089ACA9, index=64,  request_data_type=DataType.FLOAT,  unit='V',           name='nsm.u_q_u[0]',                                 description='Low voltage min. point'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x14FCA232, index=74,  request_data_type=DataType.FLOAT,  unit='P/Pn',        name='nsm.rpm_lock_out_power',                       description='Reactive Power Mode lock-out power'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x26260419, index=134, request_data_type=DataType.FLOAT,  unit='P/Pn',        name='nsm.cos_phi_p[1][0]',                          description='Point 2'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x32CD0DB3, index=167, request_data_type=DataType.FLOAT,  unit='cos(Phi)',    name='nsm.cos_phi_p[0][1]',                          description='Point 1 (positive = overexcited)'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x33F76B78, index=172, request_data_type=DataType.FLOAT,  unit='V',           name='nsm.p_u[0][1]',                                description='Point 1 voltage'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x3515F4A0, index=178, request_data_type=DataType.FLOAT,  unit='V',           name='nsm.p_u[3][1]',                                description='Point 4 voltage'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x360BDE8A, index=179, request_data_type=DataType.FLOAT,  unit='P/(Pn*s)',    name='nsm.startup_grad',                             description='Startup gradient'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x4397D078, index=229, request_data_type=DataType.FLOAT,  unit='cos(Phi)',    name='nsm.cos_phi_p[1][1]',                          description='Point 2 (positive = overexcited)'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x43CD0B6F, index=230, request_data_type=DataType.FLOAT,  unit='s',           name='nsm.pf_delay',                                 description='Delay time after P(f)'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x4A61BAEE, index=251, request_data_type=DataType.FLOAT,  unit='P/Pn',        name='nsm.p_u[3][0]',                                description='Point 4 P/Pn'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x4C2A7CDC, index=259, request_data_type=DataType.FLOAT,  unit='cos(Phi)',    name='nsm.cos_phi_p[2][1]',                          description='Point 3 (positive = overexcited)'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x4C374958, index=260, request_data_type=DataType.FLOAT,  unit='P/(Pn*s)',    name='nsm.startup_grad_after_fault',                 description='Startup gradient after fault'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x53EF7649, index=291, request_data_type=DataType.FLOAT,                      name='nsm.p_u[0][0]',                                description='Point 1 P/Pn'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x71465EAF, index=402, request_data_type=DataType.FLOAT,  unit='s',           name='nsm.cos_phi_ts',                               description='Time const for filter'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x7232F7AF, index=408, request_data_type=DataType.ENUM,                       name='nsm.apm',                                      description='Active power mode',
               enum_map={0: 'Off', 1: 'P(f)'}),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x7A5C91F8, index=437, request_data_type=DataType.FLOAT,                      name='nsm.p_u[1][0]',                                description='Point 2 P/Pn'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x7AF779C1, index=443, request_data_type=DataType.BOOL,                       name='nsm.pu_mode',                                  description='P(U) mode 0: Pn 1: Pload'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x81AF854E, index=466, request_data_type=DataType.BOOL,                       name='nsm.pu_use',                                   description='P(U) active'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x83A5333A, index=472, request_data_type=DataType.FLOAT,  unit='P/Pn',        name='nsm.cos_phi_p[0][0]',                          description='Point 1'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x88DEBCFE, index=488, request_data_type=DataType.FLOAT,  unit='var',         name='nsm.q_u_max_u_high',                           description='Qmax at upper voltage level (positive = overexcited)'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x93E6918D, index=539, request_data_type=DataType.FLOAT,  unit='Hz',          name='nsm.f_exit',                                   description='Exit frequency for P(f) over-frequency mode'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x9680077F, index=549, request_data_type=DataType.FLOAT,  unit='P/Pn',        name='nsm.cos_phi_p[2][0]',                          description='Point 3'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xA33D0954, index=583, request_data_type=DataType.BOOL,                       name='nsm.q_u_hysteresis',                           description='Curve with hysteresis'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xA5044DCD, index=586, request_data_type=DataType.FLOAT,  unit='P/Pn',        name='nsm.p_u[2][0]',                                description='Point 3'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xB76E2B4C, index=647, request_data_type=DataType.FLOAT,                      name='nsm.cos_phi_const',                            description='Cos phi constant value (positive = overexcited)'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xB98C8194, index=656, request_data_type=DataType.FLOAT,                      name='nsm.min_cos_phi',                              description='Minimum allowed cos(phi) [0..1]'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xBB617E51, index=663, request_data_type=DataType.FLOAT,  unit='V',           name='nsm.u_q_u[1]',                                 description='Low voltage max. point'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xC3352B17, index=689, request_data_type=DataType.ENUM,                       name='nsm.rpm',                                      description='Reactive power mode',
               enum_map={0: 'Off', 1: 'Const cos(phi)', 2: 'Const Q', 3: 'cos(phi)(P)', 4: 'Q(U)'}),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xC46E9CA4, index=696, request_data_type=DataType.FLOAT,  unit='V',           name='nsm.u_lock_out',                               description='Cos phi(P) lock out voltage'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xCB9E1E6C, index=725, request_data_type=DataType.FLOAT,  unit='var',         name='nsm.Q_const',                                  description='Q constant value (positive = overexcited)'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xCCB51399, index=729, request_data_type=DataType.FLOAT,  unit='var',         name='nsm.q_u_max_u_low',                            description='Qmax at lower voltage level (positive = overexcited)'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xD580567B, index=753, request_data_type=DataType.FLOAT,  unit='V',           name='nsm.u_lock_in',                                description='Cos phi(P) lock in voltage'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xD884AF95, index=759, request_data_type=DataType.FLOAT,  unit='P/(Pn*s)',    name='nsm.pf_desc_grad',                             description='Power decrease gradient for P(f) mode'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xE271C6D2, index=791, request_data_type=DataType.FLOAT,  unit='V',           name='nsm.u_q_u[2]',                                 description='High voltage min. point'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xE49BE3ED, index=795, request_data_type=DataType.FLOAT,  unit='P/(Pn*s)',    name='nsm.pf_rise_grad',                             description='Power increase gradient after P(f) restriction'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xE6F1CB83, index=803, request_data_type=DataType.FLOAT,  unit='s',           name='nsm.pu_ts',                                    description='Time const for filter'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xEB7773BF, index=815, request_data_type=DataType.FLOAT,  unit='V',           name='nsm.p_u[1][1]',                                description='Point 2 voltage'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xEE049B1F, index=820, request_data_type=DataType.BOOL,                       name='nsm.pf_hysteresis',                            description='Hysteresis mode'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xF2405AC6, index=839, request_data_type=DataType.FLOAT,  unit='W',           name='nsm.p_limit',                                  description='Max. grid power'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xF25591AA, index=841, request_data_type=DataType.FLOAT,  unit='P/Pn',        name='nsm.cos_phi_p[3][0]',                          description='Point 4'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xF49F58F2, index=852, request_data_type=DataType.FLOAT,  unit='V',           name='nsm.p_u[2][1]',                                description='Point 3 voltage'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xF6A85818, index=859, request_data_type=DataType.FLOAT,  unit='Hz',          name='nsm.f_entry',                                  description='Entry frequency for P(f) over-frequency mode'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xFCC39293, index=884, request_data_type=DataType.FLOAT,  unit='P/Pn',        name='nsm.rpm_lock_in_power',                        description='Reactive Power Mode lock-in power'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x7E75B17A, index=456, request_data_type=DataType.FLOAT,                      name='nsm.q_u_max_u_high_rel',                       description='Qmax at upper voltage level relative to Smax (positive = overexcited)'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x8D33B6BC, index=501, request_data_type=DataType.FLOAT,  unit='Hz',          name='nsm.f_low_exit',                               description='Exit frequency for P(f) under-frequency mode'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xC07E02CE, index=680, request_data_type=DataType.ENUM,                       name='nsm.q_u_sel',                                  description='Voltage selection'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xE952FF2D, index=808, request_data_type=DataType.FLOAT,                      name='nsm.q_u_max_u_low_rel',                        description='Qmax at lower voltage level relative to Smax (positive = overexcited)'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xF3FD6C4C, index=847, request_data_type=DataType.BOOL,                       name='nsm.pf_use_p_max',                             description='By over-frequency in P(f) use Pmax instead of Pmom (instant P).'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0xFAA837C8, index=870, request_data_type=DataType.FLOAT,  unit='1/Pn*Hz',     name='nsm.f_low_rise_grad',                          description='Power rise gradient for P(f) under-frequency mode without battery'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x4EAAA98,  index=13,  request_data_type=DataType.FLOAT,  unit='Hz',          name='nsm.f_low_entry',                              description='Entry frequency for P(f) under-frequency mode'),
    ObjectInfo(group=ObjectGroup.NSM,             object_id=0x38789061, index=189, request_data_type=DataType.FLOAT,  unit='1/Pn*Hz',     name='nsm.f_low_rise_grad_storage',                  description='Power rise gradient for P(f) under-frequency mode with battery'),

    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0xDF45696,  index=53,  request_data_type=DataType.BOOL,                       name='io_board.io1_polarity',                        description='Inverted signal on input I/O 1'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0xE799A56,  index=56,  request_data_type=DataType.FLOAT,                      name='io_board.rse_table[0]',                        description='K4..K1: 0000'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0xFB40090,  index=61,  request_data_type=DataType.UINT8,                      name='io_board.check_rs485_result'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x1B5445C4, index=94,  request_data_type=DataType.UINT16,                     name='io_board.check_rse_result'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x29CA60F8, index=148, request_data_type=DataType.FLOAT,                      name='io_board.rse_table[10]',                       description='K4..K1: 1010'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x2E0C6220, index=155, request_data_type=DataType.FLOAT,  unit='s',           name='io_board.home_relay_sw_off_delay',             description='Switching off delay'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x3C705F61, index=208, request_data_type=DataType.FLOAT,                      name='io_board.rse_table[8]',                        description='K4..K1: 1000'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x3DBCC6B4, index=213, request_data_type=DataType.FLOAT,                      name='io_board.rse_table[6]',                        description='K4..K1: 0110'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x4F330E08, index=275, request_data_type=DataType.ENUM,                       name='io_board.io2_usage',                           description='Digital I/O 2 usage',
               enum_map={0: 'I/O not used', 1: 'Input S0 grid power consumption', 2: 'Input S0 grid power feed-in', 3: 'Input S0 household power', 4: 'Output S0 inverter power', 5: 'Input level switch', 6: 'Input emergency turn off',
                         7: 'Output S0 grid power feed-in', 8: 'Output S0 household power', 9: 'Output S0 solar power', 10: 'Input S0 external power'}),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x54DBC202, index=296, request_data_type=DataType.FLOAT,                      name='io_board.rse_table[12]',                       description='K4..K1: 1100'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x5867B3BE, index=307, request_data_type=DataType.FLOAT,                      name='io_board.rse_table[2]',                        description='K4..K1: 0010'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x58C1A946, index=308, request_data_type=DataType.UINT8,                      name='io_board.check_state'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x5BD2DB45, index=320, request_data_type=DataType.INT16,                      name='io_board.io1_s0_imp_per_kwh',                  description='Number of impulses per kWh for S0 signal on I/O 1'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x5EE03C45, index=328, request_data_type=DataType.ENUM,                       name='io_board.alarm_home_relay_mode',               description='Multifunctional relay usage',
               enum_map={0: 'Not used', 1: 'Alarm', 2: 'Load'}),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x664A1326, index=355, request_data_type=DataType.FLOAT,                      name='io_board.rse_table[14]',                       description='K4..K1: 1110'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x6830F6E4, index=364, request_data_type=DataType.FLOAT,                      name='io_board.rse_table[9]',                        description='K4..K1: 1001'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x68BA92E1, index=365, request_data_type=DataType.INT16,                      name='io_board.io2_s0_imp_per_kwh',                  description='Number of impulses per kWh for S0 signal on I/O 2'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x6C2D00E4, index=379, request_data_type=DataType.FLOAT,                      name='io_board.rse_table[1]',                        description='K4..K1: 0001'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x7689BE6A, index=419, request_data_type=DataType.FLOAT,  unit='s',           name='io_board.home_relay_sw_on_delay',              description='Switching on delay'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x792A7B79, index=431, request_data_type=DataType.ENUM,                       name='io_board.s0_direction',                        description='S0 inputs single or bidirectional',
               enum_map={0: 'I/O 1 & I/O 2 single', 1: 'I/O 1 bidirectional', 2: 'I/O 2 bidirectional'}),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x7C556C7A, index=448, request_data_type=DataType.BOOL,                       name='io_board.io2_polarity',                        description='Inverted signal on input I/O 2'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x8320B84C, index=470, request_data_type=DataType.FLOAT,  unit='s',           name='io_board.rse_data_delay',                      description='Delay for new K4..K1 data'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x872F380B, index=479, request_data_type=DataType.FLOAT,  unit='W',           name='io_board.load_set',                            description='Dummy household load'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x88C9707B, index=487, request_data_type=DataType.FLOAT,                      name='io_board.rse_table[15]',                       description='K4..K1: 1111'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x88F36D45, index=490, request_data_type=DataType.UINT8,                      name='io_board.rse_data',                            description='Actual K4..K1 data'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x90F123FA, index=522, request_data_type=DataType.ENUM,                       name='io_board.io1_usage',                           description='Digital I/O 1 usage',
               enum_map={0: 'I/O not used', 1: 'Input S0 grid power consumption', 2: 'Input S0 grid power feed-in', 3: 'Input S0 household power', 4: 'Output S0 inverter power', 5: 'Input level switch', 6: 'Input emergency turn off',
                         7: 'Output S0 grid power feed-in', 8: 'Output S0 household power', 9: 'Output S0 solar power', 10: 'Input S0 external power'}),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x98ACC1B8, index=557, request_data_type=DataType.FLOAT,                      name='io_board.rse_table[4]',                        description='K4..K1: 0100'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0x9B92023F, index=566, request_data_type=DataType.FLOAT,                      name='io_board.rse_table[7]',                        description='K4..K1: 0111'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0xA3393749, index=582, request_data_type=DataType.UINT8,                      name='io_board.check_start'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0xAACE057A, index=612, request_data_type=DataType.FLOAT,  unit='s',           name='io_board.io1_s0_min_duration',                 description='Minimum S0 signal duration on I/O 1'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0xAC2E2A56, index=614, request_data_type=DataType.FLOAT,                      name='io_board.rse_table[5]',                        description='K4..K1: 0101'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0xB851FA70, index=655, request_data_type=DataType.FLOAT,                      name='io_board.rse_table[11]',                       description='K4..K1: 1011'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0xBCC6F92F, index=666, request_data_type=DataType.FLOAT,  unit='W',           name='io_board.home_relay_threshold',                description='Switching on threshold'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0xBDFE5547, index=674, request_data_type=DataType.FLOAT,                      name='io_board.rse_table[3]',                        description='K4..K1: 0011'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0xC7605E16, index=709, request_data_type=DataType.FLOAT,                      name='io_board.s0_sum'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0xCB1B3B10, index=722, request_data_type=DataType.FLOAT,  unit='s',           name='io_board.io2_s0_min_duration',                 description='Minimum S0 signal duration on I/O 2'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0xD45913EC, index=747, request_data_type=DataType.FLOAT,                      name='io_board.rse_table[13]',                       description='K4..K1: 1101'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0xE52B89FA, index=798, request_data_type=DataType.FLOAT,  unit='W',           name='io_board.home_relay_off_threshold',            description='Switching off threshold'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0xE96F1844, index=809, request_data_type=DataType.FLOAT,                      name='io_board.s0_external_power'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0xF42D4DD0, index=849, request_data_type=DataType.ENUM,                       name='io_board.alarm_home_value',                    description='Evaluated value',
               enum_map={0: 'Pgrid', 1: 'Pgrid + Pbat charge'}),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0xFA7DB323, index=869, request_data_type=DataType.UINT16,                     name='io_board.check_s0_result'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0xBBE6B9DF, index=664, request_data_type=DataType.FLOAT,  unit='P/Pn/s',      name='io_board.p_rse_rise_grad',                     description='Power rise gradient'),
    ObjectInfo(group=ObjectGroup.IO_BOARD,        object_id=0xDAC7DD86, index=765, request_data_type=DataType.FLOAT,  unit='P/Pn/s',      name='io_board.p_rse_desc_grad',                     description='Power descent gradient'),

    ObjectInfo(group=ObjectGroup.FLASH_RTC,       object_id=0xE0505B4,  index=54,  request_data_type=DataType.UINT32,                     name='flash_rtc.time_stamp_set',                     description='Set date/time'),
    ObjectInfo(group=ObjectGroup.FLASH_RTC,       object_id=0x2266DCB8, index=116, request_data_type=DataType.FLOAT,  unit='ppm',         name='flash_rtc.rtc_mcc_quartz_max_diff',            description='Maximum allowed quartz frequency difference between RTC and Microcontroller'),
    ObjectInfo(group=ObjectGroup.FLASH_RTC,       object_id=0x3903A5E9, index=190, request_data_type=DataType.BOOL,                       name='flash_rtc.flag_time_auto_switch',              description='Automatically adjust clock for daylight saving time'),
    ObjectInfo(group=ObjectGroup.FLASH_RTC,       object_id=0x4E0C56F2, index=267, request_data_type=DataType.FLOAT,  unit='ppm',         name='flash_rtc.rtc_mcc_quartz_ppm_difference',      description='Quartz frequency difference between RTC and Microcontroller'),
    ObjectInfo(group=ObjectGroup.FLASH_RTC,       object_id=0x7301A5A7, index=411, request_data_type=DataType.UINT32,                     name='flash_rtc.time_stamp_factory',                 description='Production date'),
    ObjectInfo(group=ObjectGroup.FLASH_RTC,       object_id=0xD166D94D, index=738, request_data_type=DataType.UINT32,                     name='flash_rtc.time_stamp',                         description='Actual date/time'),
    ObjectInfo(group=ObjectGroup.FLASH_RTC,       object_id=0xDD90A328, index=774, request_data_type=DataType.UINT32,                     name='flash_rtc.time_stamp_update',                  description='Last update date'),

    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x1156DFD0, index=67,  request_data_type=DataType.FLOAT,  unit='W',           name='power_mng.battery_power',                      description='Battery discharge power'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x1D2994EA, index=98,  request_data_type=DataType.FLOAT,  unit='W',           name='power_mng.soc_charge_power',                   description='Maintenance charge power'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x315D1490, index=165, request_data_type=DataType.UINT8,                      name='power_mng.bat_empty_full',                     description='Bit 0 - battery was empty, bit 1 - battery was full'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x36A9E9A6, index=184, request_data_type=DataType.BOOL,                       name='power_mng.use_grid_power_enable',              description='Utilize external Inverter energy'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x40B07CA4, index=968, request_data_type=DataType.STRING,                     name='power_mng.schedule[3]??'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x47A1DACA, index=971, request_data_type=DataType.STRING,                     name='power_mng.schedule[5]??'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x592B13DF, index=966, request_data_type=DataType.STRING,                     name='power_mng.schedule[1]??'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x59358EB2, index=310, request_data_type=DataType.FLOAT,  unit='V',           name='power_mng.maximum_charge_voltage',             description='Max. battery charge voltage'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x5B10CE81, index=317, request_data_type=DataType.UINT8,                      name='power_mng.is_heiphoss',                        description='HeiPhoss mode'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x6599E3D3, index=965, request_data_type=DataType.STRING,                     name='power_mng.schedule[0]??'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x682CDDA1, index=363, request_data_type=DataType.ENUM,                       name='power_mng.battery_type',                       description='Battery type',
               enum_map={0: 'Lead-acid Powerfit', 1: 'Li-Ion Akesol', 2: 'Laukner', 3: 'Li-Ion RCT Power', 4: 'Li-Ion Zach', 5: 'No battery', 6: 'Power loop 200 V', 7: 'BYD D-BOX H'}),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x7AF0AD03, index=972, request_data_type=DataType.STRING,                     name='power_mng.schedule[6]??'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x8EBF9574, index=506, request_data_type=DataType.FLOAT,                      name='power_mng.soc_min_island',                     description='Min SOC target (island)'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x93C0C2E2, index=538, request_data_type=DataType.UINT32, unit='days',        name='power_mng.bat_calib_reqularity',               description='Battery calibration interval'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x972B3029, index=551, request_data_type=DataType.FLOAT,  unit='V',           name='power_mng.stop_discharge_voltage_buffer',      description='Stop discharge voltage buffer'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x97997C93, index=552, request_data_type=DataType.FLOAT,                      name='power_mng.soc_max',                            description='Max SOC target'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x97E203F9, index=554, request_data_type=DataType.BOOL,                       name='power_mng.is_grid'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x97E3A6F2, index=555, request_data_type=DataType.FLOAT,  unit='V',           name='power_mng.u_acc_lp',                           description='Battery voltage (inverter)'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x99EE89CB, index=561, request_data_type=DataType.ENUM,                       name='power_mng.power_lim_src_index',                description='Power limit source'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x9A33F9B7, index=967, request_data_type=DataType.STRING,                     name='power_mng.schedule[2]??'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x9F52F968, index=573, request_data_type=DataType.BOOL,                       name='power_mng.feed_asymmetrical',                  description='Allow asymmetrical feed'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xA7FA5C5D, index=600, request_data_type=DataType.FLOAT,  unit='V',           name='power_mng.u_acc_mix_lp',                       description='Battery voltage'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xA95EE214, index=607, request_data_type=DataType.FLOAT,                      name='power_mng.model.bat_power_change'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xAEF76FA1, index=617, request_data_type=DataType.FLOAT,  unit='V',           name='power_mng.minimum_discharge_voltage',          description='Min. battery discharge voltage'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xB6623608, index=644, request_data_type=DataType.UINT32,                     name='power_mng.bat_next_calib_date',                description='Next battery calibration'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xBD008E29, index=667, request_data_type=DataType.FLOAT,  unit='W',           name='power_mng.battery_power_extern',               description='Battery target power (positive = discharge)'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xBD3A23C3, index=668, request_data_type=DataType.FLOAT,                      name='power_mng.soc_charge',                         description='SOC min maintenance charge'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xC7459513, index=708, request_data_type=DataType.ENUM,                       name='power_mng.force_inv_class',                    description='Change inverter class',
               enum_map={0: 'take from serial number', 1: 'power inverter', 2: 'power storage'}),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xCE266F0F, index=731, request_data_type=DataType.FLOAT,                      name='power_mng.soc_min',                            description='Min SOC target'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xD197CBE0, index=739, request_data_type=DataType.FLOAT,  unit='A',           name='power_mng.stop_charge_current',                description='Stop charge current'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xD1DFC969, index=740, request_data_type=DataType.FLOAT,                      name='power_mng.soc_target_set',                     description='Force SOC target'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xDC667958, index=770, request_data_type=DataType.UINT8,                      name='power_mng.state',                              description='Battery state machine'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xE9BBF6E4, index=810, request_data_type=DataType.FLOAT,  unit='Ah',          name='power_mng.amp_hours_measured',                 description='Measured battery capacity'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xE24B00BD, index=973, request_data_type=DataType.STRING,                     name='power_mng.schedule[7]??'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xF1342795, index=834, request_data_type=DataType.FLOAT,  unit='A',           name='power_mng.stop_discharge_current',             description='Stop discharge current'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xF168B748, index=835, request_data_type=DataType.ENUM,                       name='power_mng.soc_strategy',                       description='SOC target selection',
               enum_map={0: 'SOC target = SOC', 1: 'Constant', 2: 'External', 3: 'Middle battery voltage', 4: 'Internal', 5: 'Schedule'}),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xF393B7B0, index=846, request_data_type=DataType.FLOAT,  unit='W',           name='power_mng.calib_charge_power',                 description='Calibration charge power'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xF52C0B50, index=969, request_data_type=DataType.STRING,                     name='power_mng.schedule[4]??'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xFBD94C1F, index=875, request_data_type=DataType.FLOAT,  unit='Ah',          name='power_mng.amp_hours',                          description='Battery energy'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xC9900716, index=717, request_data_type=DataType.BOOL,                       name='power_mng.is_island_only',                     description='Island without power switch support'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xE24B00BD, index=790, request_data_type=DataType.STRING,                     name='power_mng.schedule[1]'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0xF52C0B50, index=853, request_data_type=DataType.STRING,                     name='power_mng.schedule[7]'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x11F41DB,  index=1,   request_data_type=DataType.STRING,                     name='power_mng.schedule[0]'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x15AB1A61, index=75,  request_data_type=DataType.STRING,                     name='power_mng.schedule[2]'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x40B07CA4, index=221, request_data_type=DataType.STRING,                     name='power_mng.schedule[6]'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x47A1DACA, index=244, request_data_type=DataType.STRING,                     name='power_mng.schedule[8]'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x592B13DF, index=309, request_data_type=DataType.STRING,                     name='power_mng.schedule[4]'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x6599E3D3, index=350, request_data_type=DataType.STRING,                     name='power_mng.schedule[3]'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x663F1452, index=354, request_data_type=DataType.UINT8,                      name='power_mng.n_batteries'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x672552DC, index=358, request_data_type=DataType.UINT8,                      name='power_mng.bat_calib_days_in_advance',          description='Battery calibration days in advance'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x7AF0AD03, index=442, request_data_type=DataType.STRING,                     name='power_mng.schedule[9]'),
    ObjectInfo(group=ObjectGroup.POWER_MNG,       object_id=0x9A33F9B7, index=562, request_data_type=DataType.STRING,                     name='power_mng.schedule[5]'),

    ObjectInfo(group=ObjectGroup.BUF_V_CONTROL,   object_id=0x4BC0F974, index=255, request_data_type=DataType.FLOAT,  unit='Wp',          name='buf_v_control.power_reduction_max_solar',      description='Solar plant peak power'),
    ObjectInfo(group=ObjectGroup.BUF_V_CONTROL,   object_id=0xF473BC5E, index=851, request_data_type=DataType.FLOAT,  unit='W',           name='buf_v_control.power_reduction_max_solar_grid', description='Max. allowed grid feed-in power'),
    ObjectInfo(group=ObjectGroup.BUF_V_CONTROL,   object_id=0xFE1AA500, index=890, request_data_type=DataType.FLOAT,                      name='buf_v_control.power_reduction',                description='External power reduction based on solar plant peak power [0..1]'),

    ObjectInfo(group=ObjectGroup.DB,              object_id=0x16AF2A92, index=79,  request_data_type=DataType.FLOAT,                      name='db.power_board.Current_Mean'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0x17E3AF97, index=84,  request_data_type=DataType.FLOAT,                      name='db.power_board.adc_p9V_meas'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0x1F9CBBF2, index=105, request_data_type=DataType.FLOAT,                      name='db.power_board.Calibr_Value_Mean'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0x2ED89924, index=157, request_data_type=DataType.FLOAT,  unit='s',           name='db.power_board.afi_t300',                      description='AFI 300 mA switching off time'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0x383A3614, index=188, request_data_type=DataType.FLOAT,  unit='A',           name='db.power_board.afi_i60',                       description='AFI 60 mA threshold'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0x3EFEB931, index=217, request_data_type=DataType.UINT16,                     name='db.power_board.relays_state'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0x43FF47C3, index=232, request_data_type=DataType.FLOAT,  unit='s',           name='db.power_board.afi_t60',                       description='AFI 60 mA switching off time'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0x4F735D10, index=276, request_data_type=DataType.FLOAT,  unit='°C',          name='db.temp2',                                     description='Heat sink (battery actuator) temperature'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0x5CD75669, index=322, request_data_type=DataType.FLOAT,  unit='s',           name='db.power_board.afi_t150',                      description='AFI 150 mA switching off time'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0x6279F2A3, index=338, request_data_type=DataType.UINT32,                     name='db.power_board.version_boot',                  description='PIC bootloader software version'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0x6BA10831, index=373, request_data_type=DataType.FLOAT,  unit='A',           name='db.power_board.afi_i30',                       description='AFI 30 mA threshold'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0x6FB2E2BF, index=392, request_data_type=DataType.FLOAT,  unit='A',           name='db.power_board.afi_i150',                      description='AFI 150 mA threshold'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0x742966A6, index=414, request_data_type=DataType.FLOAT,  unit='A',           name='db.power_board.afi_i300',                      description='AFI 300 mA threshold'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0x7DA7D8B6, index=452, request_data_type=DataType.UINT32,                     name='db.power_board.version_main',                  description='PIC software version'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0x80835476, index=461, request_data_type=DataType.FLOAT,                      name='db.power_board.adc_p5V_W_meas'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0x9981F1AC, index=560, request_data_type=DataType.FLOAT,                      name='db.power_board.adc_m9V_meas'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0xB0307591, index=620, request_data_type=DataType.UINT16,                     name='db.power_board.status',                        description='Power board status'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0xB69171C4, index=645, request_data_type=DataType.FLOAT,                      name='db.power_board.Current_AC_RMS'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0xC0B7C4D2, index=682, request_data_type=DataType.FLOAT,  unit='s',           name='db.power_board.afi_t30',                       description='AFI 30 mA switching off time'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0xC24E85D0, index=688, request_data_type=DataType.FLOAT,  unit='°C',          name='db.core_temp',                                 description='Core temperature'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0xDFB53AF3, index=782, request_data_type=DataType.FLOAT,                      name='db.power_board.Current_Mean_Mean_AC'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0xF0527539, index=829, request_data_type=DataType.FLOAT,                      name='db.power_board.adc_p3V3_meas'),
    ObjectInfo(group=ObjectGroup.DB,              object_id=0xF79D41D9, index=862, request_data_type=DataType.FLOAT,  unit='°C',          name='db.temp1',                                     description='Heat sink temperature'),

    ObjectInfo(group=ObjectGroup.SWITCH_ON_COND,  object_id=0x1FEB2F67, index=108, request_data_type=DataType.FLOAT,                      name='switch_on_cond.u_min',                         description='Min. voltage'),
    ObjectInfo(group=ObjectGroup.SWITCH_ON_COND,  object_id=0x234DD4DF, index=121, request_data_type=DataType.FLOAT,                      name='switch_on_cond.f_min',                         description='Min. frequency'),
    ObjectInfo(group=ObjectGroup.SWITCH_ON_COND,  object_id=0x3390CC2F, index=171, request_data_type=DataType.FLOAT,  unit='s',           name='switch_on_cond.test_time_fault',               description='Switching on time after any grid fault'),
    ObjectInfo(group=ObjectGroup.SWITCH_ON_COND,  object_id=0x4DB1B91E, index=264, request_data_type=DataType.FLOAT,                      name='switch_on_cond.f_max',                         description='Max. frequency'),
    ObjectInfo(group=ObjectGroup.SWITCH_ON_COND,  object_id=0x934E64E9, index=535, request_data_type=DataType.FLOAT,                      name='switch_on_cond.u_max',                         description='Max. voltage'),
    ObjectInfo(group=ObjectGroup.SWITCH_ON_COND,  object_id=0xECABB6CF, index=819, request_data_type=DataType.FLOAT,                      name='switch_on_cond.test_time',                     description='Test time'),
    ObjectInfo(group=ObjectGroup.SWITCH_ON_COND,  object_id=0x362346D4, index=181, request_data_type=DataType.FLOAT,  unit='s',           name='switch_on_cond.max_rnd_test_time_fault',       description='Max additional random switching on time after any grid fault'),

    ObjectInfo(group=ObjectGroup.P_REC,           object_id=0xAA372CE,  index=37,  request_data_type=DataType.FLOAT,  unit='W',           name='p_rec_req[1]',                                 description='Required battery to grid power'),
    ObjectInfo(group=ObjectGroup.P_REC,           object_id=0x1ABA3EE8, index=91,  request_data_type=DataType.FLOAT,  unit='W',           name='p_rec_req[0]',                                 description='Required compensation power'),
    ObjectInfo(group=ObjectGroup.P_REC,           object_id=0x365D12DA, index=183, request_data_type=DataType.FLOAT,  unit='W',           name='p_rec_req[2]',                                 description='Required Pac'),
    ObjectInfo(group=ObjectGroup.P_REC,           object_id=0x54829753, index=294, request_data_type=DataType.FLOAT,  unit='W',           name='p_rec_lim[1]',                                 description='Max. battery to grid power'),
    ObjectInfo(group=ObjectGroup.P_REC,           object_id=0x5D0CDCF0, index=323, request_data_type=DataType.FLOAT,  unit='W',           name='p_rec_available[2]',                           description='Available Pac'),
    ObjectInfo(group=ObjectGroup.P_REC,           object_id=0x85886E2E, index=475, request_data_type=DataType.FLOAT,  unit='W',           name='p_rec_lim[0]',                                 description='Max. compensation power'),
    ObjectInfo(group=ObjectGroup.P_REC,           object_id=0x8F0FF9F3, index=511, request_data_type=DataType.FLOAT,  unit='W',           name='p_rec_available[1]',                           description='Available battery to grid power'),
    ObjectInfo(group=ObjectGroup.P_REC,           object_id=0x9A67600D, index=564, request_data_type=DataType.FLOAT,  unit='W',           name='p_rec_lim[2]',                                 description='Pac max.'),
    ObjectInfo(group=ObjectGroup.P_REC,           object_id=0xB45FE275, index=638, request_data_type=DataType.FLOAT,  unit='W',           name='p_rec_available[0]',                           description='Available compensation power'),

    ObjectInfo(group=ObjectGroup.MODBUS,          object_id=0x31ED1B75, index=166, request_data_type=DataType.ENUM,                       name='modbus.mode',                                  description='RS485 working mode',
               enum_map={0: 'Modbus slave', 1: 'Modbus master'}),
    ObjectInfo(group=ObjectGroup.MODBUS,          object_id=0x6C243F71, index=378, request_data_type=DataType.UINT8,                      name='modbus.address',                               description='RS485 address'),

    ObjectInfo(group=ObjectGroup.BAT_MNG_STRUCT,  object_id=0x3B0C6A53, index=203, request_data_type=DataType.STRING,                     name='bat_mng_struct.profile_pdc_max'),
    ObjectInfo(group=ObjectGroup.BAT_MNG_STRUCT,  object_id=0x9DC927AA, index=570, request_data_type=DataType.UNKNOWN,                    name='bat_mng_struct.profile_load'),
    ObjectInfo(group=ObjectGroup.BAT_MNG_STRUCT,  object_id=0xB2FB9A90, index=633, request_data_type=DataType.FLOAT,                      name='bat_mng_struct.k_trust',                       description='How fast the actual prediction can be trusted [0..10]'),
    ObjectInfo(group=ObjectGroup.BAT_MNG_STRUCT,  object_id=0xDE68F62D, index=777, request_data_type=DataType.STRING,                     name='bat_mng_struct.profile_pext'),
    ObjectInfo(group=ObjectGroup.BAT_MNG_STRUCT,  object_id=0xDF6EA121, index=781, request_data_type=DataType.STRING,                     name='bat_mng_struct.profile_pdc'),
    ObjectInfo(group=ObjectGroup.BAT_MNG_STRUCT,  object_id=0xF0A03A20, index=831, request_data_type=DataType.FLOAT,                      name='bat_mng_struct.k',                             description='Forecast correction'),
    ObjectInfo(group=ObjectGroup.BAT_MNG_STRUCT,  object_id=0xF644DCA7, index=856, request_data_type=DataType.FLOAT,                      name='bat_mng_struct.k_reserve',                     description='Main reservation coefficient [0..2]'),
    ObjectInfo(group=ObjectGroup.BAT_MNG_STRUCT,  object_id=0xFB57BA65, index=872, request_data_type=DataType.STRING,                     name='bat_mng_struct.count'),
    ObjectInfo(group=ObjectGroup.BAT_MNG_STRUCT,  object_id=0x3E25C391, index=214, request_data_type=DataType.FLOAT,                      name='bat_mng_struct.bat_calib_soc_thresh',          description='Part of max historical SOC for battery calibration in advance'),
    ObjectInfo(group=ObjectGroup.BAT_MNG_STRUCT,  object_id=0xFC5AA529, index=881, request_data_type=DataType.FLOAT,                      name='bat_mng_struct.bat_calib_soc_threshold',       description='SOC threshold for battery calibration in advance'),

    ObjectInfo(group=ObjectGroup.ISO_STRUCT,      object_id=0x474F80D5, index=242, request_data_type=DataType.FLOAT,  unit='Ohm',         name='iso_struct.Rn',                                description='Insulation resistance on negative DC input'),
    ObjectInfo(group=ObjectGroup.ISO_STRUCT,      object_id=0x777DC0EB, index=423, request_data_type=DataType.FLOAT,  unit='Ohm',         name='iso_struct.r_min',                             description='Minimum allowed insulation resistance'),
    ObjectInfo(group=ObjectGroup.ISO_STRUCT,      object_id=0x8E41FC47, index=505, request_data_type=DataType.FLOAT,  unit='Ohm',         name='iso_struct.Rp',                                description='Insulation resistance on positive DC input'),
    ObjectInfo(group=ObjectGroup.ISO_STRUCT,      object_id=0xC717D1FB, index=707, request_data_type=DataType.FLOAT,  unit='Ohm',         name='iso_struct.Riso',                              description='Total insulation resistance'),

    ObjectInfo(group=ObjectGroup.GRID_LT,         object_id=0x3A3050E6, index=195, request_data_type=DataType.FLOAT,  unit='V',           name='grid_lt.threshold',                            description='Max. voltage'),
    ObjectInfo(group=ObjectGroup.GRID_LT,         object_id=0x9061EA7B, index=516, request_data_type=DataType.FLOAT,                      name='grid_lt.granularity',                          description='Resolution'),
    ObjectInfo(group=ObjectGroup.GRID_LT,         object_id=0xD9E721A5, index=761, request_data_type=DataType.FLOAT,                      name='grid_lt.timeframe',                            description='Timeframe'),

    ObjectInfo(group=ObjectGroup.CAN_BUS,         object_id=0x4539A6D4, index=236, request_data_type=DataType.UINT32,                     name='can_bus.bms_update_response[0]'),
    ObjectInfo(group=ObjectGroup.CAN_BUS,         object_id=0x69AA598A, index=370, request_data_type=DataType.INT32,                      name='can_bus.requested_id'),
    ObjectInfo(group=ObjectGroup.CAN_BUS,         object_id=0x7A67E33B, index=438, request_data_type=DataType.UINT32,                     name='can_bus.bms_update_response[1]'),
    ObjectInfo(group=ObjectGroup.CAN_BUS,         object_id=0x96629BB9, index=548, request_data_type=DataType.UINT8,                      name='can_bus.bms_update_state'),
    ObjectInfo(group=ObjectGroup.CAN_BUS,         object_id=0xBD4147B0, index=669, request_data_type=DataType.UINT32,                     name='can_bus.set_cell_resist'),
    ObjectInfo(group=ObjectGroup.CAN_BUS,         object_id=0xD143A391, index=737, request_data_type=DataType.UINT32,                     name='can_bus.set_cell_v_t'),

    ObjectInfo(group=ObjectGroup.DISPLAY_STRUCT,  object_id=0x67BF3003, index=361, request_data_type=DataType.BOOL,                       name='display_struct.display_dir',                   description='Rotate display'),
    ObjectInfo(group=ObjectGroup.DISPLAY_STRUCT,  object_id=0x8EC4116E, index=508, request_data_type=DataType.BOOL,                       name='display_struct.blink',                         description='Display blinking enable'),
    ObjectInfo(group=ObjectGroup.DISPLAY_STRUCT,  object_id=0xC1D051EC, index=687, request_data_type=DataType.UINT8,                      name='display_struct.variate_contrast',              description='Display pixel test mode'),
    ObjectInfo(group=ObjectGroup.DISPLAY_STRUCT,  object_id=0xF247BB16, index=840, request_data_type=DataType.UINT8,                      name='display_struct.contrast',                      description='Display contrast'),

    ObjectInfo(group=ObjectGroup.FLASH_PARAM,     object_id=0x43F16F7E, index=231, request_data_type=DataType.UINT16,                     name='flash_state',                                  description='Flash state'),
    ObjectInfo(group=ObjectGroup.FLASH_PARAM,     object_id=0x65A44A98, index=351, request_data_type=DataType.STRING,                     name='flash_mem'),
    ObjectInfo(group=ObjectGroup.FLASH_PARAM,     object_id=0x46892579, index=240, request_data_type=DataType.UINT32,                     name='flash_param.write_cycles',                     description='Write cycles of flash parameters'),
    ObjectInfo(group=ObjectGroup.FLASH_PARAM,     object_id=0x96E32D11, index=550, request_data_type=DataType.UINT32,                     name='flash_param.erase_cycles',                     description='Erase cycles of flash parameter'),
    ObjectInfo(group=ObjectGroup.FLASH_PARAM,     object_id=0xB238942F, index=631, request_data_type=DataType.INT16,                      name='last_successfull_flash_op'),
    ObjectInfo(group=ObjectGroup.FLASH_PARAM,     object_id=0xE63A3529, index=802, request_data_type=DataType.UINT16,                     name='flash_result',                                 description='Flash result'),

    ObjectInfo(group=ObjectGroup.FAULT,           object_id=0x234B4736, index=120, request_data_type=DataType.UINT32,                     name='fault[1].flt',                                 description='Error bit field 2'),
    ObjectInfo(group=ObjectGroup.FAULT,           object_id=0x37F9D5CA, index=186, request_data_type=DataType.UINT32,                     name='fault[0].flt',                                 description='Error bit field 1'),
    ObjectInfo(group=ObjectGroup.FAULT,           object_id=0x3B7FCD47, index=205, request_data_type=DataType.UINT32,                     name='fault[2].flt',                                 description='Error bit field 3'),
    ObjectInfo(group=ObjectGroup.FAULT,           object_id=0x7F813D73, index=458, request_data_type=DataType.UINT32,                     name='fault[3].flt',                                 description='Error bit field 4'),

    ObjectInfo(group=ObjectGroup.PRIM_SM,         object_id=0x3623D82A, index=182, request_data_type=DataType.UINT16,                     name='prim_sm.island_flag',                          description='Grid-separated'),
    ObjectInfo(group=ObjectGroup.PRIM_SM,         object_id=0x3AFEF139, index=202, request_data_type=DataType.BOOL,                       name='prim_sm.is_thin_layer',                        description='Thin-film solar module'),
    ObjectInfo(group=ObjectGroup.PRIM_SM,         object_id=0x5F33284E, index=330, request_data_type=DataType.ENUM,                       name='prim_sm.state',                                description='Inverter status',
               enum_map={0: 'Standby', 1: 'Initialization', 2: 'Standby', 3: 'Efficiency', 4: 'Insulation check', 5: 'Island check', 6: 'Power check', 7: 'Symmetry', 8: 'Relais test', 9: 'Grid passive',
                         10: 'Prepare Bat Passive', 11: 'Battery Passive', 12: 'H/W check', 13: 'Feed in'}),
    ObjectInfo(group=ObjectGroup.PRIM_SM,         object_id=0xC40D5688, index=694, request_data_type=DataType.UINT32,                     name='prim_sm.state_source'),
    ObjectInfo(group=ObjectGroup.PRIM_SM,         object_id=0xCF005C54, index=733, request_data_type=DataType.BOOL,                       name='prim_sm.phase_3_mode'),
    ObjectInfo(group=ObjectGroup.PRIM_SM,         object_id=0xFB5DE9C5, index=873, request_data_type=DataType.BOOL,                       name='prim_sm.minigrid_flag',                        description='Minigrid support'),
    ObjectInfo(group=ObjectGroup.PRIM_SM,         object_id=0x20FD4419, index=111, request_data_type=DataType.FLOAT,  unit='s',           name='prim_sm.island_next_repeat_timeout',           description='Next island trial timeout'),
    ObjectInfo(group=ObjectGroup.PRIM_SM,         object_id=0x5151D84C, index=284, request_data_type=DataType.FLOAT,  unit='min',         name='prim_sm.island_reset_retrials_counter_time',   description='Reset island trials counter in (by 0 not used)'),
    ObjectInfo(group=ObjectGroup.PRIM_SM,         object_id=0x73E3ED49, index=413, request_data_type=DataType.UINT16,                     name='prim_sm.island_max_trials',                    description='Max island trials'),
    ObjectInfo(group=ObjectGroup.PRIM_SM,         object_id=0x751E80CA, index=416, request_data_type=DataType.FLOAT,                      name='prim_sm.island_reset_retrials_operation_time'),
    ObjectInfo(group=ObjectGroup.PRIM_SM,         object_id=0xC4D87E96, index=697, request_data_type=DataType.UINT16,                     name='prim_sm.island_retrials',                      description='Island trials counter'),
    ObjectInfo(group=ObjectGroup.PRIM_SM,         object_id=0xE31F8B17, index=793, request_data_type=DataType.FLOAT,  unit='W',           name='prim_sm.Uzk_pump_grad[0]',                      description='start power'),

    ObjectInfo(group=ObjectGroup.CS_MAP,          object_id=0x6D5318C8, index=382, request_data_type=DataType.UINT8,                      name='cs_map[1]',                                    description='Associate current sensor 1 with phase L'),
    ObjectInfo(group=ObjectGroup.CS_MAP,          object_id=0xD451EF88, index=746, request_data_type=DataType.UINT8,                      name='cs_map[2]',                                    description='Associate current sensor 2 with phase L'),
    ObjectInfo(group=ObjectGroup.CS_MAP,          object_id=0xE0E16E63, index=785, request_data_type=DataType.UINT8,                      name='cs_map[0]',                                    description='Associate current sensor 0 with phase L'),

    ObjectInfo(group=ObjectGroup.LINE_MON,        object_id=0x6BBDC7C8, index=374, request_data_type=DataType.FLOAT,  unit='V',           name='line_mon.u_max',                               description='Max line voltage'),
    ObjectInfo(group=ObjectGroup.LINE_MON,        object_id=0x8D8E19F7, index=502, request_data_type=DataType.FLOAT,  unit='V',           name='line_mon.u_min',                               description='Min line voltage'),
    ObjectInfo(group=ObjectGroup.LINE_MON,        object_id=0xA1266D6B, index=575, request_data_type=DataType.FLOAT,  unit='s',           name='line_mon.time_lim',                            description='Switch off time line voltage'),

    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0xCC4BDAA,  index=46,  request_data_type=DataType.BOOL,                       name='detect_phase_shift_enable',                    description='Enable active island detection'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x108FC93D, index=65,  request_data_type=DataType.FLOAT,  unit='degrees',     name='max_phase_shift',                              description='Max. phase shift from 120 position'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x19608C98, index=89,  request_data_type=DataType.INT32,                      name='partition[3].last_id'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x1C4A665F, index=96,  request_data_type=DataType.FLOAT,  unit='Hz',          name='grid_pll[0].f',                                description='Grid frequency'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x2703A771, index=138, request_data_type=DataType.BOOL,                       name='cs_struct.is_tuned',                           description='Current sensors are tuned'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x27EC8487, index=145, request_data_type=DataType.UINT32,                     name='performance_free[0]'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x2848A1EE, index=146, request_data_type=DataType.FLOAT,                      name='grid_offset'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x3A0EA5BE, index=194, request_data_type=DataType.FLOAT,                      name='power_spring_up'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x3E728842, index=216, request_data_type=DataType.FLOAT,                      name='power_spring_bat'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x494FE156, index=248, request_data_type=DataType.FLOAT,                      name='power_spring_offset'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x4E3CB7F8, index=269, request_data_type=DataType.BOOL,                       name='phase_3_mode',                                 description='3-phase feed in'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x68BC034D, index=366, request_data_type=DataType.STRING,                     name='parameter_file',                               description='Norm'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x6C44F721, index=380, request_data_type=DataType.FLOAT,  unit='A',           name='i_dc_max',                                     description='Max. DC-component of Iac'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x7924ABD9, index=429, request_data_type=DataType.STRING,                     name='inverter_sn',                                  description='Serial number'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x7940547B, index=432, request_data_type=DataType.BOOL,                       name='inv_struct.force_dh'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x7946D888, index=433, request_data_type=DataType.FLOAT,  unit='s',           name='i_dc_slow_time',                               description='Time for slow DC-component of Iac'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x87E4387A, index=480, request_data_type=DataType.FLOAT,  unit='A',           name='current_sensor_max',                           description='Power Sensor current range'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x8FC89B10, index=512, request_data_type=DataType.ENUM,                       name='com_service',                                  description='COM service',
               enum_map={0: 'Off', 1: 'OnlineOsci protocol', 2: 'COM protocol', 3: 'Start bootloader', 4: 'Reset DSP', 5: 'Flash parameter', 6: 'Erase parameters', 7: 'Set SSID', 8: 'Restart WiFi', 9: 'Write WiFi parameters', 10: 'Read WiFi parameters', 11: 'Datalog bulk erase', 12: 'Tune current sensors', 13: 'Start battery booster test', 14: 'Stop battery booster test', 15: 'Start stack commission', 16: 'Stop stack commission', 17: 'Reset battery statistics'}),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x929394B7, index=532, request_data_type=DataType.STRING,                     name='svnversion_last_known'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0xA12E9B43, index=577, request_data_type=DataType.INT16,                      name='phase_marker',                                 description='Next phase after phase 1'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0xA76AE9CA, index=596, request_data_type=DataType.UINT16,                     name='relays.bits_real'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0xA9CF517D, index=608, request_data_type=DataType.FLOAT,                      name='power_spring_down'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0xB1D1BE71, index=625, request_data_type=DataType.FLOAT,                      name='osci_struct.cmd_response_time'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0xBF9B6042, index=675, request_data_type=DataType.STRING,                     name='svnversion_factory',                           description='Control software factory version'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0xC36675D4, index=690, request_data_type=DataType.FLOAT,  unit='A',           name='i_ac_max_set',                                 description='Maximum AC throttle current'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0xC3A3F070, index=691, request_data_type=DataType.BOOL,                       name='i_ac_extern_connected',                        description='Current sensors detected'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0xDABD323E, index=764, request_data_type=DataType.INT16,                      name='osci_struct.error',                            description='Communication error'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0xDDD1C2D0, index=775, request_data_type=DataType.STRING,                     name='svnversion',                                   description='Control software version'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0xE14B8679, index=786, request_data_type=DataType.FLOAT,  unit='A',           name='i_dc_slow_max',                                description='Max. slow DC-component of Iac'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0xE6AC95E5, index=605, request_data_type=DataType.UINT32,                     name='phase_shift_threshold',                        description='Detection threshold'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0xEBC62737, index=817, request_data_type=DataType.STRING,                     name='android_description',                          description='Device name', sim_data='RCT'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0xF2BE0C9C, index=845, request_data_type=DataType.FLOAT,  unit='W',           name='p_buf_available',                              description='Available buffer power'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x3C24F3E8, index=207, request_data_type=DataType.FLOAT,  unit='cos(Phi)',    name='inv_struct.cosinus_phi'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x4992E65A, index=250, request_data_type=DataType.UINT8,                      name='update_is_allowed_id'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x40385DB,  index=11,  request_data_type=DataType.UINT32,                     name='common_control_bits',                          description='Bit coded function'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0xD658831,  index=48,  request_data_type=DataType.FLOAT,                      name='i_bottom_max'),
    ObjectInfo(group=ObjectGroup.OTHERS,          object_id=0x9C8FE559, index=568, request_data_type=DataType.UINT32,                     name='pas.period'),

    ObjectInfo(group=ObjectGroup.FRT,             object_id=0x528D1D8,  index=14,  request_data_type=DataType.FLOAT,  unit='V',           name='frt.u_min[2]',                                 description='Point 3 voltage'),
    ObjectInfo(group=ObjectGroup.FRT,             object_id=0x22CC80C6, index=119, request_data_type=DataType.FLOAT,  unit='V',           name='frt.u_min_end',                                description='FRT end undervoltage threshold'),
    ObjectInfo(group=ObjectGroup.FRT,             object_id=0x236D2178, index=123, request_data_type=DataType.FLOAT,  unit='s',           name='frt.t_min[1]',                                 description='Point 2 time'),
    ObjectInfo(group=ObjectGroup.FRT,             object_id=0x32DCA605, index=168, request_data_type=DataType.FLOAT,  unit='V',           name='frt.u_max[0]',                                 description='Point 1 voltage'),
    ObjectInfo(group=ObjectGroup.FRT,             object_id=0x41744E11, index=223, request_data_type=DataType.FLOAT,  unit='V',           name='frt.u_min[0]',                                 description='Point 1 voltage'),
    ObjectInfo(group=ObjectGroup.FRT,             object_id=0x71277E71, index=401, request_data_type=DataType.FLOAT,  unit='V',           name='frt.u_min_begin',                              description='FRT begin undervoltage threshold'),
    ObjectInfo(group=ObjectGroup.FRT,             object_id=0x83BBEF0B, index=473, request_data_type=DataType.FLOAT,  unit='V',           name='frt.u_max_begin',                              description='FRT begin overvoltage threshold'),
    ObjectInfo(group=ObjectGroup.FRT,             object_id=0x88DFDE8B, index=489, request_data_type=DataType.FLOAT,  unit='V',           name='frt.u_max_end',                                description='FRT end overvoltage threshold'),
    ObjectInfo(group=ObjectGroup.FRT,             object_id=0x89B21223, index=491, request_data_type=DataType.FLOAT,  unit='s',           name='frt.t_max[0]',                                 description='Point 1 time'),
    ObjectInfo(group=ObjectGroup.FRT,             object_id=0x9350FE02, index=536, request_data_type=DataType.FLOAT,  unit='V',           name='frt.u_max[2]',                                 description='Point 3 voltage'),
    ObjectInfo(group=ObjectGroup.FRT,             object_id=0x93971C36, index=537, request_data_type=DataType.FLOAT,  unit='s',           name='frt.t_max[2]',                                 description='Point 3 time'),
    ObjectInfo(group=ObjectGroup.FRT,             object_id=0x9C75BD89, index=567, request_data_type=DataType.FLOAT,  unit='s',           name='frt.t_min[0]',                                 description='Point 1 time'),
    ObjectInfo(group=ObjectGroup.FRT,             object_id=0xC4FA4E33, index=698, request_data_type=DataType.FLOAT,  unit='V',           name='frt.u_min[1]',                                 description='Point 2 voltage'),
    ObjectInfo(group=ObjectGroup.FRT,             object_id=0xCB78F611, index=723, request_data_type=DataType.FLOAT,  unit='s',           name='frt.t_max[1]',                                 description='Point 2 time'),
    ObjectInfo(group=ObjectGroup.FRT,             object_id=0xD536E7E9, index=750, request_data_type=DataType.FLOAT,  unit='V',           name='frt.u_max[1]',                                 description='Point 2 voltage'),
    ObjectInfo(group=ObjectGroup.FRT,             object_id=0xE1F49459, index=789, request_data_type=DataType.FLOAT,  unit='s',           name='frt.t_min[2]',                                 description='Point 3 time'),
    ObjectInfo(group=ObjectGroup.FRT,             object_id=0xFD72CC0D, index=887, request_data_type=DataType.BOOL,                       name='frt.enabled',                                  description='Enable FRT'),

    ObjectInfo(group=ObjectGroup.PARTITION,       object_id=0x16ED8F8F, index=81,  request_data_type=DataType.INT32,                      name='partition[1].last_id'),
    ObjectInfo(group=ObjectGroup.PARTITION,       object_id=0x7AE87E39, index=441, request_data_type=DataType.INT32,                      name='partition[2].last_id'),
    ObjectInfo(group=ObjectGroup.PARTITION,       object_id=0x7C0827C5, index=447, request_data_type=DataType.INT32,                      name='partition[5].last_id'),
    ObjectInfo(group=ObjectGroup.PARTITION,       object_id=0xC3DD7850, index=693, request_data_type=DataType.INT32,                      name='partition[6].last_id'),
    ObjectInfo(group=ObjectGroup.PARTITION,       object_id=0xD5567470, index=751, request_data_type=DataType.INT32,                      name='partition[4].last_id'),
    ObjectInfo(group=ObjectGroup.PARTITION,       object_id=0xF03133E2, index=827, request_data_type=DataType.INT32,                      name='partition[0].last_id'),

    # The following have been found by observing the official app
    ObjectInfo(group=ObjectGroup.DC_CONV,         object_id=0x4AE96C12, index=253, request_data_type=DataType.FLOAT,  unit='V',           name='dc_conv.dc_conv_struct[1].mpp.mpp_step',       description='MPP search step on input B'),
    ObjectInfo(group=ObjectGroup.DC_CONV,         object_id=0xBA8B8515, index=661, request_data_type=DataType.FLOAT,  unit='V',           name='dc_conv.dc_conv_struct[0].mpp.mpp_step',       description='MPP search step on input A'),
    ObjectInfo(group=ObjectGroup.DISPLAY_STRUCT,  object_id=0x29BDA75F, index=147, request_data_type=DataType.UINT8,                      name='display_struct.brightness',                    description='Display brightness, [0..255]'),

    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x2247588,  index=5,   request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[2].u_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x35E64EA,  index=7,   request_data_type=DataType.STRING,                 name='battery_placeholder[0].module_sn[5]',              description='Module 5 Serial Number'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x48C9D69,  index=12,  request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[1].u_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x71B5514,  index=23,  request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[3].t_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x73C7E5D,  index=25,  request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].max_cell_temperature'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x74B1EF5,  index=26,  request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[3].u_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x8E81725,  index=32,  request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[0].t_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xB94A673,  index=39,  request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[6].t_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xC2A7286,  index=41,  request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells_resist[0]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xDBD5E77,  index=50,  request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[6].u_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xE4AA301,  index=55,  request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[6].u_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xEC64BA7,  index=57,  request_data_type=DataType.UINT32,                 name='battery_placeholder[0].stack_software_version[3]', description='Software version stack 3'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x1025B491, index=62,  request_data_type=DataType.FLOAT,  unit='A',       name='battery_placeholder[0].maximum_discharge_current', description='Max. discharge current'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x1639B2D8, index=77,  request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[4].u_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x1781CD31, index=83,  request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].soh',                       description='SOH (State of Health)'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x18469762, index=85,  request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[0].u_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x18BD807D, index=86,  request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[4].t_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x1D83D2A5, index=100, request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells[4]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x1E0EB397, index=101, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[6].u_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x1F44C23A, index=103, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[1].t_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x1FA192E3, index=106, request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells_resist[4]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x1FB3A602, index=107, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[2].t_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x20A3A91F, index=110, request_data_type=DataType.STRING,                 name='battery_placeholder[0].module_sn[4]',              description='Module 4 Serial Number'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x2295401F, index=118, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[3].u_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x235E0DF5, index=122, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].stack_software_version[1]', description='Software version stack 1'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x23D4A386, index=124, request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells_stat[0]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x241CFA0A, index=128, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].min_cell_temperature'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x24AC4CBB, index=130, request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells_resist[6]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x27116260, index=139, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[5].u_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x2E9F3C50, index=156, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[0].t_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x2ED8A639, index=158, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[2].u_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x2F84A0A9, index=161, request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells[2]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x31413485, index=163, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[5].u_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x314C13EB, index=164, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[5].u_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x374B5DD6, index=185, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[6].u_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x39AD4639, index=193, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[5].u_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x3A35D491, index=196, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[2].u_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x465DDB50, index=237, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[2].t_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x4686E044, index=239, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[1].u_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x46C3625D, index=241, request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells_stat[2]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x4764F9EE, index=243, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[3].t_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x4AAEB0D2, index=252, request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells_stat[1]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x4D684EF2, index=262, request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells[0]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x4DC372A0, index=265, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[4].u_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x4FC53F19, index=277, request_data_type=DataType.STRING,                 name='battery_placeholder[0].module_sn[3]',              description='Module 3 Serial Number'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x4FEDC1BE, index=278, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[5].t_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x4FF8CCE2, index=279, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].stack_software_version[5]', description='Software version stack 5'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x51E5377D, index=286, request_data_type=DataType.UINT16,                 name='battery_placeholder[0].stack_cycles[1]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x53656F42, index=288, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[2].u_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x576D2A08, index=303, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[3].t_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x57945EE4, index=304, request_data_type=DataType.FLOAT,  unit='A',       name='battery_placeholder[0].maximum_charge_current',    description='Max. charge current'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x5C93093B, index=321, request_data_type=DataType.INT32,                  name='battery_placeholder[0].status2',                   description='Battery extra status'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x5EF54372, index=329, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[0].u_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x60435F1C, index=332, request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells[6]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x6383DEA9, index=343, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[1].t_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x652B7536, index=349, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[3].t_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x6743CCCE, index=359, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[6].t_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x690C32D2, index=368, request_data_type=DataType.STRING,                 name='battery_placeholder[0].module_sn[0]',              description='Module 0 Serial Number'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x6C03F5ED, index=376, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].bms_power_version',         description='Software version BMS Power'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x6C10E96A, index=377, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[0].u_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x6D639C25, index=383, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[0].t_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x6E3336A8, index=389, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[5].t_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x75898A45, index=417, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[5].t_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x77A9480F, index=424, request_data_type=DataType.FLOAT,  unit='V',       name='battery_placeholder[0].minimum_discharge_voltage', description='Min. discharge voltage'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x77E5CEF1, index=426, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].stack_software_version[0]', description='Software version stack 0'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x78228507, index=427, request_data_type=DataType.UINT16,                 name='battery_placeholder[0].stack_cycles[6]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x7839EBCB, index=428, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[3].u_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x792897C9, index=430, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[4].t_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x79D7D617, index=435, request_data_type=DataType.FLOAT,  unit='A',       name='battery_placeholder[0].current',                   description='Battery current'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x79E66CDF, index=436, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[6].t_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x7B8E811E, index=445, request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells_stat[6]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x7BF3886B, index=446, request_data_type=DataType.UINT16,                 name='battery_placeholder[0].stack_cycles[2]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x7C863EDB, index=450, request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells[3]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x7D839AE6, index=451, request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells_resist[2]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x8128228D, index=462, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[1].u_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x8352F9DD, index=471, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[4].t_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x8594D11E, index=476, request_data_type=DataType.STRING,                 name='battery_placeholder[0].module_sn[6]',              description='Module 6 Serial Number'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x8822EF35, index=481, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].stack_software_version[2]', description='Software version stack 2'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x8AFD1410, index=495, request_data_type=DataType.UINT16,                 name='battery_placeholder[0].stack_cycles[4]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x8B4BE168, index=496, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].soc',                       description='SOC (State of charge)'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x8C6E28E4, index=499, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[2].t_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x9095FD74, index=519, request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells[5]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x90C2AC13, index=521, request_data_type=DataType.UINT16,                 name='battery_placeholder[0].stack_cycles[3]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x920AFF34, index=528, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[1].t_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x947DDC38, index=542, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[0].t_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x9486134F, index=543, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[1].t_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x95E1E844, index=546, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[2].t_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x961C8261, index=547, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[4].u_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x97DC2ECB, index=553, request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells[1]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x980C5525, index=556, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].max_cell_voltage'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0x9AAA9CAA, index=565, request_data_type=DataType.UINT16,                 name='battery_placeholder[0].stack_cycles[5]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xA23FE8B9, index=579, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[6].t_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xA2F87161, index=580, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[0].u_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xA7F4123B, index=599, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].stack_software_version[6]', description='Software version stack 6'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xA81176D0, index=602, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[1].u_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xA83F291F, index=603, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[6].u_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xA8FEAEB9, index=604, request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells_resist[5]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xAA911BEE, index=609, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[4].t_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xABA015FC, index=613, request_data_type=DataType.STRING,                 name='battery_placeholder[0].module_sn[1]',              description='Module 1 Serial Number'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xAE99F87A, index=616, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[5].t_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xB130B8D6, index=624, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[1].t_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xB1D465C7, index=626, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[4].u_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xB228EC94, index=630, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[3].t_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xB399B5B3, index=634, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[4].u_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xB403A7E6, index=635, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].soc_update_since'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xB5EDA8EC, index=643, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[3].u_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xB70D1703, index=646, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[5].u_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xBA046C03, index=660, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[5].t_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xBD95C46C, index=672, request_data_type=DataType.FLOAT,  unit='Ah',      name='battery_placeholder[0].ah_capacity',              description='Battery capacity [Ah]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xC04A5F3A, index=678, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].bms_software_version',     description='Software version BMS Master'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xC56A1346, index=700, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[4].t_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xC66665E8, index=702, request_data_type=DataType.FLOAT,  unit='°C',      name='battery_placeholder[0].temperature',              description='Battery temperature'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xC71155B5, index=706, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[2].t_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xC7E85F32, index=711, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[4].t_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xC8E56803, index=715, request_data_type=DataType.FLOAT,  unit='V',       name='battery_placeholder[0].maximum_charge_voltage',   description='Max. charge voltage'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xC937D38D, index=716, request_data_type=DataType.UINT16,                 name='battery_placeholder[0].stack_cycles[0]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xCA4E0C03, index=719, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[5].u_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xCB85C397, index=724, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[3].u_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xCBBEEB21, index=726, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[2].u_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xCD8EDAD3, index=730, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[3].t_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xCE49EB86, index=732, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[2].t_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xCF096A6B, index=735, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].stack_software_version[4]', description='Software version stack 4'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xD1F9D017, index=741, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[4].u_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xD2DEA4B1, index=742, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[5].t_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xD3F492EB, index=745, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[0].t_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xD81471DF, index=755, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[6].t_max.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xD82F2D0B, index=756, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[3].u_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xD876A4AC, index=758, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[0].u_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xE14F1CBA, index=787, request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells_stat[4]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xE19C8B79, index=788, request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells_resist[1]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xE635A6C4, index=801, request_data_type=DataType.STRING,                 name='battery_placeholder[0].module_sn[2]',             description='Module 2 Serial Number'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xE87B1F4B, index=806, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[0].u_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xEA399EA8, index=811, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].min_cell_voltage'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xEB7BCB93, index=816, request_data_type=DataType.STRING,                 name='battery_placeholder[0].bms_sn',                   description='BMS Serial Number'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xEEC44AA0, index=822, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[2].u_min.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xF1DE6E99, index=836, request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells_resist[3]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xF23D4595, index=838, request_data_type=DataType.FLOAT,                  name='battery_placeholder[0].cells_stat[1].t_min.value'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xF451E935, index=850, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[0].t_min.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xF677D737, index=857, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[6].u_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xF68ECC1F, index=858, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[1].u_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xF742C6BA, index=860, request_data_type=DataType.UINT8,                  name='battery_placeholder[0].cells_stat[1].u_max.index'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xFC1F8C65, index=880, request_data_type=DataType.UINT32,                 name='battery_placeholder[0].cells_stat[6].t_max.time'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xFCA1CBB5, index=883, request_data_type=DataType.FLOAT,  unit='V',       name='battery_placeholder[0].voltage',                   description='Battery voltage'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xFE38B227, index=891, request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells_stat[5]'),
    ObjectInfo(group=ObjectGroup.BATTERY_PLACEHOLDER, object_id=0xFF5B8A54, index=895, request_data_type=DataType.STRING,                 name='battery_placeholder[0].cells_stat[3]'),

    # Object that are known to exist but have not been documented yet (e.g. object_id missing)
    # ObjectInfo(group=ObjectGroup.OTHERS,              object_id=0x0,        index=998, request_data_type=DataType.UINT8,                  name='inv_struct.dsd_select_i_fix'),
    # ObjectInfo(group=ObjectGroup.OTHERS,              object_id=0x0,        index=999, request_data_type=DataType.UINT8,                  name='inv_struct.dsd_select_strobe_fix'),
])
