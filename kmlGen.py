
###############################################################################
#
# (c) francois.schnell  francois.schnell@gmail.com
#                       http://francois.schnell.free.fr  
#
# This script is released under the GPL v2 license
#
###############################################################################



from geoexif import *
from gpx import *
import SimpleHTTPServer,time
import SocketServer
from thread import start_new_thread
        
class KML(object):
    """
    A quick and dirty kml generator in progress for gpicsync
    (for live viewing in Google Earth)
    """
    
    def __init__(self,fileName,name,url=""):
        self.f=open(fileName+".kml","w")
        self.url=url
        kmlHead="""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.1">
<Document>
<name>"""+name+"""</name>
<Style id="lineStyle">
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
<href>root://icons/palette-4.png</href>
<x>192</x>
<y>96</y>
<w>32</w>
<h>32</h>
</Icon>
<hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
</IconStyle>
</Style>
"""
        self.f.write(kmlHead)
        
    def launchLocalServer(self):
        """minimal web server.  serves files relative to the current directory"""
        PORT = 8000
        Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        httpd = SocketServer.TCPServer(("", PORT), Handler)
        print "serving at port", PORT
        httpd.serve_forever()
        #start_new_thread(serverGo,())

    def placemark(self,picName="",lat="",long="",width="800",height="600"):
        """
        Creates a placemark tag for the given picture in the kml file.
        If only a picture path is given in argument, latitude and longitude will
        be searched in the picture EXIF.
        It's also possible to give the values in argument
        (a string representing decimal degress, - sign ok)
        """
        #print "placemark!"
        #print "lat =",lat
        #print "long =",long

        w=float(width)
        h=float(height)
        
        if width>height:
            print "width > height"
            width=(800./w)*w
            height=(800./w)*h
        
        if height>width:
            print "height  > width"
            height=(600./h)*h
            width=(600./h)*w
        
        width=str(int(width))
        height=str(int(height))
                    
        if lat and long == "":
            mypicture=GeoExif(picName)
            lat=mypicture.readLatitude()
            long=mypicture.readLongitude()
        
        pmHead="\n\n<Placemark>\n<name>"+\
        os.path.basename(picName)+"</name>\n"
        pmDescription="<description><![CDATA["+\
        "<img src='"+self.url+os.path.basename(picName)+"' width='"+width+"' height='"+height+"'/>]]>"+\
        "</description>\n<styleUrl>#camera</styleUrl>\n<Point>"+\
        "\n<coordinates>"+str(long)+","+str(lat)+",0"+\
        "</coordinates>\n</Point>\n"
        pmTail="</Placemark>"
        self.f.write(pmHead)
        self.f.write(pmDescription)
        self.f.write(pmTail)
        
    def placemark4Gmaps(self,picName="",lat="",long="",width="400",height="300"):
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
        pmHead="\n\n<Placemark>\n<name>"+\
        os.path.basename(picName)+"</name>\n"
        pmDescription="<description><![CDATA["+\
        "<a href='"+self.url+os.path.basename(picName)+"' target='_blank'> <img src='"+\
        self.url+"thumbs/thumb_"+os.path.basename(picName)+"'/></a>]]>"+\
        "</description>\n<styleUrl>#camera</styleUrl>\n<Point>"+\
        "\n<coordinates>"+str(long)+","+str(lat)+",0"+\
        "</coordinates>\n</Point>\n"
        pmTail="</Placemark>"
        self.f.write(pmHead)
        self.f.write(pmDescription)
        self.f.write(pmTail)

    def path(self,gpxFile):
        """ Creates the path of the GPX file in the kml"""

        i=1 # an iterator for the gpx file
        part=500 # cut the gpx file in part (to be sure it displays in GM) 
        
        headPath="""
\n<Placemark>
<name>Path """+str(i)+ """</name>
<styleUrl>#lineStyle</styleUrl>
<LineString>
<tessellate>1</tessellate>
<coordinates>\n"""
        endPath="\n</coordinates>\n</LineString>\n</Placemark>\n\n"
        bodyPath=""
        myGpx=Gpx(gpxFile) 
        track=myGpx.extract()
                
        for rec in track:
            if i<part:
                bodyPath=bodyPath+rec['lon']+','+rec['lat']+',0 '
                i=i+1
            if i==part:
                self.f.write(headPath)
                self.f.write(bodyPath)
                self.f.write(endPath)
                i=1
                bodyPath=""
        self.f.write(headPath)
        self.f.write(bodyPath)
        self.f.write(endPath)

    def close(self):
        """Ending of the kml file"""
        print "close kml!"
        kmlTail="\n</Document>\n</kml>"
        self.f.write(kmlTail)
        self.f.close()
        
if __name__=="__main__":
    
    import os,sys,fnmatch
    folder="C:/Documents and Settings/franz/Bureau/gpicsync.googlecode.com/trunk/GE-test"
    myKml=KML(folder+"/test")
    for fileName in os.listdir ( folder ):
        if fnmatch.fnmatch (fileName, '*.JPG') or fnmatch.fnmatch (fileName, '*.jpg'):
            myKml.placemark(folder+"/"+fileName)
    myKml.close()
    #myKml.launchLocalServer()