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
        if not line.strip():
            continue
        filename = os.path.normpath(line.strip())
        fname = os.path.basename(filename)
        if fname.startswith("."):
            continue
        if fname.endswith(".js"):
            continue
        if fname.endswith(".css"):
            continue
        if fname.endswith(".json"):
            continue
        if fname.endswith(".zip"):
            continue
        if fname.endswith(".bib"):
            continue
        if fname.endswith(".key"):
            continue
        if fname.endswith(".png"):
            continue
        if fname.endswith(".jpg"):
            continue
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
