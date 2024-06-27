#!/usr/bin/env python3

import sys
import glob
import math
import pandas as pd
import plotly.express as px
from utils.pdkit import prune, move_column
from utils.pdkit import max as df_max

DASH_STYLES = ['solid', 'dot', 'dash', 'longdash', 'dashdot', 'longdashdot']
CSS_COLORS = ['aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure',
              'beige', 'bisque', 'black', 'blanchedalmond', 'blue',
              'blueviolet', 'brown', 'burlywood', 'cadetblue',
              'chartreuse', 'chocolate', 'coral', 'cornflowerblue',
              'cornsilk', 'crimson', 'cyan', 'darkblue', 'darkcyan',
              'darkgoldenrod', 'darkgray', 'darkgrey', 'darkgreen',
              'darkkhaki', 'darkmagenta', 'darkolivegreen', 'darkorange',
              'darkorchid', 'darkred', 'darksalmon', 'darkseagreen',
              'darkslateblue', 'darkslategray', 'darkslategrey',
              'darkturquoise', 'darkviolet', 'deeppink', 'deepskyblue',
              'dimgray', 'dimgrey', 'dodgerblue', 'firebrick',
              'floralwhite', 'forestgreen', 'fuchsia', 'gainsboro',
              'ghostwhite', 'gold', 'goldenrod', 'gray', 'grey', 'green',
              'greenyellow', 'honeydew', 'hotpink', 'indianred', 'indigo',
              'ivory', 'khaki', 'lavender', 'lavenderblush', 'lawngreen',
              'lemonchiffon', 'lightblue', 'lightcoral', 'lightcyan',
              'lightgoldenrodyellow', 'lightgray', 'lightgrey',
              'lightgreen', 'lightpink', 'lightsalmon', 'lightseagreen',
              'lightskyblue', 'lightslategray', 'lightslategrey',
              'lightsteelblue', 'lightyellow', 'lime', 'limegreen',
              'linen', 'magenta', 'maroon', 'mediumaquamarine',
              'mediumblue', 'mediumorchid', 'mediumpurple',
              'mediumseagreen', 'mediumslateblue', 'mediumspringgreen',
              'mediumturquoise', 'mediumvioletred', 'midnightblue',
              'mintcream', 'mistyrose', 'moccasin', 'navajowhite', 'navy',
              'oldlace', 'olive', 'olivedrab', 'orange', 'orangered',
              'orchid', 'palegoldenrod', 'palegreen', 'paleturquoise',
              'palevioletred', 'papayawhip', 'peachpuff', 'peru', 'pink',
              'plum', 'powderblue', 'purple', 'red', 'rosybrown',
              'royalblue', 'rebeccapurple', 'saddlebrown', 'salmon',
              'sandybrown', 'seagreen', 'seashell', 'sienna', 'silver',
              'skyblue', 'slateblue', 'slategray', 'slategrey', 'snow',
              'springgreen', 'steelblue', 'tan', 'teal', 'thistle', 'tomato',
              'turquoise', 'violet', 'wheat', 'white', 'whitesmoke',
              'yellow', 'yellowgreen']

def highest(x):
  return max(filter(lambda y: not math.isnan(y), x))

#Index labels should always be of form "Version x"
def row_sort_key(x):
  return int(x.split()[-1])

#currently unused, as we are working with proportions, which we just want scaled from 0 to 1
def scale_range(df):
  y_max = df_max(df)
  y_magnitude = math.floor(math.log10(y_max))
  y_max = (10 ** y_magnitude) * math.ceil(y_max / (10 ** y_magnitude)) #rounded up to nearest next increment in order of magnitude
  return 0, y_max, y_magnitude

#read all csvs matching a prefix, create a dataframe with the proportional count of "yes" answers
def prop_yes(prefix):
  csvs = glob.glob(f'{prefix}_*.csv')
  df_yes = pd.read_csv(f'{prefix}_yes.csv', index_col = 0) #count of "yes" answers (index = version, columns = variable e.g. disease)
  df_all = pd.concat([pd.read_csv(x, index_col = 0) for x in csvs]) #count of all answers (same index, cols)
  df_yes_prop = df_yes / df_all.groupby(level = 0).sum() #therefore this gives proportional yes's
  df_yes_prop *= 100 #convert to percentages
  return df_yes_prop

