import json
import os
import re
import sys
import zlib
from datetime import datetime, timedelta

import pytz
from dateutil.parser import parse as tparse


NL = "\n"


LD_JSON_KNOWLEDGE = """{
  "@id": "https://josuakrause.github.io/info/",
  "@type": "http://schema.org/Person",
  "http://schema.org/additionalName": "Joschi",
  "http://schema.org/affiliation": {
    "@type": "http://schema.org/Organization",
    "http://schema.org/name": "Accern Corp."
  },
  "http://schema.org/alumniOf": {
    "@type": "http://schema.org/EducationalOrganization",
    "http://schema.org/name": "NYU"
  },
  "http://schema.org/birthDate": "January 18, 1988",
  "http://schema.org/familyName": "Krause",
  "http://schema.org/givenName": "Josua",
  "http://schema.org/image": {
    "@type": "http://schema.org/URL",
    "@id": "https://josuakrause.github.io/info/img/photo.jpg"
  },
  "http://schema.org/jobTitle": "Vice President of Data Science",
  "http://schema.org/name": "Josua Krause",
  "http://schema.org/sameAs": [
    {
      "@type": "http://schema.org/URL",
      "@id": "https://www.linkedin.com/in/josuakrause/"
    },
    {
      "@type": "http://schema.org/URL",
      "@id": "https://www.linkedin.com/in/josua-krause-48b3b091/"
    },
    {
      "@type": "http://schema.org/URL",
      "@id": "https://github.com/JosuaKrause/"
    },
    {
      "@type": "http://schema.org/URL",
      "@id": "https://www.youtube.com/c/JosuaKrause/"
    },
    {
      "@type": "http://schema.org/URL",
      "@id": "http://archive.engineering.nyu.edu/people/josua-krause"
    },
    {
      "@type": "http://schema.org/URL",
      "@id": "https://vimeo.com/user35425102"
    },
    {
      "@type": "http://schema.org/URL",
      "@id": "https://scholar.google.com/citations?user=hFjNgPEAAAAJ"
    },
    {
      "@type": "http://schema.org/URL",
      "@id": "https://dblp.uni-trier.de/pers/k/Krause:Josua.html"
    },
    {
      "@type": "http://schema.org/URL",
      "@id": "https://dblp.org/pers/k/Krause:Josua.html"
    },
    {
      "@type": "http://schema.org/URL",
      "@id": "https://dl.acm.org/profile/99659020297"
    },
    {
      "@type": "http://schema.org/URL",
      "@id": "https://ieeexplore.ieee.org/author/37085594931"
    },
    {
      "@type": "http://schema.org/URL",
      "@id": "https://theorg.com/org/accern/team/josua-krause"
    }
  ]
}"""

GA_TRACKING = """
<!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=UA-77732102-1">
</script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'UA-77732102-1');
</script>
"""

TAG = r"<[^>]*?>"

DESCRIPTION = """
Josua Krause is the VP of Data Science at
<a href="https://www.accern.com/">Accern</a>, a no-code AI startup with offices
in New York and Bangalore, where he leads the research, development, and
deployment of AI models. Accern allows organizations to build and deploy AI
solutions utilizing adaptive NLP and predictive features with a no-code
development platform. His focus is on deep representation learning, natural
language processing, and adaptive learning at scale. He recently has been
Adjunct Professor at <a href="http://engineering.nyu.edu/">NYU</a>
where he also received his Ph.D. in Explainable Machine Learning under
<a href="http://enrico.bertini.io/">Prof. Dr. Enrico Bertini</a>.
"""

DESCRIPTION_ADD = """
<a href="material/cv_krause.pdf">[Curriculum Vitae]</a>
"""

COPYRIGHT = "jk 2022"


_compute_self = "total_seconds" not in dir(timedelta(seconds=1))
_tz = pytz.timezone("US/Eastern")
_epoch = datetime(year=1970, month=1, day=1, tzinfo=_tz)
_DAY_SECONDS = 24 * 3600
_MILLI = 10 ** 6


def mktime(dtime):
    if dtime.tzinfo is None:
        dtime = datetime(
            year=dtime.year,
            month=dtime.month,
            day=dtime.day,
            tzinfo=_tz)
    if not _compute_self:
        res = (dtime - _epoch).total_seconds()
    else:
        tdelta = dtime - _epoch
        res = (
            tdelta.microseconds + (
                tdelta.seconds + tdelta.days * _DAY_SECONDS) * _MILLI
            ) / _MILLI
    return int(res - res % _DAY_SECONDS)


def monthtime(dtime):
    return f"{dtime.year}-{dtime.month}"


