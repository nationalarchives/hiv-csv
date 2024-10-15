#!/bin/bash
#Usage:
#Download tar file from notebook
#If it has plain data (e.g. likely if it is being used in a box plot) then untar it and cd to the dir
#.../cmp_from_notebook_aggregated.sh *
#If it has aggregated (transformed) data then you want cmp_from_notebook_aggregated.sh instead


ERRCODE=0
VERBOSE=0
while getopts "V" o; do
  case "${o}" in
    V)
      VERBOSE=1
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
  ref="${x##*_v}"
  ref="${ref%.csv}"
  sheet="${ref#0}"
  sheet="${basedir}/../output/version${sheet%_*}.csv"
  col="${ref#*_}"
  col="`${basedir}/../utils/fnam_col.py ${col}`"
  col="${col##*V}"
  if [ ${VERBOSE} -ne 0 ]; then cat <<EOF
  FILE: $x
  diff <(sort "$x") <(csvtool cols "2,${col}" "${sheet}" | sort)
  if [ $? -ne 0 ]; then ERRCODE=1; fi
  Ref:      $ref
  Sheet:    $sheet
  Column:   $col (counts from 1)
EOF
  fi
  diff <(sort "$x") <(csvtool cols "2,${col}" "${sheet}" | sort)
  if [ $? -ne 0 ]; then ERRCODE=1; fi
done
exit $ERRCODE
