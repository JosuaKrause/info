import hashlib
import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import IO, Iterable

import pytz
import requests


TZ = pytz.timezone("US/Eastern")


SITEMAP_INTERNAL = "filetimes.xml"


SITEMAP_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<urlset
  xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
    http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
"""


SITEMAP_HEADER_INTERNAL = """<?xml version="1.0" encoding="UTF-8"?>
<urlset
  xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
    http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd"
  xmlns:joschi="https://josuakrause.github.io/info">
"""


ENTRY_TEMPLATE = """  <url>
    <loc>{base}{path}</loc>
    <lastmod>{mod}</lastmod>
  </url>
"""


ENTRY_TEMPLATE_INTERNAL = """  <url>
    <loc>{base}{path}</loc>
    <lastmod>{mod}</lastmod>
    <joschi:filehash>{fhash}</joschi:filehash>
  </url>
"""


def get_hash(content: bytes) -> str:
    blake = hashlib.blake2b(digest_size=32)
    blake.update(content)
    return blake.hexdigest()


def get_previous_filetimes(
        domain: str, root: str) -> dict[str, tuple[str, str | None]]:
    url = f"{domain}{root}{SITEMAP_INTERNAL}"
    req = requests.get(url, timeout=10, stream=True)
    if req.status_code != 200:
        return {}
    print(req.content)
    tree = ET.parse(req.raw)
    res: dict[str, tuple[str, str | None]] = {}
    for entry in tree.getroot():
        fname = None
        ftime = None
        fhash = None
        for el in entry:
            print("tag", el.tag)
            if el.tag.endswith("loc"):
                fname = el.text
            elif el.tag.endswith("lastmod"):
                ftime = el.text
            elif el.tag.endswith("filehash"):
                fhash = el.text
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
        print(f"old sitemap entry: {fname[len(domain):]} {ftime} {fhash}")
        res[fname[len(domain):]] = (ftime, fhash)
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
        internal_out: IO[str],
        lines: Iterable[str]) -> None:
    out.write(SITEMAP_HEADER)
    out.flush()
    internal_out.write(SITEMAP_HEADER_INTERNAL)
    internal_out.flush()
    prev_times = get_previous_filetimes(domain, root)

    def get_online_hash(path: str, fname: str) -> str:
        url = f"{domain}{path}{fname}"
        print(f"hash from url: {url}")
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            raise ValueError(f"failed to access {url} with {res.status_code}")
        return get_hash(res.content)

    def get_file_hash(check_file: str) -> str:
        print(f"hash from file: {check_file}")
        with open(f"{check_file}", "rb") as fin:
            return get_hash(fin.read())

    def get_online_mod(path: str, fname: str) -> str | None:
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
            check_file: str | None = None,
            check_online: bool = False) -> None:
        print(f"processing: {domain}{path}{fname}")
        if check_online:
            online_mod = get_online_mod(path, fname)
            if online_mod is not None:
                mod = online_mod
            else:
                print("WARNING: could not access url for mod time")
        old_mod, old_hash = prev_times.get(f"{path}{fname}", (None, None))
        if check_file is None:
            fhash = get_online_hash(path, fname)
        else:
            fhash = get_file_hash(check_file)
        if old_mod is not None and old_hash is not None:
            if old_hash == fhash:
                mod = old_mod
                print("file hash differs")
        if mod != old_mod:
            print(f"file change detected: {mod} != {old_mod}")
        out.write(ENTRY_TEMPLATE.format(
            base=f"{domain}{path}", path=fname, mod=mod))
        internal_out.write(ENTRY_TEMPLATE_INTERNAL.format(
            base=f"{domain}{path}", path=fname, mod=mod, fhash=fhash))

    def process_line(line: str) -> str | None:
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
    internal_out.write("</urlset>\n")
    internal_out.flush()


def usage() -> None:
    print(f"""
usage: {sys.argv[0]} [-h] <file> <internal>
-h: print help
<file>: specifies the output file
<internal>: specifies the internal output file
""".strip(), file=sys.stderr)
    sys.exit(1)


def run() -> None:
    args = sys.argv[:]
    args.pop(0)
    if "-h" in args:
        usage()
    if len(args) != 2:
        usage()
    output = args[0]
    internal = args[1]
    domain = "https://josuakrause.github.io"
    root = "/info/"
    good = False
    try:
        with open(output, "w", encoding="utf-8") as f_out:
            with open(internal, "w", encoding="utf-8") as f_int:
                create_sitemap(
                    domain, root, f_out, f_int, sys.stdin.readlines())
        good = True
    finally:
        if not good:
            try:
                os.remove(output)
            except FileNotFoundError:
                pass


if __name__ == "__main__":
    run()