def year(dtime):
    return dtime.year


def chk(doc, field):
    return field in doc and doc[field]


def create_autopage(content, doc, ofile, dry_run):
    abstract = (
        "<h4>Abstract</h4><p style=\"text-align: justify;\">"
        f"{doc['abstract']}</p>" if chk(doc, "abstract") else "")
    bibtex = (
        f"<h4>Bibtex</h4><pre>{doc['bibtex'].strip()}</pre>"
        if chk(doc, 'bibtex') else "")
    image = f"""
    <div class="row">
        <div class="col-md-9">
            <img alt="{
        doc['teaser_desc'] if chk(doc, 'teaser_desc') else doc['teaser']
        }" src="{doc['teaser']}" style="margin: 0 5%; width: 90%;">
        </div>
    </div>
    """ if chk(doc, "teaser") else ""
    if chk(doc, "video"):
        m = re.match("^https?://vimeo.com/(\\d+)$", doc['video'])
        if m is not None:
            video = f"""
            <p style="text-align: center; margin: 0 auto;">
              <iframe src="https://player.vimeo.com/video/{m.group(1)}"
                      width="640" height="389" frameborder="0"
                      webkitallowfullscreen mozallowfullscreen
                      allowfullscreen></iframe>
              <br><a href="https://vimeo.com/{
                m.group(1)}">Watch video on Vimeo</a>
            </p>
            """
        else:
            video = ""
    else:
        video = ""
    if chk(doc, "talk"):
        m = re.match("^https?://vimeo.com/(\\d+)$", doc['talk'])
        if m is not None:
            talk = f"""
            <p style="text-align: center; margin: 0 auto;">
              <iframe src="https://player.vimeo.com/video/{m.group(1)}"
                      width="640" height="389" frameborder="0"
                      webkitallowfullscreen mozallowfullscreen
                      allowfullscreen></iframe>
              <br><a href="https://vimeo.com/{
                m.group(1)}">Watch talk on Vimeo</a>
            </p>
            """
        else:
            talk = ""
    else:
        talk = ""
    links = []
    add_misc_links(links, doc, video)
    keywords = []
    if "keywords" in doc:
        keywords.extend(doc["keywords"])
    output = content.format(
        title=doc["title"],
        conference=doc["conference"],
        authors=doc["authors"],
        image=image,
        abstract=abstract,
        links=(
            f"<h3 style=\"text-align: center;\">{' '.join(links)}</h3>"
            if links else ""),
        bibtex=bibtex,
        logo=doc['logo'] if chk(doc, 'logo') else "img/nologo.png",
        video=video,
        talk=talk,
        tracking=GA_TRACKING,
        description=(
            f"{doc['title']} by {doc['authors']} "
            f"appears in {doc['conference']}"),
        copyright=COPYRIGHT)
    if not dry_run:
        with open(ofile, "w", encoding="utf-8") as fout:
            fout.write(output)


def add_misc_links(appendix, doc, no_video=False):
    if chk(doc, "demo"):
        appendix.append(f"<a href=\"{doc['demo']}\">[demo]</a>")
    if chk(doc, "pdf"):
        appendix.append(f"<a href=\"{doc['pdf']}\">[pdf]</a>")
    if chk(doc, "video") and not no_video:
        appendix.append(f"<a href=\"{doc['video']}\">[video]</a>")
    if chk(doc, "talk") and not no_video:
        appendix.append(f"<a href=\"{doc['talk']}\">[talk]</a>")
    if chk(doc, "github"):
        appendix.append(f"<a href=\"{doc['github']}\">[github]</a>")
    if chk(doc, "slides"):
        appendix.append(f"<a href=\"{doc['slides']}\">[slides]</a>")
    if chk(doc, "external"):
        appendix.append(f"<a href=\"{doc['external']}\">[external]</a>")
    if chk(doc, "poster"):
        appendix.append(f"<a href=\"{doc['poster']}\">[poster]</a>")


