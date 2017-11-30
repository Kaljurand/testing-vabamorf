#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Evaluates the accuracy of the EstNLTK morphological disambiguator.

Usage:

./eval-disambiguate.py --output-types=csv,excel --verbosity=2 gold/*.txt

Input format:

- Mitmesus on esitatud kui tab-separated-values/4 tühikut.
- Sõnaliik (POSTAG) ja sõnavorm (FORM) on eraldatud kahe püstkriipsuga.
- Mitmesuse puhul on õige variant tähistatud + märgiga.
  NT: on    ole+0||V b||    ole+0||V vad||+
- Kui õige analüüs puudub, siis on korrektne variant lisatud tühiku kaugusele % märgi taha.
  NT: Noorte    Noor+te||H pl g||    Noorte+0||H sg g|| %noor+te||S pl g||
- Võõrkeelsed sõnad on saanud märgendiks W.
  NT: Difference    Difference+0||H sg n|| %difference+0||W||
- Paaril juhul on analüüside esiletoomiseks lisatud tühiku kaugusel * märk.
  NT: liku    liku+0||S sg n|| *

TODO:
  - output pivot tabel over analysis if desired
  - make sure alignment is correct
  - analyze only those that were ambiguous
  - add ambiguity count obtained from the analyzer
"""

import argparse
import re
import random
import sys
import pandas as pd
from estnltk import Text

DEFAULT_VERBOSITY = 0
DEFAULT_OUTPUT_TYPES = set(['csv'])

COLS_MATCH = ['forms_match', 'postags_match', 'postags_and_forms_match', 'all_match']
COLS_GOLD = ['gold_word_texts', 'gold_roots', 'gold_postags', 'gold_forms', 'gold_ambiguity']

pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def print_float(f):
    print("%0.2f" % f)

def as_utf8(s):
    return s.encode('utf8')

def b2n(b):
    if b:
        return 1
    return 0

def score_aux(hyp, gold, match_type=None):
    hyp_analysis = hyp.split('|')
    if match_type == 'one':
        idx = random.randint(0, len(hyp_analysis) - 1)
        return b2n(gold == hyp_analysis[idx])
    if match_type == 'unamb':
        if len(hyp_analysis) > 1:
            return 0
        # otherwise continue
    return b2n(gold in hyp_analysis)

def get_analysis(hyp):
    return set(hyp.split('|'))

def score(row, keys, match_type=None):
    """Returns the minumum score
    """
    scores = []
    for key in keys:
        scores.append(score_aux(row[key], row['gold_' + key], match_type))
    return min(scores)

def evaluate(args, hyp, gold):
    """Merge tables marking rows with 0 or 1 depending on correctness
    """
    # TODO: define in the beginning
    raw_df = {
        'forms_amb' : [],
        'forms_match' : [],
        'postags_amb' : [],
        'postags_match' : [],
        'roots_amb' : [],
        'roots_match' : [],
        'postags_and_forms_match' : [],
        'postags_and_forms_match_one' : [],
        'all_match': [],
        'all_match_unamb': [],
        'all_match_one': []
    }
    # TODO: ignore keys
    c = pd.concat([hyp, gold], axis=1)
    for index, row in c.iterrows():
        raw_df['forms_amb'].append(len(get_analysis(row['forms'])))
        raw_df['forms_match'].append(score(row, ['forms']))
        raw_df['postags_amb'].append(len(get_analysis(row['postags'])))
        raw_df['postags_match'].append(score(row, ['postags']))
        raw_df['roots_amb'].append(len(get_analysis(row['roots'])))
        raw_df['roots_match'].append(score(row, ['roots']))
        raw_df['postags_and_forms_match'].append(score(row, ['postags', 'forms']))
        raw_df['postags_and_forms_match_one'].append(score(row, ['postags', 'forms'], 'one'))
        raw_df['all_match'].append(score(row, ['forms', 'postags', 'roots']))
        raw_df['all_match_unamb'].append(score(row, ['forms', 'postags', 'roots'], 'unamb'))
        raw_df['all_match_one'].append(score(row, ['forms', 'postags', 'roots'], 'one'))
    # TODO: ignore keys
    return pd.concat([c, pd.DataFrame.from_dict(raw_df)], axis=1)

def parse_analysis(s):
    """Parse the gold standard analysis.
    Input examples:
        Oslo+0||H sg n||
        tule+a||V da||
        toime+0||S adt||+
    Output examples:
        Oslo+0, H, sg n
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
            line = raw_line.strip()
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


def save_as_excel(fn, df):
    writer = pd.ExcelWriter(fn + '.xlsx')
    df.to_excel(writer, 'Sheet1')
    writer.save()

def save_as_csv(fn, df):
    df.to_csv(fn + '.csv', sep='\t', encoding='utf-8')


def read_files(args):
    for fn in args.fns:
        try:
            text,gold = get_text(fn)
            df = evaluate(args, text.get.word_texts.roots.postags.forms.as_dataframe, gold)
            if args.verbosity > 0:
                print(fn)
                print(df.describe())
            for t in args.output_types:
                if t == 'excel':
                    save_as_excel(fn, df)
                else:
                    save_as_csv(fn, df)
            if args.verbosity > 0:
                print('Wrote: {0}'.format(fn), file=sys.stderr)
        except AttributeError as e:
            print('Warning: error: skipped: {0}: {1}'.format(fn, e), file=sys.stderr)

def get_args():
    css = lambda x: set([el for el in x.split(',')])
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('fns', metavar='FILE', type=str, nargs='+', help='gold standard')
    p.add_argument('--output-types', type=css, dest='output_types', default=DEFAULT_OUTPUT_TYPES, help='output types')
    p.add_argument('--verbosity', type=int, default=DEFAULT_VERBOSITY, help='verbosity')
    p.add_argument('-v', '--version', action='version', version='%(prog)s v0.0.3')
    return p.parse_args()

def main():
    args = get_args()
    read_files(args)

if __name__ == "__main__":
    main()
