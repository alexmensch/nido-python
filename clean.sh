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

echo "**************************************************"
echo "Proceeding will PERMANENTLY remove all development"
echo "and build files and reset the environment."
echo
echo "Proceed with caution!"
echo
read -p "Are you sure? [N/y] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    printf "Deleting..."
    rm -rf node_modules instance package-lock.json build __pycache__ nido.egg-info dist nido-venv
    echo "done."
    echo
    exit 0
fi
echo "Cancelled."
echo
exit 1
