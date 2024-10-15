#!/bin/bash
#Usage:
#Download tar file from notebook
#If it has aggregated data (e.g. likely if it is being used in a bar chart) then untar it and cd to the dir
#.../cmp_from_notebook_aggregated.sh *
#If it has plain (untransformed) data then you want cmp_from_notebook_plain.sh instead

ERRCODE=0
NOISY=0
VERBOSE=0
while getopts "vV" o; do
  case "${o}" in
    v)
      NOISY=1
    ;;
    V)
      VERBOSE=1
      NOISY=1
    ;;
    *)
      echo 'Bad args' >&2
      exit 1
    ;;
  esac
done
shift $((OPTIND-1))

basedir=`dirname "$0"`
[ $VERBOSE -ne 0 ] && echo $basedir
for x in "$@"; do
  header=$(cat "$x" | csvtool cols 2 - | head -n1)
  if [ ${VERBOSE} -ne 0 ]; then echo; echo 'FILE:' "$x"; echo 'Header:' "'$header'"; fi
  while read -r line; do
    ref="${line%%),*}"
    ref="${ref##*(}"
    sheet="${ref:1}"
    sheet="${sheet#0}"
    sheet="${basedir}/../output/version${sheet%%:*}.csv"
    col="${ref##*:}"
    col="`${basedir}/../utils/fnam_col.py ${col}`"
    col="${col##*V}"
    val="${line##*,}"

    #This happens to work out for nan case because header is blank, so grep selects everything... but then 
    #the parameter substitution deletes everything after the first number -- which is the nan value, which is blank,
    #which has been sorted to the top
    answer=$(cat "${sheet}" | csvtool cols "${col}" - | sort | uniq -c | grep "${header}$" | sed 's/^[[:blank:]]*//')
    answer="${answer%% *}"

    if [ ${VERBOSE} -ne 0 ]; then cat <<EOF
  Line:     $line
  Ref:      $ref
  Sheet:    $sheet
  Column:   $col (counts from 1)
  Got:      ${val}
  Expected: ${answer}
EOF
    fi
    if [ x"${val}" == x"${answer}" ]; then
      [ ${NOISY} -ne 0 ] && echo 'pass'
    else
      ERRCODE=1
      cat <<EOF
fail for "$line" from "$x"
  Expected: '${answer}'
  Got:      '${val}'
  (Re cat "${sheet}" | csvtool cols "${col}" - | sort | uniq -c)
  May be due to notebook normalization of field names
EOF
    fi
  done < <(cat "$x" | sed 1d)
done
exit $ERRCODE
