#!/usr/bin/env python3

import os
import sys
import atexit
import argparse
import pandas as pd
from utils.fnam_col import f2c
from utils.pdkit import df_contains

EVENTS = {
  'NO_ENCODING':     { 'msg': 'has no encoding. Using raw values.' },
  'ENCODED_LOGICAL': { 'msg': 'has logical type but also an encoding.' },
  'BAD_TYPE':        { 'msg': 'has %s type but non-%s value: %s.' },
  'UNDECODABLE':     { 'msg': 'has undecodable value: %s.' },
  'UNHANDLED_TYPE':  { 'msg': 'has unhandled type: %s.' },
}
for e in EVENTS.values(): e['count'] = 0

def log(event, col, *varargs):
  details = EVENTS[event]
  print(f'{event}: Column {col} ({f2c(col)}) ' + details['msg'] % varargs, file = args.log)
  details['count'] += 1

parser = argparse.ArgumentParser()
parser.add_argument('version',
                    type = int,
                    help = 'Version number to process')
parser.add_argument('--input_dir',
                    default = f'{os.path.dirname(sys.argv[0])}/BN-97-1',
                    help = 'Location of BN-97-1 data files')
parser.add_argument('--log',
                    type = argparse.FileType('w'),
                    default = sys.stderr)
args = parser.parse_args()
if args.log != sys.stderr:
  atexit.register(lambda: args.log.close())

responses      = pd.read_csv(args.input_dir + f'/version{args.version}.csv') #many of these need to be float (so they can include nan), some need to be object (because they can be non-integer)
response_meta  = pd.read_csv(args.input_dir + f'/version{args.version}__field_encoding.csv', index_col = ['FIELD_NAME', 'CODE']) #NB CODE has to be an Object because it can be 'V'
field_meta     = pd.read_csv(args.input_dir + f'/version{args.version}__field_attributes.csv', index_col = 'FIELD_NAME')

#check for reserved strings (by regexp)
if df_contains(responses, '^UNDECODABLE: '): raise Exception()

#Commented out for now -- written on the assumption that we use FIELD_NUM for the index, but right now I am using FIELD_NAME for the index
#Confirm that FIELD_NAME matches FIELD_NUM
#assert field_meta['FIELD_NAME'].str.startswith('V').all()
#assert len(field_meta['FIELD_NAME'].str[1:].apply(pd.to_numeric).compare(field_meta.index.to_series()).index) == 0

for col in responses.columns:
  #define some inner functions, so they can access col
  def lookup(x):
    if isinstance(x, float):
      if not x.is_integer(): raise Exception()
      x = int(x)
    try:
      return response_meta.loc[(col, str(x)), 'VALUE'] #stringification to avoid lookups failing on type issues (e.g. columns of mostly numbers that have type Object because of an odd 'V' value)
    except KeyError:
      log('UNDECODABLE', col, x)
      return f'UNDECODABLE: {x}'
    
  def logical_lookup(x):
    if x == 0: return 'No'
    if x == 1: return 'Yes'
    log('BAD_TYPE', col, 'logical', 'logical', x)

  col_type = field_meta.loc[col, 'DATATYPE']
  if col_type == 'LOGICAL':
    if col in response_meta.index.get_level_values(0): log('ENCODED_LOGICAL', col)
    responses[col] = responses[col].map(logical_lookup, na_action = 'ignore')
  elif col in response_meta.index.get_level_values(0):
    if col_type == 'INT' or col_type == 'FSTRING' or col_type == 'VSTRING': #seems that all of these types can actually contain ints, so one function suffices for all of them
      responses[col] = responses[col].map(lookup, na_action = 'ignore')
    else: log('UNHANDLED_TYPE', col, col_type)
  else: log('NO_ENCODING', col)

#Rename columns in responses with the actual questions
responses = responses.rename(columns = field_meta['DDTEXT'].fillna(field_meta['DESCRIPTION'])) #works because the index for field_meta is FIELD_NAME, which maps to the column names in responses

responses.to_csv(f'version{args.version}.csv', index = False)

print(f'\n\nNon-null data points: {responses.count().sum()}', file = args.log)
report = []
count = 0
for k, v in EVENTS.items():
  report.append(f'* {k}: {v["count"]}')
  count += v["count"]
if count > 0:
  print(f'\n{count} events encountered:\n' + '\n'.join(report), file = args.log)
