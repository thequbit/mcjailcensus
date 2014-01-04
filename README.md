mcjailcensus
============

Monroe County Jail Inmate Census

###Overview###

This is a tool that will pull the current PDF off the Monroe County website that has the County Jail Census information
within it.  The tool pulls from this [url](http://www2.monroecounty.gov/sheriff-inmate) and downloads the currently
posted PDF document.  It is important to note that the PDF is not always current, and does not appear to be uploaded at
the same time each day.

Once the script runs, it saves the PDF document locally, converts it to text, and pulls all of the inmate information out of it.  It then saves this information as a large JSON file locally.  Finally the data is pushed to a mongodb database
for storage and indexing.

###Install###

    > pip install pymongo
    > pip install bs4
    > pip install pdfminer
    
###Running###

There is a single script file that will find the pdf, download it, convert it, scrub it, process it, and then push it 
to the mongodb database.

    > python ./tools/censusprocessor.py
    
