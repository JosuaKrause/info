#!/bin/bash
set -ex

if [ -z $NO_DEFAULT ]; then
  OUTPUT="www"
  LIB_COPY="filelist.txt"
  PUBLISH=
fi

mkdir -p "${OUTPUT}"
find . -not -path '*.mypy_cache/*' -not -path '*.git*/*' -not -path '*'"${OUTPUT}/"'*' -not -path '*mvn-repo/*' -type f -not -name '*.md' -not -name '*.py' -not -name '*.tmpl' -not -name '*.sh' -not -name '*.ini' -not -name '*.toml' -not -name "${LIB_COPY}" -not -name '.*' -not -name "Makefile" -not -name "requirements.txt" > "${LIB_COPY}"
rsync -atv . "${OUTPUT}" --files-from "${LIB_COPY}"
python create_page.py --documents content.json --template index.tmpl --out "${OUTPUT}/index.html" --prefix "${OUTPUT}"
PREV_DIR=`pwd`
pushd "${OUTPUT}"
find . -not -path '*lib/*' -not -path '*lib' | python "${PREV_DIR}/create_sitemap.py" "sitemap.xml"
popd

if [ -z $PUBLISH ]; then
  echo "run 'make run-web' next"
fi
