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
        for text in parse_tei_corpus(fn, target=['artikkel']):
            text['guess'] = True
            text['disambiguate'] = True
            show_df(text.get.word_texts.roots.postags.forms.as_dataframe)

def get_args():
    p = argparse.ArgumentParser(description='')
    p.add_argument('fns', metavar='N', type=str, nargs='+', help='')
    p.add_argument('-v', '--version', action='version', version='%(prog)s v0.0.1')
    return p.parse_args()

def main():
    args = get_args()
    analyze_tei_files(args.fns)

if __name__ == "__main__":
    main()
