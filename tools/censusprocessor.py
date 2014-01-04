import datetime
import json
import os
import re

from pdfminer.pdfinterp import PDFResourceManager, process_pdf
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from cStringIO import StringIO

class CensusProcessor(object):

    def __init__(self,DEBUG=False):
    
        self.DEBUG = DEBUG
        
    def _downloadpdf(self,
                    url="http://www2.monroecounty.gov/sheriff-inmate",
                    baseurl="http://www2.monroecounty.gov",
                    linktext="Inmate Census",
                    downloaddir="./pdfs",):
    
        #try:
        if True:
            print "Downloading PDF ..."
            success = True
            filename = ""
            
            # pull down webpage, and get a tags
            html = urllib2.urlopen(url)
            soup = BeautifulSoup(html)
            atags = soup.find_all('a', href=True)
            
            # itterate and find pdf link
            for tag in atags:
                tagstr = None
                if tag.string != None:
                    tagstr = tag.string.encode("utf8").lower()
                    if tagstr.strip() == linktext.encode("utf8").lower().strip():
                        
                        pdfurl = "{0}{1}".format(baseurl,tag['href'])
                        filename = "{0}/{1}".format(downloaddir,os.path.basename(url))
                        u = urllib2.urlopen(pdfurl)
                        
                        with open(filename, "wb") as local_file:
                            local_file.write(u.read())
                        
                        break
            if self.DEBUG:
                print "... Done pulling in PDF data.")
        except:
            success = False
            filename = ""
            
        return (filename,success)
        
        
    def _convertpdf(self,filename):
    
        #try:
        if True:
            success = True
            pdfstr = ""
            
            if self.DEBUG:
                print "Converting PDF to text ..."
            
            fp = file(filename, 'rb')
            process_pdf(rsrcmgr, device, fp)
            fp.close()
            device.close()
            pdfstr = retstr.getvalue()
            retstr.close()
            
            if self.DEBUG:
                print "PDF to text conversion complete.")
        except:
            success = False
            pdfstr = ""
        
        return pdfstr,success
        
    def _scrubpdf(pdfstr,debug=False):
        
        #try:
        if True:
            if self.DEBUG:
                print "Starting PDF decode ..."
            
            if self.DEBUG:
                print "Scrubbing PDF Text ...")

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

            if self.DEBUG:
                print "Done Preprocessing PDF Text."

        #except:
        #    pdfstr = ""
        #    success = False

        return pdfstr,success

    def _parsename(fullname):
        #try:
        if True:
            parts = fullname.replace('.','').split(',')
            last = parts[0].strip()
            if parts[1].rsplit(' ',1)[0].strip() == "":
                first = parts[1].strip()
                middle = ""
            else:
                # take off middle
                first = parts[1][:-2].strip()
                middle = parts[1][-1:].strip()
        #except:
            # this happens when the name is something like "US MARCHAL" rather than a person's name
        #    first = ""
        #    middle = ""
        #    last = fullname
        
        return (first,middle,last)

    def _getinmatedata(self,pdfstr):
        #try:
        if True:
            if selg.DEBUG:
                print "Attemping to pull inmate names ..."
            success = True
            
            # pull lines from pdf
            for line in pdfstr.split('\n'):
                line = line.strip()
                if line != "":
                    lines.append(line)
                    
            # get inmate location indexes
            indexes = []
            for i in range(0,len(lines)):
                # see if it is a name in all caps
                if re.match("^[A-Z]*$", lines[i].replace(",","").replace(" ","").replace(".","").replace("-","")):
                    indexes.append(i)
            
            # package inmate names and data
            inmates = []
            for i in range(0,len(indexes)-1):
                inmatedata = []
                datarange = indexes[i+1]-indexes[i]
                for j in range(0,datarange):
                    inmatedata.append(lines[indexes[i]+j])
                inmates.append((lines[indexes[i]],inmatedata))
                
        except:
            success = False
            inmates = []
        
        if self.DEBUG:    
            print "Done pulling inmate names, pulled {0} inmates.".format(len(inmates))
            
        return inmates,success

    def _parsename(self,fullname):
        #try:
        if True:
            parts = fullname.replace('.','').split(',')
            last = parts[0].strip()
            if parts[1].rsplit(' ',1)[0].strip() == "":
                first = parts[1].strip()
                middle = ""
            else:
                # take off middle
                first = parts[1][:-2].strip()
                middle = parts[1][-1:].strip()
        #except:
        #    # this happens when the name is something like "US MARCHAL" rather than a person's name
        #    first = ""
        #    middle = ""
        #    last = fullname
        
        return (first,middle,last)

    def _parseinmates(rawinmates):
        
        if self.DEBUG:
            print "Attemping to parse inmate, custody, and booking data ..."
        
        inmatekeys = ['first','middle','last','mcid','sex','race','dob']
        
        #try:
        if True:
            success = True
            retdata = []
            for rawname,rawdata in rawinmates:
             
                if self.DEBUG:
                    print "Processing '{0}' ...".format(rawname)) 
                
                inmate = {}
                custody = {}
                bookings = []
    
                first,middle,last = self._parsename(rawname)
                inmate['first'] = first
                inmate['middle'] = middle
                inmate['last'] = last
                
                for data in rawdata:
                    if self.DEBUG:
                        print "[Inmate/Custody Info] Working on: '{0}'".format(data)
                    
                    if re.match('([0-9]{6}) [A-Z] [A-Z] ([0-9]{2})-([0-9]{2})-([0-9]{4})',data):
                        if self.DEBUG:
                            print "Inmate info match, procesing."
                        parts = data.split(' ')
                        inmate['mcid'] = parts[0]
                        inmate['sex'] = parts[1]
                        inmate['race'] = parts[2]
                        inmate['dob'] = datetime.datetime.strptime(parts[3],"%m-%d-%Y")
                        
                    elif re.match('[0-9]{2}-[0-9]{2}-[0-9]{4} [0-9]{4} [A-Z]{3}',data):
                        if self.DEBUG:
                            print "Custody info match, processing."
                        parts = data.split(' ')
                        dt = "{0} {1}".format(parts[0],parts[1])
                        custody['datetime'] = datetime.datetime.strptime(dt,"%m-%d-%Y %H%M")
                        custody['custodyclass'] = " ".join(parts[2:])
                    
                    # solution provided by https://github.com/Undeterminant - thanks!
                    elif all(key in inmate for key in inmatekeys)
                    
                        if self.DEBUG:
                            print "Inmate data populated, parsing bookings ..."
                        
                        booking = {}
                        for _data in rawdata:
                            
                            if self.DEBUG:
                                print "[Bookings] Working on: '{0}'".format(_data)
                            
                            if re.match('Book Dt:',_data):
                                if self.DEBUG:
                                    print "Found 'Book Dt.'"
                                _bookdatetime = _data.split(':')[1].strip()
                                booking['datetime'] = datetime.datetime.strptime(_bookdatetime,"%m/%d/%Y %H%M")
                            
                            elif re.match('Book Typ:',_data):
                                if self.DEBUG:
                                    print "Found 'Book Type'"
                                _bookingtype = _data.split(':')[1].strip()
                                booking['bookingtype'] = _bookingtype
                            
                            elif re.match('Cus Typ:',_data):
                                if self.DEBUG:
                                    print "Found Cus Typ"
                                _custodytype = _data.split(':')[1].strip()
                                booking['custodytype'] = _custodytype
                            
                            elif re.match('Bail:',_data):
                                if self.DEBUG:
                                    print "Found 'Bail'"
                                _bail = _data.split(':')[1].strip()
                                booking.['bail'] = _bail
                            
                            elif re.match('Bond:',_data):
                                if self.DEBUG:
                                    print "Found 'Bond'"
                                _bond = _data.split(':')[1].strip()
                                booking.['bond'] = _bond
                            
                            elif re.match('Court:',_data):
                                if self.DEBUG:
                                    print "Found 'Court'"
                                _court = _data.split(':')[1].strip()
                                booking['court'] = _court
                            
                            elif re.match('Exp Rel:',_data):
                                if self.DEBUG:
                                    print "Found 'Exp Rel'"
                                _expectedrelease = _data.split(':')[1].strip()
                                if _expectedrelease != "":
                                    booking['expectedrelease'] = datetime.datetime.strptime(_expectedrelease,"%m-%d-%Y")
                                else:
                                    booking['expectedrelease'] = None
                            
                            elif re.match('Judge:',_data):
                                if self.DEBUG:
                                    print "Found 'Judge'"
                                _judge = _data.split(':')[1].strip()
                                first,middle,last = self._parsename(_judge)
                                booking['judge'] = {'judge': _judge,
                                                    'first': first,
                                                     'middle': middle,
                                                     'last': last}
                            
                            elif re.match('Arr Agy:',_data):
                                if self.DEBUG:
                                    print "Found 'Arr Agy'"
                                _agency = _data.split(':')[1].strip()
                                booking.agency = __doagency(_agency)
                            
                            elif re.match('Arr Typ',_data):
                                if self.DEBUG:
                                    print "Found 'Arr Typ'"
                                _arresttype = _data.split(':')[1].strip()
                                booking['arresttype'] = _arresttype
                            
                            elif re.match('ROC:',_data):
                                if self.DEBUG:
                                    print "Found 'ROC'"
                                _roc = _data.split(':')[1].strip()
                                booking['roc'] = _roc
                            
                            elif re.match('Chg:',_data):
                                if self.DEBUG:
                                    print "Found 'Chg'"
                                _charge = _data.split(':')[1].strip()
                                booking['charge'] = _charge
                            
                            elif re.match('Indict:',_data):
                                if self.DEBUG:
                                    print "Found 'Indict'"
                                _indict = _data.split(':')[1].strip()
                                booking['indict'] = _indict
                            
                            elif re.match('Adj Dt:',_data):
                                if self.DEBUG:
                                    print "Found 'Adj Dt'"
                                _adjusteddate = _data.split(':')[1].strip() 
                                if _adjusteddate.strip() == "":
                                    booking['adjusteddate'] = None
                                else:
                                    booking['adjusteddate'] = datetime.datetime.strptime(_adjusteddate,"%m/%d/%Y")
                            
                            elif re.match('Term:',_data):
                                if self.DEBUG:
                                    print "Found 'Term'"
                                _term = _data.split(':')[1].strip()
                                _days = _term.split(' ')[0]
                                booking['term'] = _days
                            
                            # see if we have all of the data for one booking, and if we do then add it to the
                            # list of bookings, and reset our booking modle object
                            if booking.populated():
                               print "\tComplete Booking Found, adding to list."
                               bookings.append(booking)
                               booking = {} #BookingModel()
                               continue
                               
                        report("... Done processing bookings.")
                        break

                    # end of if
                    
                retdata.append({'inmate':inmate,
                                'custody':custody,
                                'bookings': bookings})
                
                if self.DEBUG:
                    print "\tDone working on '{0}'.".format(rawname)
                
        #except:
        #    success = False
        #    retdata = []
        
        if self.DEBUG:
            print"Done processing inmate, custody, and booking data."
            
        return retdata,success

    def processcensus(self):

        retdata = []

        filename,success = self._downloadpdf()
        if not success:
            return retdata,success

        pdfstr,success = self._convertpdf(filename)
        if not success:
            return retdata,success
        
        pdfstr,success = self._scrubpdf(pdfstr)
        if not success:
            return retdata,success
        
        inmatedata,success = self._getinmatedata(pdfstr)
        if not success:
            return retdata,success
        
        retdata,success = self._parseinmates(inmatedata)
        if not success:
            return retdata,success
        
        return retdata,success
        
if __name__ == '__main__':
 
    print "Loading Monroe County Jail Imate Census ..." 
 
    pdfprocessor = CensusProcessor()
     
    retdata,success = censusprocessor.processcensus()
    
    with open("inmates.json","w") as f:
        f.write(json.dumps(retdata))
        
    print "Exiting."