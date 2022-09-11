#!/bin/bash
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
