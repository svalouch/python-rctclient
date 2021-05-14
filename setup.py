# -*- coding: utf-8 -*-
from setuptools import setup  # type: ignore

with open('README.md', 'rt') as fh:
    long_description = fh.read()

setup(
    name='rctclient',
    version='0.0.3',
    author='Stefan Valouch',
    author_email='svalouch@valouch.com',
    description='Implementation of the RCT Power communication protocol',
    long_description=long_description,
    long_description_content_type='text/markdown',
    project_urls={
        'Documentation': 'https://rctclient.readthedocs.io/',
        'Source': 'https://github.com/svalouch/python-rctclient/',
        'Tracker': 'https://github.com/svalouch/python-rctclient/issues',
    },
    packages=['rctclient'],
    package_data={'rctclient': ['py.typed']},
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    url='https://github.com/svalouch/python-rctclient/',
    python_requires='>=3.6',

    install_requires=[
        'typing_extensions ; python_version < "3.8"',
    ],

    extras_require={
        'cli': [
            'click',
        ],
        'tests': [
            'mypy',
            'pylint',
            'pytest',
            'pytest-cov',
            'pytest-pylint',
        ],
        'docs': [
            'click',
            'Sphinx>=2.0',
            'sphinx-autodoc-typehints',
            'sphinx-click',
            'sphinx-rtd-theme',
            'recommonmark>=0.5.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'rctclient=rctclient.cli:cli [cli]',
        ],
    },

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
