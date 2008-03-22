#!/usr/bin/python

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
import gettext,time,datetime
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
        #print self.track
        self.localOffset=0 #default time offset between camera and GPS
        self.dateCheck=dateProcess
        self.UTCoffset=UTCoffset*3600
        tcam_l=int(tcam_l[0:2])*3600+int(tcam_l[3:5])*60+int(tcam_l[6:8])
        tgps_l=int(tgps_l[0:2])*3600+int(tgps_l[3:5])*60+int(tgps_l[6:8])
        self.timerange=timerange
        #self.localOffset=tcam_l-(tgps_l+self.UTCoffset)
        #self.localOffset=tgps_l-(tcam_l+self.UTCoffset) # To test before next release !
        self.localOffset=tcam_l - tgps_l + self.UTCoffset
        self.backup=backup
        self.interpolation=interpolation
        print "local UTC Offset (seconds)= ", self.localOffset
        #print self.track
    
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
        if picDateTimeSize[0]=="nodate":
            return [" : WARNING: DIDN'T GEOCODE, no Date/Time Original in this picture.",
            ""]
        
        # create a proper datetime object (self.shot_datetime)
        pict=(picDateTimeSize[0]+":"+picDateTimeSize[1]).split(":")
        #print ">>> picture original date/time from EXIF: ",pict
        self.pic_datetime=datetime.datetime(
                                            int(pict[0]),
                                            int(pict[1]),
                                            int(pict[2]),
                                            int(pict[3]),
                                            int(pict[4]),
                                            int(pict[5]))
        print ">>> self.pic_datetime (from picture EXIF): ",self.pic_datetime
        self.pic_datetimeUTC=self.pic_datetime-datetime.timedelta(seconds=self.localOffset)
        print ">>> self.pic_datetimeUTC (time corrected if offset):",self.pic_datetimeUTC
    
        self.shotTime=picDateTimeSize[1]
        self.shotDate=picDateTimeSize[0].replace(":","-")
        self.timeStamp=self.shotDate+"T"+picDateTimeSize[1]
        self.picWidth=picDateTimeSize[2]
        self.picHeight=picDateTimeSize[3]
        latitude=""
        longitude=""
        elevation=""
        #print "Picture shotTime was", self.shotTime
        tpic_tgps_l=864000 # will try  match a pic within 864000 seconds (10 days)
        
        if len(self.track)==0:
            return [_(" : WARNING: DIDN'T GEOCODE, ")+_("no track points found - ")\
                     +self.shotDate+"-"+self.shotTime,"","",self.picWidth,self.picHeight,elevation]
        
        for n,rec in enumerate(self.track):
            delta_datetime=self.pic_datetimeUTC-rec["datetime"]
            rec["tpic_tgps_l"]=delta_datetime.days*86400 +delta_datetime.seconds
            if abs(rec["tpic_tgps_l"])<tpic_tgps_l:
                N=n
                tpic_tgps_l=abs(rec["tpic_tgps_l"])
                latitude,longitude,elevation=rec['lat'],rec['lon'],rec['ele']
                if float(latitude)>0:latRef="N"
                else: latRef="S"
                if float(longitude)>0:longRef="E"
                else: longRef="W"
                
        if (self.interpolation==True) and (self.track[N]!=0):
            try:
                print ">>> N (nearest trackpoint) in GPX list is index = ",N 
                print ">>> Trackpoint N Latitude= ", latitude," Longitude= ",longitude

                if (self.track[N]["tpic_tgps_l"]*self.track[N+1]["tpic_tgps_l"])<=0: 
                    M=N+1
                    print ">>> Chose point M=N+1 as second nearest valid trackpoint for interpolation" 
                elif (self.track[N]["tpic_tgps_l"]*self.track[N+1]["tpic_tgps_l"])>0: 
                    M=N-1
                    print ">>> Chose point M=N-1 as second nearest valid trackpoint for interpolation" 
                    
                dLonNM=float(self.track[M]['lon'])-float(self.track[N]['lon'])
                dLatNM=float(self.track[M]['lat'])-float(self.track[N]['lat'])
                print ">>> dLonNM= ",dLonNM,"dLatNM= ",dLatNM
                ratio=abs(float(self.track[N]["tpic_tgps_l"]))\
                /(abs(self.track[N]["tpic_tgps_l"])+abs(self.track[M]["tpic_tgps_l"]))
                print ">>> ratio= ",ratio
                latitude=float(latitude)+ratio*dLatNM
                longitude=float(longitude)+ratio*dLonNM
                if float(latitude)>0:latRef="N"
                else: latRef="S"
                if float(longitude)>0:longRef="E"
                else: longRef="W"
                latitude=str(latitude)
                longitude=str(longitude)
            except:
                print "Had a problem with interpolation tuning, probably the time\
                of the picture is off the time of the track"

        if latitude != "" and longitude !="" and (tpic_tgps_l< self.timerange):
            print "Writing best lat./long. match to pic. EXIF -->",latitude,latRef,\
            longitude,longRef,"with tpic-tgps=",tpic_tgps_l,"seconds\n"
            pic.writeLatLong(latitude,longitude,latRef,longRef,self.backup,elevation)
            return [ _("taken ")+self.shotDate+"-"+self.shotTime+", "\
            +_("writing best latitude/longitude match to picture: ")+latRef+\
            " "+latitude+" ,"+longRef+" "+longitude+" :"+_(" time difference (s)= ")+str(int(tpic_tgps_l)),
            latitude,longitude,self.picWidth,self.picHeight,self.timeStamp,elevation]
        else:
            print "Didn't find any picture for this day or timerange"
            if tpic_tgps_l !=86400:
                return [_(" : WARNING: DIDN'T GEOCODE, ")+_("no track point below the maximum time range ")\
                +"( "+str(self.timerange)+" s) : " +self.shotDate+"-"+self.shotTime+_(" time difference (s)= ")+str(int(tpic_tgps_l))\
                +"\n"+_("For information nearest trackpoint was at lat=")+latitude+_(" long=")+longitude,"","",self.picWidth,self.picHeight,elevation]
            else:
                return [_(" : WARNING: DIDN'T GEOCODE, ")+_("no track point at this picture date ")\
                 +self.shotDate+"-"+self.shotTime,"","",self.picWidth,self.picHeight,elevation]
        
if __name__=="__main__":
    
    ## Commnand-line version
    
    import os,sys,fnmatch
    from optparse import OptionParser
    
    import gettext
    gettext.install("gpicsync-GUI", "None")
    
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
    if options.dir==None: options.dir="."
    if options.gpx==None:
        print "I need a .gpx file \nType Python gpicsync.py -h for help."
        sys.exit(1)
    options.gpx=[options.gpx]
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

    