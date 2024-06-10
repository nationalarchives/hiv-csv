#!/usr/bin/env python3

import os
import sys
import yaml
import argparse
import collections.abc
import pandas as pd

VERSIONS = list(range(1, 9)) + list(range(12, 17))

def read_map():
  with open('map.yaml') as f:
    survey_map = yaml.load(f, yaml.Loader)

  #Get answers from version 1, to use as a baseline
  question = survey_map['Q1']
  start = question['start']
  answers = [{}]
  for count, answer in enumerate(question['answers'].keys()):
    answers[0][answer] = start + count #V-number for this answer
  base_answers = answers[0]

  #Get column headings. These will be the text of the answer in the first version of the survey in which it appears.
  #We start with all of the answers in the base version.
  headings = {identifier: text for identifier, text in question['answers'].items()}

  for version in VERSIONS[1:]:
    if (not version in question) or (not 'answers' in question[version]):
      answers.append(base_answers) #read-only, so we don't need a deep copy
    elif question[version]['answers'] is None: #answers specified, but null
      answers.append({})
    else:
      x = {}
      for count, (identifier, text) in enumerate(question[version]['answers'].items()):
        x[identifier] = start + count #V-number for this question in this version
        if not identifier in headings: #Add a column heading for this identifier, if we do not already have one
          headings[identifier] = text
      answers.append(x)

  return pd.DataFrame(answers, VERSIONS).rename(headings, axis = 'columns') #VERSIONS is the index here

def count_answers(df):
  responses = {}
  for version in VERSIONS:
    responses[version] = pd.read_csv(args.input_dir + f'/version{version}.csv') #many of these need to be float (so they can include nan), some need to be object (because they can be non-integer)

  def _count_answers(v_number, version, targets, vert = True):
    #applied to a series (and so suitable to be called in apply, row-by-row (axis=1))
    #v_number is the identifier for the question
    #version is the version of the survey for which we are counting answers
    #targets is the answer(s) that we are returning a count for
    #vert means to return count for answers in targets -- if False, return for answers not in targets (i.e. invert if False)
    if pd.isna(v_number): return None

    if isinstance(targets, str) or not isinstance(targets, collections.abc.Iterable):
      targets = [targets]
    targets = map(lambda x: 'None' if x is None else x, targets)

    s = responses[version]['V' + str(int(v_number))]
    vc = s.value_counts()
    assert not 'None' in vc.index
    none_count = s.isna().value_counts().loc[True]
    vc = pd.concat([vc, pd.Series(none_count, ['None'])])
    if vert:
      return vc.loc[  vc.index.isin(targets) ].sum()
    else:
      return vc.loc[~(vc.index.isin(targets))].sum()

  #TODO: Obviously sub-optimal to essentially count everything 3 times (i.e. that we call value_counts() within 'count')
  yes         = df.apply(lambda x: x.apply(_count_answers, args = (x.name, 1)),                   axis = 1)
  no          = df.apply(lambda x: x.apply(_count_answers, args = (x.name, 0)),                   axis = 1)
  blank       = df.apply(lambda x: x.apply(_count_answers, args = (x.name, None)),                axis = 1)
  undecodable = df.apply(lambda x: x.apply(_count_answers, args = (x.name, (1, 0, None), False)), axis = 1)

  return {
    'yes': yes,
    'no': no,
    'blank': blank,
    'undecodable': undecodable,
  }


parser = argparse.ArgumentParser()
parser.add_argument('--input_dir',
                    default = f'{os.path.dirname(sys.argv[0])}/BN-97-1' if len(os.path.dirname(sys.argv[0])) else './BN-97-1',
                    help = 'Location of BN-97-1 data files')
args = parser.parse_args()

for answer, counts_df in count_answers(read_map()).items():
  counts_df.add_prefix('Version ', 'index').to_csv(f'output/q1_{answer}.csv')
