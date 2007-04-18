#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

###############################################################################
#  EXIF reader utility in relation to geolalisation
# This script is released under the GPL license v2
#
# francois.schnell (http://francois.schnell.free.fr)
#                        
# Thanks to Marc Nozell for testing GPicSync on Linux before I had the time to
# do it and for putting some specific Windows code behind a plateform check 
#(changing  "exiftool.exe" to  "exiftool" for Linux)
#  
# This script use the GPL exiftool.exe  app. see: 
# http://www.sno.phy.queensu.ca/%7Ephil/exiftool/
###############################################################################

import os,sys

class GeoExif(object):
    """
    A class to read and write few EXIF tags in .jpg pictures which can be 
    usefull for geolalisation scripts.
    """
    def __init__(self,picture):
        self.picPath=picture
        if sys.platform == 'win32':
            self.exifcmd = 'exiftool.exe'
        else:
            self.exifcmd = 'exiftool'
        
    def readExifAll(self):
        """read all exif tags and return a string of the result"""
        result=os.popen('%s "%s"' % (self.exifcmd, self.picPath)).read()
        return result
    
    def readDateTime(self):
        """
        Read the time and date when the picture was taken if available
        and return a list containing two strings [date,time]
        like  ['2007:02:12', '16:09:10']
        """
        #result=os.popen('exiftool.exe -CreateDate "%s"' % self.picPath).read()
        result=os.popen('%s -DateTimeOriginal "%s"' % (self.exifcmd, self.picPath)).read()
        timeDate= [result[34:44],result[45:53]]
        return timeDate
    
    def readLatitude(self):
        """read the latitute tag is available and return a float"""
        result=os.popen('%s -n -GPSLatitude -GPSLatitudeRef  "%s"  ' % (self.exifcmd, self.picPath)).read().split("\n")
        #print result
        if len(result)>1:
            latitude=float(result[0].split(":")[1])
            #print "latitude= ",latitude
            return latitude
        else:
            return "None"
        
    def readLongitude(self):
        """read the longitude tag if available"""
        result=os.popen('%s -n -GPSLongitude -GPSLongitudeRef   "%s" ' % (self.exifcmd, self.picPath)).read().split("\n")
        #print result
        if len(result)>1:
            longitude=float(result[0].split(":")[1])
            #print "longitude= ",longitude
            return longitude
        else:
            return "None"
    
    def readLatLong(self):
        """read latitude AND longitude at the same time"""
        result=os.popen('%s  -n -GPSLatitude -GPSLatitudeRef \
        -GPSLongitude -GPSLongitudeRef   "%s" ' \
        % (self.exifcmd, self.picPath)).read().split("\n")
        if len(result)>=4:
            result[0]=result[0].split(":")[1].strip()
            latDecimal=result[0].split(".")[1][0:6]
            result[0]=result[0].split(".")[0]+"."+latDecimal
            result[1]=result[1].split(":")[1].strip()
            result[2]=result[2].split(":")[1].strip()
            longDecimal=result[2].split(".")[1][0:6]
            result[2]=result[2].split(".")[0]+"."+longDecimal
            result[3]=result[3].split(":")[1].strip()
            latlong= result[1]+result[0]+" "+result[3]+result[2]
        else:
            latlong=None
        print latlong
        return latlong

    def writeLatitude(self,lat):
        """
        write the latitude value given in argument in the EXIF
        positive means nothern latitudes
        nagative means southest latitudes
        lat can be a float or a string
        """
         
        #os.popen('exiftool.exe -GPSAltitudeRef=0 -GPSAltitude=100 '+ self.picPath)
        if float(lat) >= 0:
            os.popen('%s -GPSLatitudeRef="N" "%s" '% (self.exifcmd, self.picPath))
        else:
            os.popen('%s -GPSLatitudeRef="S" "%s" '% (self.exifcmd, self.picPath))    
        os.popen('%s  -GPSLatitude=%s "%s"'%(self.exifcmd, lat,self.picPath))
        
    def writeLongitude(self,long):
        """
        write the longitude value given in argument in the EXIF
        positive means Eastern longitudes
        nagative means Western latitudes
        long can be a float or a string
        """
        if float(long) >= 0:
            os.popen('%s -GPSLongitudeRef="E" "%s"' % (self.exifcmd, self.picPath))
        else:
            os.popen('%s -GPSLongitudeRef="W" "%s"' % (self.exifcmd, self.picPath))
        os.popen('%s -GPSLongitude=%s  "%s" '% (self.exifcmd, long,self.picPath))
        
    def writeLatLong(self,lat,long,latRef,longRef,backup):
        """Write both latitudeRef/latitude and longitudeRef/longitude in EXIF"""
        if float(long)<0:long=str(abs(float(long)))
        if float(lat)<0:lat=str(abs(float(lat)))
        if backup==True:
            os.popen('%s -n -GPSLongitude=%s -GPSLatitude=%s \
            -GPSLongitudeRef=%s -GPSLatitudeRef=%s  -GPSAltitude=0.0 -GPSAltitudeRef=0 "%s"'%(self.exifcmd, long,lat,longRef,latRef,self.picPath))
        else:
            os.popen('%s -overwrite_original -n -GPSLongitude=%s -GPSLatitude=%s \
            -GPSLongitudeRef=%s -GPSLatitudeRef=%s  "%s"'%(self.exifcmd, long,lat,longRef,latRef,self.picPath))
            
if __name__=="__main__":
    
    mypicture=GeoExif("test.jpg")
#    exif=mypicture.readExifAll()
#    mypicture.writeLongitude(7.222333)
#    mypicture.writeLatitude(48.419973)
    dateAndTime= mypicture.readDateTime()
    mypicture.writeLatLong(7.222333,48.419973,"N","E",True)
    latitude=mypicture.readLatitude()
    longitude=mypicture.readLongitude()
    #print "dateAndTime= ",dateAndTime
    #print "latitude= ",latitude
    #print "longitude= ",longitude
    #print "EXIF= ", exif
    print mypicture.readLatLong()
