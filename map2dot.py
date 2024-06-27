#!/usr/bin/env python3
import sys
import yaml
import pydot
import textwrap

NODE_CHARS = 60
COND_CHARS = 30
EDGE_CHARS = 15

nodes = set()
branches = {}
dot = []

def q_num(q_key):
  if q_key[0] != 'Q': raise Exception(q_key)
  return int(q_key[1:])

def branch_connection(num):
  for b_entry in branches[num].values():
    target_num = q_num(b_entry['target'])
    if target_num == num: #simply target to the question with same number as this branch
      target_code = f'q{target_num}'
    elif target_num in branches: #target another branch (that is not _this_ branch)
      target_code = f'b{target_num}'
    elif target_num in nodes: #number associated with a question that isn't guarded by a branch, target that question
      target_code = f'q{target_num}'
    else: #unreachable
      raise
    label = "\\n".join(textwrap.wrap(b_entry['label'],  width = EDGE_CHARS))
    if 'direction' in b_entry:
      out_direction = b_entry['direction']
    else:
      if num == target_num: out_direction = 's'
      else: out_direction = 'w'
    dot.append(f'b{num}:{out_direction} -> {target_code}:n [ label = \"{label}\" ];')

def branch_entry(num, b_in):
  #set defaults, overwriting where alternative values are defined
  b_out = {
    True: {
      'target': f'Q{num}',
      'label': 'yes',
    },
    False: {
      'target': f'Q{num}',
      'label': 'no',
    },
  }
  for k1 in True, False:
    if k1 in b_in:
      for k2 in b_in[k1].keys():
        b_out[k1][k2] = b_in[k1][k2]

  #Some error checking
  if b_out[True]['target'] == b_out[False]['target']:
    print(f'Duplicate target {b_out[True]["target"]} in branch associated with Q{num}', file = sys.stderr)
    sys.exit(1)
  if b_out[True]['label'] and (b_out[True]['label'] == b_out[False]['label']):
    raise #labels are the same and not defaut (seems unlikely to happen)

  return b_out


dot.append('digraph G {')

#First pass: define all nodes
#Place all node numbers into a set
#Branches get an extra entry in a dict
with open('map.yaml') as f:
  questionnaire = yaml.load(f, Loader = yaml.Loader)
for k, v in questionnaire.items():
  if not k[0] == 'Q': continue

  num = q_num(k)
  if num in nodes: raise #input contains dupliate question number. Shouldn't be able to happen, given how YAML parser behaves.
  nodes.add(num)
  if not 'question' in v:
    print(f'Missing question text for question {k}', file = sys.stderr)
    sys.exit(1)
  text = "\\n".join(textwrap.wrap(v['question'], width = NODE_CHARS))
  dot.append(f'q{num} [ group = mainline, shape = rect, label = \"{num}. {text}\" ];') #group is to encourage graphviz to keep nodes in a neat column

  #branches are in addition to a question -- they insert in front of question 'num'
  if 'branch' in v:
    b_text = "\\n".join(textwrap.wrap(v['branch']['condition'], width = COND_CHARS))
    dot.append(f'b{num} [ shape = diamond, label = \"{b_text}\" ];')
    branches[num] = branch_entry(num, v['branch'])


#Make the connections in a second pass, now that all nodes exist to connect to
#Most nodes straightforwardly connect to the next question, but there are some branches

#Sort out connections going out from branches first. They can need to recurse (branch pointing to branch).
for num in branches.keys():
  branch_connection(num)

#Then fill in all the other connections
max_num = max(nodes)
for num in nodes:
  if num + 1 <= max_num:
    x = num + 1
    while x < max_num and x not in nodes:
      x += 1
    #x is now at most max_num, which is necessarily in nodes (as it is max value in nodes)
    if x in branches:
      dot.append(f'q{num}:s -> b{x}:n;')
    else:
      dot.append(f'q{num}:s -> q{x}:n;')

dot.append('}')

dot = '\n'.join(dot)

with open('output/flowcharts/version1.dot', 'w') as f:
  print(dot, file = f)
pydot.graph_from_dot_data(dot)[0].write_svg('output/flowcharts/version1.svg')
