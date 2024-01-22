#!/bin/bash
#
# Homepage of Josua Krause
# Copyright (C) 2024  Josua Krause
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
set -ex

if [ -z $NO_DEFAULT ]; then
  OUTPUT="www"
  LIB_COPY="filelist.txt"
fi

if hash open 2>/dev/null; then
  open "http://localhost:8000/www/"
fi
python -m http.server || true
rm -rf "${OUTPUT}"
rm -f "${LIB_COPY}"
