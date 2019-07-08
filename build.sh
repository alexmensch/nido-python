#!/bin/bash

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

echo "Creating build container..."
if docker build -t nido-builder -f build.docker . ; then
    echo "Cleaning up wheelhouse before building..."
    if ./clean.sh ; then
        echo "Running build container..."
        docker run -t --rm \
            -v `pwd`:/application \
            nido-builder
    else
        exit 1
    fi
else
    exit 1
fi
echo
