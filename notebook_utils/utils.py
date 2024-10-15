#Though this file is written in a reasonably general way, it doesn't really make sense as a library
#It just exists to hide complexity in notebooks

import pandas as pd
import ipywidgets as widgets
from ..utils import fnam_col

def excel_to_index(excel):
  #indices are 2 less than the corresponding V-number, because DataFrames count from 0, and because I have turned one column into an index
  return fnam_col.c2i(excel) - 2

def index_to_excel(index):
  return fnam_col.n2a(index + 2)

def display_comparison(header, version_map, colcode_map, versions, canonicals, df_key = 'df'):
  def unique_data(version, colcode):
    colnum = excel_to_index(colcode)
    colname = version_map[version][df_key].columns[colnum]
    s = pd.Series(version_map[version][df_key][colname].unique())
    s.name = colname

    box = widgets.Output()
    with box:
      display(widgets.HTML(f'<h3>Version {version}</h3>'))
      display(s)
    return box

  display(header)
  display(widgets.HBox([
    unique_data(x,  colcode_map[x][y]) for y in canonicals for x in versions
  ]))
