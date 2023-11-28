import argparse
import json
import os
import re
import sys
import zlib
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any, cast, get_args, Literal, Set, TypedDict

import pytz
from dateutil.parser import parse as tparse
from PIL import Image


Entry = TypedDict('Entry', {
    "abstract": list[str],
    "article": str,
    "authors": str,
    "autopage": bool,
    "awards": list[str],
    "bibtex": list[str],
    "conference": str,
    "date": str,
    "demo": str,
    "external": str,
    "github": str,
    "href": str,
    "keywords": list[str],
    "logo": str,
    "pdf": str,
    "poster": str,
    "published": bool,
    "short-conference": str,
    "short-title": str,
    "slides": str,
    "talk": str,
    "teaser_desc": str,
    "teaser": str,
    "title": str,
    "type": str,
    "video": str,
    "ogimg": str,
    "ogimgwidth": int,
    "ogimgheight": int,
}, total=False)
EntryField = Literal[
    "abstract",
    "article",
    "authors",
    "autopage",
    "awards",
    "bibtex",
    "conference",
    "date",
    "demo",
    "external",
    "github",
    "href",
    "keywords",
    "logo",
    "pdf",
    "poster",
    "published",
    "short-conference",
    "short-title",
    "slides",
    "talk",
    "teaser_desc",
    "teaser",
    "title",
    "type",
    "video",
]
ALLOWED_FIELDS: Set[EntryField] = set(get_args(EntryField))


def parse_entry(obj: dict[str, Any]) -> Entry:
    for key in obj.keys():
        if key not in ALLOWED_FIELDS:
            raise ValueError(f"unknown field: {key}")
    return cast(Entry, obj)


Group = TypedDict('Group', {
    "color": str,
    "docs": list[Entry],
    "name": str,
    "type": str,
})


def parse_group(obj: dict[str, Any]) -> Group:
    return {
        "name": f"{obj['name']}",
        "type": f"{obj['type']}",
        "color": f"{obj['color']}",
        "docs": [],
    }


Event = TypedDict('Event', {
    "id": str,
    "group": str,
    "name": str,
    "time": int,
    "link": str,
})


NL = "\n"


LD_JSON_KNOWLEDGE = """{
  "@context": "https://json-ld.org/contexts/person.jsonld",
  "@id": "https://www.josuakrause.com/",
  "@type": "http://schema.org/Person",
  "http://schema.org/additionalName": "Joschi",
  "http://schema.org/affiliation": {
    "@type": "http://schema.org/Organization",
    "http://schema.org/name": "UNDP Accelerator Labs"
  },
  "http://schema.org/alumniOf": {
    "@type": "http://schema.org/EducationalOrganization",
    "http://schema.org/name": "NYU"
  },
  "http://schema.org/birthDate": "1988-01-18",
  "http://schema.org/familyName": "Krause",
  "http://schema.org/givenName": "Josua",
  "http://schema.org/image": {
    "@type": "http://schema.org/URL",
    "@id": "https://www.josuakrause.com/img/photo.jpg"
  },
  "http://schema.org/jobTitle": "NLP Researcher",
  "http://schema.org/name": "Josua Krause",
  "http://schema.org/sameAs": [
    {
      "@type": "http://schema.org/URL",
      "@id": "https://www.linkedin.com/in/josuakrause/"
    },
    {
      "@type": "http://schema.org/URL",
      "@id": "https://medium.josuakrause.com/"
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
      "@id": "https://vimeo.com/user35425102"
    },
    {
      "@type": "http://schema.org/URL",
      "@id": "https://scholar.google.com/citations?user=hFjNgPEAAAAJ"
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
      "@id": "https://www.researchgate.net/profile/Josua-Krause"
    },
    {
      "@type": "http://schema.org/URL",
      "@id": "https://orcid.org/0000-0001-7292-7196"
    },
    {
      "@type": "http://schema.org/URL",
      "@id": "https://www.semanticscholar.org/author/Josua-Krause/39697904"
    }
  ]
}"""

GA_TRACKING = """
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-4DHJEMESJD">
</script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-4DHJEMESJD');
</script>
<!-- Google tag end -->
""".strip()

TAG = r"<[^>]*?>"
SPACES = r"\s+"

DESCRIPTION_SHORT = """
Josua Krause has led Data Science teams for research, development, and
deployment of AI models. His focus is on accessibility of large language models
in low-resource environments and facilitating information access in
low-bandwidth communities through LLMs.
""".strip()

