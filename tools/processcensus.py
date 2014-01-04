import datetime
import time

from models import *

from sqlalchemy import create_engine
from zope.sqlalchemy import ZopeTransactionExtension

import transaction

DBSession = None 

import os
import re
import urllib
import urllib2
from urllib2 import urlopen
from bs4 import BeautifulSoup
from pdfminer.pdfinterp import PDFResourceManager, process_pdf
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from cStringIO import StringIO

import ConfigParser

debug = False
verbose = False

def report(text):
    global verbose
    if(verbose):
        print "[{0}] {1}".format(datetime.datetime.now().strftime("%x %X"),text)

def _downloadpdf(url,downloaddir="./pdfs"):
    # report("Downloading PDF ...")
    f = urlopen(url)
    filename = "{0}/{1}".format(downloaddir,os.path.basename(url))
    with open(filename, "wb") as local_file:
        local_file.write(f.read())
    #report("... Done downloading PDF.")
    return filename

def _decodepdf(filename,debug=False):
    pdfstr = ""
    if debug==True:
        report("Debug mode enabled, reading inmates from rawfile.txt ...")
        with open("rawfile.txt","r") as rawfile:
            pdfstr = rawfile.read()
        report("... Done reading inmates from disk.")
    else:
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)

        report("Converting PDF to text ...")
        fp = file(filename, 'rb')
        process_pdf(rsrcmgr, device, fp)
        fp.close()
        device.close()
        pdfstr = retstr.getvalue()
        retstr.close()
        report("... Done converting PDF to text.")

        report("Saving converted PDF text to rawfile.txt ...")
        with open("rawfile.txt","w") as rawfile:
            rawfile.write(pdfstr)
        report("... Done saving converted PDF text.")

    report("Preprocessing PDF Text ...")

    labels = ['Book Dt:','Book Typ:','Cus Typ:','Bail:','Bond:','Court:','Judge:',
              'Exp Rls:','Arr Agy:','Arr Typ:','ROC:','Chg:','Indict:','Adj Dt:','Term:']

    for label in labels:
        pdfstr = pdfstr.replace(label,"\n{0} ".format(label))

    # preprocess to get rid of duplicate spaces and \n's
    pdfstr = re.sub(' +',' ',pdfstr)
    pdfstr = re.sub('\n+','\n',pdfstr)

    # handle current sentence going to next line
    # (time from custody date/time + first three capital leters form sentence type)
    pdfstr = re.sub('([0-9]{4})(?: )?\n([A-Z]{3})','\\1 \\2',pdfstr)

    #ith open("rawfile2.txt","w") as rawfile:
    #   rawfile.write(pdfstr)

    # handle inmate ID not being on same line as inmate data
    # (in some casses mcid, sex, race, and dob can all be on different lines ...)
    pdfstr = re.sub('([0-9]{6})(?: )?(?:\n)?([A-Z])(?: )?(?:\n)?([A-Z])(?: )?(?:\n)?([0-9]{2}-[0-9]{2}-[0-9]{2})','\\1 \\2 \\3 \\4',pdfstr)

    #ith open("rawfile3.txt","w") as rawfile:
    #   rawfile.write(pdfstr)

    # remove page header
    pdfstr = re.sub('Current Census for Date: [0-9]{2}-[0-9]{2}-[0-9]{4}(?: )?(?:\n)?','',pdfstr)
    pdfstr = re.sub('Name(?: )?(?:\n)?Location(?: )?(?:\n)?','',pdfstr)
    pdfstr = re.sub('MCJ Sex Rce DOB(?: )?(?:\n)?','',pdfstr)
    pdfstr = re.sub('Custody(?: )?(?:\n)?Time(?: )?(?:\n)?Date(?: )?(?:\n)?Classification(?: )?(?:\n)?','',pdfstr)
    pdfstr = re.sub('Min(?: )?(?:\n)?Rel(?: )?(?:\n)?Date(?: )?(?:\n)?','',pdfstr)

    # remove page footers
    pdfstr = re.sub('Facility:(?: )?(?:\n)?','',pdfstr)
    pdfstr = re.sub('Page \d+ of \d+(?: )?(?:\n)?','',pdfstr)
    pdfstr = re.sub('Printed:(?: )?\n([0-9]{2}-[0-9]{2}-[0-9]{4}) [0-9]{4}','',pdfstr)

    # page-to-page formating issue
    pdfstr = re.sub('\x0C(?: )?(?:\n)?','',pdfstr)

    # Note: probably not nessisary
    # post-process to get rid of duplicate spaces and \n's
    pdfstr = re.sub(' +',' ',pdfstr)
    pdfstr = re.sub('\n+','\n',pdfstr)

    #ith open("rawfile4.txt","w") as rawfile:
    #   rawfile.write(pdfstr)

    report("... Done Preprocessing PDF Text.")

    return pdfstr,True

