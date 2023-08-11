import os
import shutil
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Dict, IO, Iterable, Optional

import pytz
import requests


TZ = pytz.timezone("US/Eastern")


SITEMAP = "sitemap.xml"


def get_previous_filetimes(domain: str, root: str) -> Dict[str, str]:
    url = f"{domain}{root}{SITEMAP}"
    req = requests.get(url, timeout=10, stream=True)
    if req.status_code != 200:
        return {}
    try:
        tree = ET.parse(req.raw)
    except ET.ParseError:
        return {}
    res: Dict[str, str] = {}
    for entry in tree.getroot():
        fname = None
        ftime = None
        for el in entry:
            if el.tag.endswith("loc"):
                fname = el.text
            elif el.tag.endswith("lastmod"):
                ftime = el.text
        if fname is None or ftime is None:
            print(
                "WARNING: incomplete entry "
                f"loc={fname} lastmod={ftime}", file=sys.stderr)
            continue
        if not fname.startswith(domain):
            print(
                "WARNING: invalid entry "
                f"loc={fname} lastmod={ftime}", file=sys.stderr)
            continue
        res[fname[len(domain):]] = ftime
    return res


def has_private_folder(filename: str) -> bool:
    fname = os.path.basename(filename)
    if fname.startswith(".") and fname != ".":
        return True
    rec = os.path.dirname(filename)
    if not rec:
        return False
    return has_private_folder(rec)


def create_sitemap(
        domain: str,
        root: str,
        out: IO[str],
        lines: Iterable[str]) -> None:
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
    prev_times = get_previous_filetimes(domain, root)

    def same_file(fname: str, check_file: str) -> bool:
        if not check_file:
            check_file = "index.html"
        url = f"{domain}{root}{fname}"
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            return False
        with open(f"{check_file}", "rb") as fin:
            return res.content == fin.read()

    def get_online_mod(path: str, fname: str) -> Optional[str]:
        url = f"{domain}{path}{fname}"
        res = requests.head(url, timeout=10)
        if res.status_code != 200:
            return None
        lmod = res.headers.get("last-modified")
        if lmod is None:
            return None
        dout = parsedate_to_datetime(lmod)
        dout = dout.astimezone(TZ)
        return dout.isoformat()

    def write_entry(
            path: str,
            fname: str,
            mod: str,
            *,
            check_file: Optional[str] = None,
            check_online: bool = False) -> None:
        print(f"processing: {domain}{path}{fname}")
        old_mod = prev_times.get(f"{path}{fname}")
        if old_mod is not None:
            if check_file is None or same_file(fname, check_file):
                mod = old_mod
        if check_online:
            online_mod = get_online_mod(path, fname)
            if online_mod is not None:
                mod = online_mod
        if mod != old_mod:
            print(f"file change detected: {mod} != {old_mod}")
        out.write(tmpl.format(base=f"{domain}{path}", path=fname, mod=mod))

    def process_line(line: str) -> Optional[str]:
        filename = os.path.normpath(line.strip())
        print(f"checking: {domain}{root}{filename}")
        if has_private_folder(filename):
            return None
        fname = os.path.basename(filename)
        if filename == ".":
            return None
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
        if fname.endswith("index.html"):
            return None
        if fname.endswith("sitemap.xml"):
            return None
        if fname.endswith("cv.pdf"):
            return None
        if os.path.isdir(filename) and not os.path.exists(
                os.path.join(filename, "index.html")):
            return None
        dtime = datetime.fromtimestamp(os.path.getmtime(filename), tz=TZ)
        dtime = dtime.replace(microsecond=0)
        mtime = dtime.isoformat()
        filename = filename.rstrip(".")
        write_entry(root, filename, mtime, check_file=filename)
        return os.path.dirname(filename)

    for line in sorted(set(lines)):
        if not line.strip():
            continue
        if process_line(line) is None:
            print(f"rejecting {line}")

    curtime = datetime.fromtimestamp(time.time(), tz=TZ).isoformat()
    # NOTE: duplicate, non-canonical, and redirect
    # write_entry(root, "", curtime)
    write_entry("/", "", curtime, check_file="index.html")
    write_entry("/mdsjs/", "", curtime, check_online=True)
    write_entry("/bubblesets-js/", "", curtime, check_online=True)
    write_entry("/bubblesets-js/", "bench.html", curtime, check_online=True)
    write_entry("/bubblesets-js/", "cliques.html", curtime, check_online=True)
    write_entry("/searchspace/", "", curtime, check_online=True)
    write_entry("/searchspace/", "demo0.html", curtime, check_online=True)
    write_entry("/searchspace/", "demo1.html", curtime, check_online=True)
    write_entry("/searchspace/", "demo2.html", curtime, check_online=True)
    out.write("</urlset>\n")
    out.flush()


def usage() -> None:
    print(f"""
usage: {sys.argv[0]} [-h] <file>
-h: print help
<file>: specifies the output file
""".strip(), file=sys.stderr)
    sys.exit(1)


def run() -> None:
    args = sys.argv[:]
    args.pop(0)
    if "-h" in args:
        usage()
    if len(args) != 1:
        usage()
    output = args[0]
    domain = "https://josuakrause.github.io"
    root = "/info/"
    good = False
    try:
        with open(output, "w", encoding="utf-8") as f_out:
            create_sitemap(domain, root, f_out, sys.stdin.readlines())
        good = True
    finally:
        if not good:
            try:
                os.remove(output)
            except FileNotFoundError:
                pass
            url = f"{domain}{root}{SITEMAP}"
            print("attempting to reuse old sitemap")
            try:
                req = requests.get(url, timeout=10, stream=True)
                if req.status_code == 200:
                    with open(output, "wb") as f_out:
                        shutil.copyfileobj(req.raw, f_out)
            except OSError:
                print("reusing old sitemap failed")


if __name__ == "__main__":
    run()
