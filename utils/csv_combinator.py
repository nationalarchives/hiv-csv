#!/usr/bin/env python3

import os
import sys
import argparse
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('versions',
                    nargs = '*',
                    type = int,
                    default = list(range(1, 9)) + list(range(12, 17)),
                    help = 'Survey versions to include (defaults to all)')
parser.add_argument('--output', '-o',
                    default = 'all_response_counts',
                    help = 'Basename for files storing all responses')
parser.add_argument('--blank-response', '-b',
                    default = '-1',
                    help = 'Value used to represent a blank response')
parser.add_argument('--input-dir', '-i',
                    default = f'{os.path.dirname(sys.argv[0])}/../BN-97-1' if len(os.path.dirname(sys.argv[0])) else '../BN-97-1',
                    help = 'Location of BN-97-1 data files')
parser.add_argument('--fake', '-f',
                    action = 'append',
                    type = str,
                    help = 'Fake data to modify the output with. Example: -f \'2@invented@V26@42\' to add a count of 42 responses of "invented" to question V26 in survey version 2.')
args = parser.parse_args()

responses = {}
for version in args.versions:
  responses[version] = pd.read_csv(args.input_dir + f'/version{version}.csv', dtype = object) #many of these need to be float (so they can include nan), some need to be object (because they can be non-integer)

combination = pd.concat(responses, verify_integrity = True) #concatenate all responses into a single dataframe. This will now have a multilevel index, with the highest level being the version number of the questionnaire
combination.index = combination.index.droplevel(1) #drop the original default index from the multiindex
combination = combination.melt(ignore_index=False, value_name = 'response') #convert into a two-column dataframe such that the identifier code (V10 etc), previously the column headers, instead are themselves now a column named variable. The second column is the value previously at the .loc[<index>][<V code>] location. We keep the index, so the values previously retrieved with combination.loc[1]['V10'] are now retrieved with combination.loc[combination['variable']=='V10'].loc[1]
combination = combination.reset_index(names = 'version') #convert the index into a column named 'version'
combination = combination.groupby(['version', 'variable', 'response'], dropna=False) #group up on these variables -- so each group contains n rows for each case where version, variable and response have given values? If so, then for example if 3 people gave the answer yes (coded as 1) and 2 people gave the answer no (coded as 2) in response to question V10 (in the variable column) in version 1, then there would be a 3-row group for version=1,variable=V10,response=1 and a 2-row groups for version=1,variable=V10,response=0
combination = combination.size() #count the number of rows in each group and convert that information back into a Series. So in the previous example, our Series has multiindex composed of version,variable,response, and the content is .loc[1,'V1',0] = 2 and .loc[1,'V1',1] = 3
combination = combination.unstack(1) #and finally, take the 'variable' element of the multiindex and turn it into columns. So now we have a dataframe with multindex version,response (where 'response' means the code for the response given) and columns that are V-codes.

#Finally, as it seems hard/impossible to look up nan in an index, substitute the nans with a value that is not already in the index
if args.blank_response in combination.index.levels[-1]:
  print(f'--blank-response "{args.blank_response}" should not be present in index "response"', file = sys.stderr)
  sys.exit(1)
combination.index = combination.index.set_levels(combination.index.levels[-1].fillna(args.blank_response), level = 'response')

#insert any fake data (for testing purposes)
if args.fake:
  for fake in args.fake:
    parts = fake.split('@')
    if len(parts) != 4:
      print(f'{fake} does not contain 4 parts', file = sys.stderr)
      sys.exit(1)
    version, response, v_code, count = parts
    count = int(count)
    version = int(version)
    combination.loc[(version, response), v_code] = count

combination.to_csv(args.output + '.csv')
combination.to_pickle(args.output + '.pkl')
