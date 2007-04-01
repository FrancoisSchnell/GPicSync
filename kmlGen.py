
###############################################################################
#
# (c) francois.schnell  francois.schnell@gmail.com
#                       http://francois.schnell.free.fr  
#
# This script is released under the GPL license
#
###############################################################################

"""
A quick and dirty kml generator in progress for gpicsync
(for live viewing in Google Earth)
"""

from geoexif import *
import SimpleHTTPServer,time
import SocketServer
from thread import start_new_thread
        
class KML(object):
    """
    A quick and dirty kml generator in progress for gpicsync
    (for live viewing in Google Earth)
    """
    
    def __init__(self,fileName):
        self.f=open(fileName+".kml","w")
        kmlHead="""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.1">
<Document>
<name>"""+fileName+"""</name>
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

    def placemark(self,picName):
        print "placemark!"
        mypicture=GeoExif(picName)
        lat=mypicture.readLatitude()
        long=mypicture.readLongitude()
        pmHead="""<Placemark>
        <name>"""+picName+"</name>"
        pmDescription="<description><![CDATA["+\
        "<img src='"+picName+"' width='640' height='480'/>]]>"+\
        "</description><name>"+os.path.basename(picName)+"</name><Point>"+\
        "\n<coordinates>"+str(long)+","+str(lat)+",0"+\
        "</coordinates></Point>"
        pmTail="</Placemark>"
        self.f.write(pmHead)
        self.f.write(pmDescription)
        self.f.write(pmTail)
        
    def close(self):
        print "close kml!"
        kmlTail="""
        </Document>
        </kml>
        """
        self.f.write(kmlTail)
        self.f.close()
        
if __name__=="__main__":
    
    import os,sys,fnmatch
    # folder = basename of the path ? => portable even if created outside
    # of gpicsync intall directory : integrate as a default the intial sync
    # and add a comment in the kml to explain what to do for live
    folder="C:/Documents and Settings/franz/Bureau/gpicsync.googlecode.com/trunk/GE-test"
    myKml=KML(folder+"/test")
    for fileName in os.listdir ( folder ):
        if fnmatch.fnmatch (fileName, '*.JPG') or fnmatch.fnmatch (fileName, '*.jpg'):
            myKml.placemark(folder+"/"+fileName)
    myKml.close()
    #myKml.launchLocalServer()