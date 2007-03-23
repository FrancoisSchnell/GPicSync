#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

###############################################################################
#
# (c) francois.schnell  francois.schnell@gmail.com
#                       http://francois.schnell.free.fr  
#
# This script is released under the GPL license
#
###############################################################################

"""
GPicSync is a geolocalisation tool to synchronise data from a GPS and a camera.
USAGE (preparation):
- Synchronize the time on your GPS and camera. 
- Leave your GPS always ON (taking a track log) when outdoor
- After coming back extract the track-log of the day in your GPS and save it as
 a .gpx file(with a freeware like easygps on windows or another software)

USAGE (command line):
---------------------

python gpicsync.py -d myfoderWithPictures -g myGpxFile.gpx -o UTCoffset

For more options type gpicsync.py --help

"""

from geoexif import *
from gpx import *

class GpicSync(object):
    """
    A class to manage the geolocalisation from a .gpx file.
    """
    def __init__(self,gpxFile,tcam_l="00:00:00",tgps_l="00:00:00",UTCoffset=0,dateProcess=True):
        """Extracts data from the gpx file and compute local offset duration"""
        myGpx=Gpx(gpxFile)   
        self.track=myGpx.extract()
        self.localOffset=0 #default time offset between camera and GPS
        self.dateCheck=dateProcess
        self.UTCoffset=UTCoffset*3600
        tcam_l=int(tcam_l[0:2])*3600+int(tcam_l[3:5])*60+int(tcam_l[6:8])
        tgps_l=int(tgps_l[0:2])*3600+int(tgps_l[3:5])*60+int(tgps_l[6:8])
        self.localOffset=tcam_l-(tgps_l+self.UTCoffset)
        print "local UTC Offset (seconds)= ", self.localOffset
        #print self.track
        
    def compareTime(self,t1,t2):
        """
        Compute and return the duration (int) in seconds  between two times
        """
        #print "t1=",t1
        #print "t2=",t2
        t1sec=int(t1[0:2])*3600+int(t1[3:5])*60+int(t1[6:8])
        t2sec=int(t2[0:2])*3600+int(t2[3:5])*60+int(t2[6:8])
        delta_t=(t2sec-t1sec)-self.localOffset
        #print "delta_t =",delta_t
        return delta_t
    
    def syncPicture(self,picture):
        """ 
        Find the nearest trackpoint from the recorded time in the picture.
        Returns tpic_tgps_l (to judge the quality of the geolocalisation)
        """
        pic=GeoExif(picture)
        self.shotTime=pic.readDateTime()[1]
        self.shotDate=pic.readDateTime()[0].replace(":","-")
        latitude=""
        longitude=""
        #print "Picture shotTime was", self.shotTime
        tpic_tgps_l=86400 # maximum seconds interval in a day
        if self.dateCheck==True:
            for rec in self.track:
                if rec['date']==self.shotDate:
                    rec["tpic_tgps_l"]= self.compareTime(self.shotTime,rec["time"])
                    if abs(rec["tpic_tgps_l"])<tpic_tgps_l:
                        tpic_tgps_l=abs(rec["tpic_tgps_l"])
                        latitude=rec['lat']
                        #print "latitude =",rec['lat']
                        longitude=rec['lon']
                        #print "longitude =",rec['lon']
                        if float(latitude)>0:
                            latRef="N"
                        else: latRef="S"
                        if float(longitude)>0:
                            longRef="E"
                        else: longRef="W"
        if self.dateCheck==False:
            for rec in self.track:
                rec["tpic_tgps_l"]= self.compareTime(self.shotTime,rec["time"])
                if abs(rec["tpic_tgps_l"])<tpic_tgps_l:
                    tpic_tgps_l=abs(rec["tpic_tgps_l"])
                    latitude=rec['lat']
                    #print "latitude =",rec['lat']
                    longitude=rec['lon']
                    trkptDay=rec['date']
                    #print "longitude =",rec['lon']
                    if float(latitude)>0:
                        latRef="N"
                    else: latRef="S"
                    if float(longitude)>0:
                        longRef="E"
                    else: longRef="W"
        if self.dateCheck==True:
            if latitude != "" and longitude !="":
                if float(longitude)<0:longitude=str(abs(float(longitude)))
                if float(latitude)<0:latitude=str(abs(float(latitude)))
                print "Writting best lat./long. match to pic. EXIF -->",latitude,latRef,\
                longitude,longRef,"with tpic-tgps=",tpic_tgps_l,"seconds\n"
                pic.writeLatLong(latitude,longitude,latRef,longRef)
                #return tpic_tgps_l
                return "taken "+self.shotDate+"-"+self.shotTime+\
                "  - Writting best match to picture  -> "+latRef+\
                " "+latitude+" ,"+longRef+" "+longitude+" : time difference (s)= "+str(tpic_tgps_l)
            else:
                print "Didn't find any picture for this day"
                return " : Failure, didn't find any trackpoint at this picture's date: "\
                +self.shotDate+"-"+self.shotTime
        if self.dateCheck==False:
            if latitude != "" and longitude !="":
                if float(longitude)<0:longitude=str(abs(float(longitude)))
                if float(latitude)<0:latitude=str(abs(float(latitude)))
                print "Writting best lat./long. match to pic. EXIF -->",latitude,latRef,\
                longitude,longRef,"with tpic-tgps=",tpic_tgps_l,"seconds\n"
                pic.writeLatLong(latitude,longitude,latRef,longRef)
                response= "Writting best latitude/longitude match to EXIF picture: "+latRef+\
                " "+latitude+" ,"+longRef+" "+longitude+" with time difference (s)= "+str(tpic_tgps_l)
                if self.shotDate != trkptDay:
                    response=response+"\nWarning: Picture date "+self.shotDate+\
                   " and track point date "+trkptDay+" are different ! " 
                return response
            else:
                print "Didn't find any suitable trackpoint"
                return "Didn't find any suitable trackpoint"
            
