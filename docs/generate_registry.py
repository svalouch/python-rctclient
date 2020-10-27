#!/usr/bin/env python3

'''
Generator for CSV files from REGISTRY content.
'''

import csv
from typing import Dict

from rctclient.registry import REGISTRY as R
from rctclient.types import DataType, ObjectGroup


def generate_registry_csv() -> None:
    '''
    Generates the registry csv files from the REGISTRY instance.
    '''
    files: Dict[ObjectGroup, Dict] = dict()
    for ogroup in ObjectGroup:
        files[ogroup] = dict()
        files[ogroup]['file'] = open(f'objectgroup_{ogroup.name.lower()}.csv', 'wt')
        files[ogroup]['csv'] = csv.writer(files[ogroup]['file'])
        files[ogroup]['csv'].writerow(['OID', 'Request Type', 'Response Type', 'Unit', 'Name', 'Description'])

    for oinfo in sorted(R.all()):
        description = oinfo.description if oinfo.description is not None else ''
        if oinfo.request_data_type == DataType.ENUM:
            if len(description) > 0 and description[-1] != '.':
                description += '.'
            if oinfo.enum_map is not None:
                # list the mappings in the description
                enum = ', '.join([f'"{v}" = ``0x{k:02X}``' for k, v in oinfo.enum_map.items()])
                description += f' ENUM values: {enum}'
            else:
                description += ' (No enum mapping defined)'

        files[oinfo.group]['csv'].writerow([f'``0x{oinfo.object_id:X}``', oinfo.request_data_type.name,
                                            oinfo.response_data_type.name, oinfo.unit, f'``{oinfo.name}``',
                                            description])

    for val in files.values():
        val['file'].close()


if __name__ == '__main__':
    generate_registry_csv()
