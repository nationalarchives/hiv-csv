#!/usr/bin/env python3

import sys
import pandas as pd
import collections
from pathlib import Path

def dfs2xlsx(sheets, output, engine_kwargs = {}, to_excel_kwargs = {}):
  if not isinstance(sheets, dict):
    if isinstance(sheets, pd.DataFrame):
      sheets = { 'Sheet 1': sheets }
    else:
      print(f'Variable sheets is neither dict nor DataFrame', file = sys.stderr)
      sys.exit(1)

  #re https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_excel.html
  with pd.ExcelWriter(output, **engine_kwargs) as writer:
    for name, df in sheets.items():
      assert isinstance(df, pd.DataFrame), f'Variable "df" has non-DataFrame type {type(df)} with value {df}'
      df.to_excel(writer, sheet_name = name, **to_excel_kwargs)

def csvs2xslx(csvs, output, engine_kwargs, to_excel_kwargs):
  if isinstance(csvs, str):
    csvs = [csvs]
  elif not isinstance(csvs, collections.abc.Sequence):
    print(f'csvs is neither str nor sequence', file = sys.stderr)
    sys.exit(1)
  dfs2xlsx({Path(x).stem: pd.read_csv(x) for x in csvs}, output, engine_kwargs, to_excel_kwargs)


if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('csvs',
                      type = str,
                      nargs = '+',
                      help = 'CSV files to convert into XLSX sheets')
  parser.add_argument('--output', '-o',
                      default = 'output.xlsx',
                      help = 'Filename for output spreadsheet')
  args = parser.parse_args()
  engine_kwargs = {
    'mode': 'w',
    'engine': 'openpyxl',
  }
  to_excel_kwargs = {
    'index': None,
  }
  csvs2xslx(args.csvs, args.output, engine_kwargs, to_excel_kwargs)
