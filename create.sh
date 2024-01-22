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
  PUBLISH=
fi

mkdir -p "${OUTPUT}"
find . \
  -not -path '*node_modules/*' \
  -not -path '*.pytest_cache/*' \
  -not -path '*.mypy_cache/*' \
  -not -path '*.git*/*' \
  -not -path '*'"${OUTPUT}/"'*' \
  -type f \
  -not -name '*.md' \
  -not -name '*.py' \
  -not -name '*.tmpl' \
  -not -name '*.sh' \
  -not -name '*.ini' \
  -not -name '*.toml' \
  -not -name "${LIB_COPY}" \
  -not -name '.*' \
  -not -name "Makefile" \
  -not -name "requirements.txt" \
  -not -name "jsconfig.json" \
  -not -name "package-lock.json" \
  -not -name "package.json" \
  -not -name "tsconfig.json" \
  -not -name "content.json" \
  > "${LIB_COPY}"
rsync -atv . "${OUTPUT}" --files-from "${LIB_COPY}"
python create_page.py \
  --documents content.json \
  --template index.tmpl \
  --out "${OUTPUT}/index.html" \
  --prefix "${OUTPUT}"
PREV_DIR=`pwd`
pushd "${OUTPUT}"
find . \
  -not -path '*lib/*' \
  -not -path '*lib' \
  | python "${PREV_DIR}/create_sitemap.py" "sitemap.xml" "filetimes.xml"
popd

if [ -z $PUBLISH ]; then
  echo "run 'make run-web' next"
fi
