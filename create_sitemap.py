import os
import io
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import IO, Dict, Iterable, List, Optional

import pytz


TZ = pytz.timezone("US/Eastern")


GH_REMOTE = "origin"
GH_BRANCH = "gh-pages"
GH_SITEMAP = "sitemap.xml"


def check_command(args: List[str]) -> bool:
    print(f"*CMD* {' '.join(args)}", file=sys.stderr)
    proc = subprocess.run(
        args,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    stdout_str = proc.stdout.decode("utf-8").strip()
    stderr_str = proc.stderr.decode("utf-8").strip()
    if stderr_str:
        print("*STDERR START*", file=sys.stderr)
        print(stderr_str, file=sys.stderr)
        print("*STDERR END*", file=sys.stderr)
    if stdout_str:
        print("*STDOUT START*", file=sys.stderr)
        print(stdout_str, file=sys.stderr)
        print("*STDOUT END*", file=sys.stderr)
    print(f"*EXIT CODE* {proc.returncode}")
    return proc.returncode == 0


def run_command(args: List[str], stderr: IO[str] = sys.stderr) -> IO[str]:
    stderr_buff = io.StringIO()
    try:
        proc = subprocess.run(
            args,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        res = io.StringIO(proc.stdout.decode("utf-8"))
        shutil.copyfileobj(io.StringIO(proc.stderr.decode("utf-8")), stderr)
        return res
    except subprocess.CalledProcessError:
        stderr_buff.seek(0, io.SEEK_SET)
        stderr_str = stderr_buff.read()
        if stderr_str:
            print("*STDERR START*", file=sys.stderr)
            print(stderr_str, file=sys.stderr)
            print("*STDERR END*", file=sys.stderr)
        print(f"error while executing: {' '.join(args)}", file=sys.stderr)
        raise


def print_command(args: List[str]) -> None:
    print(f"*CMD* {' '.join(args)}", file=sys.stderr)
    stderr = io.StringIO()
    out = run_command(args, stderr=stderr)
    stderr.seek(0, io.SEEK_SET)
    stderr_str = stderr.read().strip()
    if stderr_str:
        print("*STDERR START*", file=sys.stderr)
        print(stderr_str, file=sys.stderr)
        print("*STDERR END*", file=sys.stderr)
    stdout = out.read().strip()
    if stdout:
        print("*STDOUT START*", file=sys.stderr)
        print(stdout, file=sys.stderr)
        print("*STDOUT END*", file=sys.stderr)


def fetch_gh_pages() -> None:
    print_command(["git", "fetch", GH_REMOTE, GH_BRANCH])


def get_previous_filetimes(domain: str) -> Dict[str, str]:
    res = {}
    gin = run_command(["git", "show", f"{GH_REMOTE}/{GH_BRANCH}:{GH_SITEMAP}"])
    tree = ET.parse(gin)
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


def same_file(fname: str, check_file: str) -> bool:
    if not fname:
        fname = "index.html"
    return check_command([
        "git",
        "diff",
        "--quiet",
        f"{GH_REMOTE}/{GH_BRANCH}:{fname}",
        check_file])


def has_private_folder(filename: str) -> bool:
    fname = os.path.basename(filename)
    if fname.startswith(".") and fname != ".":
        return True
    rec = os.path.dirname(filename)
    if not rec:
        return False
    return has_private_folder(rec)


def create_sitemap(out: IO[str], lines: Iterable[str]) -> None:
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
    domain = "https://josuakrause.github.io"
    root = "/info/"
    fetch_gh_pages()
    prev_times = get_previous_filetimes(domain)

    def write_entry(
            path: str,
            fname: str,
            mod: str,
            check_file: Optional[str] = None) -> None:
        print(f"processing: {domain}{path}{fname}")
        old_mod = prev_times.get(f"{path}{fname}")
        if old_mod is not None:
            if check_file is None or same_file(fname, check_file):
                mod = old_mod
        if mod != old_mod:
            print(f"file change detected: {mod} != {old_mod}")
        out.write(tmpl.format(base=f"{domain}{path}", path=fname, mod=mod))

    def process_line(line: str) -> Optional[str]:
        filename = os.path.normpath(line.strip())
        print(f"checking: {domain}{root}{filename}")
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
        if fname.endswith("index.html"):
            return None
        if fname.endswith("sitemap.xml"):
            return None
        if fname.endswith("cv.pdf"):
            return None
        if os.path.isdir(filename) and not os.path.exists(
                os.path.join(filename, "index.html")):
            return None
        mtime = datetime.fromtimestamp(
            os.path.getmtime(filename), tz=TZ).isoformat()
        actual_file = filename
        filename = filename.rstrip(".")
        write_entry(root, filename, mtime, check_file=actual_file)
        return os.path.dirname(filename)

    for line in sorted(set(lines)):
        if not line.strip():
            continue
        process_line(line)

    curtime = datetime.fromtimestamp(time.time(), tz=TZ).isoformat()
    # NOTE: duplicate, non-canonical, and redirect
    # write_entry(root, "", curtime)
    write_entry("/", "", curtime, check_file="index.html")
    write_entry("/mdsjs/", "", curtime)
    write_entry("/bubblesets-js/", "", curtime)
    write_entry("/bubblesets-js/", "bench.html", curtime)
    write_entry("/bubblesets-js/", "cliques.html", curtime)
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
    with open(output, "w", encoding="utf-8") as f_out:
        create_sitemap(f_out, sys.stdin.readlines())


if __name__ == "__main__":
    run()
