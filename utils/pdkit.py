import pandas as pd

def df_contains(df, *regexps):
  for c in df.columns:
    s = df[c]
    if pd.api.types.is_string_dtype(s) or pd.api.types.is_object_dtype(s):
      for regexp in regexps:
        if s.str.contains(regexp).any():
          return True
  return False
