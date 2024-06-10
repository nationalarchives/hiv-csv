#In a Unix shell, type 'make -j' to create the output spreadsheet
#-j will tell make to run as much in parallel as it can
#Generally, the thing on the left of the colon is something to make
#And the thing on the right of the colon is the things that it depends on
#i.e. if anything on the right of the colon has changed, the thing on the left of the colon must be re-made

#A variable listing all versions that exist
VERSIONS := $(shell seq 1 8) $(shell seq 12 16)

#These ones don't (directly) make a file
.PHONY: all clean csvs $(VERSIONS)

all: output/hiv_survey.xlsx output/q1.xlsx

csvs: $(VERSIONS)

clean:
	rm -rf output/

#This involved line is saying that we must create every CSV file before creating the Excel file
#The $^ bit just repeats everything to the right of the colon
#$@ is the thing to the left of the colon
output/hiv_survey.xlsx: utils/csv2xlsx.py data/index.csv $(patsubst %,output/version%.csv,$(VERSIONS))
	python3 $^ -o $@ --freeze-row 1 --na-rep BLANK

output/q%.xlsx: utils/csv2xlsx.py output/q%_yes.csv output/q%_no.csv output/q%_blank.csv output/q%_undecodable.csv
	python3 $^ -o $@ --freeze-row 1 --freeze-col 1 --index-col 0 --float-format %.0f

output/q%_yes.csv output/q%_no.csv output/q%_blank.csv output/q%_undecodable.csv: extract_questions.py map.yaml | output
	python3 $<

#The % here is a placeholder for a number
#$* is the same number
#So this one rule describes how to create each of the csv files, from version1.csv to version16.csv
#$< is the first thing named to the right of the colon
output/version%.csv: to_csv.py | output output/LOG
	(cd output; python3 ../$< $* --log LOG/$*)

output:
	mkdir output

output/LOG: | output
	mkdir output/LOG

to_csv.py: utils/fnam_col.py utils/pdkit.py

utils/csv2xlsx.py: utils/pdkit.py

#This is just a trick so that I can write e.g. 'make 1' instead of 'make output/version1.csv'
.SECONDEXPANSION:
$(VERSIONS): output/version$$@.csv

#Got some help from https://stackoverflow.com/a/6542238 on variable targets
