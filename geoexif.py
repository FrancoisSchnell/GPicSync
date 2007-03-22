#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

###############################################################################
#  EXIF reader utility in relation to geolalisation
# (c) francois.schnell  francois.schnell@gmail.com
#                       http://francois.schnell.free.fr 
#  
# This script is released under the GPL license v2
#
# Integrated patch from Marc Nozell (http://nozell.com/blog):
# for multi-OS compatibility with exiftool (windows-linux) 
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
        print result
        if len(result)>1:
            latitude=float(result[0].split(":")[1])
            print "latitude= ",latitude
            return latitude
        else:
            return "None"
        
    def readLongitude(self):
        """read the longitude tag if available"""
        result=os.popen('%s -n -GPSLongitude -GPSLongitudeRef   "%s" ' % (self.exifcmd, self.picPath)).read().split("\n")
        print result
        if len(result)>1:
            longitude=float(result[0].split(":")[1])
            print "longitude= ",longitude
            return longitude
        else:
            return "None"
        
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
        
    def writeLatLong(self,lat,long,latRef,longRef):
        """Write both latitudeRef/latitude and longitudeRef/longitude in EXIF"""
        os.popen('%s -GPSLongitude=%s -GPSLatitude=%s \
        -GPSLongitudeRef=%s -GPSLatitudeRef=%s  "%s"'%(self.exifcmd, long,lat,longRef,latRef,self.picPath))

if __name__=="__main__":
    
    mypicture=GeoExif("test.jpg")
#    exif=mypicture.readExifAll()
#    mypicture.writeLongitude(7.222333)
#    mypicture.writeLatitude(48.419973)
    dateAndTime= mypicture.readDateTime()
#    mypicture.writeLatLong(7.222333,48.419973,"N","E")
    latitude=mypicture.readLatitude()
    longitude=mypicture.readLongitude()
    print "dateAndTime= ",dateAndTime
    print "latitude= ",latitude
    print "longitude= ",longitude
    print "EXIF= ", exif
