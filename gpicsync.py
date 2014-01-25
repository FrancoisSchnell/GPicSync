#!/usr/bin/python
# -*- coding: utf-8 -*-

###############################################################################
#
# Developer: francois.schnell   francois.schnell@gmail.com
#                               http://francois.schnell.free.fr
#
# Contributors, see: http://code.google.com/p/gpicsync/wiki/Contributions
#
# This script is released under the GPL license version 2 license
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
#import pytz

try: import pytz
except ImportError: pass

from geoexif import *
from gpx import *


class GpicSync(object):
    """
    A class to manage the geolocalisation from a .gpx file.
    """
    def __init__(self,gpxFile,tcam_l="00:00:00",tgps_l="00:00:00",UTCoffset=0,timezone=None,
    dateProcess=True,timerange=3600,backup=True,interpolation=False,qr_time_image=None):
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
        if timezone is not None:
            self.timezone = pytz.timezone(timezone)
            self.UTCoffset = 0
        else:
            self.timezone = None
        self.localOffset=tcam_l - tgps_l + self.UTCoffset
        self.backup=backup
        self.interpolation=interpolation
        if qr_time_image is None:
            print "local UTC Offset (seconds)= ", self.localOffset

    def parseQrTime(self,qr_time_images):
        import zbar
        import Image
        import time
        import dateutil.parser
        min_offset = None
        max_offset = None
        for fileName, filePath in qr_time_images:
            pic=GeoExif(filePath)
            picDateTimeSize=pic.readDateTimeSize()
            scanner = zbar.ImageScanner()
            scanner.parse_config('enable')
            pil = Image.open(filePath).convert('L')
            width, height = pil.size
            raw = pil.tostring()
            image = zbar.Image(width, height, 'Y800', raw)
            scanner.scan(image)
            for symbol in image:
                try:
                    tgps = dateutil.parser.parse(symbol.data)
                    tcam = dateutil.parser.parse('%s %s UTC' % tuple(picDateTimeSize[:2]))
                    offset = tcam - tgps
                    print "Found QR code in file '%s' with difference %s" % (fileName, offset)
                    offset = offset.seconds + offset.days * 24 * 3600
                    if not min_offset or offset < min_offset:
                        min_offset = offset
                    if not max_offset or offset > max_offset:
                        max_offset = offset
                except:
                    pass
        if not min_offset or not max_offset:
            print "Found no sutable QR codes"
            sys.exit(1)
        if max_offset - min_offset > 60:
            print "Minimum and maximum offsets differ too much"
            sys.exit(1)
        self.timezone = None
        self.localOffset = (max_offset + min_offset) / 2
        print "Offset calculated by QR codes (seconds) = ", self.localOffset

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
        #print ">>> self.pic_datetime (from picture EXIF): ",self.pic_datetime
        self.pic_datetimeUTC=self.pic_datetime-datetime.timedelta(seconds=self.localOffset)
        if self.timezone:
            self.pic_datetimeUTC = self.timezone.localize(self.pic_datetimeUTC).astimezone(pytz.utc).replace(tzinfo=None)
        #print ">>> self.pic_datetimeUTC (time corrected if offset):",self.pic_datetimeUTC

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
                #print ">>> N (nearest trackpoint) in GPX list is index = ",N
                #print ">>> Trackpoint N Latitude= ", latitude," Longitude= ",longitude

                if (self.track[N]["tpic_tgps_l"]*self.track[N+1]["tpic_tgps_l"])<=0:
                    M=N+1
                    #print ">>> Chose point M=N+1 as second nearest valid trackpoint for interpolation"
                elif (self.track[N]["tpic_tgps_l"]*self.track[N+1]["tpic_tgps_l"])>0:
                    M=N-1
                    #print ">>> Chose point M=N-1 as second nearest valid trackpoint for interpolation"

                dLonNM=float(self.track[M]['lon'])-float(self.track[N]['lon'])
                dLatNM=float(self.track[M]['lat'])-float(self.track[N]['lat'])
                #print ">>> dLonNM= ",dLonNM,"dLatNM= ",dLatNM
                ratio=abs(float(self.track[N]["tpic_tgps_l"]))\
                /(abs(self.track[N]["tpic_tgps_l"])+abs(self.track[M]["tpic_tgps_l"]))
                #print ">>> ratio= ",ratio
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

