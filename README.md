# redline-and-hx-enterprise-search-extractor
### Description
FireEye HX Enterprise Search &amp; Redline both output data in a fairly useless CSV. 

I've written a horrible RegEx and script to try and pull these fields out. It's not perfect but it does a pretty decent job. 

Exports in CSV, JSON and a JSON for Splunk


```
$ python ./hx enterprise search or redline export parser.py -f input_file.csv
Parsing the data and mapping new headers...
  New header: File Name
  New header: File Full Path
  New header: File MD5 Hash
  New header: Process Name
  New header: Parent Process Name
  New header: Parent Process Path
  New header: Process Event Type
  New header: Process ID
  New header: Username
  New header: Process Arguments
  New header: Timestamp - Event
  New header: Timestamp - Last Run
  New header: Timestamp - Accessed
  New header: Timestamp - Started
  Written file: new_input_file.csv
```

### Usage

```
usage: hx enterprise search or redline export parser.py [-h] -f FILENAME
                                                        [-w WRITE_FILE]
                                                        [--csv | --json-splunk | --json]
optional arguments:
  -h, --help            show this help message and exit
  -f FILENAME, --filename FILENAME
                        Provide a filename to parse.
  -w WRITE_FILE, --write-file WRITE_FILE
                        Provide a filename to write the new file out to. If
                        none specified, the script will write it out to a file
                        with "new_" prepended to the input file.
  --csv                 [default option] Write the data out as CSV.
  --json-splunk         Write the data out as JSON for Splunk.
  --json                Write the data out as ordinary JSON.```
