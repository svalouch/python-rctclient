#!/usr/bin/env python3

import csv
from typing import Dict

from rctclient.registry import REGISTRY as R
from rctclient.types import ObjectGroup


def generate_registry_csv() -> None:
    files: Dict[ObjectGroup, Dict] = dict()
    for og in ObjectGroup:
        files[og] = dict()
        files[og]['file'] = open(f'objectgroup_{og.name.lower()}.csv', 'wt')
        files[og]['csv'] = csv.writer(files[og]['file'])
        files[og]['csv'].writerow(['OID', 'Request Type', 'Response Type', 'Unit', 'Name', 'Description'])

    for oinfo in sorted(R.all()):
        files[oinfo.group]['csv'].writerow([f'``0x{oinfo.object_id:X}``', oinfo.request_data_type.name,
                                            oinfo.response_data_type.name, oinfo.unit, f'``{oinfo.name}``',
                                            oinfo.description])

    for val in files.values():
        val['file'].close()


if __name__ == '__main__':
    generate_registry_csv()