DESCRIPTION = """
Josua Krause has led Data Science teams for research, development, and
deployment of AI models. His focus is on accessibility of large language models
in low-resource environments and facilitating information access in
low-bandwidth communities through LLMs.
He received his Ph.D. in Explainable Machine Learning under
<a href="https://enrico.bertini.io/">Prof. Dr. Enrico Bertini</a>
at
<a href="https://engineering.nyu.edu/">NYU</a>.
""".strip()

DESCRIPTION_ADD = """
Curriculum Vitae:
<a href="material/cv_krause_short.pdf">[Short CV]</a>
<a href="material/cv_krause.pdf">[Long CV]</a>
""".strip()

COPYRIGHT = "jk 2023"


COMPUTE_SELF: bool = "total_seconds" not in dir(timedelta(seconds=1))
TZ_DEFAULT = pytz.timezone("US/Eastern")
EPOCH: datetime = datetime(year=1970, month=1, day=1, tzinfo=TZ_DEFAULT)
DAY_SECONDS: int = 24 * 3600
MILLI: int = 10 ** 6


def mktime(dtime: datetime) -> int:
    if dtime.tzinfo is None:
        dtime = datetime(
            year=dtime.year,
            month=dtime.month,
            day=dtime.day,
            tzinfo=TZ_DEFAULT)
    if not COMPUTE_SELF:
        res = (dtime - EPOCH).total_seconds()
    else:
        tdelta = dtime - EPOCH
        large_units = tdelta.seconds + tdelta.days * DAY_SECONDS
        res = (tdelta.microseconds + large_units * MILLI) / MILLI
    return int(res - res % DAY_SECONDS)


def normdate(datestr: str) -> str:
    if "," not in datestr:
        return f"Jan 1, {datestr}"
    monthday, tyear = datestr.split(",", 1)
    if any(char.isdigit() for char in monthday):
        return datestr
    return f"{monthday} 1, {tyear}"


def monthtime(dtime: datetime) -> str:
    return f"{dtime.year}-{dtime.month}"


def year(dtime: datetime) -> int:
    return dtime.year


def datetuple(dtime: datetime) -> tuple[int, int, int]:
    return (dtime.year, dtime.month, dtime.day)


def chk(doc: Entry, field: EntryField) -> bool:
    return field in doc and bool(doc[field])


BADNESS = 0.1


def resize_img(
        prefix: str,
        image: str,
        width: int | None,
        height: int | None,
        *,
        nostretch: bool = True,
        noupscale: bool = False,
        record_size: Callable[[int, int], None] | None = None) -> str:
    img = Image.open(os.path.join(prefix, image))
    iwidth = img.width
    iheight = img.height

    def record(owidth: int, oheight: int) -> None:
        if record_size is None:
            return
        record_size(owidth, oheight)

    if iwidth == 1 and iheight == 1:
        record(iwidth, iheight)
        return image
    if ((width is None and height is None)
            or (width == iwidth and height == iheight)):
        record(iwidth, iheight)
        return image
    if width is None:
        assert height is not None
        width = iwidth * height // iheight
    if height is None:
        height = iheight * width // iwidth
    if nostretch and (
            int(BADNESS * iwidth / width) != int(BADNESS * iheight / height)):
        raise ValueError(
            "resizing would stretch the image: "
            f"{iwidth}x{iheight} to {width}x{height} "
            f"(rw: {iwidth / width} rh: {iheight / height})")
    if noupscale and (iwidth < width or iheight < height):
        record(iwidth, iheight)
        return image
    oimg = img.resize((width, height))
    ext_ix = image.rindex(".")
    oname = f"{image[:ext_ix]}_{oimg.width}x{oimg.height}.png"
    ofname = os.path.join(prefix, oname)
    # if os.path.exists(ofname):
    #     raise ValueError(f"image already exists! {ofname}")
    record(oimg.width, oimg.height)
    oimg.save(ofname)
    return oname


def create_autopage(
        content: str, doc: Entry, ofile: str, dry_run: bool) -> None:
    abstract = (
        "<h4>Abstract</h4><p style=\"text-align: justify;\">"
        f"{NL.join(doc['abstract'])}</p>" if chk(doc, "abstract") else "")
    bibtex = (
        f"<h4>Bibtex</h4><pre>{(NL.join(doc['bibtex'])).strip()}</pre>"
        if chk(doc, "bibtex") else "")
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
            style = (
                "text-align: center; "
                "margin: 0 auto; "
                "width: 640px; "
                "height: 389px"
            )
            video = f"""
            <p style="{style}">
              <iframe
                src="https://player.vimeo.com/video/{m.group(1)}"
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
            style = (
                "text-align: center; "
                "margin: 0 auto; "
                "width: 640px; "
                "height: 389px"
            )
            talk = f"""
            <p style="{style}">
              <iframe
                src="https://player.vimeo.com/video/{m.group(1)}"
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
    links: list[str] = []
    add_misc_links(links, doc, bool(video))
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
        copyright=COPYRIGHT,
        canonical=os.path.basename(ofile),
        ogtitle=doc["title"],
        ogdescription=f"by {doc['authors']} appears in {doc['conference']}",
        ogimg=doc["ogimg"],
        ogimgwidth=doc["ogimgwidth"],
        ogimgheight=doc["ogimgheight"])
    if not dry_run:
        with open(ofile, "w", encoding="utf-8") as fout:
            fout.write(output)


