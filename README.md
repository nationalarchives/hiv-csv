# Quick Start


## Get data files

Download the [BN 97/1 data files](https://discovery.nationalarchives.gov.uk/details/r/C11521961).
Then:

```
mkdir BN-97-1/ #assuming you're in the directory that contains this readme file
cd BN-91-1
unzip ~/Downloads/BN-97-1.zip #or whatever the download path is
```


## Get dependencies

Ideally in a virtualenv (e.g. `mkvirtualenv hiv`):

`pip install -r requirements.txt`


## Build the project

To build everything: `make -j`

To build just the CSV files and associated reports: `make -j csvs`

To open up the documentation: `./directory.sh` (requires firefox)

To get a report on unusual cases and total data points produced: `./report.sh`


# More details

For completeness, fuller dependencies are listed in `requirements_all.txt`.

This project was developed with Python 3.10.12 on Ubuntu 22.04 (Jammy)