def _pullpdf(url="http://www2.monroecounty.gov/sheriff-inmate",
             baseurl="http://www2.monroecounty.gov",
             linktext="Inmate Census",
             downloaddir="./pdfs",
             debug=False
            ):
    report("Pulling in PDF data ...")
    #debug = True
    pdftext = ""
    success = False
    filename = ""
    if debug:
        report("debug enabled, decoding file from disk ...")
        pdftext,success = _decodepdf(filename,debug)
    else:
        report("Looking for census link on html page ...")
        html = urllib2.urlopen(url)
        soup = BeautifulSoup(html)
        atags = soup.find_all('a', href=True)
        for tag in atags:
            tagstr = None
            if tag.string != None:
                tagstr = tag.string.encode("utf8").lower()
                if tagstr.strip() == linktext.encode("utf8").lower().strip():
                    report("... Link found.")
                    pdfurl = "{0}{1}".format(baseurl,tag['href'])
                    report("Downloading PDF ...")
                    filename = _downloadpdf(pdfurl,downloaddir)
                    report("... Done Downloading PDF.")
                    report("Decoding PDF ...")
                    pdftext,success = _decodepdf(filename)
                    report("... Done Decoding PDF.")
                    report("Saving PDF Text to pdftext.txt ...");
                    with open("pdftext.txt", "w") as txtfile:
                        txtfile.write(pdftext)
                    report("... Done saving file.")
                    break
    report("... Done pulling in PDF data.")
    return (pdftext,success)

def _getlines(pdftext):
    lines = []
    for line in pdftext.split('\n'):
        line = line.strip()
        if line != "":
            lines.append(line)
    return lines

def _pullinmates(pdftext):
    report("Attemping to pull inmate names ...")
    success = True
    try:
        indexes = []
        lines = _getlines(pdftext)
        for i in range(0,len(lines)):
            # see if it is a name in all caps
            if re.match("^[A-Z]*$", lines[i].replace(",","").replace(" ","").replace(".","").replace("-","")):
                indexes.append(i)
        inmates = []
        for i in range(0,len(indexes)-1):
            inmatedata = []
            datarange = indexes[i+1]-indexes[i]
            for j in range(0,datarange):
                inmatedata.append(lines[indexes[i]+j])
            inmates.append((lines[indexes[i]],inmatedata))
    except:
        success = False
    report("... Done attemping to pull inmate names, pulled {0} inmates.".format(len(inmates)))
    return inmates,success

def _parsename(fullname):
    try:
        parts = fullname.replace('.','').split(',')
        last = parts[0].strip()
        if parts[1].rsplit(' ',1)[0].strip() == "":
            first = parts[1].strip()
            middle = ""
        else:
            # take off middle
            first = parts[1][:-2].strip()
            middle = parts[1][-1:].strip()
    except:
        # this happens when the name is something like "US MARCHAL" rather than a person's name
        first = ""
        middle = ""
        last = fullname
    return (first,middle,last)

def __dobookingtype(fullname):
    try:
        bookingtype = DBSession.query(BookingTypeModel).filter(BookingTypeModel.fullname == fullname).one()
        #report("Booking type '{0}' already in database, using query'd row".format(fullname))
    except:
        #report("Booking type not found in database, inserting new type: '{0}'".format(fullname))
        bookingtype = BookingTypeModel(fullname=fullname)
        DBSession.add(bookingtype)
    DBSession.flush()
    transaction.commit()
        
        #print "FULLNAME: {0}".format(bookingtype.fullname)
    return bookingtype

def __docustodytype(shortname):
    try:
        custodytype = DBSession.query(CustodyTypeModel).filter(CustodyTypeModel.shortname == shortname).one()
    except:
        custodytype = CustodyTypeModel(shortname=shortname)
        DBSession.add(custodytype)
    DBSession.flush()
    transaction.commit()
    return custodytype

def __docourt(shortname):
    try:
        court = DBSession.query(CourtModel).filter(CourtModel.shortname == shortname).one()
    except:
        court = CourtModel(shortname=shortname)
        DBSession.add(court)
    DBSession.flush()
    transaction.commit()
    return court

