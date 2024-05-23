def apply_version(d, version):
  if not version in d: return

  #if anything was specified for this version, replace value in original
  #everything unspecified in version will be left untouched
  #answers are a special case, see below
  def replace_version(original, replacement):
    for k, v in replacement.items():
      if isinstance(v, dict):
        if k == 'answers':
          result = {}
          for k1, v1 in v.items():
            if v1:
              result[k1] = v1
            else:
              if k1 in original['answers']: result[k1] = original['answers'][k1]
              else: raise Exception() #unreachable
          original['answers'] = result
        else: replace_version(original[k], v)
      else: original[k] = v

  replace_version(d, d[version])
  del(d[version])
