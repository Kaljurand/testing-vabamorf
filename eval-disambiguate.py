#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Evaluates the accuracy of the EstNLTK morphological disambiguator.
"""

from __future__ import division, print_function

"""
TODO:
  - output pivot tabel over analysis if desired
  - make sure alignment is correct
  - analyze only those that were ambiguous
  - add ambiguity count obtained from the analyzer
"""

import argparse
from estnltk import Text
from estnltk.teicorpus import parse_tei_corpus
import re
import sys
import pandas as pd

DEFAULT_VERBOSITY = 0

def print_float(f):
    print("%0.2f" % f)

def as_utf8(s):
    return s.encode('utf8')

def score_aux(hyp, gold):
    """Returns a number between 0 and 1
    0: no match, or
    1/n: where n is the number of |-separated hypotheses
    """
    hyp_analysis = set(hyp.split('|'))
    if gold in hyp_analysis:
        return 1/len(hyp_analysis)
    return 0

def score(row, keys):
    """Returns the minumum score
    """
    scores = []
    for key in keys:
        scores.append(score_aux(row[key], row['gold_' + key]))
    return min(scores)

def evaluate(args, hyp, gold):
    """Merge tables marking rows with 0 or 1 depending on correctness
    """
    # TODO: define in the beginning
    raw_df = {
        'forms_match' : [],
        'postags_match' : [],
        'postags_and_forms_match' : [],
        'all_match': []
    }
    # TODO: ignore keys
    c = pd.concat([hyp, gold], axis=1)
    for index, row in c.iterrows():
        raw_df['forms_match'].append(score(row, ['forms']))
        raw_df['postags_match'].append(score(row, ['postags']))
        raw_df['postags_and_forms_match'].append(score(row, ['postags', 'forms']))
        raw_df['all_match'].append(score(row, ['forms', 'postags', 'roots']))

    if args.verbosity > 0:
        print_float(sum(raw_df['forms_match']) / len(raw_df['forms_match']))
        print_float(sum(raw_df['postags_match']) / len(raw_df['postags_match']))
        print_float(sum(raw_df['postags_and_forms_match']) / len(raw_df['postags_and_forms_match']))
    # TODO: ignore keys
    return pd.concat([c, pd.DataFrame.from_dict(raw_df)], axis=1)

def parse_analysis(s):
    """Parse the gold standard analysis.
    Input examples:
        %Oslo+0||H sg n||
        tule+a||V da||
        toime+0||S adt||+
    Output examples:
        %Oslo+0, H, sg n
        tule+a, V, da
        toime+0, S, adt
    """
    fields = re.split('\|\|', s)
    if len(fields) == 3:
        return re.sub('\+.*', '', fields[0]), fields[1][0], fields[1][2:]
    raise ValueError('{0}: {1}'.format(len(fields), as_utf8(s)))

def parse_line(line):
    """Parse the gold standard analysis line.
    Examples:
        Oslo    Oslo+0||H sg g|| %Oslo+0||H sg n||
        tulla    tule+a||V da||
        toime    toim+0||S adt||    toime+0||S adt||+
    """
    fields = re.split('  +', line)
    num_of_fields = len(fields)
    if num_of_fields < 2:
        raise ValueError('{0}: {1}'.format(num_of_fields, as_utf8(line)))

    ambiguity = num_of_fields - 1
    extra_analysis = fields[-1].split('|| %')
    if len(extra_analysis) == 2:
        root,postag,form = parse_analysis(extra_analysis[1])
    else:
        analysis = fields[1]
        for i in range(2, len(fields)):
            if fields[i][-1] == '+':
                analysis = fields[i]
                break
        root,postag,form = parse_analysis(analysis)
    return fields[0],root,postag,form,ambiguity

def get_text(fn):
    """
    TODO: construct the text from the gold standard tokenization
    """
    data = ''
    raw_df = {
        'gold_word_texts' : [],
        'gold_roots': [],
        'gold_postags': [],
        'gold_forms': [],
        'gold_ambiguity': []
    }
    with open(fn, "r") as f:
        for raw_line in f:
            line = raw_line.decode('utf8').strip()
            try:
                word_text, root, postag, form, ambiguity = parse_line(line)
            except ValueError as e:
                print('Warning: syntax error: {0}: {1}'.format(fn, e), file=sys.stderr)
                continue
            data += word_text + ' '
            raw_df['gold_word_texts'].append(word_text)
            raw_df['gold_roots'].append(root)
            raw_df['gold_postags'].append(postag)
            raw_df['gold_forms'].append(form)
            raw_df['gold_ambiguity'].append(ambiguity)
    return Text(data, guess=True, disambiguate=True), pd.DataFrame.from_dict(raw_df)


def save_as_excel(args, fn, df):
    writer = pd.ExcelWriter(fn + '.xlsx')
    df.to_excel(writer,'Sheet1')
    writer.save()
    if args.verbosity > 0:
        print('Wrote: {0}'.format(fn), file=sys.stderr)


def read_files(args):
    for fn in args.fns:
        try:
            text,gold = get_text(fn)
            df = evaluate(args, text.get.word_texts.roots.postags.forms.as_dataframe, gold)
            save_as_excel(args, fn, df)
        except AttributeError as e:
            print('Warning: error: skipped: {0}: {1}'.format(fn, e), file=sys.stderr)

def get_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('fns', metavar='N', type=str, nargs='+', help='gold standard')
    p.add_argument('--verbosity', type=int, default=DEFAULT_VERBOSITY, help='verbosity')
    p.add_argument('-v', '--version', action='version', version='%(prog)s v0.0.1')
    return p.parse_args()

def main():
    args = get_args()
    read_files(args)

if __name__ == "__main__":
    main()
