mcjailcensus
============

Monroe County Jail Inmate Census

###Overview###

This is a tool that will pull the current PDF off the Monroe County website that has the County Jail Census information
within it.  The tool pulls from this [url](http://www2.monroecounty.gov/sheriff-inmate) and downloads the currently
posted PDF document.  It is important to note that the PDF is not always current, and does not appear to be uploaded at
the same time each day.

Once the script runs, it saves the PDF document locally, converts it to text, and pulls all of the inmate information out of it.  It then saves this information as a large JSON file locally.  Finally the data is pushed to a mongodb database for storage and indexing.

You could configure your mongodb database in a number of differnet ways.  This script assumes no configuration has been done, and a default install of mongodb exists, and is running on the same machine (localhost) as the python script.

###Install###

For the python side of things, you will need:

    > pip install pymongo
    > pip install bs4
    > pip install pdfminer=20110515
    
For the Linux side of things, you will need:

Ubuntu: 

    > apt-get install mongodb
    
Fedora:

    > yum install mongo-10gen mongo-10gen-server

###Running###

There is a single script file that will find the pdf, download it, convert it, scrub it, process it, and then push it 
to the mongodb database.

    > python ./tools/censusprocessor.py
    
If you want to run this script every day (or maybe twice a day since the folks at the jail don't appear to upload it at a specific time), I would recommend writting a python script to call the censusprocessor.py function(s), or make a crontab entry.

###Processing The Data###

The following is how to get the census (which includes downloading it, converting it, parsing it, and processing it),
and then push the data to the mongodb database.

    from dbtool import DatabaseTool
    from censusprocessor import CensusProcessor
    
    # create an instanace of our CensusProcessor
    cp = CensusProcessor(DEBUG=True) # if you don't want a bunch of print out, make DEBUG=False
    
    # download, convert, parse, and process the census pdf
    retdata,filename,success = cp.processcensus(usefile=False)

    # create an instance of our database interface tool
    dt = DatabaseTool(DEBUG=True) # if you don't want a bunch of print out, make DEBUG=False
    
    # add all of the items to the database
    dt.addmultiple(retdata)
    
###Data Format###

if you are interested in working with the data in python, and have no need to push it to the mongodb database, here is the scheme of the data that is returned from the CensusProcessor.processcensus() function:

    retval = [
        {
            "inmate": {
                "last": "ABDUL-WAHHAB",
                "dob": "1986-07-08 00:00:00",
                "sex": "M",
                "middle": "",
                "race": "B",
                "mcid": "344500",
                "first": "KHALID"
            },
            "bookings": [
                {
                    "adjusteddate": null,
                    "roc": "MOTI",
                    "court": "COUN",
                    "arresttype": "NON SENTENCED",
                    "agency": "IRONDEQUOIT POLICE",
                    "term": "",
                    "datetime": "2013-09-23 08:58:00",
                    "charge": "PL 135.10 EF1 - UNLAWFUL IMPRISONMENT 1ST",
                    "indict": "2013-0966",
                    "judge": {
                        "judge": "ARGENTO, VICTORIA",
                        "middle": "",
                        "last": "ARGENTO",
                        "first": "VICTORIA"
                    },
                    "custodytype": "MISC",
                    "bail": "$5,000.00",
                    "bookingtype": "Commitment",
                    "bond": "$5,000.00"
                }
            ],
            "custody": {
                "custodyclass": "NON SENTENCED",
                "datetime": "2013-09-23 09:19:00"
            }
        }
    ]
    
Note that every field seen above will exist within every item within the returned array, however not every field will be populated with information.