if __name__=="__main__":
    
    ## Commnand-line version
    import os,sys,fnmatch
    from optparse import OptionParser

    parser=OptionParser()
    parser.add_option("-d", "--directory",dest="dir",
    help="Directory containing the pictures. Expl. mypictures")
    parser.add_option("-g", "--gpx",dest="gpx",
    help="Path to the gpx file. Expl. mypicture/tracklog.gpx")
    parser.add_option("-o", "--offset",dest="offset",
    help="A positive or negative number to indicate offset hours\
    to the greenwich meriadian (East positive, West negative, 1 for France)")
    parser.add_option("--tcam",dest="tcam",
    help="Actual time of the camera only if it was out of sync with the gps \
     Expl. 09:34:02")
    parser.add_option("--tgps",dest="tgps",
    help="Actual time of the GPS only if it was out of sync with the camera \
    Expl. 10:06:00")
    
    (options,args)=parser.parse_args()
    
    if options.tcam==None: options.tcam="00:00:00"
    if options.tgps==None: options.tgps="00:00:00"
    if options.offset==None: options.offset=0
    if options.offset==None: options.dir="."
    if options.gpx==None:
        print "I need a .gpx file \nType Python gpicsync.py -h for help."
        sys.exit(1)
    
    print "\n Engage using the following arguments ...\n" 
    print "-Directory containing the pictures:",options.dir
    print "-Path to the gpx file:",options.gpx
    print "-UTC Offset (hours):",options.offset
    print "-- Camera local display time:",options.tcam
    print "-- GPS local display time:",options.tgps
    print "\n"
    
    geo=GpicSync(gpxFile=options.gpx,
    tcam_l=options.tcam,tgps_l=options.tgps,UTCoffset=int(options.offset))
    
    for fileName in os.listdir ( options.dir ):
        #will add a '*.JPG' or '*.jpg' match
        if fnmatch.fnmatch ( fileName, '*.JPG' ):
            print "\nFound fileName ",fileName," Processing now ..."
            geo.syncPicture(options.dir+'/'+fileName)

    