def __dojudge(fullname,first,middle,last):
    try:
        judge = DBSession.query(JudgeModel).filter(JudgeModel.fullname == fullname).one()
    except:
        judge = JudgeModel(fullname=fullname,first=first,middle=middle,last=last)
        DBSession.add(judge)
    DBSession.flush()
    transaction.commit()
    return judge

def __doagency(fullname):
    try:
        agency = DBSession.query(AgencyModel).filter(AgencyModel.fullname == fullname).one()
    except:
        agency = AgencyModel(fullname=fullname)
        DBSession.add(agency)
    DBSession.flush()
    transaction.commit()
    return agency

def __doarresttype(fullname):
    try:
        arresttype = DBSession.query(ArrestTypeModel).filter(ArrestTypeModel.fullname == fullname).one()
    except:
        arresttype = ArrestTypeModel(fullname=fullname)
        DBSession.add(arresttype)
    DBSession.flush()
    transaction.commit()
    return arresttype

def __docharge(fullname):
    try:
        charge = DBSession.query(ChargeModel).filter(ChargeModel.fullname == fullname).one()
        #report("Charge '{0}' already in database, using query'd row".format(fullname))
    except:
        #report("Charge not found in database, inserting new type: '{0}'".format(fullname))
        charge = ChargeModel(fullname=fullname)
        DBSession.add(charge)
    DBSession.flush()
    transaction.commit()
    return charge

def _parseinmates(rawinmates):
    report("Attemping to parse inmate, custody, and booking data ...")
    success = True
    retdata = []
    for rawinmate in rawinmates:
        inmate = InmateModel()
        custody = CustodyModel()
        rawname,rawdata = rawinmate
        report("Processing '{0}' ...".format(rawname)) 
        first,middle,last = _parsename(rawname)
        inmate.first = first
        inmate.middle = middle
        inmate.last = last
        bookings = [] 
        for data in rawdata:
            report("[Inmate/Custody Info] Working on: '{0}'".format(data))
            if re.match('([0-9]{6}) [A-Z] [A-Z] ([0-9]{2})-([0-9]{2})-([0-9]{4})',data):
                report("Inmate info match, procesing.")
                parts = data.split(' ')
                inmate.mcid = parts[0]
                inmate.sex = parts[1]
                inmate.race = parts[2]
                inmate.dob = datetime.datetime.strptime(parts[3],"%m-%d-%Y")
            if re.match('[0-9]{2}-[0-9]{2}-[0-9]{4} [0-9]{4} [A-Z]{3}',data):
                report("Custody info match, processing.")
                parts = data.split(' ')
                dt = "{0} {1}".format(parts[0],parts[1])
                custody.datetime = datetime.datetime.strptime(dt,"%m-%d-%Y %H%M")
                custody.custodyclass = " ".join(parts[2:])
            if inmate.populated():
                report("Inmate data populated, parsing bookings ...")
                booking = BookingModel()
                for _data in rawdata:
                    report("[Bookings] Working on: '{0}'".format(_data))
                    if re.match('Book Dt:',_data):
                        report("Found 'Book Dt.'")
                        _bookdatetime = _data.split(':')[1].strip()
                        booking.datetime = datetime.datetime.strptime(_bookdatetime,"%m/%d/%Y %H%M")
                    if re.match('Book Typ:',_data):
                        report("Found 'Book Type'")
                        _bookingtype = _data.split(':')[1].strip()
                        booking.bookingtype = __dobookingtype(_bookingtype)
                    if re.match('Cus Typ:',_data):
                        report("Found Cus Typ")
                        _custodytype = _data.split(':')[1].strip()
                        booking.custodytype = __docustodytype(_custodytype)
                    if re.match('Bail:',_data):
                        report("Found 'Bail'")
                        _bail = _data.split(':')[1].strip()
                        booking.bail = _bail
                    if re.match('Bond:',_data):
                        report("Found 'Bond'")
                        _bond = _data.split(':')[1].strip()
                        booking.bond = _bond
                    if re.match('Court:',_data):
                        report("Found 'Court'")
                        _court = _data.split(':')[1].strip()
                        booking.court = __docourt(_court)
                    if re.match('Exp Rel:',_data):
                        report("Found 'Exp Rel'")
                        _expectedrelease = _data.split(':')[1].strip()
                        if _expectedrelease != "":
                            booking.expectedrelease = datetime.datetime.strptime(_expectedrelease,"%m-%d-%Y")
                        else:
                            booking.expectedrelease = None
                    if re.match('Judge:',_data):
                        report("Found 'Judge'")
                        _judge = _data.split(':')[1].strip()
                        first,middle,last = _parsename(_judge)
                        booking.judge = __dojudge(_judge,first,middle,last)
                    if re.match('Arr Agy:',_data):
                        report("Found 'Arr Agy'")
                        _agency = _data.split(':')[1].strip()
                        booking.agency = __doagency(_agency)
                    if re.match('Arr Typ',_data):
                        report("Found 'Arr Typ'")
                        _arresttype = _data.split(':')[1].strip()
                        booking.arresttype = __doarresttype(_arresttype)
                    if re.match('ROC:',_data):
                        report("Found 'ROC'")
                        _roc = _data.split(':')[1].strip()
                        booking.roc = _roc
                    if re.match('Chg:',_data):
                        report("Found 'Chg'")
                        _charge = _data.split(':')[1].strip()
                        booking.charge = __docharge(_charge)
                    if re.match('Indict:',_data):
                        report("Found 'Indict'")
                        _indict = _data.split(':')[1].strip()
                        booking.indict = _indict
                    if re.match('Adj Dt:',_data):
                        report("Found 'Adj Dt'")
                        _adjusteddate = _data.split(':')[1].strip() 
                        if _adjusteddate.strip() == "":
                            booking.adjusteddate = None
                        else:
                            booking.adjusteddate = datetime.datetime.strptime(_adjusteddate,"%m/%d/%Y")
                    if re.match('Term:',_data):
                        report("Found 'Term'")
                        _term = _data.split(':')[1].strip()
                        days = _term.split(' ')[0]
                        booking.term = days
                    # see if we have all of the data for one booking, and if we do then add it to the
                    # list of bookings, and reset our booking modle object
                    if booking.populated():
                       report("\tComplete Booking Found, adding to list.")
                       bookings.append(booking)
                       booking = BookingModel()
                       continue
                report("... Done processing bookings.")
                break

            # end of if


        retdata.append((inmate,custody,bookings))
        report("... Done working on {0}.".format(rawname))
    report("... Done attempting to process inmate, custody, and booking data.")
    return retdata,success

