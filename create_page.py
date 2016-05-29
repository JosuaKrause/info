#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import division

import io
import re
import os
import csv
import sys
import json
import pytz
import zlib

from dateutil.parser import parse as tparse
from datetime import datetime, timedelta, tzinfo

ld_json_knowledge = u"""{
"@context": "http://schema.org/",
"@id": "https://josuakrause.github.io/info/",
"@type": "Person",
"name": "Josua Krause",
"additionalName": "Joschi",
"birthDate": "January 18, 1988",
"url": "https://josuakrause.github.io/info/",
"image": "https://josuakrause.github.io/info/img/photo.jpg",
"sameAs" : [
    "https://www.linkedin.com/in/josua-krause-48b3b091",
    "https://github.com/JosuaKrause/",
    "https://plus.google.com/+JosuaKrause/",
    "https://www.youtube.com/user/j0sch1",
    "https://www.facebook.com/josua.krause",
    "http://engineering.nyu.edu/people/josua-krause",
    "https://vimeo.com/user35425102",
    "https://scholar.google.com/citations?user=hFjNgPEAAAAJ",
    "http://dblp.uni-trier.de/pers/hd/k/Krause:Josua"
]
}"""

ga_tracking = u"""
(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','https://www.google-analytics.com/analytics.js','ga');

ga('create', 'UA-77732102-1', 'auto');
ga('require', 'linkid');
ga('send', 'pageview');
"""

_compute_self = "total_seconds" not in dir(timedelta(seconds=1))
_tz = pytz.timezone('US/Eastern')
_epoch = datetime(year=1970, month=1, day=1, tzinfo=_tz)
_day_seconds = 24 * 3600
_milli = 10**6
def mktime(dt):
    if dt.tzinfo is None:
        dt = datetime(year=dt.year, month=dt.month, day=dt.day, tzinfo=_tz)
    if not _compute_self:
        res = (dt - _epoch).total_seconds()
    else:
        td = dt - _epoch
        res = (td.microseconds + (td.seconds + td.days * _day_seconds) * _milli) / _milli
    return int(res - res % _day_seconds)

def monthtime(dt):
    return "{0}-{1}".format(dt.year, dt.month)

def chk(doc, field):
    return field in doc and doc[field]

def create_autopage(content, doc, ofile):
    abstract = u"<h4>Abstract</h4><p>{0}</p>".format(doc['abstract']) if chk(doc, 'abstract') else ""
    bibtex = u"<h4>Bibtex</h4><pre>{0}</pre>".format(doc['bibtex'].strip()) if chk(doc, 'bibtex') else ""
    image = u"""
    <div class="row">
        <div class="col-md-9">
            <img alt="{0}" src="{1}" style="margin: 0 5%; width: 90%;">
        </div>
    </div>
    """.format(doc['teaser_desc'] if chk(doc, 'teaser_desc') else doc['teaser'], doc['teaser']) if chk(doc, 'teaser') else ""
    if chk(doc, 'video'):
        m = re.match("^https?://vimeo.com/(\d+)$", doc['video'])
        if m is not None:
            video = u"""
            <p style="text-align: center;margin: 0 auto;">
              <iframe src="https://player.vimeo.com/video/{0}" width="640" height="389" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>
              <br><a href="https://vimeo.com/{0}">Watch on Vimeo</a>
            </p>
            """.format(m.group(1))
        else:
            video = ""
    else:
        video = ""
    links = []
    add_misc_links(links, doc, video)
    keywords = []
    if 'keywords' in doc:
        keywords.extend(doc['keywords'])
    output = content.format(
        title=doc['title'],
        conference=doc['conference'],
        authors=doc['authors'],
        image=image,
        abstract=abstract,
        links=u"""<h3 style="text-align: center;">{0}</h3>""".format(" ".join(links)) if links else "",
        bibtex=bibtex,
        logo=doc['logo'] if chk(doc, 'logo') else "img/nologo.png",
        video=video,
        tracking=ga_tracking,
        description=u"""{0} by {1} appears in {2}""".format(doc['title'], doc['authors'], doc['conference']),
    )
    if not dry_run:
        with io.open(ofile, 'w', encoding='utf-8') as outf:
            outf.write(output)

