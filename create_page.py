#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import division

import os
import csv
import sys
import json
from dateutil.parser import parse as tparse

def create_media(types, docs):
    type_lookup = {}
    for type in types:
        type_lookup[type['type']] = type
        type['docs'] = []
    for doc in docs:
        type = type_lookup[doc['type']]
        type['docs'].append(doc)
    content = ''
    for type in types:
        content += '<h3>{0}</h3>'.format(type['name'])
        type['docs'].sort(key=lambda t: (tparse(t['date']), t['title']), reverse=True)
        for doc in type['docs']:
            entry = """
            <div class="media">
              <a class="pull-left" href="{0}">
                <img class="media-object" src="{1}" title="{2}" alt="{3}" style="width: 64px;">
              </a>
              <div class="media-body">
                <h4 class="media-heading"><a href="{0}">{2}</a><br/>
                <small>{4}</small></h4>
                <em>{5} &mdash; {6}</em>
            </div>
            """.format(
                doc['href'],
                doc['logo'],
                doc['title'],
                doc['short-title'],
                doc['authors'],
                doc['conference'],
                doc['date'] if doc['published'] else "to be published&hellip;"
            )
            content += entry
    return content

def apply_template(tmpl, docs):
    with open(tmpl, 'r') as tf:
        content = tf.read()
    with open(docs, 'r') as df:
        dobj = json.loads(df.read())
    type_order = dobj['types']
    doc_objs = dobj['documents']
    media = create_media(type_order, doc_objs)
    return content.format(media)

def usage():
    print("""
usage: {0} [-h] [--out <file>] --documents <file> --template <file>
-h: print help
--documents <file>: specifies the documents input
--template <file>: specifies the template file
--out <file>: specifies the output file. default is STD_OUT.
""".strip().format(sys.argv[0]), file=sys.stderr)
    exit(1)

if __name__ == '__main__':
    tmpl = None
    docs = None
    out = '-'
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
        else:
            print('unrecognized argument: {0}'.format(arg), file=sys.stderr)
            usage()
    if tmpl is None or docs is None:
        print('input is underspecified', file=sys.stderr)
        usage()
    content = apply_template(tmpl, docs)
    if out != '-':
        with open(out, 'w') as outf:
            outf.write(content)
    else:
        sys.stdout.write(content)
        sys.stdout.flush()
