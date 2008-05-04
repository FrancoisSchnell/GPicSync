#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

###############################################################################
#  EXIF reader utility in relation to geolalisation
# This script is released under the GPL license v2
#
# francois.schnell (http://francois.schnell.free.fr)
#                        
# Contributors, see: http://code.google.com/p/gpicsync/wiki/Contributions
#
# This script is released under the GPL license version 2 license
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
        self.xmpOption=False
        if self.xmpOption==True:
            if os.path.basename(picture).find(".CRW")>0\
            or os.path.basename(picture).find(".CR2")>0:
                self.sidecarFile = os.path.splitext(picture)[0]+".xmp"
                #print ">>>>> self.sidecarFile",self.sidecarFile
            else:
                self.sidecarFile = ''
        if sys.platform == 'win32':
            self.exifcmd = 'exiftool.exe'
        else:
            self.exifcmd = 'exiftool'
        
    def readExifAll(self):
        """read all exif tags and return a string of the result"""
        result=os.popen('%s -n "%s"' % (self.exifcmd, self.picPath)).read()
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
    
    def readDateTimeSize(self):
        """
        Read the time / date when the picture was taken (if available)
        plus the size of the picture
        Returns a list containing strings[date,time,width,height]
        like  ['2007:02:12', '16:09:10','800','600']
        """
        answer=os.popen('%s -DateTimeOriginal -ImageSize "%s"' % (self.exifcmd, self.picPath)).read()
        print "readDateTimeSize answer", answer
        if "Date" in answer:
            date=answer[34:44]
            time=answer[45:53]
        else:
            date,time="nodate","notime"
        #timeDate= [answer[34:44],answer[45:53]]
        try:
            size=answer.split("Image Size")[1].split(":")[1].strip().split("x")
            width=size[0]
            height=size[1]
        except:
            width=640
            height=480
        return [date,time,width,height]
    
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
        print result
        if len(result)>=4:
            result[0]=result[0].split(":")[1].strip()
            try:
                latDecimal=result[0].split(".")[1][0:]
            except:
                latDecimal="0"
            result[0]=result[0].split(".")[0]+"."+latDecimal
            result[1]=result[1].split(":")[1].strip()
            result[2]=result[2].split(":")[1].strip()
            try:
                longDecimal=result[2].split(".")[1][0:]
            except:
                longDecimal="0"
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
        option=''
        if self.xmpOption==True:
            if(self.sidecarFile != ""):
                option = option + " -o '"+self.sidecarFile+"'"
        #os.popen('exiftool.exe -GPSAltitudeRef=0 -GPSAltitude=100 '+ self.picPath)
        if float(lat) >= 0:
            os.popen('%s -m -GPSLatitudeRef="N" %s "%s" '% (self.exifcmd, option, self.picPath))
        else:
            os.popen('%s -m -GPSLatitudeRef="S" %s "%s" '% (self.exifcmd, option, self.picPath))    
        os.popen('%s  -m -GPSLatitude=%s "%s"'%(self.exifcmd, lat,self.picPath))
        
    def writeLongitude(self,long):
        """
        write the longitude value given in argument in the EXIF
        positive means Eastern longitudes
        nagative means Western latitudes
        long can be a float or a string
        """
        option=''
        if self.xmpOption==True:
            if(self.sidecarFile != ""):
                option = option + " -o '"+self.sidecarFile+"'"
        if float(long) >= 0:
            os.popen('%s -m -GPSLongitudeRef="E" %s "%s"' % (self.exifcmd, option, self.picPath))
        else:
            os.popen('%s -m -GPSLongitudeRef="W" %s "%s"' % (self.exifcmd, option, self.picPath))
        os.popen('%s -m -GPSLongitude=%s  "%s" '% (self.exifcmd, long,self.picPath))
        
    def writeLatLong(self,lat,long,latRef,longRef,backup,elevation="None"):
        """Write both latitudeRef/latitude and longitudeRef/longitude in EXIF"""
        option='"-DateTimeOriginal>FileModifyDate"'
        if self.xmpOption==True:
            if(self.sidecarFile != ""):
                option = option + " -o '"+self.sidecarFile+"'"
                #print "option: ,option
        if float(long)<0:long=str(abs(float(long)))
        if float(lat)<0:lat=str(abs(float(lat)))
        altRef=0 #"Above Sea Level"
        
        if elevation!="None":
            if float(elevation)<0: 
                altRef=1 #"Below Sea Level"
                elevation=str(abs(float(elevation)))
        #print ">>> altRef=",altRef
        #print ">>> elevation ", elevation
            
        if backup==True:
            if elevation=="None":
                os.popen('%s -n -m -GPSLongitude=%s -GPSLatitude=%s \
                -GPSLongitudeRef=%s -GPSLatitudeRef=%s  %s "%s" '\
                %(self.exifcmd, long,lat,longRef,latRef,option,self.picPath))
            else:
                os.popen('%s -n -m -GPSLongitude=%s -GPSLatitude=%s -GPSLongitudeRef=%s \
                -GPSLatitudeRef=%s  -GPSAltitudeRef=%s -GPSAltitude=%s %s "%s" '\
                %(self.exifcmd, long,lat,longRef,latRef,altRef,elevation,option,self.picPath))
        else:
            if elevation=="None":
                os.popen('%s -m -overwrite_original -n -GPSLongitude=%s -GPSLatitude=%s \
                -GPSLongitudeRef=%s -GPSLatitudeRef=%s  %s "%s" '\
                %(self.exifcmd, long,lat,longRef,latRef,option, self.picPath))
            else:
                os.popen('%s -m -overwrite_original -n -GPSLongitude=%s -GPSLatitude=%s \
                -GPSLongitudeRef=%s -GPSLatitudeRef=%s -GPSAltitudeRef=%s -GPSAltitude=%s %s "%s"'\
                %(self.exifcmd, long,lat,longRef,latRef,altRef,elevation,option,self.picPath))
            
if __name__=="__main__":
    
    mypicture=GeoExif("test.jpg")
#    exif=mypicture.readExifAll()
#    mypicture.writeLongitude(7.222333)
#    mypicture.writeLatitude(48.419973)
    print  mypicture.readDateTimeSize()
    #mypicture.writeLatLong(7.222333,48.419973,"N","E",True)
    #latitude=mypicture.readLatitude()
    #longitude=mypicture.readLongitude()
    #print "dateAndTime= ",dateAndTime
    #print "latitude= ",latitude
    #print "longitude= ",longitude
    #print "EXIF= ", exif
    #print mypicture.readLatLong()
