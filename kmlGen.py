
###############################################################################
#
# (c) francois.schnell  francois.schnell@gmail.com
#                       http://francois.schnell.free.fr  
#
# This script is released under the GPL v2 license
#
###############################################################################

import time
from thread import start_new_thread

from geoexif import *
from gpx import *
        
class KML(object):
    """
    A quick and dirty kml generator in progress for gpicsync
    (for live viewing in Google Earth)
    """
    
    def __init__(self,fileName,name,url="",timeStampOrder=False,utc="0",eleMode=0,iconsStyle=0,gmaps=False):
        self.f=open(fileName+".kml","wb")
        self.url=url
        self.timeStampOrder=timeStampOrder
        self.eleMode=eleMode # Elevation mode
        self.iconsStyle=iconsStyle
        gmaps=gmaps
        #self.utcOffest=utc
        if float(utc)>=0: sign="+"
        if float(utc)<0: sign="-"
        self.utcOffset=sign+str(abs(int(float(utc))))+":00"
        print ">>> self.utcOffest in kml for time stamps: ", self.utcOffset
        
        #check if GM URL finishes with "/" and add it if necessary
        if self.url != "":
            if url[-1:]!="/":
                self.url=self.url+"/"
        
        kmlHead_p1=u"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.1">
<Document>
<name>"""+unicode(name)+"""</name>"""

        if (self.iconsStyle==0) and (gmaps==False):
            kmlHead_p2=u"""
<Style id="hoverIcon0">
<IconStyle>
<scale>5.0</scale>
</IconStyle>
</Style>
<Style id="defaultIcon0">
<LabelStyle>
<scale>0</scale>
</LabelStyle>
<IconStyle>
<scale>1.0</scale>
</IconStyle>
</Style>
<StyleMap id="defaultStyle1">
<Pair>
<key>normal</key>
<styleUrl>#defaultIcon0</styleUrl>
</Pair>
<Pair>
<key>highlight</key>
<styleUrl>#hoverIcon0</styleUrl>
</Pair>
</StyleMap>"""
        else: kmlHead_p2=u""

        kmlHead_p3=u"""
