#   Nido, a Raspberry Pi-based home thermostat.
#
#   Copyright (C) 2016 Alex Marshall
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.
#   If not, see <http://www.gnu.org/licenses/>.

from setuptools import find_packages, setup

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='libnido',
    version='0.1.0',
    author='Alex Marshall',
    author_email='alex@moveolabs.com',
    description='Library for Nido, a Raspberry Pi-based home thermostat',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/alexmensch/nido',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU General Public License v3'
        ' or later (GPLv3+)',
        'Programming Language :: Python :: 3.5'
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'APScheduler',
        'future',
        'PyYAML',
        'RPi.GPIO',
        'rpyc',
        'smbus2'
    ]
)
