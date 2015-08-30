#!/usr/bin/python

###############################################################################
# (c) francois.schnell  francois.schnell@gmail.com
#                       http://francois.schnell.free.fr 
#  
# This script is released under the GPL v2 license
#
###############################################################################

"""
A class to read longitude, latitude, time&date from track points in a gpx file.

It creates a list with a  dictionary per valid gps track point.
        Dictionary keys:
        'date': returns a string date like '2006-11-05'
        'lat': returns a string latitude like '48.5796761739'
        'lon': returns a string longitude like '7.2847080265'
        'time': returns a string 24h time (hh mm sss) like '15:21:27'
        'ele': returns the elevation if it exist and "None" otherwise
"""

import xml.etree.ElementTree as ET,re,sys,datetime

class Gpx(object):
    def __init__(self,gpxFile):
        """ create a list with the trkpts found in the .gpx file """
        self.gpx_trkpts=[]#The valid list of trackpoints
        gpx_file=""
        i=0
        for f in gpxFile:
            gpx_file+= open(gpxFile[i],'r').read()
            i+=1
        #print gpx_file
        regex=re.compile('(<trkpt.*?</trkpt>)',re.S)
        gpx_trkpts_found=regex.findall(gpx_file)
        #print gpx_trkpts_found
        print "Number of raw track points found: ",len(gpx_trkpts_found)
        i=1
        for trkpt in gpx_trkpts_found:
            if trkpt.find("time")>0: self.gpx_trkpts.append(trkpt)
            i=i+1
        regex=re.compile('(<wpt.*?</wpt>)',re.S)
        gpx_wpts_found=regex.findall(gpx_file)
        for waypoint in gpx_wpts_found:
            if waypoint.find("time")>0:
                #print "transforming waypoints into trackpoints"
                waypoint="<trkpt "+waypoint[5:-7]+"\n</trkpt>"
                #print waypoint,"\n"
                self.gpx_trkpts.append(waypoint)
        if len(self.gpx_trkpts)==0:print "Didn't find any valid trkpt :("
        print "Number of valid track points found: ",len(self.gpx_trkpts)
        #print self.gpx_trkpts

    def extract(self):
        """
        Create a list with a  dictionary per gps track point.
        Dictionary keys:
        'date': returns a string date like '2006-11-05'
        'lat': returns a string latitude like '48.5796761739'
        'lon': returns a string longitude like '7.2847080265'
        'time': returns a string 24h time (hh mm sss) like '15:21:27'
        """
        print "Extracting data from valids track points ..."
        self.geoData=[]
        for line in self.gpx_trkpts:
            #lineTree=ET.fromstring(line)
            time= re.search('(<time.*?</time>)',line).group()
            try:
                elevation=re.search('(<ele>.*?</ele>)',line).group()
                elevation=elevation.split("</ele>")[0].split("<ele>")[1]
            except:
                elevation="None"
            #print elevation
            gpst=((time[6:16].replace("-",":"))+":"+time[17:25]).split(":")
            #print ">>> gpst:",gpst
            gps_datetimeUTC=datetime.datetime(
                                            int(gpst[0]),
                                            int(gpst[1]),
                                            int(gpst[2]),
                                            int(gpst[3]),
                                            int(gpst[4]),
                                            int(gpst[5]))
            #print ">>>self.gps_datetimeUTC:",gps_datetimeUTC
            self.geoData.append({
            'date':time[6:16],
            'time':time[17:25],
            'lat':re.search('lat=".*?"',line).group().split('"')[1].strip(),
            'lon':re.search('lon=".*?"',line).group().split('"')[1].strip(),
            #'lat':lineTree.attrib["lat"].strip(),
            #'lon':lineTree.attrib["lon"].strip(),
            'ele':str(elevation).strip(),
            'datetime':gps_datetimeUTC,
            })
        #print self.geoData
        return self.geoData
    
if __name__=="__main__":
    myGpx=Gpx("test2.gpx") 
    print myGpx.extract()     
