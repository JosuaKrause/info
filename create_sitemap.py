import hashlib
import os
import sys
import time
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterable
from datetime import datetime
from email.utils import parsedate_to_datetime
from io import BytesIO
from typing import IO

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
  xmlns:joschi="https://www.josuakrause.com/">
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
        domain: Callable[[str], str],
        root: str) -> dict[str, tuple[str, str | None]]:
    url = f"{domain('')}{root}{SITEMAP_INTERNAL}"
    req = requests.get(url, timeout=10)
    if req.status_code != 200:
        return {}
    tree = ET.parse(BytesIO(req.content))
    res: dict[str, tuple[str, str | None]] = {}
    for entry in tree.getroot():
        fname = None
        ftime = None
        fhash = None
        for el in entry:
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
        if ".josuakrause.com/" not in fname:
            print(
                "WARNING: invalid entry "
                f"loc={fname} lastmod={ftime}", file=sys.stderr)
            continue
        res[fname] = (ftime, fhash)
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
        domain: Callable[[str], str],
        root: str,
        out: IO[str],
        internal_out: IO[str],
        lines: Iterable[str]) -> None:
    out.write(SITEMAP_HEADER)
    out.flush()
    internal_out.write(SITEMAP_HEADER_INTERNAL)
    internal_out.flush()
    prev_times = get_previous_filetimes(domain, root)
    entries: list[tuple[datetime, Callable[[], None]]] = []

    def get_online_hash(subdomain: str, path: str, fname: str) -> str:
        url = f"{domain(subdomain)}{path}{fname}"
        print(f"hash from url: {url}")
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            raise ValueError(f"failed to access {url} with {res.status_code}")
        return get_hash(res.content)

    def get_file_hash(check_file: str) -> str:
        print(f"hash from file: {check_file}")
        with open(f"{check_file}", "rb") as fin:
            return get_hash(fin.read())

    def get_online_mod(subdomain: str, path: str, fname: str) -> str | None:
        url = f"{domain(subdomain)}{path}{fname}"
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
            subdomain: str,
            path: str,
            fname: str,
            mod: str,
            *,
            check_file: str | None = None,
            check_online: bool = False) -> None:
        print(f"processing: {domain(subdomain)}{path}{fname}")
        if check_online:
            online_mod = get_online_mod(subdomain, path, fname)
            if online_mod is not None:
                mod = online_mod
            else:
                print("WARNING: could not access url for mod time")
        old_mod, old_hash = prev_times.get(
            f"{domain(subdomain)}{path}{fname}", (None, None))
        if check_file is None:
            fhash = get_online_hash(subdomain, path, fname)
        else:
            fhash = get_file_hash(check_file)
        if old_mod is not None and old_hash is not None:
            if old_hash == fhash:
                mod = old_mod
            else:
                print(f"file hash differs: new[{fhash}] != old[{old_hash}]")
        if mod != old_mod:
            print(f"file change detected: new[{mod}] != old[{old_mod}]")

        def write_out() -> None:
            out.write(ENTRY_TEMPLATE.format(
                base=f"{domain(subdomain)}{path}", path=fname, mod=mod))
            internal_out.write(ENTRY_TEMPLATE_INTERNAL.format(
                base=f"{domain(subdomain)}{path}",
                path=fname,
                mod=mod,
                fhash=fhash))

        entries.append((datetime.fromisoformat(mod), write_out))

    def process_line(subdomain: str, line: str) -> str | None:
        filename = os.path.normpath(line.strip())
        print(f"checking: {domain(subdomain)}{root}{filename}")
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
        if fname.endswith("404.html"):
            return None
        if fname.endswith("sitemap.xml"):
            return None
        if fname.endswith("robots.txt"):
            return None
        if fname.endswith("LICENSE"):
            return None
        if os.path.isdir(filename) and not os.path.exists(
                os.path.join(filename, "index.html")):
            return None
        dtime = datetime.fromtimestamp(os.path.getmtime(filename), tz=TZ)
        dtime = dtime.replace(microsecond=0)
        mtime = dtime.isoformat()
        filename = filename.rstrip(".")
        write_entry(subdomain, root, filename, mtime, check_file=filename)
        return os.path.dirname(filename)

    for line in sorted(set(lines)):
        if not line.strip():
            continue
        if process_line("www", line) is None:
            print(f"rejecting {line}")

    curtime = datetime.fromtimestamp(time.time(), tz=TZ).isoformat()
    # NOTE: duplicate, non-canonical, and redirect
    # write_entry(root, "", curtime)
    write_entry("www", "/", "", curtime, check_file="index.html")
    write_entry("mdsjs", "/", "", curtime, check_online=True)
    write_entry("medium", "/", "", curtime, check_online=True)
    write_entry("bubblesets-js", "/", "", curtime, check_online=True)
    write_entry(
        "bubblesets-js", "/", "bench.html", curtime, check_online=True)
    write_entry(
        "bubblesets-js", "/", "cliques.html", curtime, check_online=True)
    write_entry("searchspace", "/", "", curtime, check_online=True)
    write_entry("searchspace", "/", "demo0.html", curtime, check_online=True)
    write_entry("searchspace", "/", "demo1.html", curtime, check_online=True)
    write_entry("searchspace", "/", "demo2.html", curtime, check_online=True)
    write_entry("jk-js", "/", "", curtime, check_online=True)

    entries.sort(key=lambda elem: elem[0], reverse=True)
    for _, entry_cb in entries:
        entry_cb()
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

    def domain(subdomain: str) -> str:
        if not subdomain:
            return "https://josuakrause.com"
        return f"https://{subdomain}.josuakrause.com"

    root = "/"
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
