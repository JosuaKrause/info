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
    for type in types:
        if not type['docs']:
            continue
        content += '<h3>{0}</h3>'.format(type['name'])
        type['docs'].sort(key=lambda t: (tparse(t['date']), t['title']), reverse=True)
        for doc in type['docs']:
            entry_id = "entry{:08x}".format(zlib.crc32("{0}_{1}_{2}".format(type['name'], doc['title'], mktime(tparse(doc['date'])))) & 0xffffffff)
            appendix = []
            if 'href' in doc and doc['href']:
                appendix.append(u"""<a href="{0}">[page]</a>""".format(doc['href']))
            if 'demo' in doc and doc['demo']:
                appendix.append(u"""<a href="{0}">[demo]</a>""".format(doc['demo']))
            if 'pdf' in doc and doc['pdf']:
                appendix.append(u"""<a href="{0}">[pdf]</a>""".format(doc['pdf']))
            if 'video' in doc and doc['video']:
                appendix.append(u"""<a href="{0}">[video]</a>""".format(doc['video']))
            if 'github' in doc and doc['github']:
                appendix.append(u"""<a href="{0}">[github]</a>""".format(doc['github']))
            if 'bibtex' in doc and doc['bibtex']:
                bibtex = doc['bibtex'].strip()
                link = "bibtex/{0}.bib".format(entry_id)
                filename = os.path.join(pref if pref is not None else ".", link)
                if not dry_run:
                    if not os.path.exists(os.path.dirname(filename)):
                        os.makedirs(os.path.dirname(filename))
                    with io.open(filename, 'w', encoding='utf-8') as f:
                        print(bibtex, file=f)
                appendix.append(u"""<a href="{0}">[bibtex]</a>""".format(link))
            body = u"""
            <h4 class="media-heading"><a href="#{0}">{1}</a><br/>
            <small>{2}</small></h4>
            <em>{3} &mdash; {4}</em>{5}
            """.format(
                entry_id,
                doc['title'],
                doc['authors'],
                doc['conference'],
                doc['date'] if doc['published'] else "to be published&hellip;",
                "<br/>\n{0}".format(" ".join(appendix)) if appendix else ""
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
                doc['logo'] if 'logo' in doc else "img/nologo.png",
                doc['title'],
                doc['short-title'] if 'short-title' in doc else doc['title'],
                body
            )
            content += u"""
            <div class="media" id="{0}">
              {1}
            </div>
            """.format(entry_id, entry)
            group = type['name']
            etime = mktime(tparse(doc['date']))
            if etime not in event_times:
                event_times[etime] = set()
            num = 1
            while group in event_times[etime]:
                num += 1
                group = "{0} ({1})".format(type['name'], num)
            event_times[etime].add(group)
            event = {
                "id": doc['short-conference'] if 'short-conference' in doc else doc['conference'],
                "group": group,
                "name": doc['title'],
                "time": etime,
                "link": "#{0}".format(entry_id),
            }
            events.append(event)
    if not dry_run:
        timeline_fn = os.path.join(pref if pref is not None else ".", "material/timeline.json")
        if not os.path.exists(os.path.dirname(timeline_fn)):
            os.makedirs(os.path.dirname(timeline_fn))
        with open(timeline_fn, 'wb') as tl:
            print(json.dumps({ "events": events }, sort_keys=True, indent=2, encoding='utf-8'), file=tl)
    return content

def apply_template(tmpl, docs, pref, dry_run):
    with io.open(tmpl, 'r', encoding='utf-8') as tf:
        content = tf.read()
    with open(docs, 'rb') as df:
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
      var h = 300;
      var radius = 8;
      var textHeight = 20;
      var timeline = new Timeline(d3.select("#div-timeline"), w, h, radius, textHeight);
      d3.json("material/timeline.json", function(err, data) {
        if(err) {
          console.warn(err);
          d3.select("#timeline-row").style({
            "display": "none"
          });
          return;
        }
        timeline.events(data["events"]);
        timeline.update();
      });
    }
    """
    return content.format(media, js_fillin)

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
