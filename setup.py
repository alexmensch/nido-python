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
import platform

with open("README.md", "r") as fh:
    long_description = fh.read()

install_requires = [
    "APScheduler>=3.6,<4",
    "flask>=1.0.2,<2",
    "gunicorn>=19.8.1,<20",
    "paho-mqtt>=1.3.1,<2",
    "requests>=2.20,<3",
    "PyYAML>=4.2b1,<5",
    "rpyc>=4.0.2,<5",
    "smbus2>=0.2.0,<1",
    "SQLAlchemy>=1.3,<2",
]

if platform.machine() in ["armv6l", "armv7l", "armhf"]:
    install_requires.append("RPi.GPIO>=0.6,<1")

setup(
    name="nido",
    version="1.0.3",
    author="Alex Marshall",
    author_email="amars@alumni.stanford.edu",
    description="Nido, a Raspberry Pi-based home thermostat",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alexmensch/nido-python",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
)
