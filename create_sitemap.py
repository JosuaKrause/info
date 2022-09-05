import os
import sys
import time
from datetime import datetime

import pytz


_tz = pytz.timezone("US/Eastern")


def has_private_folder(filename):
    fname = os.path.basename(filename)
    if fname.startswith(".") and fname != ".":
        return True
    rec = os.path.dirname(filename)
    if not rec:
        return False
    return has_private_folder(rec)


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

    def process_line(line):
        filename = os.path.normpath(line.strip())
        print(f"checking: {base}{filename}")
        if has_private_folder(filename):
            return None
        fname = os.path.basename(filename)
        if fname.endswith(".js"):
            return None
        if fname.endswith(".css"):
            return None
        if fname.endswith(".json"):
            return None
        if fname.endswith(".zip"):
            return None
        if fname.endswith(".bib"):
            return None
        if fname.endswith(".key"):
            return None
        if fname.endswith(".png"):
            return None
        if fname.endswith(".jpg"):
            return None
        if os.path.isdir(filename) and not os.path.exists(
                os.path.join(filename, "index.html")):
            return None
        mtime = datetime.fromtimestamp(
            os.path.getmtime(filename), tz=_tz).isoformat()
        filename = filename.rstrip(".")
        print(f"processing: {base}{filename}")
        out.write(tmpl.format(base=base, path=filename, mod=mtime))
        out.flush()
        return os.path.dirname(filename)

    for line in sorted(set(lines)):
        if not line.strip():
            continue
        process_line(line)

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
