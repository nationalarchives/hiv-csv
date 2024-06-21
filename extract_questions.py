#!/usr/bin/env python3

import os
import re
import sys
import copy
import yaml
import argparse
import pandas as pd
from utils.utils import apply_version

def read_map(question):
  #Get answers from version 1, to use as a baseline
  full_question = survey_map[question.upper()]
  question = copy.deepcopy(full_question)
  final_answers = [{}]
  if question['method']['type'] == 'card':
    cards = copy.deepcopy(survey_map['cards'])
    apply_version(cards, 1)
    if question['method']['subtype'] == 'select 3':
      answers = question['method']['subquestions']
    else:
      answers = cards[question['method']['set']]['answers']
  else:
    answers = question['answers']
  for count, answer in enumerate(answers.keys()):
    if 'start' in question:
      final_answers[0][answer] = question['start'] + count #V-number for this answer
    else:
      final_answers[0][answer] = read_map.start[1] + count #V-number for this answer
  base_answers = final_answers[0]

  #Get column headings. These will be the text of the answer in the first version of the survey in which it appears.
  #We start with all of the answers in the base version.
  headings = {identifier: text for identifier, text in answers.items()}

  for version in args.versions[1:]:
    question = copy.deepcopy(full_question)
    apply_version(question, version)
    if question['method']['type'] == 'card':
      cards = copy.deepcopy(survey_map['cards'])
      apply_version(cards, version)
      if question['method']['subtype'] == 'select 3':
        answers = question['method']['subquestions']
      else:
        answers = cards[question['method']['set']]['answers']
    else:
      answers = question['answers']

    if answers is None: #answers specified, but null
      final_answers.append({})
    else:
      x = {}
      for count, (identifier, text) in enumerate(answers.items()):
        if 'start' in question:
          x[identifier] = question['start'] + count #V-number for this question in this version
        else:
          x[identifier] = read_map.start[version] + count #V-number for this question in this version
        if not identifier in headings: #Add a column heading for this identifier, if we do not already have one
          headings[identifier] = text
      final_answers.append(x)
  df = pd.DataFrame(final_answers, args.versions)
  read_map.start = df.max(axis = 1).add(1).to_dict()

  qmt = question['method']['type']

  #not sure about the 'or' in the first clause here -- it should happen to work for q7 and q8, but may not generalise
  #TODO: The correct way to do this is to get the field's datatype from field_meta -- we just want to know whether it is logical or not
  #      I can likely do this at the caller, rather than here
  if qmt == 'open question' or (qmt == 'card' and question['method']['subtype'] == 'board_none_dontknow'): qmt = 'yesno'
  else: qmt = 'defined'
  return df.rename(headings, axis = 'columns'), qmt #args.versions is the index here

def get_answers(df):
  #start with all possible answers to first sub-question in first row
  #I assume that this will always be defined. If not, I'll get an exception here.
  print(df)
  base = response_meta[1].loc[f'V{int(df.iloc[0,0])}']['VALUE'].squeeze() #using squeeze here forces this to be returned as a new series, suppressing later warnings about setting a value on a copy of a slice of a data frame -- and ensuring that I'm not accidentally updating the underlying dataframe

  #confirm that possible answers to a question are always the same
  for index, row in df.iterrows(): #Feels like not the Pandas way to be using iterrows
    for col_num in range(0, len(row.index)):
      code = row.iloc[col_num]
      if pd.isna(code):
        continue #question does not exist in this version, so cannot have different answers
      code = str(int(code))
      try:
        s = response_meta[index].loc['V' + code]['VALUE']
      except:
        print(response_meta[index])
        print('index\n', index, '\n\n', 'row\n', row, '\n\ncode\n', code, '\n\n', file = sys.stderr)
        raise
      try:
        if len(base.compare(s).index) > 0: raise
      except:
        print('index\n', index, '\n\n', 'row\n', row, '\n\ncode\n', code, '\n\n', file = sys.stderr)
        print(f'Different answer(s) between base and version {index}, code V{code}', file = sys.stderr)
        print(base, file = sys.stderr)
        print(s, file = sys.stderr)
        print(base.compare(s), file = sys.stderr)
        raise

  if args.blank_response in base.index:
    print(f'Blank response {args.blank_response} should not be present in possible responses', file = sys.stderr)
    sys.exit(1)
  base.loc[args.blank_response] = 'Blank'

  #answers are always the same, return them
  return base

