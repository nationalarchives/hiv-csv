#!/bin/bash

function filter_original {
  csvtool col 4 ../discovery_downloads/BN-97-1/version${1}__field_attributes.csv | \
    grep 'Q\.\([123456789]\|1[01]\)\.' | grep -v '^RECORD THE FOLLOWING INFORMATION AFTER THE INTERVIEW:' | \
    sed 's/^"//' | sed 's/"$//' | sed 's/^[[:blank:]]*//' | sed 's/[[:blank:]]*$//' | tr '[:upper:]' '[:lower:]' | tr '"' "'" | \
    sed "s/''/'/g" | \
    sed 's/\bsyphillis\b/syphilis/g' | \
    sed "s/\blegionnaire's\b/legionnaires/g" | \
    sed 's/infeced/infected/g' | \
    sed 's/(do not prompt respondent)/(do not prompt)/' | \
    sed 's/(do not prompt)/do not prompt/' | \
    sed 's/\.//g' | sed 's/[[:blank:]]//g'
}

function filter_regeneration {
  ./regenerate.py "$1" | \
    sed 's/\.//g' | tr '[:blank:]' ' ' | tr -s ' ' | tr '[:upper:]' '[:lower:]' | tr '"' "'" | \
    sed "s/\blegionnaire's\b/legionnaires/g" | sed 's/[[:blank:]]//g'
}

for x in 1 16; do
  diff <(filter_original "$x") <(filter_regeneration "$x")
  code=$?
  echo "Version ${x}: exit code ${code}"
  if [[ $code -ne 0 ]]; then
    meld <(filter_original "$x") <(filter_regeneration "$x") 2>/dev/null
    exit $code
  fi
done
