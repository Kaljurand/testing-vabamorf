#! /usr/bin/env python

"""
Converts a set of text files into the etana input format (in JSON).
The input is assumed to contain a paragraph per line. Lines that do not start with
a letter or number are ignored. A simple tokenizer and sentence splitter is applied
to the paragraphs. Note that some symbols are not preserved as tokens.

The input format to etana is documented at: https://github.com/Filosoft/vabamorf/issues/2
Note that the input is expected to contain a stream of paragraphs, so we flatten
the set of text files to a sequence of paragraphs, but add an id with the file name
to each paragraph.

Usage:

    txt-to-json.py *.txt | etana analyze -lex et.dct | etdisamb -lex et3.dct

Author: Kaarel Kaljurand <kaljurand@gmail.com>

TODO: improve tokenization
TODO: improve sentence splitting
"""

from __future__ import print_function
import sys
import re
import json
import argparse
import itertools

# TODO: add "" (currently makes etana produce wrong output)
token = re.compile(r'[\d%]+|[\w\'-]+|[.,!?;(){}%]', re.UNICODE)

def get_args():
    p = argparse.ArgumentParser(description='')
    p.add_argument('fns', metavar='N', type=str, nargs='+', help='')
    p.add_argument('-v', '--version', action='version', version='%(prog)s v0.0.1')
    return p.parse_args()


def is_paragraph(line):
    """
    Paragraph is something that starts with a letter or number.
    """
    return re.search("^[A-Za-z0-9]", line)


def get_tokens(line):
    """
    TODO: call a serious tokenizer here
    """
    return token.findall(line)


def is_sentence_end_symbol(tok):
    """
    TODO: replace with a serious sentence splitter
    """
    return tok == '.' or tok == '!' or tok == '?'


def get_sentences(line):
    s = []
    for tok in get_tokens(line):
        s.append(tok)
        if is_sentence_end_symbol(tok):
            yield { 'words': [ {'text' : x } for x in s ] }
            s = []
    if len(s):
        yield { 'words': [ {'text' : x } for x in s ] }


def get_paragraphs(fn):
    """
    Each line is a possible paragraph
    """
    with open(fn) as f:
        for raw_line in f:
            line = raw_line.decode('utf8')
            if is_paragraph(line):
                paragraph = {}
                paragraph['id'] = fn
                paragraph['sentences'] = list(get_sentences(line.strip()))
                yield paragraph


def get_documents(fns):
    """
    Each file is a document, but since Vabamorf assumes that the input is a single
    document then we flatten all documents into a single paragraph stream.
    """
    for fn in fns:
        for p in get_paragraphs(fn):
            yield p


def main():
    j = {}
    args = get_args()
    j['paragraphs'] = list(get_documents(args.fns))
    print(json.dumps(j, indent=2, ensure_ascii=False).encode('utf8'))

if __name__ == "__main__":
    main()
