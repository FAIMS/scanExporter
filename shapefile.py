'''
Python:
    accept epsg as argument

    copy into new DB
    create structure for 3nf
    add geometry columns
    Call Ruby:
        Write responses into 3nf
    write geometries into 3nf tables

    call shapefile tool


    TODO:
        convert ruby calls into rbenv or system ruby calls
        figure out how shell script wrapper needs to work for exporter


'''

import unicodedata
import sqlite3
import csv, codecs, cStringIO
from xml.dom import minidom
import sys
import pprint
import glob
import json
import os
import shutil
import re
import zipfile
import subprocess
import glob
import tempfile
import errno
import imghdr
import bz2
import tarfile
import codecs
import lsb_release

from collections import defaultdict
import zipfile
try:
    import zlib
    compression = zipfile.ZIP_DEFLATED
except:
    compression = zipfile.ZIP_STORED

modes = { zipfile.ZIP_DEFLATED: 'deflated',
          zipfile.ZIP_STORED:   'stored',
          }



if lsb_release.get_lsb_information()['RELEASE'] == '16.04':
    LIBSPATIALITE = 'mod_spatialite.so'
else:
    LIBSPATIALITE = 'libspatialite.so.5'



print sys.argv

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def convertBuffer(self, obj):

        #print type(obj)        
        
        if isinstance(obj, basestring):         
            #print obj.encode("utf-8", errors="replace")
            return obj.encode("utf-8", errors="replace").replace('"',"''")
        if isinstance(obj, buffer):         
            bufferCon = sqlite3.connect(':memory:')
            bufferCon.enable_load_extension(True)
            bufferCon.load_extension(LIBSPATIALITE)
            foo = bufferCon.execute("select astext(?);", ([obj])).fetchone()            
            return foo[0]
        if obj == None:
            return ""
        return obj



    def writerow(self, row):
        self.writer.writerow(['"%s"' % self.convertBuffer(s) for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data.replace('"""','"').replace('"None"',''))
        # empty queue
        self.queue.truncate(0)
        self.stream.flush()

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
        


    



def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def upper_repl(match):
    if (match.group(1) == None):
        return "_"
    return "_"+match.group(1)

def clean(str):
     out = re.sub(" ([a-z])|[^A-Za-z0-9]+", upper_repl, str)     
     return out

def cleanWithUnder(str):
     out = re.sub("[^a-zA-Z0-9]+", "_", str)     
     return out  

def makeSurePathExists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


originalDir = sys.argv[1]
exportDir = tempfile.mkdtemp()+"/"
finalExportDir = sys.argv[2]+"/"

options = {"Rotation":"90"}
with open(sys.argv[3]) as json_file:
    options = json.load(json_file)


importDB = originalDir+"db.sqlite3"
exportDB = exportDir+"shape.sqlite3"
jsondata = json.load(open(originalDir+'module.settings'))
srid = jsondata['srid']
arch16nFiles=[]
for file in glob.glob(originalDir+"*.properties"):
    arch16nFiles.append(file)

arch16nFile = next((s for s in arch16nFiles if '.0.' in s), arch16nFiles[0])
# print jsondata
moduleName = clean(jsondata['name'])
fileNameType = "Identifier" #Original, Unchanged, Identifier

images = None
#try:
#    foo= json.load(open(sys.argv[3],"r"))
#    # print foo["Export Images and Files?"]
#    if (foo["Export Images and Files?"] != []):
#        images = True
#    else:
#        images = False
#except:
#    sys.stderr.write("Json input failed")
#    images = True

#print "Exporting Images %s" % (images)

def zipdir(path, zip):
    for root, dirs, files in os.walk(path):
        for file in files:
            zip.write(os.path.join(root, file))


try:
    os.remove(exportDB)
except OSError:
    pass

importCon = sqlite3.connect(importDB)
importCon.enable_load_extension(True)
importCon.load_extension(LIBSPATIALITE)
exportCon = sqlite3.connect(exportDB)
exportCon.enable_load_extension(True)
exportCon.load_extension(LIBSPATIALITE)


exportCon.execute("select initSpatialMetaData(1)")
'''
for line in importCon.iterdump():
    try:
        exportCon.execute(line)
    except sqlite3.Error:       
        pass
'''     
            
exifCon = sqlite3.connect(exportDB)
exifCon.row_factory = dict_factory
exportCon.enable_load_extension(True)
exportCon.load_extension(LIBSPATIALITE)


  
exportCon.execute("create table keyval (key text, val text);")

f = open(arch16nFile, 'r')
for line in f:
    if "=" in line:
        keyval = line.replace("\n","").replace("\r","").decode("utf-8").split('=',1)
        keyval[0] = '{'+keyval[0]+'}'
        exportCon.execute("replace into keyval(key, val) VALUES(?, ?)", keyval)
f.close()







for aenttypeid, aenttypename in importCon.execute("select aenttypeid, aenttypename from aenttype"): 
    aenttypename = clean(aenttypename)
    attributes = ['identifier', 'createdBy', 'createdAtGMT', 'modifiedBy', 'modifiedAtGMT']
    for attr in importCon.execute("select distinct attributename from attributekey join idealaent using (attributeid) where aenttypeid = ? group by attributename order by aentcountorder", [aenttypeid]):
        attrToInsert = clean(attr[0])
        if attrToInsert not in attributes:
            attributes.append(attrToInsert)
    attribList = " TEXT, \n\t".join(attributes)
    createStmt = "Create table if not exists %s (\n\tuuid TEXT PRIMARY KEY,\n\t%s TEXT);" % (aenttypename, attribList)

    exportCon.execute(createStmt)

geometryColumns = []
for row in importCon.execute("select aenttypename, geometrytype(geometryn(geospatialcolumn,1)) as geomtype, count(distinct geometrytype(geometryn(geospatialcolumn,1))) from latestnondeletedarchent join aenttype using (aenttypeid) where geomtype is not null group by aenttypename having  count(distinct geometrytype(geometryn(geospatialcolumn,1))) = 1"):
    geometryColumns.append(row[0])
    geocolumn = "select addGeometryColumn('%s', 'geospatialcolumn', %s, '%s', 'XY');" %(clean(row[0]),srid,row[1]);
    
    exportCon.execute(geocolumn)





for aenttypename, uuid, createdAt, createdBy, modifiedAt, modifiedBy,geometry in importCon.execute("select aenttypename, uuid, createdAt || ' GMT', createdBy, datetime(modifiedAt) || ' GMT', modifiedBy, geometryn(transform(geospatialcolumn,casttointeger(%s)),1) from latestnondeletedarchent join aenttype using (aenttypeid) join createdModifiedAtBy using (uuid) order by createdAt" % (srid)):
    
    if (aenttypename in geometryColumns):       
        insert = "insert into %s (uuid, createdAtGMT, createdBy, modifiedAtGMT, modifiedBy, geospatialcolumn) VALUES(?, ?, ?, ?, ?, ?)" % (clean(aenttypename))
        exportCon.execute(insert, [str(uuid), createdAt, createdBy, modifiedAt, modifiedBy, geometry])
    else:
        insert = "insert into %s (uuid, createdAtGMT, createdBy, modifiedAtGMT, modifiedBy) VALUES(?, ?, ?, ?, ?)" % (clean(aenttypename))
        exportCon.execute(insert, [str(uuid), createdAt, createdBy, modifiedAt, modifiedBy])



try:
    os.remove(exportDir+'shape.out')
except OSError:
    pass


subprocess.call(["bash", "./format.sh", originalDir, exportDir, exportDir])



updateArray = []

for line in codecs.open(exportDir+'shape.out', 'r', encoding='utf-8').readlines():  
    out = line.replace("\n","").replace("\\r","").split("\t")
    #print "!!%s -- %s!!" %(line, out)
    if (len(out) ==4):      
        update = "update %s set %s = ? where uuid = %s;" % (clean(out[1]), clean(out[2]), out[0])
        data = (unicode(out[3].replace("\\n","\n").replace("'","''")),)
        # print update, data
        exportCon.execute(update, data)




exportCon.commit()
files = [exportDir+'shape.sqlite3']



for directory in importCon.execute("select distinct aenttypename, attributename from latestnondeletedaentvalue join attributekey using (attributeid) join latestnondeletedarchent using (uuid) join aenttype using (aenttypeid) where attributeisfile is not null and measure is not null"):
   makeSurePathExists("%s/%s/%s" % (exportDir,clean(directory[0]), clean(directory[1])))
 
filehash = defaultdict(int)
 
 
 

for directory in importCon.execute("select distinct aenttypename, attributename from latestnondeletedaentvalue join attributekey using (attributeid) join latestnondeletedarchent using (uuid) join aenttype using (aenttypeid) where attributeisfile is not null and measure is not null"):
   makeSurePathExists("%s/%s/%s" % (exportDir,clean(directory[0]), clean(directory[1])))
 
filehash = defaultdict(int)
 
exportPhotos = []
realExportList = {}

#print "* UUIDs exported:"
for filename in importCon.execute("""
select uuid, measure, freetext, certainty, attributename, aenttypename, substr(measure,48) as sortname
  from latestnondeletedaentvalue 
  join attributekey using (attributeid) 
  join latestnondeletedarchent using (uuid) 
  join aenttype using (aenttypeid) 
  join idealaent using (aenttypeid, attributeid) 
 where attributeisfile is not null and measure is not null
 order by sortname;                                  
                                  """):
    try:        
        oldPath = filename[1].split("/")
        oldFilename = oldPath[2]
        aenttypename = clean(filename[5])
        attributename = clean(filename[4])
        newFilename = "%s/%s/%s" % (aenttypename, attributename, oldFilename)
        if os.path.isfile(originalDir+filename[1]):
            if (fileNameType == "Identifier"):
                #print filename[0], 
                
                filehash["%s%s" % (filename[0], attributename)] += 1
                

                foo = exportCon.execute("select identifier from %s where uuid = %s" % (aenttypename, filename[0]))
                identifier=cleanWithUnder(foo.fetchone()[0])

                r= re.search("(\.[^.]*)$",oldFilename)

                delimiter = ""
                
                if filename[2]:
                    delimiter = "a"

                newFilename =  "%s/%s/%s/%s_%s%s%s" % (aenttypename, attributename, identifier, identifier, filehash["%s%s" % (filename[0], attributename)],delimiter, r.group(0))
                makeSurePathExists("%s/%s/%s/%s" % (exportDir, clean(directory[0]), clean(directory[1]), identifier))


            exifdata = exifCon.execute("select * from %s where uuid = %s" % (aenttypename, filename[0])).fetchone()
            iddata = [] 
            for id in importCon.execute("select coalesce(measure, vocabname, freetext) from latestnondeletedarchentidentifiers where uuid = %s union select aenttypename from latestnondeletedarchent join aenttype using (aenttypeid) where uuid = %s" % (filename[0], filename[0])):
                iddata.append(id[0])


            shutil.copyfile(originalDir+filename[1], exportDir+newFilename)

            mergedata = exifdata.copy()
            mergedata.update(jsondata)
            mergedata.pop("geospatialcolumn", None)
            exifjson = {"SourceFile":exportDir+newFilename, 
                        "UserComment": [json.dumps(mergedata)], 
                        "ImageDescription": exifdata['identifier'], 
                        "XPSubject": "Annotation: %s" % (filename[2]),
                        "Keywords": iddata,
                        "Artist": exifdata['createdBy'],
                        "XPAuthor": exifdata['createdBy'],
                        "Software": "FAIMS Project",
                        "ImageID": exifdata['uuid'],
                        "Copyright": jsondata['name']


                        }
            with open(exportDir+newFilename+".json", "w") as outfile:
                json.dump(exifjson, outfile)    

            if imghdr.what(exportDir+newFilename):
                
                subprocess.call(["exiftool", "-m", "-q", "-sep", "\"; \"", "-overwrite_original", "-j=%s" % (exportDir+newFilename+".json"), exportDir+newFilename])

            #exportPhotos.append((clean(aenttypename), attributename, newFilename, filename[0]))
            #print "    * %s" % (newFilename)
            #files.append(exportDir+newFilename+".json")
            #files.append(exportDir+newFilename)
        else:
            print "<b>Unable to find file %s, from uuid: %s" % (originalDir+filename[1], filename[0]) 
    except:
            print "<b>Unable to find file (exception thrown) %s, from uuid: %s" % (originalDir+filename[1], filename[0])    


exportAttributes = {}
for aenttypename, attributename, newFilename, uuid in exportPhotos:
    if aenttypename not in realExportList:
        realExportList[aenttypename] = {}
        exportAttributes[aenttypename] = attributename
    if uuid not in realExportList[aenttypename]:
        realExportList[aenttypename][uuid] = []

    #realExportList[aenttypename][uuid].append(newFilename)

#print "    ",realExportList


for aenttypename in realExportList:

    for uuid in realExportList[aenttypename]:
        exportCon.execute("update %s set %s = ? where uuid = ?" % (aenttypename, exportAttributes[aenttypename]), (', '.join(realExportList[aenttypename][uuid]), uuid))
exportCon.commit()




    # check input flag as to what filename to export




for row in importCon.execute("select aenttypename, geometrytype(geometryn(geospatialcolumn,1)) as geomtype, count(distinct geometrytype(geometryn(geospatialcolumn,1))) from latestnondeletedarchent join aenttype using (aenttypeid) where geomtype is not null group by aenttypename having  count(distinct geometrytype(geometryn(geospatialcolumn,1))) = 1"):
    cmd = ["spatialite_tool", "-e", "-shp", "%s" % (clean(row[0]).decode("ascii")), "-d", "%sshape.sqlite3" % (exportDir), "-t", "%s" % (clean(row[0])), "-c", "utf-8", "-g", "geospatialcolumn", "-s", "%s" % (srid), "--type", "%s" % (row[1])]
    files.append(exportDir+"%s.dbf" % (clean(row[0])))
    files.append(exportDir+"%s.shp" % (clean(row[0])))
    files.append(exportDir+"%s.shx" % (clean(row[0])))
    # print cmd
    subprocess.call(cmd, cwd=exportDir)

for at in importCon.execute("select aenttypename from aenttype"):
    aenttypename = "%s" % (clean(at[0]))


    cursor = exportCon.cursor()
    try:
        cursor.execute("select * from %s" % (aenttypename)) 
    except:
        cursor.execute("select * from %s" % (aenttypename))     


    files.append(exportDir+"Entity-%s.csv" % (aenttypename))

    csv_writer = UnicodeWriter(open(exportDir+"Entity-%s.csv" % (aenttypename), "wb+"))
    csv_writer.writerow([i[0] for i in cursor.description]) # write headers
    csv_writer.writerows(cursor)

    #spatialite_tool -e -shp surveyUnitTransectBuffer -d db.sqlite3 -t surveyUnitWithTransectBuffer -c utf-8 -g surveyBuffer --type polygon



relntypequery = '''select distinct relntypeid, relntypename from relntype left outer join latestnondeletedrelationship using (relntypeid);'''

relnquery = '''select distinct parent.uuid as parentuuid, child.uuid as childuuid, parent.participatesverb
                 from latestnondeletedaentreln parent 
                 join latestnondeletedaentreln child using (relationshipid)
                 join relationship using (relationshipid)
                 join relntype using (relntypeid)
                where parent.uuid != child.uuid
                  and relntypename = ?'''


relntypecursor = importCon.cursor()
relncursor = importCon.cursor()
for relntypeid, relntypename in relntypecursor.execute(relntypequery): 
    relncursor.execute(relnquery, [relntypename])
    #print relntypenaprintme

    exportCon.execute("CREATE TABLE %s (parentuuid TEXT, childuuid TEXT, participatesverb TEXT);" % (clean(relntypename)))
    for i in relncursor:
        exportCon.execute("INSERT INTO %s VALUES(?,?,?)" % (clean(relntypename)), i)
    csv_writer = UnicodeWriter(open(exportDir+"Relationship-%s.csv" % (clean(relntypename)), "wb+"))
    csv_writer.writerow([i[0] for i in relncursor.description]) # write headers
    csv_writer.writerows(relncursor)


for aenttypeid, aenttypename in importCon.execute("select aenttypeid, aenttypename from aenttype"): 
    aenttypename = clean(aenttypename)
    attributes = [u'identifier', u'createdBy', u'createdAtGMT', u'modifiedBy', u'modifiedAtGMT', 'uuid']


    cursor = exifCon.cursor()
    attrHeader = [u'Identifier', u'Created By', u'Created At (GMT)', u'Modified By', u'Modified At (GMT)', 'uuid']
    for attr in importCon.execute(u"select distinct attributename from attributekey join idealaent using (attributeid) where aenttypeid = ? group by attributename order by aentcountorder", [aenttypeid]):

        attrToInsert = clean(attr[0])
        if attrToInsert not in attributes:
            attributes.append(attrToInsert)
            attrHeader.append(attr[0])


    #print "select %s from %s" % (', '.join(attributes), aenttypename)
    
    for line in cursor.execute("select %s from %s" % (', '.join(attributes).encode('utf-8'), aenttypename)):




        metadata = """
InfoKey: Subject
InfoValue: wibble
""" 

        meta = codecs.open("%s/%s.info"% (exportDir,clean(line['identifier'])), "w", "utf-8")  
        meta.write(metadata)
        meta.close()

        f = codecs.open("%s/%s.md" % (exportDir,clean(line['identifier'])), "w", "utf-8")  
        photofiles =""


        for num,key in enumerate(attrHeader):
        
            if key == "Identifier":
                prefix = u"# "
            else:
                prefix = u"* "
            if key != "uuid":
                writeline = u"%s%s: %s\n" % (prefix, key, line[attributes[num]])
            else:
                uuid=line[attributes[num]]            
            f.write(writeline)
            if key == "Identifier":
                f.write("\n")


        f.close()
        
        try:
            output= subprocess.check_output(["bash", "./stitchPDF.sh", originalDir, exportDir, clean(line['identifier']), options['Rotation']], stderr=subprocess.STDOUT)
            print output
        except Exception as e:
            print e, e.output



files = files + glob.glob("%s/pdf/*/*" % (exportDir))


tarf = tarfile.open("%s/%s-export.tar.bz2" % (finalExportDir,moduleName), 'w:bz2')
try:
    for file in files:
        tarf.add(file, arcname=moduleName+'/'+file.replace('//','/').replace(exportDir,''))
        
finally:
    tarf.close()


try:
    os.remove(exportDir)
except OSError:
    pass