def create_media(pref, types, group_by, docs, *, event_types, dry_run):
    type_lookup = {}
    for kind in types:
        type_lookup[kind["type"]] = kind
        kind["docs"] = []
    for doc in docs:
        kind = type_lookup[group_by(doc)]
        kind["docs"].append(doc)
    etype_order = {}
    event_kind_lookup = {}
    for (ix, kind) in enumerate(event_types):
        event_kind_lookup[kind["type"]] = kind
        etype_order[kind["type"]] = len(event_types) - ix
    event_times = {}
    events = []
    content = ""
    auto_pages = []
    for kind in types:
        if not kind["docs"]:
            continue
        content += (
            "<h3 class=\"group_header\" "
            f"id=\"{kind['type']}\">{kind['name']}</h3>")

        def skey(t):
            return (
                etype_order[t["type"]],
                tparse(t["date"]),
                t["title"],
            )

        kind["docs"].sort(key=skey, reverse=True)
        for doc in kind["docs"]:
            id_str = (
                f"{kind['name']}_{doc['title']}_"
                f"{mktime(tparse(doc['date']))}")
            hash_id = zlib.crc32(id_str.encode("utf-8")) & 0xffffffff
            entry_id = f"entry{hash_id:08x}"
            appendix = []
            if "href" in doc and doc["href"]:
                if chk(doc, "autopage"):
                    auto_pages.append(doc)
                appendix.append(
                    f"<a href=\"{doc['href']}\">[page]</a>")
            add_misc_links(appendix, doc)
            if chk(doc, "bibtex"):
                bibtex = doc["bibtex"].strip()
                bibtex_link = f"bibtex/{entry_id}.bib"
                bibtex_filename = os.path.join(
                    pref if pref is not None else ".", bibtex_link)
                if not dry_run:
                    if not os.path.exists(os.path.dirname(bibtex_filename)):
                        os.makedirs(os.path.dirname(bibtex_filename))
                    with open(bibtex_filename, "w", encoding="utf-8") as f:
                        print(bibtex, file=f)
                appendix.append(
                    f"<a href=\"{bibtex_link}\" rel=\"nofollow\">[bibtex]</a>")
            authors = doc["authors"].replace(
                "Josua Krause",
                "<span style=\"text-decoration: underline;\">"
                "Josua Krause</span>")
            awards = [
                "<img src=\"img/badge.png\" "
                "style=\"width: 1em; height: 1em;\" "
                f"alt=\"{award}\" title=\"{award}\">"
                for award in doc["awards"]
            ] if chk(doc, "awards") else []
            pub = (
                doc["date"] if doc["published"] else "to be published&hellip;")
            appx = f"<br/>{NL}{' '.join(appendix)}" if appendix else ""
            awds = (
                f"{' ' if appx else f'<br/>{NL}'}{' '.join(awards)}"
                if awards else "")
            kind_name = event_kind_lookup[doc["type"]]["name"]
            body = f"""
            <h4 class="media-heading">
              <a href="#{entry_id}" class="anchor">
                {doc['title']}
                <i class="fa fa-thumb-tack fa-1" aria-hidden="true"></i>
              </a><br/>
              <small>{kind_name}: {authors}</small>
            </h4>
            <em>{doc['conference']} &mdash; {pub}</em>{appx}{awds}
            """
            lsrc = doc["logo"] if chk(doc, "logo") else "img/nologo.png"
            sttl = (
                doc["short-title"]
                if chk(doc, "short-title")
                else doc["title"])
            entry = f"""
            <a class="pull-left" href="#{entry_id}">
              <img
                class="media-object"
                src="{lsrc}"
                title="{doc['title']}"
                alt="{sttl}"
                style="width: 64px; height: 64px;">
            </a>
            <div class="media-body">
              {body}
            </div>
            """
            content += f"""
            <div class="media type_{doc['type']} mg_{kind['type']}">
              <div class="smt_anchor" id="{entry_id}"></div>
              {entry}
            </div>
            """
            otid = (
                doc["short-conference"]
                if chk(doc, "short-conference")
                else doc["conference"])
            tid = otid
            mtime = monthtime(tparse(doc["date"]))
            if mtime not in event_times:
                event_times[mtime] = set()
            num = 1
            while tid in event_times[mtime]:
                num += 1
                tid = f"{otid} ({num})"
            event_times[mtime].add(tid)
            event = {
                "id": tid,
                "group": doc["type"],
                "name": doc["title"],
                "time": mktime(tparse(doc["date"])),
                "link": f"#{entry_id}",
            }
            events.append(event)
    if not dry_run:
        timeline_fn = os.path.join(
            pref if pref is not None else ".", "material/timeline.json")
        if not os.path.exists(os.path.dirname(timeline_fn)):
            os.makedirs(os.path.dirname(timeline_fn))
        with open(timeline_fn, "w", encoding="utf-8") as tlout:
            type_names = {}
            for kind in event_types:
                type_names[kind["type"]] = kind["name"]
            print(json.dumps({
                "events": events,
                "type_names": type_names,
            }, sort_keys=True, indent=2), file=tlout)
    if auto_pages:
        with open("page.tmpl", "r", encoding="utf-8") as tfin:
            page_tmpl = tfin.read()
        for doc in auto_pages:
            create_autopage(
                page_tmpl, doc, os.path.join(
                    pref if pref is not None else ".", doc["href"]), dry_run)
    return content