def add_misc_links(appendix, doc, no_video=False):
    if chk(doc, 'demo'):
        appendix.append(u"""<a href="{0}">[demo]</a>""".format(doc['demo']))
    if chk(doc, 'pdf'):
        appendix.append(u"""<a href="{0}">[pdf]</a>""".format(doc['pdf']))
    if chk(doc, 'video') and not no_video:
        appendix.append(u"""<a href="{0}">[video]</a>""".format(doc['video']))
    if chk(doc, 'github'):
        appendix.append(u"""<a href="{0}">[github]</a>""".format(doc['github']))

def create_media(pref, types, docs, dry_run):
    type_lookup = {}
    for type in types:
        type_lookup[type['type']] = type
        type['docs'] = []
    for doc in docs:
        type = type_lookup[doc['type']]
        type['docs'].append(doc)
    event_times = {}
    events = []
    content = ''
    auto_pages = []
    for type in types:
        if not type['docs']:
            continue
        content += u'<h3 id="{0}">{1}</h3>'.format(type['type'], type['name'])
        type['docs'].sort(key=lambda t: (tparse(t['date']), t['title']), reverse=True)
        for doc in type['docs']:
            entry_id = u"entry{:08x}".format(zlib.crc32(u"{0}_{1}_{2}".format(type['name'], doc['title'], mktime(tparse(doc['date']))).encode('utf-8')) & 0xffffffff)
            appendix = []
            if 'href' in doc and doc['href']:
                if chk(doc, 'autopage'):
                    auto_pages.append(doc)
                appendix.append(u"""<a href="{0}">[page]</a>""".format(doc['href']))
            add_misc_links(appendix, doc)
            if chk(doc, 'bibtex'):
                bibtex = doc['bibtex'].strip()
                bibtex_link = u"bibtex/{0}.bib".format(entry_id)
                bibtex_filename = os.path.join(pref if pref is not None else ".", bibtex_link)
                if not dry_run:
                    if not os.path.exists(os.path.dirname(bibtex_filename)):
                        os.makedirs(os.path.dirname(bibtex_filename))
                    with io.open(bibtex_filename, 'w', encoding='utf-8') as f:
                        print(bibtex, file=f)
                appendix.append(u"""<a href="{0}">[bibtex]</a>""".format(bibtex_link))
            authors = doc['authors'].replace("Josua Krause", "<span style=\"text-decoration: underline;\">Josua Krause</span>")
            awards = [ u"""<img src="img/badge.png" style="height: 1em;" alt="{0}" title="{0}">""".format(award) for award in doc['awards'] ] if chk(doc, 'awards') else []
            body = u"""
            <h4 class="media-heading"><a href="#{0}">{1}</a><br/>
            <small>{2}</small></h4>
            <em>{3} &mdash; {4}</em>{5}{6}
            """.format(
                entry_id,
                doc['title'],
                authors,
                doc['conference'],
                doc['date'] if doc['published'] else u"to be published&hellip;",
                u"<br/>\n{0}".format(" ".join(appendix)) if appendix else "",
                u"{0}{1}".format(" " if appendix else u"<br/>\n", " ".join(awards)) if awards else "",
            )
            entry = u"""
            <a class="pull-left" href="#{0}">
              <img class="media-object" src="{1}" title="{2}" alt="{3}" style="width: 64px;">
            </a>
            <div class="media-body">
              {4}
            </div>
            """.format(
                entry_id,
                doc['logo'] if chk(doc, 'logo') else "img/nologo.png",
                doc['title'],
                doc['short-title'] if chk(doc, 'short-title') else doc['title'],
                body,
            )
            content += u"""
            <div class="media" id="{0}">
              {1}
            </div>
            """.format(entry_id, entry)
            otid = doc['short-conference'] if chk(doc, 'short-conference') else doc['conference']
            tid = otid
            mtime = monthtime(tparse(doc['date']))
            if mtime not in event_times:
                event_times[mtime] = set()
            num = 1
            while tid in event_times[mtime]:
                num += 1
                tid = "{0} ({1})".format(otid, num)
            event_times[mtime].add(tid)
            event = {
                "id": tid,
                "group": type['type'],
                "name": doc['title'],
                "time": mktime(tparse(doc['date'])),
                "link": u"#{0}".format(entry_id),
            }
            events.append(event)
    if not dry_run:
        timeline_fn = os.path.join(pref if pref is not None else ".", "material/timeline.json")
        if not os.path.exists(os.path.dirname(timeline_fn)):
            os.makedirs(os.path.dirname(timeline_fn))
        with open(timeline_fn, 'wb') as tl:
            type_names = {}
            for type in types:
                type_names[type['type']] = type['name']
            print(json.dumps({
                "events": events,
                "type_names": type_names,
            }, sort_keys=True, indent=2, encoding='utf-8'), file=tl)
    if auto_pages:
        with io.open("page.tmpl", 'r', encoding='utf-8') as tf:
            page_tmpl = tf.read()
        for doc in auto_pages:
            create_autopage(page_tmpl, doc, os.path.join(pref if pref is not None else ".", doc['href']))
    return content

