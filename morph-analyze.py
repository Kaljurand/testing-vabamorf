#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Morf. analyze the given texts.

TODO:
  - explicitly mark sentence borders
"""

from __future__ import print_function
import argparse
from estnltk import Text
from estnltk.teicorpus import parse_tei_corpus
import sys

def get_target(fnm):
    """
    See: https://github.com/estnltk/estnltk/issues/42#issuecomment-172461822
    """
    if 'drtood' in fnm:
        return 'dissertatsioon'
    if 'ilukirjandus' in fnm:
        return 'tervikteos'
    if 'seadused' in fnm:
        return 'seadus'
    if 'EestiArst' in fnm:
        return 'ajakirjanumber'
    if 'foorum' in fnm:
        return 'teema'
    if 'kommentaarid' in fnm:
        return 'kommentaarid'
    if 'uudisgrupid' in fnm:
        return 'uudisgrupi_salvestus'
    if 'jututoad' in fnm:
        return 'jututoavestlus'
    if 'stenogrammid' in fnm:
        return 'stenogramm'
    return 'artikkel'

def fix(el):
    if len(el):
        el = el.encode('utf8')
        return el.replace(' ', '_')
    return '<0>'

def show_df(df):
    for index, row in df.iterrows():
        els = [row['word_texts'], row['roots'], row['postags'], row['forms']]
        els_fixed = [fix(el) for el in els]
        print(' '.join(els_fixed), end=' ')

def analyze_files(fns):
    for fn in fns:
        with open(fn, "r") as f:
            data = f.read().replace('\n', '')
            text = Text(data, guess=True, disambiguate=True)
            #print(text.get.word_texts.roots.postags.forms.as_dataframe)
            show_df(text.get.word_texts.roots.postags.forms.as_dataframe)

def analyze_tei_files(fns):
    for fn in fns:
        try:
            for text in parse_tei_corpus(fn, target=get_target(fn)):
                text['guess'] = True
                text['disambiguate'] = True
                show_df(text.get.word_texts.roots.postags.forms.as_dataframe)
        except AttributeError:
            print('Warning: parse error: skipped: {0}'.format(fn), file=sys.stderr)

def get_args():
    p = argparse.ArgumentParser(description='')
    p.add_argument('fns', metavar='N', type=str, nargs='+', help='')
    p.add_argument('-v', '--version', action='version', version='%(prog)s v0.0.2')
    return p.parse_args()

def main():
    args = get_args()
    analyze_tei_files(args.fns)

if __name__ == "__main__":
    main()
