#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

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
"""

import xml.etree.ElementTree as ET,re,sys

class Gpx(object):
    def __init__(self,gpxFile):
        """ create a list with the trkpts found in the .gpx file """
        self.gpx_trkpts=[]#The valid list of trackpoints
        gpx_file = open(gpxFile,'r').read()
        #print gpx_file
        regex=re.compile('(<trkpt.*?</trkpt>)',re.S)
        gpx_trkpts_found=regex.findall(gpx_file)
        #print gpx_trkpts_found
        print "Number of raw track points found: ",len(gpx_trkpts_found)
        i=1
        for trkpt in gpx_trkpts_found:
            if trkpt.find("time")>0: self.gpx_trkpts.append(trkpt)
            i=i+1
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
            lineTree=ET.fromstring(line)
            self.geoData.append({
            'date':lineTree[1].text[0:10],
            'time':lineTree[1].text[11:-1],
            'lat':lineTree.attrib["lat"],
            'lon':lineTree.attrib["lon"]
            })
        #print self.geoData
        return self.geoData
    
if __name__=="__main__":
    myGpx=Gpx("test2.gpx") 
    print myGpx.extract()     
