#!/usr/bin/env python3
import sys
import copy
import yaml
from utils.utils import apply_version

with open('map.yaml') as f:
  questionnaire = yaml.load(f, Loader = yaml.Loader)

for version in map(lambda x: int(x), sys.argv[1:]):
  cards = copy.deepcopy(questionnaire['cards'])
  apply_version(cards, version)
  for question, data in filter(lambda x: x[0][0:1] == 'Q', questionnaire.items()):
    apply_version(data, version)
    answers = None
    method_type = data['method']['type']
    assert not (answers and method_type == 'card')
    if method_type == 'card':
      if data['method']['subtype'] == 'select 3':
        answers = data['method']['subquestions']
      else:
        answers = cards[data['method']['set']]['answers'].values()
    else:
      answers = data['answers'].values()
    assert answers, f'version {version}, {question}'

    #Horribly complicated! But definable :)
    prefix = ''; suffix = ''
    if 'branch' in data:
      prefix = f"{data['branch']['condition']} SKIP TO {data['branch']['target']} OTHERS ASK : "
    if 'subtype' in data['method']:
      if 'no prompt' in data['method']['subtype']:
        suffix = ' DO NOT PROMPT'
      if 'write in' in data['method']['subtype']:
        suffix += ' WRITE IN ANSWER BELOW'
    output = f'{prefix}{question[0:1]}.{question[1:]}. {data["question"]}{suffix}'
    if method_type == 'card' and data['method']['subtype'] == 'select 1':
      print(f'{output} CODE IN GRID')
    else:
      for count, answer in enumerate(answers):
        if method_type == 'card':
          suffix = ''
          if data['method']['subtype'] == 'select 3':
            print(f'{output} WHEN RESPONDENT HAS SORTED OUT THREE CARDS ASK {answer} CODE IN GRID')
          else:
            if   data['method']['subtype'] == 'elimination': suffix = 'CODE IN GRID. COLLECT THOSE "Not Heard Of"'
            elif data['method']['subtype'] == 'board' or \
                 data['method']['subtype'] == 'board_none_dontknow': suffix = 'CODE IN GRID'
            print(f'{output} {suffix} {count + 1}. {answer}')
        else:
          print(f'{output}: {answer}')
      if method_type == 'card' and data['method']['subtype'] == 'board_none_dontknow':
        for answer in ['None', "Don't know"]:
          print(f'{output} {suffix} {answer}')
