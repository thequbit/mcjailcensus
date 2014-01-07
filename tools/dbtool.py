from pymongo import MongoClient

class DatabaseTool(object):

    def __init__(self,uri='mongodb://localhost:27017/',DEBUG=False):
        
        self.DEBUG = DEBUG

        self.client = MongoClient(uri)
        self.db = self.client.mcjailcensus
        #self.inmates = db.inmates

        self.db.inmates.remove()

    def addmultiple(self,newdata):

        if self.DEBUG:
            print "Loading inmates ..."

        inmates = self.db.inmates

        for data in newdata:
            #inmates.find( {  } )
            insertid = inmates.insert(data)
            if self.DEBUG:
                print "Inserted '{0},{1}' as [{2}]".format(data['inmate']['last'],data['inmate']['first'],insertid)

        if self.DEBUG:
            print "All inmates loaded successfully."

    def searchinmates(self,first,last):

        if self.DEBUG:
            print "Searching for '{0},{1}' ...".format(last,first)
       
    def deletedb(self):
        if self.DEBUG:
            print "Deleting database contents."

        self.db.dropDatabase()

        if self.DEBUG:
            print "Done."
