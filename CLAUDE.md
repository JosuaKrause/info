# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static personal website (josuakrause.com) built by Python scripts and deployed to GitHub Pages. All site content lives in `content.json`; Python scripts render it into HTML via templates.

## Commands

```bash
make install      # install Python deps
make create       # build the site into www/
make run-web      # build and serve locally (removes www/ on exit)
make clean        # remove www/ and filelist.txt

make lint-flake8       # check trailing commas and import order
make lint-type-check   # mypy
make lint-pylint       # pylint
make lint-all          # all three lints

make pre-commit        # install pre-commit hook and run isort

npm ci                 # install JS dev tools
npm run lint           # eslint on js/ and the templates
npm run typecheck      # tsc in strict mode
npm run format         # prettier --write
npm run check          # lint, typecheck and prettier --check
```

There are no automated tests beyond the lint checks. CI runs `lint-flake8`, `lint-type-check`, `lint-pylint`, then `make create` on every push to `master` and deploys to GitHub Pages. CI does not run the JS checks.

## Architecture

### Data → HTML pipeline

1. **`content.json`** — single source of truth. Contains a `types` array (category definitions) and a `documents` array (every entry on the site: papers, employment, projects, blog posts, etc.).

2. **`create_page.py`** — main build script. Reads `content.json` + `index.tmpl`, produces:
   - `www/index.html` — the full homepage
   - `www/<href>` — individual auto-pages for entries where `"autopage": true`, rendered from `page.tmpl`
   - `www/bibtex/<id>.bib` — BibTeX files for entries with `bibtex` field
   - `www/material/timeline.json` — event data consumed by the JS timeline
   - Resized copies of images (e.g. `img/photo_128x128.jpg`) written into `www/`

3. **`create_sitemap.py`** — reads the file tree of `www/` from stdin and writes `www/sitemap.xml` + `www/filetimes.xml`. Uses content-hashing to preserve `lastmod` when files haven't changed.

4. **`create.sh`** — orchestrates the build: rsync static assets (everything except `.py`, `.tmpl`, `.sh`, `content.json`, etc.) into `www/`, then runs both Python scripts.

### Entry ID stability

Each document gets a stable anchor ID computed as `CRC32("{type_name}_{title}_{mktime(date)}")`, formatted as `entry{hash:08x}`. Avoid changing `title`, `type`, or `date` on existing entries as it will break anchor links.

### content.json schema

Each document object is validated by the `Entry` TypedDict in `create_page.py`. All field names must match the `EntryField` Literal exactly — the parser raises `ValueError` on unknown keys. Notable fields:

- `"autopage": true` — triggers generation of a standalone HTML page at `href`
- `"end-date": "current"` — marks ongoing entries (employment, etc.)
- `"published": false` — shows "to be published…" instead of the date

### Frontend

`js/index.js` and `js/timeline.js` handle the interactive timeline (D3-based). The timeline data is loaded from `material/timeline.json` at runtime. CSS lives in `js/index.css` and `js/timeline.css`. Vendored libs (`lib/bootstrap`, `lib/d3`, `lib/font-awesome`) are committed directly.

### Templates

`index.tmpl` and `page.tmpl` use Python `str.format()` with named placeholders (e.g. `{content}`, `{tracking}`). They are not Jinja2 — curly braces in HTML must be escaped as `{{` / `}}`.
