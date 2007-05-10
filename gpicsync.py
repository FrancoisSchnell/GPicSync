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
import gettext
from geoexif import *
from gpx import *


class GpicSync(object):


    """
    A class to manage the geolocalisation from a .gpx file.
    """
    def __init__(self,gpxFile,tcam_l="00:00:00",tgps_l="00:00:00",UTCoffset=0,
    dateProcess=True,timerange=3600,backup=True,interpolation=False):
        """Extracts data from the gpx file and compute local offset duration"""
        myGpx=Gpx(gpxFile)   
        self.track=myGpx.extract()
        self.localOffset=0 #default time offset between camera and GPS
        self.dateCheck=dateProcess
        self.UTCoffset=UTCoffset*3600
        tcam_l=int(tcam_l[0:2])*3600+int(tcam_l[3:5])*60+int(tcam_l[6:8])
        tgps_l=int(tgps_l[0:2])*3600+int(tgps_l[3:5])*60+int(tgps_l[6:8])
        self.timerange=timerange
        #self.localOffset=tcam_l-(tgps_l+self.UTCoffset)
        self.localOffset=tgps_l-(tcam_l+self.UTCoffset) # To test before next release !
        self.backup=backup
        self.interpolation=interpolation
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
        This method returns now a list [response,latitude,longitude]
        where 'response' is the general reslult to be show to the user
        latitude and longitude are strings (+- decimal degrees) to be use
        by other part of the program calling this method. 
        """
        interpolation=True # To use or not an interpolation mode(instead of nearest point)
        pic=GeoExif(picture)
        picDateTimeSize=pic.readDateTimeSize()
        self.shotTime=picDateTimeSize[1]
        self.shotDate=picDateTimeSize[0].replace(":","-")
        self.picWidth=picDateTimeSize[2]
        self.picHeight=picDateTimeSize[3]
        latitude=""
        longitude=""
        #print "Picture shotTime was", self.shotTime
        tpic_tgps_l=86400 # maximum seconds interval in a day
        
        if self.dateCheck==True:
            for n,rec in enumerate(self.track):
                if rec['date']==self.shotDate:
                    rec["tpic_tgps_l"]= self.compareTime(self.shotTime,rec["time"])
                    if abs(rec["tpic_tgps_l"])<tpic_tgps_l:
                        N=n
                        tpic_tgps_l=abs(rec["tpic_tgps_l"])
                        latitude=rec['lat']
                        #print "Nearest point latitude =",rec['lat']
                        longitude=rec['lon']
                        #print "Nearest point longitude =",rec['lon']
                        elevation=rec['ele']
                        if float(latitude)>0:
                            latRef="N"
                        else: latRef="S"
                        if float(longitude)>0:
                            longRef="E"
                        else: longRef="W"
            if self.interpolation==True and rec['date']==self.shotDate:
                print "N is= ",N #N (index in the list) is the nearest trackpoint 
                print "Latitude of N= ", latitude
                print "Longitude of N =",longitude
                if abs(self.track[N+1]["tpic_tgps_l"])<abs(self.track[N-1]["tpic_tgps_l"]):
                    M=N+1
                else:
                    M=N-1
                print "M is= ",M # M is the second nearest trackpoint
                dLonNM=float(self.track[M]['lon'])-float(self.track[N]['lon'])
                dLatNM=float(self.track[M]['lat'])-float(self.track[N]['lat'])
                print "dLonNM= ",dLonNM
                print "dLatNM= ",dLatNM
                ratio=abs(float(self.track[N]["tpic_tgps_l"]))/\
                (abs(self.track[N]["tpic_tgps_l"])+abs(self.track[M]["tpic_tgps_l"]))
                print "ratio= ",ratio
                latitude=float(latitude)+ratio*dLatNM
                longitude=float(longitude)+ratio*dLonNM
                if float(latitude)>0:
                    latRef="N"
                else: latRef="S"
                if float(longitude)>0:
                    longRef="E"
                else: longRef="W"
                latitude=str(latitude)
                longitude=str(longitude)
                
        if self.dateCheck==False:
            for n,rec in enumerate(self.track):
                rec["tpic_tgps_l"]= self.compareTime(self.shotTime,rec["time"])
                if abs(rec["tpic_tgps_l"])<tpic_tgps_l:
                    N=n
                    tpic_tgps_l=abs(rec["tpic_tgps_l"])
                    latitude=rec['lat']
                    #print "latitude =",rec['lat']
                    longitude=rec['lon']
                    trkptDay=rec['date']
                    #print "longitude =",rec['lon']
                    elevation=rec['ele']
                    if float(latitude)>0:
                        latRef="N"
                    else: latRef="S"
                    if float(longitude)>0:
                        longRef="E"
                    else: longRef="W"
            if self.interpolation==True:
                print "N is= ",N
                print "Latitude of N= ", latitude
                print "Longitude of N =",longitude
                if abs(self.track[N+1]["tpic_tgps_l"])<abs(self.track[N-1]["tpic_tgps_l"]):
                    M=N+1
                else:
                    M=N-1
                print "M is= ",M
                dLonNM=float(self.track[M]['lon'])-float(self.track[N]['lon'])
                dLatNM=float(self.track[M]['lat'])-float(self.track[N]['lat'])
                print "dLonNM= ",dLonNM
                print "dLatNM= ",dLatNM
                ratio=abs(float(self.track[N]["tpic_tgps_l"]))/\
                (abs(self.track[N]["tpic_tgps_l"])+abs(self.track[M]["tpic_tgps_l"]))
                print "ratio= ",ratio
                latitude=float(latitude)+ratio*dLatNM
                longitude=float(longitude)+ratio*dLonNM
                if float(latitude)>0:
                    latRef="N"
                else: latRef="S"
                if float(longitude)>0:
                    longRef="E"
                else: longRef="W"
                latitude=str(latitude)
                longitude=str(longitude)
                
        if self.dateCheck==True:
            if latitude != "" and longitude !="" and (tpic_tgps_l< self.timerange):
                #if float(longitude)<0:longitude=str(abs(float(longitude)))
                #if float(latitude)<0:latitude=str(abs(float(latitude)))
                print "Writting best lat./long. match to pic. EXIF -->",latitude,latRef,\
                longitude,longRef,"with tpic-tgps=",tpic_tgps_l,"seconds\n"
                pic.writeLatLong(latitude,longitude,latRef,longRef,self.backup,elevation)
                #return tpic_tgps_l
                return [ _("taken ")+self.shotDate+"-"+self.shotTime+", "\
                +_("writting best latitude/longitude match to picture: ")+latRef+\
                " "+latitude+" ,"+longRef+" "+longitude+" :"+_(" time difference (s)= ")+str(int(tpic_tgps_l)),
                latitude,longitude,self.picWidth,self.picHeight]
            else:
                print "Didn't find any picture for this day or timerange"
                if tpic_tgps_l !=86400:
                    return [_(" : WARNING: DIDN'T GEOCODE, ")+_("no track point below the maximum time range ")\
                    +"( "+str(self.timerange)+" s) : " +self.shotDate+"-"+self.shotTime+_(" time difference (s)= ")+str(int(tpic_tgps_l))\
                    +"\n"+_("For information nearest trackpoint was at lat=")+latitude+_(" long=")+longitude,"","",self.picWidth,self.picHeight]
                else:
                    return [_(" : WARNING: DIDN'T GEOCODE, ")+_("no track point at this picture date ")\
                     +self.shotDate+"-"+self.shotTime,"","",self.picWidth,self.picHeight]
        
        if self.dateCheck==False:
            if latitude != "" and longitude !=""and (tpic_tgps_l<self.timerange):
                #if float(longitude)<0:longitude=str(abs(float(longitude)))
                #if float(latitude)<0:latitude=str(abs(float(latitude)))
                print "Writting best lat./long. match to pic. EXIF -->",latitude,latRef,\
                longitude,longRef,"with tpic-tgps=",tpic_tgps_l,"seconds\n"
                pic.writeLatLong(latitude,longitude,latRef,longRef,self.backup,elevation)
                response= _("writting best latitude/longitude match to picture: ")+latRef+\
                " "+latitude+" ,"+longRef+" "+longitude+" with"+_(" time difference (s)= ")+str(int(tpic_tgps_l))
                if self.shotDate != trkptDay:
                    response=response+"\n"+_("Warning: Picture date ")+self.shotDate+\
                   _(" and track point date ")+trkptDay+_(" are different ! ") 
                return [response,latitude,longitude,self.picWidth,self.picHeight]
            else:
                print " WARNING: DIDN'T GEOCODE, no suitable track point below maximum time difference (seconds)= ",self.timerange
                return [_(" : WARNING: DIDN'T GEOCODE, ")+_(" no suitable track point below maximum time difference, ")+_(" time difference (s)= ")+str(int(tpic_tgps_l)),"","",self.picWidth,self.picHeight]
            
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
    to the greenwich meridian (East positive, West negative, 1 for France)")
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
    
    print "\nEngage processing using the following arguments ...\n" 
    print "-Directory containing the pictures:",options.dir
    print "-Path to the gpx file:",options.gpx
    print "-UTC Offset (hours):",options.offset
    print "-- Camera local display time:",options.tcam
    print "-- GPS local display time:",options.tgps
    print "\n"
    
    geo=GpicSync(gpxFile=options.gpx,
    tcam_l=options.tcam,tgps_l=options.tgps,UTCoffset=int(options.offset),timerange=3600)
    
    for fileName in os.listdir ( options.dir ):
        if fnmatch.fnmatch (fileName, '*.JPG') or fnmatch.fnmatch (fileName, '*.jpg'):
            print "\nFound fileName ",fileName," Processing now ..."
            geo.syncPicture(options.dir+'/'+fileName)[0]

    