for prefix in sys.argv[1:]: #e.g. output/q1
  df, dropped_rows, dropped_cols = prune(prop_yes(prefix))
  if len(dropped_rows):
    print('Dropped empty rows:',  ', '.join([f'"{x}"' for x in sorted(dropped_rows, key = row_sort_key)]))
  if len(dropped_cols):
    print('Dropped empty cols: ', ', '.join([f'"{x}"' for x in sorted(dropped_cols)]))
  df = df.reindex(sorted(df.columns), axis = 1)
  for end_col in 'Other', 'Other (CODE AND STATE)', "Don't know":
    if end_col in df.columns:
      df = move_column(df, end_col)
  df = df.reindex(sorted(df.index, key = row_sort_key))
  print(df)

  fig = px.line(df, markers = True) #https://stackoverflow.com/a/11067072
  fig.update_xaxes(title_text = 'Survey Version')
  fig.update_yaxes(title_text = '"Yes" Proportion (%)', range = [0, 100])

  #sorting these by peak increases the chance that lines near to one another will look different
  for count, trace in enumerate(sorted(fig['data'], key = lambda x: highest(x['y']), reverse = True)):
    trace['marker']['symbol'] = count
    trace['line']['dash'] = DASH_STYLES[count % len(DASH_STYLES)]
    #print(max(trace['y']), trace['legendgroup'], trace['line']['dash'])

    #if highest(trace['y']) < (10 ** y_magnitude): #default-off for lines with max value below 1 order of magnitude
    if highest(trace['y']) < 10: #default-off for lines with max value below 10%
      trace['visible'] = 'legendonly'

  fig.update_layout(title = "Q1: Most serious diseases & infections, all versions", legend_title_text = 'Disease')
  fig.show()

  df_adult = df.loc[df.index.isin(['Version 1', 'Version 3', 'Version 7', 'Version 15'])]
  df_adult.index = [1, 2, 3, 4]
  df_adult.index.name = 'wave'
  df_gay   = df.loc[df.index.isin(['Version 2', 'Version 4', 'Version 8', 'Version 16'])]
  df_gay.index = [1, 2, 3, 4]
  df_gay.index.name = 'wave'
  #df_combined = pd.concat([df_adult, df_gay], keys = ['adult', 'gay'], names = ['sample', 'wave'])#.unstack(0)

  print(df_adult)
  print(df_gay)
  #print(df_combined)

  #px.line(df_combined).show()

  import plotly.graph_objects as go
  
  #data = [go.Scatter(x = df_adult.index, y = df_adult[disease], name = disease, line = {'dash': DASH_STYLES[count % len(DASH_STYLES)]}) for count, disease in enumerate(df_adult.columns)]
  #data.extend([go.Scatter(x = df_gay.index, y = df_gay[disease], name = disease, line = {'dash': 'dash', 'color': CSS_COLORS[(count + 2) * 5]}, legend = 'legend2') for count, disease in enumerate(df_gay.columns)])
  adult_data = [go.Scatter(x = df_adult.index, y = df_adult[disease], name = disease, line = {'dash': 'dot', 'color': f'hsv({(count * 6) % 100}%,100%,100%)'}, hoverinfo = 'y+name+text', text = 'adult') for count, disease in enumerate(df_adult.columns)]
  gay_data = [go.Scatter(x = df_gay.index, y = df_gay[disease], name = disease, line = {'dash': 'dash', 'color': f'hsv({(count * 6) % 100}%,100%,100%)'}, hoverinfo = 'y+name+text', text = 'gay', legend = 'legend2') for count, disease in enumerate(df_gay.columns)]
  for a_trace, g_trace in zip(adult_data, gay_data):
    if highest(a_trace['y']) < 10 and highest(g_trace['y']) < 10: #default-off for lines with max value below 10%
      a_trace['visible'] = 'legendonly'
      g_trace['visible'] = 'legendonly'

  fig = go.Figure(
    data = adult_data + gay_data,
    layout=dict(
        hovermode = 'x',
        #hoversubplots = 'axis',
        title="Sample",
        legend={
            "title": "Adult",
            #"xref": "container",
            #"yref": "container",
            "y": 1.65,
            "bgcolor": "Orange",
            'yanchor': 'top',
        },
        legend2={
            "title": "Gay",
            #"xref": "container",
            #"yref": "container",
            "y": 15.85,
            "bgcolor": "Gold",
            'yanchor': 'top',

        },
    ),
  )
  fig.update_xaxes(tickvals = list(range(1,5)), range = [1, 4])
  fig.update_yaxes(tickvals = list(range(0,101,10)))
  fig.update_xaxes(title_text = 'Wave')
  fig.update_yaxes(title_text = '"Yes" Proportion (%)', range = [0, 100])

  fig.update_layout(title = "Q1: Most serious diseases & infections, all versions", legend_title_text = 'Disease')
  fig.show()

