import pandas as pd

def max(df):
  return df.max().max()

def df_contains(df, *regexps):
  for c in df.columns:
    s = df[c]
    if pd.api.types.is_string_dtype(s) or pd.api.types.is_object_dtype(s):
      for regexp in regexps:
        if s.str.contains(regexp).any():
          return True
  return False

def prune(df):
  pruned_df = df.dropna(how = 'all').dropna(axis = 1, how = 'all')
  dropped_rows = df.index.difference(pruned_df.index)
  dropped_cols = df.columns.difference(pruned_df.columns)
  return pruned_df, dropped_rows, dropped_cols

#re https://stackoverflow.com/a/67894930
def move_column(df, col_name, pos = -1):
  if not col_name in df.columns:
    raise

  if pos < 0:
    pos = len(df.columns) + pos
  c = df.pop(col_name)
  df.insert(pos, col_name, c)
  return df
