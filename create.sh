#!/bin/bash
set -ex

OUTPUT="www"
LIB_COPY="filelist.txt"
NO_WEB=1
PUBLISH=

if [ -z $NO_WEB ]; then
  git submodule update --init --recursive
  pip install --upgrade pip
  pip install --upgrade python-dateutil ghp-import pytz
fi

mkdir -p "${OUTPUT}"
find . -not -path '*.git/*' -not -path '*'"${OUTPUT}/"'*' -not -path '*mvn-repo/*' -type f -not -name '*.py' -not -name '*.tmpl' -not -name "${LIB_COPY}" -not -name '.*' > "${LIB_COPY}"
rsync -av . "${OUTPUT}" --files-from "${LIB_COPY}"
./create_page.py --documents content.json --template index.tmpl --out "${OUTPUT}/index.html" --prefix "${OUTPUT}"

if [ -z $PUBLISH ]; then
  python -m SimpleHTTPServer || echo ""
  rm -rf "${OUTPUT}"
  rm "${LIB_COPY}"
else
  ghp-import -n "${OUTPUT}" &&
  git push -qf "https://${GH_TOKEN}@github.com/${TRAVIS_REPO_SLUG}.git" gh-pages
fi