def getFileList(dir):
    for fileName in sorted(os.listdir ( dir )):
        if (fnmatch.fnmatch ( fileName, '*.JPG' )
         or fnmatch.fnmatch ( fileName, '*.jpg' )
         or fnmatch.fnmatch ( fileName, '*.CR2' )
         or fnmatch.fnmatch ( fileName, '*.cr2' )
         or fnmatch.fnmatch ( fileName, '*.CRW' )
         or fnmatch.fnmatch ( fileName, '*.crw' )
         or fnmatch.fnmatch ( fileName, '*.NEF' )
         or fnmatch.fnmatch ( fileName, '*.nef' )
         or fnmatch.fnmatch ( fileName, '*.PEF' )
         or fnmatch.fnmatch ( fileName, '*.pef' )
         or fnmatch.fnmatch ( fileName, '*.RAW' )
         or fnmatch.fnmatch ( fileName, '*.raw' )
         or fnmatch.fnmatch ( fileName, '*.ORF' )
         or fnmatch.fnmatch ( fileName, '*.orf' )
         or fnmatch.fnmatch ( fileName, '*.DNG' )
         or fnmatch.fnmatch ( fileName, '*.dng' )
         or fnmatch.fnmatch ( fileName, '*.RAF' )
         or fnmatch.fnmatch ( fileName, '*.raf' )
         or fnmatch.fnmatch ( fileName, '*.MRW' )
         or fnmatch.fnmatch ( fileName, '*.mrw' )):
            yield fileName, options.dir+'/'+fileName

if __name__=="__main__":

    # Minimal commnand-line version (mainly for tests purposes)
    # The command-line version doesn't have all the feature of the GUI version,
    # like the KMLs output

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
    parser.add_option("-z", "--timezone", dest="timezone",
     help="A Time Zone name in which the photos have been taken (Europe/Paris for France).")
    parser.add_option("--tcam",dest="tcam",
     help="Actual time of the camera only if it was out of sync with the gps \
     Expl. 09:34:02")
    parser.add_option("--tgps",dest="tgps",
     help="Actual time of the GPS only if it was out of sync with the camera \
    Expl. 10:06:00")
    parser.add_option("--qr-time-image",dest="qr_time_image",
     help="Image with QR code with time from GPS phone with same camera to \
     calculate offset or 'auto' to detect the image automatically")

    (options,args)=parser.parse_args()

    if options.qr_time_image is not None and (options.offset is not None 
        or options.timezone is not None or options.tcam is not None 
            or options.tgps is not None):
        print >> sys.stderr, "You cannot specify any time options along with --qr-time-image"
        sys.exit(1)
    if options.tcam==None: options.tcam="00:00:00"
    if options.tgps==None: options.tgps="00:00:00"
    if options.offset is not None and options.timezone is not None:
        print >> sys.stderr, "You cannot specify both timezone and offset. Please choose one."
        sys.exit(1)
    if options.offset==None: options.offset=0
    if options.dir==None: options.dir="."
    if options.gpx==None:
        print >> sys.stderr, "I need a .gpx file \nType Python gpicsync.py -h for help."
        sys.exit(1)
    options.gpx=[options.gpx]
    print "\nEngage processing using the following arguments ...\n"
    print "-Directory containing the pictures:",options.dir
    print "-Path to the gpx file:",options.gpx
    if options.timezone:
        print "-Time Zone name:",options.timezone
    else:
        print "-UTC Offset (hours):",options.offset
    print "-- Camera local display time:",options.tcam
    print "-- GPS local display time:",options.tgps
    print "\n"

    geo=GpicSync(gpxFile=options.gpx,
    tcam_l=options.tcam,tgps_l=options.tgps,UTCoffset=int(options.offset),timerange=3600,timezone=options.timezone,
    qr_time_image=options.qr_time_image)

    files = list(getFileList(options.dir))

    if options.qr_time_image is not None:
        qr_time_images = [(options.qr_time_image,options.qr_time_image)]
        if options.qr_time_image == 'auto':
            qr_time_images = files
        geo.parseQrTime(qr_time_images)

    for fileName, filePath in files:
        print "\nFound fileName ",fileName," Processing now ..."
        geo.syncPicture(filePath)[0]
    print "Finished"
