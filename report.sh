#!/bin/bash

for x in NO_ENCODING ENCODED_LOGICAL BAD_TYPE UNDECODABLE UNHANDLED_TYPE; do
  echo -n "${x}: "
  grep "^\* ${x}: " output/LOG/* | sed 's/.* //' | paste -sd+ | bc | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta'
done

echo -n 'Total data points: '
grep '^Non-null data points: ' output/LOG/* | sed 's/.* //' | paste -sd+ | bc | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta'

#for 1000s-separator sed trick, see https://www.baeldung.com/linux/bash-use-thousands-separator#:~:text=The%20printf%20command%20in%20Bash,separator%20to%20a%20number%20directly.&text=In%20the%20above%20code%2C%20we,numbers%20separated%20by%20thousands%20separators.