def count_responses(df, answers):
  def count_decodable(version_response_v_codes):
    #called once for each possible response within each survey version (rows in the df)
    #version_response_v_codes is a Series of v-codes corresponding to a given response to a question
    #breakpoint()
    counts = [] #count of each possible response to the question in the survey version
    labels = [] #label for the response (i.e. the answer given to the question)
    for label, v_code in version_response_v_codes.items():
      if pd.isna(v_code):
        counts.append(v_code) #question is not defined for this version
      else:
        count = response_counts.loc[version_response_v_codes.name][f'V{int(v_code)}']
        counts.append(0 if pd.isna(count) else count) #if count is na this means the question was defined for the current version, but no-one gave this response
      labels.append(label)
    return pd.Series(counts, labels)

  def count_undecodable(version_response_v_codes):
    counts = [] #count of each possible response to the question in the survey version
    labels = [] #label for the response (i.e. the answer given to the question)
    for label, v_code in version_response_v_codes.items():
      if pd.isna(v_code):
        counts.append(v_code) #question is not defined for this version
      else:
        rcv = response_counts.loc[version_response_v_codes.name][f'V{int(v_code)}'] #all responses for this V-code in this version
        rcv = rcv.loc[~(rcv.index.isin(answers.index.to_list()))].dropna()
        counts.append(0 if rcv.size == 0 else rcv.sum())
      labels.append(label)
    return pd.Series(counts, labels)

  df_u = df.apply(count_undecodable, axis = 1)
  df_u = pd.concat([df_u], keys = ['undecodable'], names = ['response', 'version']).swaplevel()

  df = pd.concat([df] * len(answers), keys = answers.index, names = ['response', 'version']).swaplevel()
  df = df.apply(count_decodable, axis = 1) #convert v_codes in df into counts of responses given to that question

  return pd.concat([df, df_u])


parser = argparse.ArgumentParser()
parser.add_argument('versions',
                    nargs = '*',
                    type = int,
                    default = list(range(1, 9)) + list(range(12, 17)),
                    help = 'Survey versions to include (defaults to all)')
parser.add_argument('--input-dir',
                    default = f'{os.path.dirname(sys.argv[0])}/BN-97-1' if len(os.path.dirname(sys.argv[0])) else './BN-97-1',
                    help = 'Location of BN-97-1 data files')
parser.add_argument('--all-response-counts',
                    default = f'{os.path.dirname(sys.argv[0])}/output/intermediates/all_response_counts.pkl' if len(os.path.dirname(sys.argv[0])) else './output/intermediates/all_response_counts.pkl',
                    help = 'Location of cached all_response_counts dataframe')
parser.add_argument('--blank-response', '-b',
                    default = '-1',
                    help = 'Value used to represent a blank response')
args = parser.parse_args()

with open('map.yaml') as f:
  survey_map = yaml.load(f, yaml.Loader)

response_meta = {}
for version in args.versions:
  response_meta[version] = pd.read_csv(args.input_dir + f'/version{version}__field_encoding.csv', index_col = ['FIELD_NAME', 'CODE'], converters = {'CODE': str})
response_counts = pd.read_pickle('output/intermediate/all_response_counts.pkl')

for question in [f'q{x}' for x in range(1, 10)]:
  if question == 'q6':
    for k, v in read_map.start.items():
      read_map.start[k] = v + 3
    continue
  print(question.upper() + '...', end = '')
  question_df, question_type = read_map(question)
  if question_type == 'yesno':
    answers = pd.Series(['No', 'Yes', 'blank'], ['0', '1', args.blank_response])
    results = count_responses(question_df, answers)
  elif question_type == 'defined':
    answers = get_answers(question_df)
    results = count_responses(question_df, answers)
  else:
    assert False, f'Unhandled question_type {question_type}'

  #dump out csv per response
  for code, label in answers.items():
    x = results.query(f'response == @code')
    x.index = x.index.droplevel('response')
    x.index.name = None
    x.add_prefix('Version ', 'index').to_csv(f'output/{question}_{"_".join([re.sub("[^a-z0-9]", "", x) for x in label.lower().split()])}.csv')

  #and add a csv for the undecoded
  y = answers.index.to_list()
  x = results.query('response not in @y')
  if not x.empty:
    x.index = x.index.droplevel('response')
    x.index.name = None
    x.add_prefix('Version ', 'index').to_csv(f'output/{question}_undecodable.csv')
  print('done')