def apply_template(tmpl, docs, pref, dry_run):
    with io.open(tmpl, 'r', encoding='utf-8') as tf:
        content = tf.read()
    with io.open(docs, 'r', encoding='utf-8') as df:
        data = df.read()

        def sanitize(m):
            return m.group(0).replace('\n', '\\n')

        data = re.sub(u'''"([^"]|\\\\")*":\s*"([^"]|\\\\")*"''', sanitize, data)
        dobj = json.loads(data, encoding='utf-8')
    type_order = dobj['types']
    doc_objs = dobj['documents']
    media = create_media(pref, type_order, doc_objs, dry_run)
    js_fillin = u"""
    function start() {
      var w = "100%";
      var h = 200;
      var radius = 8;
      var textHeight = 20;
      var timeline = new Timeline(d3.select("#div-timeline"), d3.select("#div-legend"), w, h, radius, textHeight);
      d3.json("material/timeline.json", function(err, data) {
        if(err) {
          console.warn(err);
          d3.select("#timeline-row").style({
            "display": "none"
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
        name=u"""Josua (Joschi) Krause""",
        description=u"""
Hi, I'm Josua (Joschi) Krause, PhD Candidate in Computer Science at NYU Tandon School of Engineering. I'm interested in the intersection of Visual Analytics and Machine Learning especially in the field of Health Care Analytics.
        """.strip(),
        description_long=u"""
Hi, I'm a PhD Candidate in Computer Science at <a href="http://engineering.nyu.edu/">NYU Tandon School of Engineering</a>, Brooklyn, NY.
My advisor is <a href="http://enrico.bertini.me/">Prof. Dr. Enrico Bertini</a>.
I'm interested in the intersection of Visual Analytics and Machine Learning especially in the field of Health Care Analytics.
You can find my <a href="material/cv.pdf">CV here</a>.
        """.strip(),
        content=media,
        js=js_fillin,
        tracking=ga_tracking,
        knowledge=ld_json_knowledge,
    )

def usage():
    print("""
usage: {0} [-h] [--dry] [--out <file>] --documents <file> --template <file>
-h: print help
--documents <file>: specifies the documents input
--template <file>: specifies the template file
--prefix <file>: specifies the file prefix
--out <file>: specifies the output file. default is STD_OUT.
--dry: do not produce any output
""".strip().format(sys.argv[0]), file=sys.stderr)
    exit(1)

if __name__ == '__main__':
    tmpl = None
    docs = None
    pref = None
    out = '-'
    dry_run = False
    args = sys.argv[:]
    args.pop(0)
    while args:
        arg = args.pop(0)
        if arg == '-h':
            usage()
        elif arg == '--template':
            if not args:
                print("--template requires argument", file=sys.stderr)
                usage()
            tmpl = args.pop(0)
        elif arg == '--out':
            if not args:
                print("--out requires argument", file=sys.stderr)
                usage()
            out = args.pop(0)
        elif arg == '--documents':
            if not args:
                print("--documents requires argument", file=sys.stderr)
                usage()
            docs = args.pop(0)
        elif arg == '--prefix':
            if not args:
                print("--prefix requires argument", file=sys.stderr)
                usage()
            pref = args.pop(0)
        elif arg == '--dry':
            dry_run = True
        else:
            print('unrecognized argument: {0}'.format(arg), file=sys.stderr)
            usage()
    if tmpl is None or docs is None:
        print('input is underspecified', file=sys.stderr)
        usage()
    content = apply_template(tmpl, docs, pref, dry_run)
    if not dry_run:
        if out != '-':
            with io.open(out, 'w', encoding='utf-8') as outf:
                outf.write(content)
        else:
            sys.stdout.write(content)
            sys.stdout.flush()
