
###############################################################################
#
# A tool to search for geonames metadata either:
# - the path of a geocoded picture
# - by giving a latitude and longitude values (decimal degrees format)
#
# (c) francois.schnell  francois.schnell@gmail.com
#                       http://francois.schnell.free.fr  
#
# This script is released under the GPL license v2
#
# More informations and help can be found here: http://code.google.com/p/gpicsync/
#
###############################################################################

from geoexif import *
from urllib2 import urlopen
import xml.etree.ElementTree as ET, re, decimal

class Geonames(object):
    
    def __init__(self,picName="",lat="",long=""):
        """
        Either give the path to a geocoded picture or 
        give latitute/longitude strings
        """
            
        self.lat=lat
        self.long=long
        self.picName=picName
        
        if self.lat == "" and self.long == "":
            mypicture=GeoExif(picName)
            self.lat=mypicture.readLatitude()
            self.long=mypicture.readLongitude()
            print self.lat, self.long
            
        print "latitude= ",self.lat,"  longitude= ",self.long
        
        url= "http://ws.geonames.org/findNearbyPlaceName?lat="+str(self.lat)+"&lng="+str(self.long)+"&style=full"
        print "url= ",url
        self.page = urlopen(url).read()
        print self.page
        
    def searchTag(self,tag,page):
        """
        Returns the content of a <tag> in the given page (string)
        """
        content=re.search('(<'+tag+'>.*</'+tag+'>)',page).group()
        content=content.split("<"+tag+">")[1].split("</"+tag+">")[0]
        return content
        
    def findNearbyPlace(self):
        """ find nearby place at geonames.org"""
        self.nearbyPlace=self.searchTag("name",self.page)
        print self.nearbyPlace
        return self.nearbyPlace
    
    def findDistance(self):
        """find distance in km to nearby place"""
        self.distance=self.searchTag("distance",self.page)
        self.distance=decimal.Decimal(self.distance)
        self.distance=str(self.distance.quantize(decimal.Decimal('0.01')))
        print self.distance
        return self.distance
    
    def findCountry(self):
        """ find country at geonames.org"""
        self.countryName=self.searchTag("countryName",self.page)
        print self.countryName
        return self.countryName

    def findRegion(self):
        """ find region (adminName1) at geonames.org"""
        self.regionName=self.searchTag("adminName1",self.page)
        print self.regionName
        return self.regionName
    
if __name__=="__main__":
    nearby=Geonames(picName="test.jpg")
    #nearby=Geonames(lat="48.57",long="7.84")
    nearby.findNearbyPlace()
    nearby.findDistance()
    nearby.findCountry()
    nearby.findRegion()
    
    