<Style id="lineStyle">
<PolyStyle>
<color>3feeee17</color>
</PolyStyle>
<LineStyle>
<color>99eeee17</color>
<width>6</width>
</LineStyle>
</Style>
<Style id="camera">
<scale>1.1</scale>
<IconStyle>
<color>ffffffff</color>
<Icon>
<href>http://maps.google.com/mapfiles/kml/pal4/icon38.png</href>
<x>192</x>
<y>96</y>
<w>32</w>
<h>32</h>
</Icon>
<hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
</IconStyle>
</Style>
"""
#<href>root://icons/palette-4.png</href>

        #self.f.write(kmlHead_p1+kmlHead_p2+kmlHead_p3)
        kmlHead=kmlHead_p1+kmlHead_p2+kmlHead_p3
        self.f.write(kmlHead.encode("utf-8"))
        
    def writeInKml(self,text):
        """
        Print the given string in the kml file
        """
        #self.f.write(text)
        self.f.write(text.encode("utf-8"))

    def footerPlacemark(self,picName,type="GE"):
        """
        Returning a footer to the description of a placemark
        """

        pmDescriptionFooter=""
        mediaFile=picName.split(".")[0]
        
        for ext in [".mp3",".wma",".ogg",".wav"]:
            if os.path.exists(mediaFile+ext):
                print "Found mediaFile= ",repr(mediaFile+ext)
                if type=="GE":
                    pmDescriptionFooter=u"<br><br><a href='"+\
                    mediaFile+ext+"'>Play Audio</a>"
                elif type=="GM":
                    pmDescriptionFooter=u"<br><br><a href='"+\
                    self.url+os.path.basename(picName.split(".")[0])+ext+"'>Play Audio</a>"
                
        for ext in [".wmv",".mov",".avi"]:
            if os.path.exists(mediaFile+ext):
                print "Found mediaFile= ",repr(mediaFile+ext)
                if type=="GE":
                    pmDescriptionFooter=u"<br><br><a href='"+\
                    mediaFile+ext+"'>Play Video</a>"
                elif type=="GM":
                    pmDescriptionFooter=u"<br><br><a href='"+\
                    self.url+os.path.basename(picName.split(".")[0])+ext+"'>Play Video</a>"
                    
        if os.path.exists(mediaFile+".txt"):
            print "Found .txt file to add= ",repr(mediaFile)+".txt"
            fileHandle = open (mediaFile+".txt")
            pmDescriptionFooter=pmDescriptionFooter+u"<br><br>"+fileHandle.read()
            fileHandle.close() 
        
        return pmDescriptionFooter
            
    def placemark(self,picName="",lat="",long="",ele="",width="800",height="600",
                  timeStamp="",elevation=""):
        """
        Creates a placemark tag for the given picture in the kml file.
        If only a picture path is given in argument, latitude and longitude will
        be searched in the picture EXIF.
        It's also possible to give the values in argument
        (a string representing decimal degress, - sign ok)
        """
        
        if elevation=="" or elevation=="None": elevation="0"
        if self.timeStampOrder==True:
            timeStamp1=u"<TimeStamp><when>"+timeStamp+self.utcOffset+"</when> </TimeStamp>\n"
            timeStamp2=u"<TimeSpan><begin>"+timeStamp+self.utcOffset+"</begin></TimeSpan>\n"
            timeStamp=timeStamp1
        else:
            timeStamp=""
        
        print "timeStamp=",timeStamp
        w=float(width)
        h=float(height)
                
        if width>height:
            print "width > height"
            width=(600./w)*w
            height=(600./w)*h
        
        if height>width:
            print "height  > width"
            height=(400./h)*h
            width=(400./h)*w
        
        width=str(int(width))
        height=str(int(height))
                    
        if lat and long == "":
            mypicture=GeoExif(picName)
            lat=mypicture.readLatitude()
            long=mypicture.readLongitude()
        
        pmHead=u"\n\n<Placemark>\n<name>"+\
        os.path.basename(picName)+"</name>\n"
        
        if self.eleMode==1 or self.eleMode==2:
            eleAdd=u"\n<altitudeMode>absolute</altitudeMode>"
        else: eleAdd=""
            
        if self.iconsStyle==1:
            iconLook=u"<styleUrl>#camera</styleUrl>"
        elif self.iconsStyle==0: 
            iconLook=u"<styleUrl>#defaultStyle1</styleUrl><Style><IconStyle><Icon><href>thumbs/thumb_"+\
            os.path.basename(picName)+"</href></Icon></IconStyle></Style>"\

        #Adding a footer to the description
        pmDescriptionFooter=self.footerPlacemark(picName,type="GE")
        
        pmDescription=u"<description><![CDATA["+\
        "<img src='"+self.url+os.path.basename(picName)+"' width='"+width+"' height='"+height+"'/>"+\
        pmDescriptionFooter+\
        "]]>\n</description>\n"+iconLook+\
        "\n<Point>"+eleAdd+\
        "\n<coordinates>"+str(long)+","+str(lat)+","+elevation+\
        "</coordinates>\n</Point>\n"+timeStamp
        
        pmTail=u"</Placemark>"
        
        #self.f.write(pmHead)
        #self.f.write(pmDescription)
        #self.f.write(pmTail)
        pm=pmHead+pmDescription+pmTail
        self.f.write(pm.encode("utf-8"))
        
    def placemark4Gmaps(self,picName="",lat="",long="",width="400",height="300",elevation=""):
        """
        The same as placemark but with special values and features for G maps.
        Creates a placemark tag for the given picture in the kml file.
        If only a picture path is given in argument, latitude and longitude will
        be searched in the picture EXIF.
        It's also possible to give the values in argument
        (a string representing decimal degress, - sign ok)
        """
        w=float(width)
        h=float(height)
        if width>height:
            print "width > height"
            width=(200./w)*w
            height=(200./w)*h
        if height>width:
            print "height  > width"
            height=(200./h)*h
            width=(200./h)*w
        width=str(int(width))
        height=str(int(height))
        if lat and long == "":
            mypicture=GeoExif(picName)
            lat=mypicture.readLatitude()
            long=mypicture.readLongitude()
        pmHead=u"\n\n<Placemark>\n<name>"+\
        os.path.basename(picName)+"</name>\n"
        iconLook="<styleUrl>#camera</styleUrl>"
        
        #Adding a footer to the description
        pmDescriptionFooter=self.footerPlacemark(picName,type="GM")        
        pmDescription=u"<description><![CDATA["+\
        "<a href='"+self.url+os.path.basename(picName)+"' target='_blank'> <img src='"+\
        self.url+"thumbs/thumb_"+os.path.basename(picName)+"'/></a>"+\
        pmDescriptionFooter+\
        "]]>"+\
        "</description>\n"+iconLook+\
        "\n<Point>"+\
        "\n<coordinates>"+str(long)+","+str(lat)+","+elevation+\
        "</coordinates>\n</Point>\n"
        pmTail=u"</Placemark>"
        #self.f.write(pmHead)
        #self.f.write(pmDescription)
        #self.f.write(pmTail)
        pm=pmHead+pmDescription+pmTail
        self.f.write(pm.encode("utf-8"))

    def path(self,gpxFile,cut=500):
        """ Creates the path of the GPX file in the kml"""
        #self.f.write(u"\n<Folder>\n<name>Track</name>")
        pathHead=u"\n<Folder>\n<name>Track</name>"
        self.f.write(pathHead.encode("utf-8"))
        i=1 # an iterator for the gpx file
        part=cut # cut the gpx file in part (to be sure it displays in GM)
        j=1 #Path j (a number for each section) 
        
        if self.eleMode==1:
            pathAdd=u"\n<altitudeMode>absolute</altitudeMode>"
        elif self.eleMode==2:
            pathAdd=u"\n<altitudeMode>absolute</altitudeMode>\n<extrude>1</extrude>"
        else: pathAdd=u""
        
        def makeHeadPath(j):
            headPath=u"\n<Placemark>\n<name>Path "+str(j)+"</name>\n"\
            +"<styleUrl>#lineStyle</styleUrl>\n<LineString>\n<tessellate>1</tessellate>"\
            +pathAdd+"\n<coordinates>\n"
            return headPath
        
        endPath=u"\n</coordinates>\n</LineString>\n</Placemark>\n\n"
        bodyPath=u""
        myGpx=Gpx(gpxFile) 
        track=myGpx.extract()
                
        for rec in track:
            if rec['ele']=="None" or rec['ele']=="": rec['ele']="0"
            if i<part:
                bodyPath=bodyPath+rec['lon']+','+rec['lat']+','+rec['ele']+" "
                i=i+1
            if i==part:
                #self.f.write(makeHeadPath(j))
                #self.f.write(bodyPath)
                #self.f.write(endPath)
                cont=u""+makeHeadPath(j)+bodyPath+endPath
                self.f.write(cont.encode("utf-8"))
                i=1
                j=j+1
                bodyPath=""

        #self.f.write(makeHeadPath(j))
        #self.f.write(bodyPath)
        #self.f.write(endPath)
        #self.f.write("</Folder>\n")
        content=makeHeadPath(j)+bodyPath+endPath+u"</Folder>\n"
        self.f.write(content.encode("utf-8"))

    def close(self):
        """Ending of the kml file"""
        print "close kml!"
        kmlTail=u"\n</Document>\n</kml>"
        #self.f.write(kmlTail)
        self.f.write(kmlTail.encode("utf-8"))
        self.f.close()
        
if __name__=="__main__":
    
    import os,sys,fnmatch
    folder="C:/Documents and Settings/franz/Bureau/gpicsync.googlecode.com/trunk/GE-test"
    myKml=KML(folder+"/test") # deprecated see __init__
    for fileName in os.listdir ( folder ):
        if fnmatch.fnmatch (fileName, '*.JPG') or fnmatch.fnmatch (fileName, '*.jpg'):
            myKml.placemark(folder+"/"+fileName)
    myKml.close()
