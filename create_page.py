#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import division

import io
import re
import os
import csv
import sys
import zlib
import json
from dateutil.parser import parse as tparse

def create_media(types, docs, dry_run):
    type_lookup = {}
    for type in types:
        type_lookup[type['type']] = type
        type['docs'] = []
    for doc in docs:
        type = type_lookup[doc['type']]
        type['docs'].append(doc)
    content = ''
    for type in types:
        if not type['docs']:
            continue
        content += '<h3>{0}</h3>'.format(type['name'])
        type['docs'].sort(key=lambda t: (tparse(t['date']), t['title']), reverse=True)
        for doc in type['docs']:
            entry_id = "entry{:08x}".format(zlib.crc32("{0}_{1}".format(type['name'], doc['title'])) & 0xffffffff)
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
                filename = "bibtex/{0}.bib".format(entry_id)
                if not dry_run:
                    if not os.path.exists(os.path.dirname(filename)):
                        os.makedirs(os.path.dirname(filename))
                    with io.open(filename, 'w', encoding='utf8') as f:
                        print(bibtex, file=f)
                appendix.append(u"""<a href="{0}">[bibtex]</a>""".format(filename))
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
    return content

def apply_template(tmpl, docs, dry_run):
    with io.open(tmpl, 'r', encoding='utf8') as tf:
        content = tf.read()
    with open(docs, 'rb') as df:
        data = df.read()

        def sanitize(m):
            return m.group(0).replace('\n', '\\n')

        data = re.sub(u'''"([^"]|\\\\")*":\s*"([^"]|\\\\")*"''', sanitize, data)
        dobj = json.loads(data, encoding='utf-8')
    type_order = dobj['types']
    doc_objs = dobj['documents']
    media = create_media(type_order, doc_objs, dry_run)
    return content.format(media)

def usage():
    print("""
usage: {0} [-h] [--dry] [--out <file>] --documents <file> --template <file>
-h: print help
--documents <file>: specifies the documents input
--template <file>: specifies the template file
--out <file>: specifies the output file. default is STD_OUT.
--dry: do not produce any output
""".strip().format(sys.argv[0]), file=sys.stderr)
    exit(1)

if __name__ == '__main__':
    tmpl = None
    docs = None
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
        elif arg == '--dry':
            dry_run = True
        else:
            print('unrecognized argument: {0}'.format(arg), file=sys.stderr)
            usage()
    if tmpl is None or docs is None:
        print('input is underspecified', file=sys.stderr)
        usage()
    content = apply_template(tmpl, docs, dry_run)
    if not dry_run:
        if out != '-':
            with io.open(out, 'w', encoding='utf8') as outf:
                outf.write(content)
        else:
            sys.stdout.write(content)
            sys.stdout.flush()
