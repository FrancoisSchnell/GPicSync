
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
    
    def __init__(self,fileName,name):
        self.f=open(fileName+".kml","w")
        kmlHead="""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.1">
<Document>
<name>"""+name+"""</name>
<Style id="lineStyle">
<LineStyle>
<color>64eeee17</color>
<width>6</width>
</LineStyle>
</Style>
<Style id="sh_ylw-pushpin_copy2">
<IconStyle>
<scale>1.3</scale>
<Icon>
<href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href>
</Icon>
<hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
</IconStyle>
</Style>
<Style id="sn_ylw-pushpin_copy2">
<IconStyle>
<scale>1.1</scale>
<Icon>
    <href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href>
</Icon>
<hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
</IconStyle>
</Style>
<StyleMap id="msn_ylw-pushpin_copy2">
<Pair>
    <key>normal</key>
    <styleUrl>#sn_ylw-pushpin_copy2</styleUrl>
</Pair>
<Pair>
    <key>highlight</key>
    <styleUrl>#sh_ylw-pushpin_copy2</styleUrl>
</Pair>
</StyleMap>
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

    def placemark(self,picName="",lat="",long=""):
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
        if lat and long == "":
            mypicture=GeoExif(picName)
            lat=mypicture.readLatitude()
            long=mypicture.readLongitude()
        
        pmHead="\n\n<Placemark>\n<name>"+\
        os.path.basename(picName)+"</name>\n"
        pmDescription="<description><![CDATA["+\
        "<img src='"+os.path.basename(picName)+"' width='640' height='480'/>]]>"+\
        "</description>\n<Point>"+\
        "\n<coordinates>"+str(long)+","+str(lat)+",0"+\
        "</coordinates>\n</Point>\n"
        pmTail="</Placemark>"
        self.f.write(pmHead)
        self.f.write(pmDescription)
        self.f.write(pmTail)
        
    def path(self,gpxFile):
        """ Creates the path of the GPX file in the kml"""
        headPath="""
\n<Placemark>
<name>Path</name>
<styleUrl>#lineStyle</styleUrl>
<LineString>
<tessellate>1</tessellate>
<coordinates>\n"""
        endPath="\n</coordinates>\n</LineString>\n</Placemark>\n\n"
        bodyPath=""
        myGpx=Gpx(gpxFile) 
        track=myGpx.extract()
        for rec in track:
            bodyPath=bodyPath+rec['lon']+','+rec['lat']+',0 '
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