def add_misc_links(
        appendix: list[str], doc: Entry, no_video: bool = False) -> None:
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
    if chk(doc, "article"):
        appendix.append(f"<a href=\"{doc['article']}\">[article]</a>")
    if chk(doc, "poster"):
        appendix.append(f"<a href=\"{doc['poster']}\">[poster]</a>")


def create_media(
        prefix: str,
        types: list[Group],
        group_order: list[str],
        group_by: Callable[[Entry], str],
        docs: list[Entry],
        *,
        event_types: list[Group],
        dry_run: bool) -> str:
    type_lookup: dict[str, Group] = {}
    for kind in types:
        type_lookup[kind["type"]] = kind
        kind["docs"] = []
    for doc in docs:
        kind = type_lookup[group_by(doc)]
        kind["docs"].append(doc)
    etype_order: dict[str, int] = {}
    event_kind_lookup: dict[str, Group] = {}
    for (ix, kind) in enumerate(event_types):
        event_kind_lookup[kind["type"]] = kind
        etype_order[kind["type"]] = len(event_types) - ix
    event_times: dict[str, Set[str]] = {}
    events: list[Event] = []
    content = ""
    auto_pages: list[Entry] = []
    for kind in types:
        if not kind["docs"]:
            continue
        content += (
            "<h3 class=\"group_header\" "
            f"id=\"{kind['type']}\">{kind['name']}</h3>")

        def skey(t: Entry) -> tuple[int, int, int, int, str]:
            tyear, tmonth, tday = datetuple(tparse(normdate(t["date"])))
            print(t, tyear, tmonth, tday)
            return (
                tyear,
                tmonth,
                tday,
                etype_order[t["type"]],
                t["title"],
            )

        def set_og(doc: Entry) -> Callable[[int, int], None]:

            def inner(owidth: int, oheight: int) -> None:
                doc["ogimgwidth"] = owidth
                doc["ogimgheight"] = oheight

            return inner

        kind["docs"].sort(key=skey, reverse=True)
        for doc in kind["docs"]:
            id_str = (
                f"{kind['name']}_{doc['title']}_"
                f"{mktime(tparse(doc['date']))}")
            print(f"hashing: {id_str}")
            hash_id = zlib.crc32(id_str.encode("utf-8")) & 0xffffffff
            entry_id = f"entry{hash_id:08x}"
            appendix = []
            if "href" in doc and doc["href"]:
                if chk(doc, "autopage"):
                    if chk(doc, "logo") and doc["logo"] != "img/nologo.png":
                        ogimg = doc["logo"]
                    elif chk(doc, "teaser"):
                        ogimg = doc["teaser"]
                    else:
                        ogimg = "img/photo.jpg"
                    doc["ogimg"] = resize_img(
                        prefix,
                        ogimg,
                        None,
                        630,
                        noupscale=True,
                        record_size=set_og(doc))
                    auto_pages.append(doc)
                appendix.append(
                    f"<a href=\"{doc['href']}\">[page]</a>")
            add_misc_links(appendix, doc)
            if chk(doc, "bibtex"):
                bibtex = (NL.join(doc["bibtex"])).strip()
                bibtex_link = f"bibtex/{entry_id}.bib"
                bibtex_filename = os.path.join(prefix, bibtex_link)
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
            lsrc = (
                resize_img(prefix, doc["logo"], 128, None)
                if chk(doc, "logo")
                else "img/nologo.png")
            sttl = (
                doc["short-title"]
                if chk(doc, "short-title")
                else doc["title"])
            add_class = ""
            if lsrc == "img/nologo.png":
                add_class = " no-img"
            entry = f"""
            <a class="pull-left" href="#{entry_id}">
              <img
                class="media-object{add_class}"
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
            event: Event = {
                "id": tid,
                "group": doc["type"],
                "name": doc["title"],
                "time": mktime(tparse(doc["date"])),
                "link": f"#{entry_id}",
            }
            events.append(event)
    if not dry_run:
        timeline_fn = os.path.join(prefix, "material/timeline.json")
        if not os.path.exists(os.path.dirname(timeline_fn)):
            os.makedirs(os.path.dirname(timeline_fn))
        with open(timeline_fn, "w", encoding="utf-8") as tlout:
            type_names = {}
            for kind in event_types:
                type_names[kind["type"]] = kind["name"]
            print(json.dumps({
                "events": events,
                "type_names": type_names,
                "type_order": group_order,
            }, sort_keys=True, indent=2), file=tlout)
    if auto_pages:
        with open("page.tmpl", "r", encoding="utf-8") as tfin:
            page_tmpl = tfin.read()
        for doc in auto_pages:
            create_autopage(
                page_tmpl, doc, os.path.join(prefix, doc["href"]), dry_run)
    return content


def apply_template(
        tmpl: str,
        docs: str,
        prefix: str,
        *,
        is_ordered_by_type: bool,
        dry_run: bool) -> str:
    resize_img(prefix, "img/mediumlogo.png", None, 64)
    resize_img(prefix, "img/scholarlogo.png", None, 64)
    resize_img(prefix, "img/linkedinlogo.png", None, 64)
    resize_img(prefix, "img/researchgatelogo.png", None, 64)
    resize_img(prefix, "img/github-mark.png", None, 64)
    resize_img(prefix, "img/photo.jpg", None, 128)
    ogimg = resize_img(prefix, "img/photo.jpg", None, 630)
    with open(tmpl, "r", encoding="utf-8") as tfin:
        content = tfin.read()
    with open(docs, "r", encoding="utf-8") as dfin:
        data = dfin.read()

        def sanitize(m: re.Match) -> str:
            return m.group(0).replace("\n", "\\n")

        data = re.sub(
            r'''"([^"]|\\\\")*":\s*"([^"]|\\\\")*"''', sanitize, data)
        dobj = json.loads(data)
        all_groups = [parse_group(tobj) for tobj in dobj["types"]]
        all_docs = [parse_entry(doc) for doc in dobj["documents"]]

    def get_type(doc: Entry) -> str:
        return doc["type"]

    def get_date(doc: Entry) -> str:
        return f"{year(tparse(doc['date']))}"

    if is_ordered_by_type:
        type_order = all_groups
        group_by = get_type
    else:
        types = set()
        for doc in all_docs:
            types.add(get_date(doc))
        group_by = get_date
        type_order = [
            {
                "type": f"{year_str}",
                "name": f"{year_str}",
                "color": "black",
                "docs": [],
            } for year_str in sorted(types, key=int, reverse=True)
        ]
    group_order: list[str] = [
        group["type"]
        for group in all_groups
    ]
    media = create_media(
        prefix,
        type_order,
        group_order,
        group_by,
        all_docs,
        event_types=all_groups,
        dry_run=dry_run)
    js_fillin = """
    function adjustSizes() {
      var header_height = d3.select("#smt_header").node().clientHeight;
      var hd_margin_and_border = 22;
      var el_margin_small = 15;
      d3.select("#smt_pad").style({
        "height": (hd_margin_and_border + header_height) + "px",
      });
      d3.selectAll(".smt_anchor").style({
        "top": -(el_margin_small + header_height) + "px",
      });
    }

    function start() {
      window.addEventListener("resize", adjustSizes);
      adjustSizes();
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
        timeline.typeOrder(data["type_order"]);
        timeline.events(data["events"]);
        timeline.initVisibleGroups({".type_committee": false});
        timeline.update();
      });
    }
    """
    return content.format(
        name="Josua Krause (Joschi)",
        description=DESCRIPTION_SHORT,
        description_long=DESCRIPTION,
        description_add=DESCRIPTION_ADD,
        content=media,
        js=f'<script type="text/javascript">{js_fillin}</script>',
        tracking=GA_TRACKING,
        knowledge=LD_JSON_KNOWLEDGE,
        copyright=COPYRIGHT,
        ogimg=ogimg)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog=f"python {os.path.basename(__file__)}",
        description="Create pages")
    parser.add_argument(
        "--documents",
        type=str,
        help="specifies the documents input")
    parser.add_argument(
        "--template",
        type=str,
        help="specifies the template file")
    parser.add_argument(
        "--prefix",
        type=str,
        default=".",
        help="specifies the file prefix")
    parser.add_argument(
        "--out",
        type=str,
        default="-",
        help="specifies the output file. default is STD_OUT.")
    parser.add_argument(
        "--dry",
        action="store_true",
        help="do not produce any output")
    return parser.parse_args()


def run() -> None:
    args = parse_args()
    tmpl = args.template
    docs = args.documents
    prefix = args.prefix
    out = args.out
    dry_run = args.dry
    content = apply_template(
        tmpl,
        docs,
        prefix,
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
