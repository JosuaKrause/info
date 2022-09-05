#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, print_function

import os
import sys
import time
from datetime import datetime

import pytz


_tz = pytz.timezone("US/Eastern")


def create_sitemap(out, lines):
    out.write("""<?xml version="1.0" encoding="UTF-8"?>
<urlset
  xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
""")
    out.flush()
    tmpl = """  <url>
    <loc>{base}{path}</loc>
    <lastmod>{mod}</lastmod>
  </url>
"""
    base = "https://josuakrause.github.io/info/"
    for line in sorted(set(lines)):
        line = line.strip().lstrip("./")
        if not line:
            continue
        if line.startswith("."):
            continue
        if line.endswith(".js"):
            continue
        if line.endswith(".css"):
            continue
        if line.endswith(".json"):
            continue
        if line.endswith(".zip"):
            continue
        if line.endswith(".bib"):
            continue
        if line.endswith(".key"):
            continue
        if line.endswith(".png"):
            continue
        if line.endswith(".jpg"):
            continue
        filename = line if line else "."
        if os.path.isdir(filename) and not os.path.exists(
                os.path.join(filename, "index.html")):
            continue
        print(f"processing: {line}")
        mtime = datetime.fromtimestamp(
            os.path.getmtime(filename), tz=_tz).isoformat()
        out.write(tmpl.format(base=base, path=line, mod=mtime))
        out.flush()
    curtime = datetime.fromtimestamp(time.time(), tz=_tz).isoformat()
    out.write(tmpl.format(base=base, path="", mod=curtime))
    out.write(tmpl.format(
        base="https://josuakrause.github.io/",
        path="",
        mod=curtime))
    out.write("</urlset>\n")
    out.flush()


def usage():
    print(f"""
usage: {sys.argv[0]} [-h] <file>
-h: print help
<file>: specifies the output file
""".strip(), file=sys.stderr)
    sys.exit(1)


def run():
    args = sys.argv[:]
    args.pop(0)
    if "-h" in args:
        usage()
    if len(args) != 1:
        usage()
    output = args[0]
    with open(output, "w", encoding="utf-8") as f_out:
        create_sitemap(f_out, sys.stdin.readlines())


if __name__ == "__main__":
    run()