def apply_template(tmpl, docs, pref, *, is_ordered_by_type, dry_run):
    with open(tmpl, "r", encoding="utf-8") as tfin:
        content = tfin.read()
    with open(docs, "r", encoding="utf-8") as dfin:
        data = dfin.read()

        def sanitize(m):
            return m.group(0).replace("\n", "\\n")

        data = re.sub(
            r'''"([^"]|\\\\")*":\s*"([^"]|\\\\")*"''', sanitize, data)
        dobj = json.loads(data)

    def get_type(doc):
        return doc["type"]

    def get_date(doc):
        return f"{year(tparse(doc['date']))}"

    if is_ordered_by_type:
        type_order = dobj["types"]
        group_by = get_type
    else:
        types = set()
        for doc in dobj["documents"]:
            types.add(get_date(doc))
        group_by = get_date
        type_order = [
            {
                "type": f"{year_str}",
                "name": f"{year_str}",
                "color": "black",
            } for year_str in sorted(types, key=int, reverse=True)
        ]
    doc_objs = dobj["documents"]
    media = create_media(
        pref,
        type_order,
        group_by,
        doc_objs,
        event_types=dobj["types"],
        dry_run=dry_run)
    js_fillin = """
    function start() {
      var header_height = d3.select("#smt_header").node().clientHeight;
      var hd_margin_and_border = 22;
      var el_margin_small = 15;
      d3.select("#smt_pad").style({
        "height": (hd_margin_and_border + header_height) + "px",
      });
      d3.selectAll(".smt_anchor").style({
        "top": -(el_margin_small + header_height) + "px",
      });
      var w = "100%";
      var h = 300;
      var radius = 8;
      var textHeight = 20;
      var timeline = new Timeline(
        d3.select("#div-timeline"),
        d3.select("#div-legend"),
        w, h, radius, textHeight);
      d3.json("material/timeline.json", function(err, data) {
        if(err) {
          console.warn(err);
          d3.select("#timeline-row").style({
            "display": "none",
          });
          return;
        }
        timeline.typeNames(data["type_names"]);
        timeline.events(data["events"]);
        timeline.update();
      });
    }
    """
    return content.format(
        name="Josua (Joschi) Krause",
        description=re.sub(TAG, "", DESCRIPTION),
        description_long=DESCRIPTION,
        description_add=DESCRIPTION_ADD,
        content=media,
        js=js_fillin,
        tracking=GA_TRACKING,
        knowledge=LD_JSON_KNOWLEDGE,
        copyright=COPYRIGHT)


def usage():
    print(f"""
usage: {
    sys.argv[0]
    } [-h] [--dry] [--out <file>] --documents <file> --template <file>
-h: print help
--documents <file>: specifies the documents input
--template <file>: specifies the template file
--prefix <file>: specifies the file prefix
--out <file>: specifies the output file. default is STD_OUT.
--dry: do not produce any output
""".strip(), file=sys.stderr)
    sys.exit(1)


def run():
    tmpl = None
    docs = None
    pref = None
    out = "-"
    dry_run = False
    args = sys.argv[:]
    args.pop(0)
    while args:
        arg = args.pop(0)
        if arg == "-h":
            usage()
        elif arg == "--template":
            if not args:
                print("--template requires argument", file=sys.stderr)
                usage()
            tmpl = args.pop(0)
        elif arg == "--out":
            if not args:
                print("--out requires argument", file=sys.stderr)
                usage()
            out = args.pop(0)
        elif arg == "--documents":
            if not args:
                print("--documents requires argument", file=sys.stderr)
                usage()
            docs = args.pop(0)
        elif arg == "--prefix":
            if not args:
                print("--prefix requires argument", file=sys.stderr)
                usage()
            pref = args.pop(0)
        elif arg == "--dry":
            dry_run = True
        else:
            print(f"unrecognized argument: {arg}", file=sys.stderr)
            usage()
    if tmpl is None or docs is None:
        print("input is underspecified", file=sys.stderr)
        usage()
    content = apply_template(
        tmpl,
        docs,
        pref,
        is_ordered_by_type=False,
        dry_run=dry_run)
    if not dry_run:
        if out != "-":
            with open(out, "w", encoding="utf-8") as outf:
                outf.write(content)
        else:
            sys.stdout.write(content)
            sys.stdout.flush()


if __name__ == "__main__":
    run()
