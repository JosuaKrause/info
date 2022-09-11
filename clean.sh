#!/bin/bash
set -ex

if [ -z $NO_DEFAULT ]; then
  OUTPUT="www"
  LIB_COPY="filelist.txt"
fi

rm -rf "${OUTPUT}"
rm -f "${LIB_COPY}"