def getinmates(debug=False,downloaddir='./pdfs'):
    inmates = []
    sucess = False
    if debug == True:
        success = True
        with open("pdftext.txt", "r") as _file:
            pdftext = _file.read()
    else:
        pdftext,success = _pullpdf(debug=debug,downloaddir=downloaddir)
    if success:
        _inmates,success = _pullinmates(pdftext)
    if success:
        inmates,success = _parseinmates(_inmates)
    return inmates,success

def main():
    report("Application Starting: processcensus.py")

    report("Reading configuration from config.ini ...")
    global debug
    global verbose
    #try:
    config = ConfigParser.ConfigParser()
    config.read('config.ini')
    debug = config.getboolean('processcensus','debug')
    verbose = config.get('processcensus','verbose')
    uri = config.get('processcensus','uri')
    downloaddir = config.get('processcensus','downloaddir')
    #except:
    #    raise Exception("There is an error in your config.ini file.")
    report("... Done reading configuration.")

    engine =  create_engine(uri)
    Session = sessionmaker(bind=engine)
    global DBSession
    DBSession = scoped_session(
        sessionmaker(extension=ZopeTransactionExtension()))
    DBSession.configure(bind=engine)
    Base.metadata.create_all(bind=engine)

    report("Pulling census from the interwebs ...")

    theinmates,success = getinmates(debug,downloaddir)
    if success:
        report("... Done pulling and processing census.")
    else:
        raise Exception("Something bad happened ... no inmates were pulled.")

    report("Pushing {0} inmates to the database ...".format(len(theinmates)))

    for inmate,custody,bookings in theinmates:
        # try and pull the inmate if it exists, if error then add them
        try:
            inmate = DBSession.query(InmateModel).filter(
                InmateModel.first == inmate.first,
                InmateModel.last == inmate.last,
                InmateModel.middle == inmate.middle,
                InmateModel.mcid == inmate.mcid
            ).one()
            report("Inmate already exists, pulling from DB.")
        except:
            report("Inmate doesn't exist, creating '{0}, {1} {2}'".format(inmate.last,inmate.first,inmate.middle))
            DBSession.add(inmate)
        DBSession.add(custody)
        for booking in bookings:
            DBSession.add(booking)
        DBSession.flush()
        transaction.commit()

    report("Application Exit.\n");

main()
