#!/usr/bin/python
# -*- coding: utf-8 -*-

###############################################################################
#
# Developer: francois.schnell   francois.schnell@gmail.com
#                               http://francois.schnell.free.fr
#
# Contributors, see: https://github.com/metadirective/GPicSync/graphs/contributors
#
# This application is released under the GPL license version 2
#
# More informations and help can be found here: https://github.com/metadirective/GPicSync
#
################################################################################

"""
GUI Part of GPicSync, a Free Software tool to geolocalize informations from:
- a GPS (.gpx file)
- pictures from a camera
The resulting pictures have latitude/longitude informations in their EXIF
meta-data and can be used with software or webservice which can read them
(like Flickr or Google Earth)
More informations at this URL:
https://github.com/metadirective/GPicSync
"""

# trying wxpython  2.9.3.1 for unicode geonames problems
from unidecode import unidecode # unicode to ascii (see issue 117 regarding Python 2.x and command line to exiftool containing unicode)

if 0:
    import wxversion
    wxversion.select("2.9")

import wx,wx.lib.colourdb

print (wx.VERSION)

import time,decimal,gettext,shutil,configparser
import os,sys,fnmatch,zipfile,subprocess
import traceback
#if sys.platform == 'win32':
#    import win32com.client
# win32.com deprecated as Google Earth API too
# will automatically open kml folder at the end of geocoding?
from _thread import start_new_thread
from PIL import Image
from PIL import JpegImagePlugin
from PIL import GifImagePlugin

from geoexif import *
from gpx import *
from gpicsync import *
from kmlGen import *
from geonames import *

import locale
codeset = locale.getdefaultlocale()[1]



#if 1: # checking wx version installed (for unicde dev)
#    import wxversion
#    print ("wxversion", wxversion.getInstalled())
#    print ("Python verion is",(sys.version))

try:
    import pytz
except ImportError:
    print ("couldn't import pytz")
    timezones = []
else:
    timezones = pytz.common_timezones
if 0: # tests
    import pytz
    timezones = pytz.common_timezones
    print (timezones)
    fzones=open("zones.txt","w")
    fzones.write(str(timezones))
    fzones.close()
    
class GUI(wx.Frame):
    """Main Frame of GPicSync"""
    def __init__(self,parent, title):
        """Initialize the main frame"""
        global bkg

        wx.Frame.__init__(self, parent, wx.ID_ANY, title="GPicSync",size=(1000,600))
        favicon = wx.Icon('gpicsync.ico', wx.BITMAP_TYPE_ICO, 16, 16)
        wx.Frame.SetIcon(self, favicon)

        self.tcam_l="00:00:00"
        self.tgps_l="00:00:00"
        self.log=False
        self.stop=False
        self.interpolation=False
        self.picDir=""
        self.timezone=None
        self.utcOffset="0"
        self.backup=True
        self.picDirDefault=""
        self.GMaps=False
        self.urlGMaps=""
        self.geonames_username="gpicsync"
        self.geonamesTags=False
        self.geoname_nearbyplace=True
        self.geoname_region=True
        self.geoname_country=True
        self.geoname_summary=True
        self.geoname_caption=True
        self.datesMustMatch=True
        self.geoname_userdefine=""
        self.maxTimeDifference="300"
        self.language="English"
        self.timeStamp=False
        self.defaultLat="0.000000"
        self.defaultLon="0.000000"
        self.geoname_IPTCsummary=""

        # Search for an eventual gpicsync.conf file
        configFile=False
        
        if sys.platform=="win32":
            confPath=os.environ["ALLUSERSPROFILE"]+"/gpicsync.conf"
            print ("Searching configuration file "+confPath)
            if os.path.isfile(confPath):
                configFile=True
                fconf=open(os.environ["ALLUSERSPROFILE"]+"/gpicsync.conf","r+")
            else: configFile= False
        # if sys.platform==("linux" or "darwin"):
        if sys.platform in ["linux", "darwin"]:
            confPath=os.path.expanduser("~/.gpicsync.conf")
            print ("Searching configuration file ~/.gpicsync.conf")
            if os.path.isfile(confPath):
                configFile=True
                fconf=open(os.path.expanduser("~/.gpicsync.conf"),"r+")
            else:
                confPath="./gpicsync.conf"
                if os.path.isfile(confPath):
                    configFile=True
                    fconf=open(confPath,"r+")
                else:
                    configFile=False
        if configFile==False:
            print ("Couldn't find the configuration file.")
            dialog=wx.MessageDialog(self,message="Couldn't find the configuration file",
            style=wx.OK|wx.CANCEL|wx.ICON_INFORMATION)
            dialog.ShowModal()
            wx.CallAfter(self.consolePrint,"\n"+"Couldn't find the configuration file."+"\n")
            
        print ("Attempting to read the configuration file...")
        #try: 
        if configFile!=False:   
            conf = configparser.ConfigParser()
            conf.read_file(fconf) #parse the config file
            if conf.has_option("gpicsync","timezone") == True:
                self.timezone=conf.get("gpicsync","timezone")
                if self.timezone=="": self.timezone=None
                print ("Timezone is :"+str(self.timezone))
            if conf.has_option("gpicsync","UTCOffset") == True:
                self.utcOffset=conf.get("gpicsync","utcoffset")
            if conf.has_option("gpicsync","backup") == True:
                self.backup=eval(conf.get("gpicsync","backup"))
            if conf.has_option("gpicsync","urlGMaps") == True:
                self.urlGMaps=conf.get("gpicsync","urlGMaps")
            if conf.has_option("gpicsync","geonamesTags") == True:
                self.geonamesTags=eval(conf.get("gpicsync","geonamesTags"))
            if conf.has_option("gpicsync","interpolation") == True:
                self.interpolation=eval(conf.get("gpicsync","interpolation"))
            if conf.has_option("gpicsync","datesMustMatch") == True:
                self.datesMustMatch=eval(conf.get("gpicsync","datesMustMatch"))
            if conf.has_option("gpicsync","log") == True:
                self.log=eval(conf.get("gpicsync","log"))
            if conf.has_option("gpicsync","GMaps") == True:
                self.GMaps=eval(conf.get("gpicsync","GMaps"))
            if conf.has_option("gpicsync","UTCOffset") == True:
                self.utcOffset=conf.get("gpicsync","UTCOffset")
            if conf.has_option("gpicsync","maxTimeDifference") == True:
                self.maxTimeDifference=conf.get("gpicsync","maxTimeDifference")
            if conf.has_option("gpicsync","language") == True:
                self.language=conf.get("gpicsync","language")
            if conf.has_option("gpicsync","geonames_username") == True:
                geonames_username_fromConf=conf.get("gpicsync","geonames_username")
                print ("reading from conf file geonames_username", geonames_username_fromConf, type(geonames_username_fromConf))
                if geonames_username_fromConf not in ["","gpicsync"]: 
                    self.geonames_username=geonames_username_fromConf
                print ("This unsername for geonames will be used:", self.geonames_username)
            if conf.has_option("gpicsync","geoname_nearbyplace") == True:
                self.geoname_nearbyplace=eval(conf.get("gpicsync","geoname_nearbyplace"))
            if conf.has_option("gpicsync","geoname_region") == True:
                self.geoname_region=eval(conf.get("gpicsync","geoname_region"))
            if conf.has_option("gpicsync","geoname_country") == True:
                self.geoname_country=eval(conf.get("gpicsync","geoname_country"))
            if conf.has_option("gpicsync","geoname_summary") == True:
                self.geoname_summary=eval(conf.get("gpicsync","geoname_summary"))
            if conf.has_option("gpicsync","geoname_userdefine") == True:
                self.geoname_userdefine=conf.get("gpicsync","geoname_userdefine")
            if conf.has_option("gpicsync","geoname_caption") == True:
                self.geoname_caption=eval(conf.get("gpicsync","geoname_caption"))
            if conf.has_option("gpicsync","geoname_IPTCsummary") == True:
                self.geoname_IPTCsummary=conf.get("gpicsync","geoname_IPTCsummary")
            if conf.has_option("gpicsync","defaultdirectory") == True:
                self.picDir=conf.get("gpicsync","defaultdirectory")
            if conf.has_option("gpicsync","getimestamp") == True:
                self.timeStamp=eval(conf.get("gpicsync","getimestamp"))
            fconf.close()        
            print ("Finished reading the conf. file")
        #except:
        if 0:
            wx.CallAfter(self.consolePrint,"\n"
            +"An error happened while reading the configuration file."+"\n")
        try:
            #print self.language
            locale_dir="locale"
            if self.language=="system":
                lang = gettext.translation('gpicsync-GUI', locale_dir, codeset=codeset)
                lang.install(unicode=True)
            elif self.language=="French":
                lang = gettext.translation('gpicsync-GUI', locale_dir, languages=['fr'], codeset=codeset)
                lang.install(unicode=True)
            elif self.language=="Italian":
                lang = gettext.translation('gpicsync-GUI', locale_dir, languages=['it'], codeset=codeset)
                lang.install(unicode=True)
            elif self.language=="German":
                #lang = gettext.translation('gpicsync-GUI', locale_dir, languages=['de'], codeset=codeset)
                lang = gettext.translation('gpicsync-GUI', locale_dir, languages=['de'])
                lang.install(unicode=True)
            elif self.language=="S.Chinese":
                lang = gettext.translation('gpicsync-GUI', locale_dir, languages=['zh_CN'], codeset=codeset)
                lang.install(unicode=True)
            elif self.language=="T.Chinese":
                lang = gettext.translation('gpicsync-GUI', locale_dir, languages=['zh_TW'], codeset=codeset)
                lang.install(unicode=True)
            elif self.language=="Catalan":
                lang = gettext.translation('gpicsync-GUI', locale_dir, languages=['ca'], codeset=codeset)
                lang.install(unicode=True)
            elif self.language=="Spanish":
                lang = gettext.translation('gpicsync-GUI', locale_dir, languages=['es'], codeset=codeset)
                lang.install(unicode=True)
            elif self.language=="Polish":
                lang = gettext.translation('gpicsync-GUI', locale_dir, languages=['pl'], codeset=codeset)
                lang.install(unicode=True)
            elif self.language=="Dutch":
                lang = gettext.translation('gpicsync-GUI', locale_dir, languages=['nl'], codeset=codeset)
                lang.install(unicode=True)
            elif self.language=="Portuguese":
                lang = gettext.translation('gpicsync-GUI', locale_dir, languages=['pt'], codeset=codeset)
                lang.install(unicode=True)
            elif self.language=="Brazilian Portuguese":
                lang = gettext.translation('gpicsync-GUI', locale_dir, languages=['pt_BR'], codeset=codeset)
                lang.install(unicode=True)
            elif self.language=="Czech":
                lang = gettext.translation('gpicsync-GUI', locale_dir, languages=['cs'], codeset=codeset)
                lang.install(unicode=True)
            elif self.language=="Russian":
                lang = gettext.translation('gpicsync-GUI', locale_dir, languages=['ru'], codeset=codeset)
                lang.install(unicode=True)
            else:
                gettext.install('gpicsync-GUI', "None",unicode=True)
        except:
            print ("Couldn't load translation.")
        del locale_dir
        #####   Menus  #####

        bkg=wx.Panel(self)
        #bkg.SetBackgroundColour((244,180,56))
        menuBar=wx.MenuBar()
        menu1=wx.Menu()
        timeShift=menu1.Append(wx.ID_NEW, "",("Local time correction"))
        languageChoice=menu1.Append(wx.ID_NEW, "",("Language"))
        self.Bind(wx.EVT_MENU,self.languageApp,languageChoice)
        if sys.platform == 'win32':
            configFile=menu1.Append(wx.NewIdRef(count=1),("Configuration file"))
            self.Bind(wx.EVT_MENU,self.showConfig,configFile)
        menuBar.Append(menu1,("&Options"))
        menu2=wx.Menu()
        about=menu2.Append(wx.ID_NEW, "",("About..."))
        menuTools=wx.Menu()
        menuBar.Append(menuTools,("&Tools"))
        exifReader=menuTools.Append(wx.ID_NEW, "",("EXIF reader"))
        exifGeoWriter=menuTools.Append(wx.ID_NEW, "",("EXIF writer"))
        renameToolMenu=menuTools.Append(wx.ID_NEW, "",("Geo-Rename pictures"))
        gpxInspectorMenu=menuTools.Append(wx.ID_NEW, "",("GPX Inspector"))
        kmzGeneratorMenu=menuTools.Append(wx.ID_NEW, "",("KMZ Generator"))
        menuBar.Append(menu2,("&Help"))
        statusBar=self.CreateStatusBar()
        self.Bind(wx.EVT_MENU,self.localtimeFrame,timeShift)
        self.Bind(wx.EVT_MENU,self.aboutApp,about)
        self.Bind(wx.EVT_MENU,self.exifFrame,exifReader)
        self.Bind(wx.EVT_MENU,self.geoWriterFrame,exifGeoWriter)
        self.Bind(wx.EVT_MENU,self.renameFrame,renameToolMenu)
        self.Bind(wx.EVT_MENU,self.gpxInspectorFrame,gpxInspectorMenu)
        self.Bind(wx.EVT_MENU,self.kmzGeneratorFrame,kmzGeneratorMenu)

        #####   Mains panel widgets definitions #####

        # Pictures dir and Gpx search buttons
        dirButton=wx.Button(bkg,size=(150,-1),label=("Pictures folder"))
        gpxButton=wx.Button(bkg,size=(150,-1),label=("GPS file"))
        self.dirEntry=wx.TextCtrl(bkg)
        self.gpxEntry=wx.TextCtrl(bkg)
        self.Bind(wx.EVT_BUTTON, self.findPictures, dirButton)
        self.Bind(wx.EVT_BUTTON, self.findGpx, gpxButton)

        # Commands buttons (sync,quit,stop,etc)
        syncButton=wx.Button(bkg,size=(250,-1),label=(" Synchronise ! "))
        quitButton=wx.Button(bkg,label=("Quit"),size=(-1,-1))
        quitAndSaveButton=wx.Button(bkg,label=("Quit and save settings"),size=(-1,-1))
        stopButton=wx.Button(bkg,label=("Stop"),size=(-1,-1))
        clearButton=wx.Button(bkg,label=("Clear"),size=(-1,-1))
        if sys.platform != 'win32':
            viewInGEButton=wx.Button(bkg,label=("View in Google Earth"),size=(-1,-1))
        self.Bind(wx.EVT_BUTTON, self.syncPictures, syncButton)
        self.Bind(wx.EVT_BUTTON, self.exitApp,quitButton)
        self.Bind(wx.EVT_BUTTON, self.exitAppSave,quitAndSaveButton)
        self.Bind(wx.EVT_BUTTON, self.stopApp,stopButton)
        self.Bind(wx.EVT_BUTTON, self.clearConsole,clearButton)
        if sys.platform != 'win32':
            self.Bind(wx.EVT_BUTTON, self.viewInGE,viewInGEButton)

        # Main Options box
        optionPrebox=wx.StaticBox(bkg, -1, ("Options:"))
        optionbox=wx.StaticBoxSizer(optionPrebox, wx.VERTICAL)

        # Elevation options
        eleLabel=wx.StaticText(bkg, -1," "+("Elevation")+":")
        eleList=[("Clamp to the ground"),
        ("absolute value (for flights)"),("absolute value + extrude (for flights)")]
        self.elevationChoice=wx.Choice(bkg, -1, (-1,-1), choices = eleList)
        self.elevationChoice.SetSelection(0)

        # Google Earth Icons choice
        iconsLabel=wx.StaticText(bkg, -1," "+("Icons")+":")
        iconsList=[("picture thumb"),
        ("camera icon")]
        self.iconsChoice=wx.Choice(bkg, -1, (-1,-1), choices = iconsList)
        self.iconsChoice.SetSelection(0)

        # Geonames options
        tmp1=("Geonames in specific IPTC fields")
        tmp2=("Geonames in XMP format")
        gnOptList=[("Geonames in IPTC + HTML Summary in IPTC caption"),("Geonames in IPTC"),
                   ("Geonames/geotagged in EXIF keywords + HTML summary in IPTC caption"),("Geonames/geotagged in EXIF keywords")]
        self.gnOptChoice=wx.Choice(bkg, -1, (-1,-1), choices = gnOptList)
        self.gnOptChoice.SetSelection(0)

        # UTC value and timezone
        self.utcLabel = wx.StaticText(bkg, -1,("UTC Offset="))
        self.utcEntry=wx.TextCtrl(bkg,size=(40,-1))
        self.utcEntry.SetValue(self.utcOffset)
        if timezones:
            #if 1:
            tzLabel = wx.StaticText(bkg, -1,("Select time zone:"))
            self.tzButton = wx.Button(bkg, -1, ("Manual UTC offset"), size=(150,-1), style=wx.BU_LEFT)
            if self.timezone:
                self.tzButton.SetLabel(self.timezone)
                self.utcLabel.Disable()
                self.utcEntry.Disable()
            self.tzMenu = wx.Menu()
            manualTZmenu = self.tzMenu.Append(wx.ID_NEW, "", ("Manual UTC offset"))
            self.Bind(wx.EVT_MENU, self.manualTZ, manualTZmenu)
            tz_regions = {}
            for i,item in enumerate(timezones):
                items = item.split('/')
                reg = ""
                menu = self.tzMenu
                for r in items[:-1]:
                    reg += '/' + r
                    if reg not in tz_regions:
                        newmenu = wx.Menu()
                        menu.AppendMenu(-1, r, newmenu)
                        menu = newmenu
                        tz_regions[reg] = menu
                    else:
                        menu = tz_regions[reg]
                z = items[-1]
                menu.Append(3000+i, z)
                self.Bind(wx.EVT_MENU, self.selectTZ, id=3000+i)
            self.Bind(wx.EVT_BUTTON, self.tzMenuPopup, self.tzButton)

        # Timerange
        timerangeLabel=wx.StaticText(bkg, -1,("Geocode picture only if time difference to nearest track point is below (seconds)="))
        self.timerangeEntry=wx.TextCtrl(bkg,size=(40,-1))
        self.timerangeEntry.SetValue(self.maxTimeDifference)

        # Log file,  dateCheck (deprecated)
        self.logFile=wx.CheckBox(bkg,-1,("Create a log file in picture folder"))
        self.logFile.SetValue(self.log)
        self.dateCheck=wx.CheckBox(bkg,-1,("Dates must match"))
        self.dateCheck.SetValue(self.datesMustMatch)
        self.dateCheck.Hide()

        # Google Earth and Google Maps
        self.geCheck=wx.CheckBox(bkg,-1,("Create a Google Earth file")+": ")
        self.geCheck.SetValue(True)
        self.geCheck.Hide()
        geInfoLabel=wx.StaticText(bkg, -1," "+"[Google Earth]->")
        self.geTStamps=wx.CheckBox(bkg,-1,("with TimeStamp"))
        self.geTStamps.SetValue(self.timeStamp)
        self.gmCheck=wx.CheckBox(bkg,-1,("Google Maps export, folder URL="))
        self.gmCheck.SetValue(self.GMaps)
        self.urlEntry=wx.TextCtrl(bkg,size=(500,-1))
        self.urlEntry.SetValue(self.urlGMaps)

        # backup, interpolations mod and geonames
        self.backupCheck=wx.CheckBox(bkg,-1,("backup pictures"))
        self.backupCheck.SetValue(self.backup)
        self.interpolationCheck=wx.CheckBox(bkg,-1,("interpolation"))
        self.interpolationCheck.SetValue(self.interpolation)
        self.geonamesCheck=wx.CheckBox(bkg,-1,("add geonames and geotagged"))
        self.geonamesCheck.SetValue(self.geonamesTags)
        self.Bind(wx.EVT_CHECKBOX,self.geonamesMessage,self.geonamesCheck)

        # Main output text console
        self.consoleEntry=wx.TextCtrl(bkg,style=wx.TE_MULTILINE | wx.HSCROLL)

        ##### GUI LAYOUT / SIZERS #####

        # directory and GPX choices sizer
        dirChoiceBox=wx.BoxSizer()
        dirChoiceBox.Add(dirButton,proportion=0,flag=wx.LEFT,border=5)
        dirChoiceBox.Add(self.dirEntry,proportion=1,flag=wx.EXPAND)
        gpxChoiceBox=wx.BoxSizer()
        gpxChoiceBox.Add(gpxButton,proportion=0,flag=wx.LEFT,border=5)
        gpxChoiceBox.Add(self.gpxEntry,proportion=1,flag=wx.EXPAND)

        # Google Earth elevation and time stamp horizontal sizer
        gebox=wx.BoxSizer()
        gebox.Add(geInfoLabel,flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL,border=10)
        gebox.Add(iconsLabel,flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=10)
        gebox.Add(self.iconsChoice,flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=10)
        gebox.Add(eleLabel,flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=10)
        gebox.Add(self.elevationChoice,flag= wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=10)
        gebox.Add(self.geTStamps,flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=10)

        # Google maps export and associated URL
        gmbox=wx.BoxSizer()
        gmbox.Add(self.gmCheck,proportion=0,flag=wx.EXPAND| wx.LEFT,border=10)
        gmbox.Add(self.urlEntry,proportion=0,flag=wx.EXPAND| wx.ALL,border=1)

        # line with log check, interpolation check and backup check
        settingsbox=wx.BoxSizer()
        settingsbox.Add(self.logFile,proportion=0,flag=wx.LEFT| wx.ALL,border=10)
        #settingsbox.Add(self.dateCheck,proportion=0,flag=wx.LEFT| wx.ALL,border=10)
        settingsbox.Add(self.interpolationCheck,proportion=0,flag=wx.LEFT| wx.ALL,border=10)
        settingsbox.Add(self.backupCheck,proportion=0,flag=wx.EXPAND| wx.ALL,border=10)

        # Image preview box
        prebox=wx.StaticBox(bkg, -1, ("Image preview:"),size=(200,200))
        previewbox=wx.StaticBoxSizer(prebox, wx.VERTICAL)
        self.imgWhite=wx.Image('default.jpg', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.imgPrev=wx.StaticBitmap(bkg,-1,self.imgWhite,size=(160,160))#style=wx.SIMPLE_BORDER
        previewbox.Add(self.imgPrev, 0, flag= wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL,border=10)

        # Geonames line
        gnhbox=wx.BoxSizer()
        gnhbox.Add(self.geonamesCheck,proportion=0,flag=wx.EXPAND| wx.LEFT,border=10)
        gnhbox.Add(self.gnOptChoice,proportion=0,flag=wx.EXPAND| wx.LEFT,border=10)

        # UTC and timezone line
        utcBox=wx.BoxSizer()
        if timezones:
            utcBox.Add(tzLabel,proportion=0,flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL,border=10)
            utcBox.Add(self.tzButton,proportion=0,flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL,border=10)
        utcBox.Add(self.utcLabel,proportion=0,flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL,border=10)
        utcBox.Add(self.utcEntry,proportion=0,flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL,border=10)

        # Timerange line
        rangeBox = wx.BoxSizer()
        rangeBox.Add(timerangeLabel,proportion=0,flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL,border=10)
        rangeBox.Add(self.timerangeEntry,proportion=0,flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL,border=10)

        # commands line
        commandsBox=wx.BoxSizer()
        commandsBox.Add(syncButton,proportion=0,flag=wx.LEFT,border=5)
        commandsBox.Add(stopButton,proportion=0,flag=wx.LEFT,border=5)
        commandsBox.Add(clearButton,proportion=0,flag=wx.LEFT,border=5)
        if sys.platform != 'win32':
            commandsBox.Add(viewInGEButton,proportion=0,flag=wx.LEFT,border=5)
        commandsBox.Add(quitButton,proportion=0,flag=wx.LEFT,border=5)
        commandsBox.Add(quitAndSaveButton,proportion=0,flag=wx.LEFT,border=5)

        # select picture directory and GPX box
        headerbox=wx.BoxSizer(wx.VERTICAL)
        headerbox.Add(dirChoiceBox,proportion=0,flag=wx.EXPAND | wx.ALL,border=5)
        headerbox.Add(gpxChoiceBox,proportion=0,flag=wx.EXPAND | wx.ALL,border=5)

        optionbox.Add(gebox,proportion=0,flag=wx.ALL,border=7)
        optionbox.Add(gmbox,proportion=0,flag=wx.ALL,border=7)
        optionbox.Add(settingsbox,proportion=0,flag=wx.ALL,border=7)
        optionbox.Add(gnhbox,proportion=0,flag=wx.ALL,border=7)

        # Options box + picture preview sizer
        middlebox=wx.BoxSizer()
        middlebox.Add(optionbox,proportion=1,flag=wx.LEFT,border=15)
        middlebox.Add(previewbox,proportion=0,flag=wx.LEFT,border=20)

        footerbox=wx.BoxSizer(wx.VERTICAL)
        footerbox.Add(utcBox,proportion=0,flag=wx.EXPAND | wx.ALL,border=5)
        footerbox.Add(rangeBox,proportion=0,flag=wx.EXPAND | wx.ALL,border=5)
        footerbox.Add(commandsBox,proportion=0,flag=wx.EXPAND | wx.ALL,border=5)
        footerbox.Add(self.consoleEntry,proportion=1,flag=wx.EXPAND | wx.LEFT, border=5)

        allBox= wx.BoxSizer(wx.VERTICAL)
        allBox.Add(headerbox,proportion=0,flag=wx.EXPAND | wx.ALL,border=5)
        allBox.Add(middlebox,proportion=0,flag=wx.EXPAND | wx.ALL,border=5)
        allBox.Add(footerbox,proportion=1,flag=wx.EXPAND | wx.ALL,border=5)

        #bkg.SetSizer(vbox)
        bkg.SetSizer(allBox)

        self.SetMenuBar(menuBar)
        self.Show(True)
        if sys.platform == 'darwin':
            self.SetSize(self.GetSize()+(100,50))

        if sys.platform == 'win32':
            self.exifcmd = 'exiftool.exe'
        else:
            self.exifcmd = 'exiftool'
        
        if self.geonamesTags==True:
                    self.geonamesMessage(None)
    
    def geonamesMessage(self,evt):
        """Message to show in console if the user check the geonames check box """
        if self.geonames_username in ["","gpicsync"]: 
            if self.geonamesCheck.GetValue() ==  True:
                wx.CallAfter(self.consolePrint,("For better Geonames disponibility it is highly recommended to get your own free username account at http://www.geonames.org")+"\n")
                wx.CallAfter(self.consolePrint,("Your username can then be set in Menu option > configuration file > geonames_username=YourUserName. Save in Notepad, then 'quit' gpicsync (not 'quit and save settings') and reload.")+"\n")
                wx.CallAfter(self.consolePrint,("More informations for the Geonames webservice can be find at http://www.geonames.org/export/")+"\n")
            
    def writeConfFile(self):
        """Write the whole configuration file"""
        try:
            fconf=open(os.environ["ALLUSERSPROFILE"]+"/gpicsync.conf","r+")
        except:
            fconf=open(os.path.expanduser("~/.gpicsync.conf"),"w")
        header="#This is a configuration file for GPicSync geocoding software\n"+\
        "#Read the comments below to see what you can set. Boolean value (True or False) and\n"+\
        "#the default language option must always begin with a Capital Letter\n\n[gpicsync]\n\n"
        fconf.write(header)
        fconf.write("#Default language at start-up that you can also change in 'options'>'languages'\n")
        fconf.write("language="+self.language+"\n\n")
        fconf.write("#Default Time Zone\n")
        if self.timezone:
            fconf.write("timezone="+str(self.timezone)+"\n\n")
        else:
            fconf.write("timezone=\n\n")
        fconf.write("#Default UTC Offset\n")
        fconf.write("utcoffset="+self.utcEntry.GetValue()+"\n\n")
        fconf.write("#geocode picture only if time difference to nearest trackpoint is below X seconds\n")
        fconf.write("maxtimedifference="+str(self.timerangeEntry.GetValue())+"\n\n")
        fconf.write("#Backup pictures by default (True or False)\n")
        fconf.write("backup="+str(self.backupCheck.GetValue())+"\n\n")
        fconf.write("#geolocalize pictures by default only if dates match by default (True or False)\n")
        fconf.write("datesmustmatch="+str(self.dateCheck.GetValue())+"\n\n")
        fconf.write("#Enable TimeStamp option for the Google Earth doc.kml file (True or False)\n")
        fconf.write("getimestamp="+str(self.geTStamps.GetValue())+"\n\n")
        fconf.write("#Create a Google Map export (doc-web.kml) by default (True or False)\n")
        fconf.write("gmaps="+str(self.gmCheck.GetValue())+"\n\n")
        fconf.write("#Default base URL for Google Maps export\n")
        fconf.write("urlgmaps="+self.urlEntry.GetValue()+"\n\n")
        fconf.write("#Use the interpolation mode by default (True or False)\n")
        fconf.write("interpolation="+str(self.interpolationCheck.GetValue())+"\n\n")
        fconf.write("#Create a log file by default\n")
        fconf.write("log="+str(self.logFile.GetValue())+"\n\n")
        fconf.write("#For better Geonames disponibility (cap usage) consider creating a free username account at http://www.geonames.org/login\n")
        fconf.write("geonames_username="+self.geonames_username+"\n")
        fconf.write("#Add geonames and geotagged in EXIF by default (True or False) and select the ones you want\n")
        fconf.write("geonamestags="+str(self.geonamesCheck.GetValue())+"\n")
        fconf.write("geoname_nearbyplace="+str(self.geoname_nearbyplace)+"\n")
        fconf.write("geoname_region="+str(self.geoname_region)+"\n")
        fconf.write("geoname_country="+str(self.geoname_country)+"\n")
        fconf.write("geoname_summary="+str(self.geoname_summary)+"\n")
        fconf.write("geoname_userdefine="+self.geoname_userdefine+"\n\n")
        fconf.write("#Add summary in IPTC with the following variables (if you use quotes escape them: \\\"  ):\n")
        fconf.write("#{LATITUDE} {LONGITUDE} {DISTANCETO} {NEARBYPLACE} {REGION} {COUNTRY} {ORIENTATION} \n")
        fconf.write("geoname_caption="+str(self.geoname_caption)+"\n")
        fconf.write("geoname_IPTCsummary="+str(self.geoname_IPTCsummary)+"\n\n")
        fconf.write("#Set default or last directory automatically used\n")
        fconf.write("Defaultdirectory="+self.picDir)
        fconf.write("")
        fconf.close()

    def showConfig(self,evt):
        """open the configuration file in notepad.exe"""
        os.popen('notepad.exe "%s"'% (os.environ["ALLUSERSPROFILE"]+"/gpicsync.conf"))
        wx.CallAfter(self.consolePrint,"\n"+("If you've changed and saved the configuration file you should restart the application to take effect.")+"\n")

    def consolePrint(self,msg):
        """
        Print the given message in the console window
        (GUI safe to call with a CallAfter in threads to avoid refresh problems)
        """
        if 0:
            self.consoleEntry.AppendText(msg.decode( 'utf-8', 'ignore' ))
        if 1:
            self.consoleEntry.AppendText(msg)

    def imagePreview(self,prevPath=""):
        """ GUI Image preview"""
        Img=wx.Image(prevPath,wx.BITMAP_TYPE_JPEG)
        Img.Scale(width=160,height=160)
        Img.SetRGB(0,0, 235,233,237)
        self.imgPrev.SetBitmap(self.imgWhite)
        self.imgPrev.SetBitmap(wx.BitmapFromImage(Img))

    def languageApp(self,evt):
        """
        select a language to display the GUI with
        """
        choices = [ 'system', 'Catalan','S.Chinese','T.Chinese','Czech','Dutch','English', 'French',
        'German','Italian','Polish','Portuguese','Brazilian Portuguese','Russian','Spanish']
        dialog=wx.SingleChoiceDialog(self,("Choose a language"),("languages choice"),choices)
        dialog.SetSelection(choices.index(self.language))
        if dialog.ShowModal() == wx.ID_OK:
            choice=dialog.GetStringSelection()
            print ("choice is : ", choice)
            self.language=choice
            wx.CallAfter(self.consolePrint,"\n"+"Next time you launch GPicSync it will be in "+self.language+".\n")
            self.writeConfFile()
            dialog.Destroy()
        else:
            dialog.Destroy()

    def aboutApp(self,evt):
        """An about message dialog"""
        text="GPicSync  1.33 - 2014 - \n\n"\
        +"GPicSync is Free Software (GPL v2)\n\n"\
        +("More informations and help:")+"\n\n"+\
        "https://github.com/metadirective/GPicSync"+"\n\n"\
        +"2014 - notfrancois AT gmail.com"
        dialog=wx.MessageDialog(self,message=text,
        style=wx.OK|wx.CANCEL|wx.ICON_INFORMATION)
        dialog.ShowModal()

    def geoWriterFrame(self,evt):
        """ Frame to manually write latitude/longitude in the EXIF header of the picture"""
        self.winGeoFrame=wx.Frame(win,size=(300,300),title=("Manual latitude/longitude EXIF writer"))
        bkg=wx.Panel(self.winGeoFrame)
        instructionLabel = wx.StaticText(bkg, -1,("Enter coordinates in decimal degrees"))
        latLabel = wx.StaticText(bkg, -1,("Latitude")+":")
        self.latEntry=wx.TextCtrl(bkg,size=(100,-1))
        self.latEntry.SetValue(str(self.defaultLat))
        lonLabel = wx.StaticText(bkg, -1,("Longitude")+":")
        self.lonEntry=wx.TextCtrl(bkg,size=(100,-1))
        self.lonEntry.SetValue(str(self.defaultLon))
        eleLabel = wx.StaticText(bkg, -1,("Eventual elevation (meters)")+":")
        self.eleEntry=wx.TextCtrl(bkg,size=(100,-1))
        selectButton=wx.Button(bkg,size=(-1,-1),label=("Select and write in picture(s)"))
        self.Bind(wx.EVT_BUTTON, self.manualGeoWrite, selectButton)
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.Add(instructionLabel,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=20)
        vbox.Add(latLabel,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=5)
        vbox.Add(self.latEntry,proportion=0,flag=wx.ALIGN_CENTER,border=5)
        vbox.Add(lonLabel,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=5)
        vbox.Add(self.lonEntry,proportion=0,flag=wx.ALIGN_CENTER,border=5)
        vbox.Add(eleLabel,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=5)
        vbox.Add(self.eleEntry,proportion=0,flag=wx.ALIGN_CENTER,border=5)
        vbox.Add(selectButton,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=20)
        bkg.SetSizer(vbox)
        self.winGeoFrame.Show()

    def manualGeoWrite(self,evt):
        """manually write latitude/longitude in the EXIF header of the picture"""
        picture=wx.FileDialog(self,style=wx.FD_MULTIPLE)
        picture.ShowModal()
        self.winGeoFrame.Hide()
        latitude=self.latEntry.GetValue()
        self.defaultLat=latitude
        longitude=self.lonEntry.GetValue()
        elevation=self.eleEntry.GetValue()
        self.winGeoFrame.Close()
        self.defaultLon=longitude
        self.pathPictures=picture.GetPaths()
        #print "###############", self.pathPictures
        wx.CallAfter(self.consolePrint,"\n---\n")
        def writeEXIF(latitude,longitude,latRef,longRef):
            if len(self.pathPictures)!=0:
                for pic in self.pathPictures:
                    wx.CallAfter(self.consolePrint,("Writing GPS latitude/longitude ")+\
                    latRef+latitude+" / "+longRef+longitude+" ---> "+os.path.basename(pic)+"\n")
                    if elevation!="":
                        eleExif= " -GPSAltitude="+elevation+" -GPSAltitudeRef=0 "
                    else: eleExif=""

                    """
                    order='%s -n "-DateTimeOriginal>FileModifyDate" \
                     -GPSLatitude=%s -GPSLongitude=%s %s\
                     -GPSLatitudeRef=%s -GPSLongitudeRef=%s "%s" '\
                    %(self.exifcmd,latitude,longitude,eleExif, latRef,longRef,pic)
                    print order
                    """

                    os.popen('%s -n "-DateTimeOriginal>FileModifyDate" \
                     -GPSLatitude=%s -GPSLongitude=%s %s\
                     -GPSLatitudeRef=%s -GPSLongitudeRef=%s "%s" '\
                    %(self.exifcmd,latitude,longitude,eleExif, latRef,longRef,pic))
                wx.CallAfter(self.consolePrint,"---"+("Finished")+"---\n")
        try:
            if float(latitude)>0:
                latRef="N"
            else: latRef="S"
            if float(longitude)>0:
                    longRef="E"
            else: longRef="W"
            latitude=str(abs(float(latitude)))
            longitude=str(abs(float(longitude)))
            start_new_thread(writeEXIF,(latitude,longitude,latRef,longRef))
        except:
            wx.CallAfter(self.consolePrint,"\n"+("Latitude or Longitude formats are not valid: no geocoding happened.")+"\n")


    def viewInGE(self,evt):
        """View a local kml file in Google Earth"""
        if sys.platform == 'win32':
            #googleEarth =win32com.client.Dispatch("GoogleEarth.ApplicationGE")
            #com interface to Google Earth removed from Google
            pass
        else:
            if sys.platform.find("linux")!=-1:
                p=subprocess.Popen(['which', 'googleearth', 'google-earth'], stdout=subprocess.PIPE)

                googleEarthPaths= p.stdout.read().splitlines()
                if(len(googleEarthPaths) > 0):
                    # take first found google earth binary
                    googleEarth = googleEarthPaths[0]
                else:
                    googleEarth= os.path.expanduser("~/google-earth/googleearth")
            else:
                if sys.platform == 'darwin':
                     googleEarth= "/Applications/Google\ Earth.app/Contents/MacOS/Google\ Earth"
        try:
            path=self.picDir+'/doc.kml'
            print ("path=",path)
        except:
            text=("To visualize the results in Google Earth you must either:")+"\n\n"\
            +("- finish a synchronisation")+"\n"\
            +("- select a folder you've already synchronized or double-click on the kml file in his folder'")
            wx.CallAfter(self.consolePrint,text)
        try:
            if sys.platform == 'win32':
                #googleEarth.OpenKmlFile(path,True)
                pass
            else:
                if sys.platform.find("linux")!=-1:
                    def goGELinux():
                        os.system(googleEarth +" "+path)
                    start_new_thread(goGELinux,())
                else:
                    if sys.platform == 'darwin':
                        def goGEOSX():
                            os.system(googleEarth +" "+path)
                        start_new_thread(goGEOSX,())
        except:
            wx.CallAfter(self.consolePrint,"\n"+_("Couldn't find or launch Google Earth")+"\n")

    def exitApp(self,evt):
        """Quit properly the app"""
        print ("Exiting the app...")
        self.Close()
        self.Destroy()
        sys.exit(1)

    def exitAppSave(self,evt):
        """Quit properly the app and save current settings in configuration file"""
        print ("Exiting the app and save settings...")
        self.writeConfFile()
        self.Close()
        self.Destroy()
        sys.exit(1)

    def stopApp(self,evt):
        """Stop current processing"""
        self.stop=True

    def clearConsole(self,evt):
        """clear the output console"""
        self.imgPrev.SetBitmap(self.imgWhite)
        self.consoleEntry.Clear()
        self.imgPrev.SetBitmap(self.imgWhite)

    def findGpx(self,evt):
        """
        Select the .gpx file to use or create one if necessary through GPSbabel
        """
        if sys.platform == 'win32':
            openGpx=wx.FileDialog(self,style=wx.FD_MULTIPLE)
        else:
            if sys.platform.find("linux")!=-1:
            	openGpx=wx.FileDialog(self)
            else:
            	if sys.platform == 'darwin':
                     openGpx=wx.FileDialog(self)
        openGpx.SetWildcard("GPX Files(*.gpx)|*.gpx|NMEA Files (*.txt)|*.txt")
        openGpx.ShowModal()
        if sys.platform == 'win32':
            self.gpxFile=openGpx.GetPaths()
        else:
            if sys.platform.find("linux")!=-1:
            	self.gpxFile=[openGpx.GetPath()]
            else:
                if sys.platform == 'darwin':
                     self.gpxFile=[openGpx.GetPath()]
        j=0
        for track in self.gpxFile:
            if os.path.basename(self.gpxFile[j]).find(".txt")>0 or\
            os.path.basename(self.gpxFile[j]).find(".TXT")>0:
                try:
                    target=self.gpxFile[j].split(".txt")[0]+".gpx"
                    babelResult=os.popen('gpsbabel -i nmea -f "%s" -o gpx -F "%s"' \
                    % (self.gpxFile[j],target)).read()
                    #print babelResult
                    self.gpxFile[j]=target
                    j+=1
                    if os.path.isfile(target)==True:
                        wx.CallAfter(self.consolePrint,\
                        ("For information, GPX file created with GPSBabel in your picture folder."))
                    else:
                        wx.CallAfter(self.consolePrint,("Possible problem with the creation of the gpx file"))

                except:
                    wx.CallAfter(self.consolePrint,("Couldn't create the necessary GPX file."))

        gpxPaths=""
        i=0
        for path in self.gpxFile:
            gpxPaths+=self.gpxFile[i]+" "
            i+=1
        self.gpxEntry.SetValue(gpxPaths)

    def findPictures(self,evt):
        """Select the folder pictures to use"""
        openDir=wx.DirDialog(self)
        # openDir.SetPath(self.picDirDefault)
        if self.picDir!="":
            openDir.SetPath(self.picDir)
        openDir.ShowModal()
        self.picDir=openDir.GetPath()
        self.dirEntry.SetValue(self.picDir)
    
    def syncPictures(self,evt):
        """Sync. pictures with the .gpx file"""
        if self.dirEntry.GetValue()=="" or self.gpxEntry.GetValue=="":
                wx.CallAfter(self.consolePrint,("You must first select a pictures folder and a GPX file.")+"\n")
        else:
            pass
        self.geCheck.SetValue(True) # Oblige the cration of a GE file anyway
        self.stop=False
        self.utcOffset=float(self.utcEntry.GetValue())#testing float for UTC
        dateProcess=self.dateCheck.GetValue()
        self.log=self.logFile.GetValue()
        self.interpolation=self.interpolationCheck.GetValue()
        timeStampOrder=self.geTStamps.GetValue()
        #print "self.utcOffset= ",self.utcOffset
        eleMode=self.elevationChoice.GetSelection()

        def sync():
            if self.dirEntry.GetValue()!="" and self.gpxEntry.GetValue!="":
                if self.timezone:
                    wx.CallAfter(self.consolePrint,"\n------\n"+("Beginning synchronization with ")\
                    +("Time zone is ")+self.timezone+\
                    (" and maximum time difference = ")+self.timerangeEntry.GetValue()+(" seconds")+"\n")
                else:
                    wx.CallAfter(self.consolePrint,"\n------\n"+("Beginning synchronization with ")\
                    +("UTC Offset =")+self.utcEntry.GetValue()+\
                    (" hours and maximum time difference = ")+self.timerangeEntry.GetValue()+(" seconds")+"\n")

            else:
                pass
            geo=GpicSync(gpxFile=self.gpxFile,tcam_l=self.tcam_l,tgps_l=self.tgps_l,timezone=self.timezone,
            UTCoffset=self.utcOffset,dateProcess=dateProcess,timerange=int(self.timerangeEntry.GetValue()),
            backup=False,interpolation=self.interpolation)

            if self.backupCheck.GetValue()==True:
                backupFolder=self.picDir+'/originals-backup-'+os.path.basename(self.picDir)+'/'
                wx.CallAfter(self.consolePrint,"\n"+
                ("Creating an 'originals-backup' folder.")+"\n")
                try:
                    os.mkdir(backupFolder)
                except:
                    print ("Couldn't create the backup folder, it maybe already exist")

            if self.geCheck.GetValue()==True:
                wx.CallAfter(self.consolePrint,"\n"+("Starting to generate a Google Earth file (doc.kml) in the picture folder ...")+" \n")
                localKml=KML(self.picDir+"/doc",os.path.basename(self.picDir),timeStampOrder=timeStampOrder,
                utc=self.utcEntry.GetValue(),eleMode=eleMode,iconsStyle=self.iconsChoice.GetSelection(),gmaps=False)
                localKml.writeInKml("\n<Folder>\n<name>Photos</name>")
                try:
                    os.mkdir(self.picDir+'/thumbs')
                except:
                    print ("Couldn't create the thumbs folder, it maybe already exist")

            if self.gmCheck.GetValue()==True:
                wx.CallAfter(self.consolePrint,"\n"+("Starting to generate a Google Map file (doc-web.kml) in the picture folder")+" ... \n")
                webKml=KML(self.picDir+"/doc-web",os.path.basename(self.picDir),url=self.urlEntry.GetValue(),
                utc=self.utcEntry.GetValue(),gmaps=True)
                webKml.path(self.gpxFile)
                webKml.writeInKml("\n<Folder>\n<name>Photos</name>")

            if self.log==True:
                try:
                    f=open(self.picDir+'/gpicsync.log','w')
                    f.write(("Geocoded with UTC Offset= ")+
                    self.utcEntry.GetValue()+(" and  Maximum time difference = ")\
                    +self.timerangeEntry.GetValue()+"\n")
                    f.write(("Pictures Folder: ")+self.picDir+"\n")
                    f.write(("GPX file: ")+self.gpxEntry.GetValue()+"\n\n")
                except:
                    pass

            for fileName in sorted(os.listdir ( self.picDir )):
                if self.stop==True: break
                if fnmatch.fnmatch ( fileName, '*.JPG' )\
                or fnmatch.fnmatch ( fileName, '*.jpg' )\
                or fnmatch.fnmatch ( fileName, '*.CR2' )\
                or fnmatch.fnmatch ( fileName, '*.cr2' )\
                or fnmatch.fnmatch ( fileName, '*.arw' )\
                or fnmatch.fnmatch ( fileName, '*.ARW' )\
                or fnmatch.fnmatch ( fileName, '*.CRW' )\
                or fnmatch.fnmatch ( fileName, '*.crw' )\
                or fnmatch.fnmatch ( fileName, '*.NEF' )\
                or fnmatch.fnmatch ( fileName, '*.nef' )\
                or fnmatch.fnmatch ( fileName, '*.PEF' )\
                or fnmatch.fnmatch ( fileName, '*.pef' )\
                or fnmatch.fnmatch ( fileName, '*.RAW' )\
                or fnmatch.fnmatch ( fileName, '*.raw' )\
                or fnmatch.fnmatch ( fileName, '*.rw2' )\
                or fnmatch.fnmatch ( fileName, '*.ORF' )\
                or fnmatch.fnmatch ( fileName, '*.orf' )\
                or fnmatch.fnmatch ( fileName, '*.DNG' )\
                or fnmatch.fnmatch ( fileName, '*.dng' )\
                or fnmatch.fnmatch ( fileName, '*.RAF' )\
                or fnmatch.fnmatch ( fileName, '*.raf' )\
                or fnmatch.fnmatch ( fileName, '*.MRW' )\
                or fnmatch.fnmatch ( fileName, '*.mrw' ):

                    print ("\nFound fileName ",fileName," Processing now ...")
                    wx.CallAfter(self.consolePrint,"\n"+("(Found ")+fileName+" ...")
                    print (self.picDir+'/'+fileName)

                    backupFolder=self.picDir+'/originals-backup-'+os.path.basename(self.picDir)+'/'

                    if self.backupCheck.GetValue()==True\
                    and os.path.isfile(backupFolder+fileName)==False:
                        shutil.copyfile(self.picDir+'/'+fileName,backupFolder+fileName)

                    #Create thumb and make a preview
                    if fnmatch.fnmatch (fileName, '*.JPG') or fnmatch.fnmatch (fileName, '*.jpg'):
                        print ("Create a thumb now!")
                        try:
                            im=Image.open(self.picDir+'/'+fileName)
                            width=int(im.size[0])
                            height=int(im.size[1])
                            if width>height:
                                max=width
                            else:
                                max=height
                            zoom=float(160.0/max)
                            im.thumbnail((int(width*zoom),int(height*zoom)))
                            im.save(self.picDir+"/thumbs/"+"thumb_"+fileName)
                            wx.CallAfter(self.imagePreview,self.picDir+"/thumbs/"+"thumb_"+fileName)
                        except:
                            print ("Warning: didn't create thumbnail, no JPG file ?")

                    result=geo.syncPicture(self.picDir+'/'+fileName)
                    wx.CallAfter(self.consolePrint,result[0]+"\n")

                    #Check if the picture have Date/Time infos, otherwise go to next pic.
                    if result[0]==" : WARNING: DIDN'T GEOCODE, no Date/Time Original in this picture.":
                        continue

                    if self.log==True:
                        try:
                            #f.write(("Processed image ")+fileName+" : "+result[0]+"\n")
                            f.write("Processed image "+unidecode(fileName)+" : "+result[0]+"\n")
                        except:
                            pass

                    if self.geCheck.GetValue()==True and result[1] !="" and result[2] !="":
                        localKml.placemark(self.picDir+'/'+fileName,lat=result[1],
                        long=result[2],width=result[3],height=result[4],timeStamp=result[5],
                        elevation=result[6])

                    if self.gmCheck.GetValue()==True and result[1] !="" and result[2] !="":
                        webKml.placemark4Gmaps(self.picDir+'/'+fileName,lat=result[1],long=result[2],width=result[3],height=result[4],elevation=result[6])

                    if self.geonamesCheck.GetValue()==True and result[1] !="" and result[2] !="": # checks if geonames checked and lat/lon exist
                        try:
                            nearby=Geonames(lat=result[1],long=result[2],username=self.geonames_username)
                        except:
                            wx.CallAfter(self.consolePrint,("Couldn't retrieve geonames data...")+"\n")
                        try:
                            if self.geoname_nearbyplace==True:
                                gnPlace=str(nearby.findNearbyPlace())
                            else: gnPlace=""
                        except:
                            print ("oooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo")
                            gnPlace=""
                        try:
                            gnDistance=str(nearby.findDistance())
                        except:
                            gnDistance=""
                        try:
                            if self.geoname_region==True:
                                gnRegion=str(nearby.findRegion())
                            else: gnRegion=""
                        except:
                            gnRegion=""
                        try:
                            if self.geoname_country==True:
                                gnCountry=str(nearby.findCountry())
                            else: 
                                gnCountry=""
                        except:
                            gnCountry=""
                        try:
                            if self.geoname_userdefine !="":
                                userdefine=self.geoname_userdefine
                            else: userdefine=""
                        except:
                            userdefine=""
                        try:
                            gnCountryCode=nearby.findCountryCode()
                        except:
                            gnCountryCode=""
                            print ("!!! Something went wrong while retreiving country code !!!")
                        try:
                            gnOrientation=nearby.findOrientation()
                        except:
                            gnOrientation=""
                            print ("!!! Something went wrong while retreiving orientation !!!")
                        #try:
                        if 1:
                            if self.geoname_summary==True:
                                gnSummary=gnDistance+"  Km to "+str(gnPlace)+"  in "+str(gnRegion)+" "+str(gnCountry)
                            else:
                                gnSummary=""
                            gnInfos="Geonames: "+gnDistance+" Km "+gnOrientation +" "+ gnPlace+" "+gnRegion+" "+gnCountry+" "+gnCountryCode
                            #print "gnInfos:",gnInfos
                            geotag="geotagged"
                            tempLat=str(decimal.Decimal(result[1]).quantize(decimal.Decimal('0.000001')))
                            tempLong=str(decimal.Decimal(result[2]).quantize(decimal.Decimal('0.000001')))
                            geotagLat="geo:lat="+tempLat
                            geotagLon="geo:lon="+tempLong
                            wx.CallAfter(self.consolePrint,gnInfos+(", writing geonames)")+"\n")

                            geonameKeywords="" # create initial geonames string command
                            exiftagOptions = []
                            exiftagOptions.append(self.exifcmd)
                            
                            print (userdefine)
                            if self.gnOptChoice.GetSelection() in [2,3]:
                                for geoname in [gnPlace,gnRegion,gnCountry,gnSummary,geotag,geotagLat,geotagLon,userdefine]:
                                    if geoname !="":
                                        geonameKeywords+=' -keywords="%s" ' % str(geoname)
                                        exiftagOptions.append((u'-keywords="%s" ' % geoname))

                            if self.geoname_caption==True:
                                gnIPTCsummary= self.geoname_IPTCsummary
                                for var in [("{LATITUDE}",tempLat),("{LONGITUDE}",tempLong),
                                ("{DISTANCETO}",gnDistance),("{NEARBYPLACE}",str(gnPlace)),
                                ("{REGION}",str(gnRegion)),("{COUNTRY}",str(gnCountry)),("{ORIENTATION}",gnOrientation)]:
                                    gnIPTCsummary=gnIPTCsummary.replace(var[0],var[1])
                                gnIPTCsummary=' -iptc:caption-abstract="'+gnIPTCsummary+'"' #took space out before -iptc
                                #print "=== gnIPTCsummary=== ",gnIPTCsummary, "======"

                            if self.gnOptChoice.GetSelection() in [0,1]:
                                if gnPlace !="": geonameKeywords+=' -iptc:city="'+str(gnPlace)+'"'
                                if gnRegion !="": geonameKeywords+=' -iptc:province-state="'+str(gnRegion)+'"'
                                if gnCountry !="": geonameKeywords+=' -iptc:Country-PrimaryLocationName="'+str(gnCountry)+'"'
                                
                                if gnPlace !="": exiftagOptions.append(('-iptc:city="'+str(gnPlace)+'"'))
                                if gnRegion !="": exiftagOptions.append(('-iptc:province-state="'+str(gnRegion)+'"'))
                                if gnCountry !="": exiftagOptions.append(('-iptc:Country-PrimaryLocationName="'+str(gnCountry)+'"'))
                                #print "*************",gnCountryCode,type(gnCountryCode)
                                if gnCountryCode !="": geonameKeywords+=' -iptc:Country-PrimaryLocationCode="'+str(gnCountryCode)+'"'
                                if gnCountryCode !="": exiftagOptions.append(('-iptc:Country-PrimaryLocationCode="'+str(gnCountryCode)+'"'))
                                if 1:
                                    geonameKeywords+=' -iptc:Sub-location="'+str(gnDistance)+" Km "+str(gnOrientation)+" "+str(gnPlace)+'"'
                                    exiftagOptions.append(('-iptc:Sub-location="'+str(gnDistance)+" Km "+str(gnOrientation)+" "+str(gnPlace)+'"'))
                                if gnPlace !="": geonameKeywords+=' -iptc:city="'+str(gnPlace)+'"'

                            if self.gnOptChoice.GetSelection() in [0,2]:
                                geonameKeywords+=str(gnIPTCsummary)
                                exiftagOptions.append(gnIPTCsummary)

                            #print "\n=== geonameKeywords ===\n", geonameKeywords,"\n======"
                            # WRITE GEONAMES
                            ## I'm stuck at writing the Geonames in utf-8 on Windows 7
                            ## It works when the script gpicsync-GUI.py is excecuted from the Eclipse but fail when gpicsync-GUI.py is excecuted from the DOS cmd.
                            ## It seems related to this issue http://bugs.python.org/issue1759845 which apparently is solved but only for Python 3 ??
                            ## Help would be appreciated !!!  :/
                            if 1:
                                # tried: str(geonameKeywords).encode(locale.getpreferredencoding())  ??
                                # tried: str(s.decode("utf-8")).encode("utf-8") 
                                # tried: -tagsfromfile @ -iptc:all -codedcharacterset=utf8
                                # tried : geonameKeywords.decode("utf-8")).encode("iso-8859-1")
                                # trying lib unidecode see unicode to ascii (see issue 117 regarding Python 2.x and command line to exiftool containing unicode)
                                #print geonameKeywords
                                # if sys.platform!=("linux" or "darwin"): # Usage of unidecode for now on windows due to above problem ( https://code.google.com/p/gpicsync/issues/detail?id=117 )
                                if sys.platform not in ["linux", "darwin"]:
                                    if 0: # in current build 1.32
                                        os.popen('%s -tagsfromfile @ -iptc:all -codedcharacterset=utf8  %s  -overwrite_original "-DateTimeOriginal>FileModifyDate"  "%s"  '%(self.exifcmd,unidecode(geonameKeywords),self.picDir+'/'+fileName))
                                    if 1: # experimental
                                        print ("!!!!!!!!!!!!!!!!!!!!! New unicode test !!!!!!!!!!!!!!!!!!!!!!!")
                                        startupinfo = subprocess.STARTUPINFO()
                                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                                        command= '%s %s  -overwrite_original "-DateTimeOriginal>FileModifyDate" "%s" '%(self.exifcmd,geonameKeywords,self.picDir+'/'+fileName)
                                        subprocess.call(command.encode("utf-8"),startupinfo=startupinfo, shell=False)
                                        
                                else: # following line contributed by hsivonen which may work on OSX / Linux ( https://code.google.com/p/gpicsync/issues/detail?id=91 )
                                    os.popen(('%s %s  -overwrite_original "-DateTimeOriginal>FileModifyDate" "%s" '%(self.exifcmd,geonameKeywords,self.picDir+'/'+fileName)))
                                    
                                #os.popen('%s -tagsfromfile @ -iptc:all -codedcharacterset=utf8 %s  -overwrite_original "-DateTimeOriginal>FileModifyDate"  "%s"  '%(self.exifcmd,str(geonameKeywords).encode("utf-8"),self.picDir+'/'+fileName))
                            
                            if 0:
                                exiftagOptions.append(u'-overwrite_original')
                                exiftagOptions.append(u'-DateTimeOriginal>FileModifyDate')
                                exiftagOptions.append(self.picDir+'/'+fileName)
                                print(exiftagOptions)
                                subprocess.call(exiftagOptions)

                        #except:
                        if 0:
                            print ("Had problem when writing geonames")
                            traceback.print_exc(file=sys.stdout)

            if self.stop==False:
                wx.CallAfter(self.consolePrint,"\n*** "+("FINISHED GEOCODING PROCESS")+" ***\n")
            if self.stop==True:
                wx.CallAfter(self.consolePrint,"\n *** "+("PROCESSING STOPPED BY THE USER")+" ***\n")
            if self.log==True: f.close()

            if self.geCheck.GetValue()==True:
                localKml.writeInKml("</Folder>\n")
                wx.CallAfter(self.consolePrint,"\n"+("Adding the GPS track log to the Google Earth kml file")+"...\n")
                localKml.path(self.gpxFile,cut=10000)
                localKml.close()
                wx.CallAfter(self.consolePrint,"\n"+("Click on the 'View in Google Earth' button to visualize the result")+".\n")
                wx.CallAfter(self.consolePrint,("( A Google Earth doc.kml file has been created in your picture folder.)")+"\n")

            if self.gmCheck.GetValue()==True:
                webKml.writeInKml("</Folder>\n")
                webKml.close()
                wx.CallAfter(self.consolePrint,("( A Google Maps doc-web.kml file has been created with the given url )")+"\n")
            wx.CallAfter(self.consolePrint,("If the geocoding process was not satisfactory, consider using the GPX inspector from Tools menu to debug your GPX")+"\n")

        start_new_thread(sync,())

    def localtimeCorrection(self,evt):
            """ Local time correction if GPS and camera wasn't synchronized """
            self.tcam_l=self.camEntry.GetValue()
            self.tgps_l=self.gpsEntry.GetValue()
            wx.CallAfter(self.consolePrint,"\n"+("A time correction has been set")+" : "+
            ("Time camera= ")+self.tcam_l+(" Time GPS= ")+self.tgps_l+" .\n")
            print ("tcam_l =",self.tcam_l)
            print ("tgps_l =",self.tgps_l)

    def quitLocaltimeCorrection(self,evt):
            self.winOpt.Close()

    def localtimeFrame(self,evt):
        """A frame for local time correction"""
        frameWidth=440
        if sys.platform == 'darwin':
            frameWidth=530
        self.winOpt=wx.Frame(win,size=(frameWidth,280),title=("Local time corrections"))
        bkg=wx.Panel(self.winOpt)
        #bkg.SetBackgroundColour('blue steel')
        text="\t"+("Use this option ONLY if your camera local time is wrong.")\
        +"\n\n"+("Indicate here the local time now displayed by your camera and GPS (hh:mm:ss)")
        utcLabel = wx.StaticText(bkg, -1,text)
        camLabel = wx.StaticText(bkg, -1,("Local time displayed now by the camera"))
        self.camEntry=wx.TextCtrl(bkg,size=(100,-1))
        self.camEntry.SetValue(self.tcam_l)
        gpsLabel = wx.StaticText(bkg, -1,("Local time displayed now by the GPS"))
        self.gpsEntry=wx.TextCtrl(bkg,size=(100,-1))
        self.gpsEntry.SetValue(self.tgps_l)
        applyButton=wx.Button(bkg,size=(130,30),label=("Apply correction"))
        quitButton=wx.Button(bkg,size=(70,30),label=("Quit"))
        self.Bind(wx.EVT_BUTTON, self.localtimeCorrection, applyButton)
        self.Bind(wx.EVT_BUTTON, self.quitLocaltimeCorrection, quitButton)

        hbox=wx.BoxSizer()
        hbox.Add(applyButton,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=20)
        hbox.Add(quitButton,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=20)

        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.Add(utcLabel,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=20)
        vbox.Add(camLabel,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=5)
        vbox.Add(self.camEntry,proportion=0,flag=wx.ALIGN_CENTER,border=5)
        vbox.Add(gpsLabel,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=5)
        vbox.Add(self.gpsEntry,proportion=0,flag=wx.ALIGN_CENTER,border=5)
        vbox.Add(hbox,proportion=0,flag=wx.ALIGN_CENTER,border=5)
        bkg.SetSizer(vbox)
        self.winOpt.Show()

    def exifFrame(self,evt):
        """A frame for the exifReader tool"""
        frameWidth=280
        if sys.platform == 'darwin':
            frameWidth=330
        self.winExifReader=wx.Frame(win,size=(frameWidth,220),title=("EXIF Reader"))
        bkg=wx.Panel(self.winExifReader)
        #bkg.SetBackgroundColour('White')
        text=("Read the EXIF metadata of the selected picture.")
        introLabel = wx.StaticText(bkg, -1,text)
        self.ExifReaderSelected=("All EXIF metadata")
        radio1=wx.RadioButton(bkg,-1,("All EXIF metadata"))
        radio2=wx.RadioButton(bkg,-1,("Date/Time/Lat./Long."))
        def onRadio(evt):
            radioSelected=evt.GetEventObject()
            self.ExifReaderSelected=radioSelected.GetLabel()
        for eachRadio in [radio1,radio2]:
            self.Bind(wx.EVT_RADIOBUTTON ,onRadio,eachRadio)
        readButton=wx.Button(bkg,size=(130,30),label=("Select a picture"))
        self.Bind(wx.EVT_BUTTON, self.readEXIF, readButton)

        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.Add(introLabel,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=20)
        vbox.Add(radio1,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=10)
        vbox.Add(radio2,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=10)
        vbox.Add(readButton,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=20)
        bkg.SetSizer(vbox)
        self.winExifReader.Show()

    def readEXIF(self,evt):
        """read the selected EXIF informations and eventually crate a thumb"""
        print ("Selected ",self.ExifReaderSelected)
        picture=wx.FileDialog(self)
        picture.ShowModal()
        pathPicture=picture.GetPath()
        if pathPicture !="" or None:
            myPicture=GeoExif(pathPicture)
            try:
                pathThumb=str(os.path.dirname(pathPicture))+"/thumbs/thumb_"+str(os.path.basename(pathPicture))
                print ("Thumb path",pathThumb)
                if os.path.isfile(pathThumb)==False:
                    if os.path.isdir(os.path.dirname(pathThumb))==False:
                        os.mkdir(os.path.dirname(pathThumb))
                    im=Image.open(pathPicture)
                    width=im.size[0]
                    height=im.size[1]
                    if width>height:max=width
                    else: max=height
                    zoom=float(160.0/max)
                    im.thumbnail((int(im.size[0]*zoom),int(im.size[1])*zoom))
                    im.save(pathThumb)
                self.imagePreview(prevPath=pathThumb)
            except:
                print ("Coudln't create a thumnail, probably not a JPG file")
            def read():
                wx.CallAfter(self.consolePrint,"\n\n"+("Selected metada ")+"\n")
                wx.CallAfter(self.consolePrint,"-------------------\n")
                if self.ExifReaderSelected==("All EXIF metadata"):
                    wx.CallAfter(self.consolePrint,pathPicture+"\n\n")
                    wx.CallAfter(self.consolePrint,myPicture.readExifAll())

                if self.ExifReaderSelected==("Date/Time/Lat./Long."):
                    dateTime=myPicture.readDateTime()
                    datetimeString=dateTime[0]+":"+dateTime[1]
                    wx.CallAfter(self.consolePrint,pathPicture+"\n\n")
                    if len(datetimeString)>5:
                        wx.CallAfter(self.consolePrint,datetimeString)
                        wx.CallAfter(self.consolePrint,"    "+("lat./long.")+"="+str(myPicture.readLatLong()))
                    else:
                        wx.CallAfter(self.consolePrint,("None"))
            start_new_thread(read,())
            self.winExifReader.Close()

    def renameFrame(self,evt):
        """A frame for the rename tool"""
        self.winRenameTool=wx.Frame(win,size=(300,220),title=("Renaming tool"))
        bkg=wx.Panel(self.winRenameTool)
        #bkg.SetBackgroundColour('White')
        text=("This tool renames your pictures with the ")+"\n"+("original time/date and lat./long.(if present)")
        introLabel = wx.StaticText(bkg, -1,text)
        readButton=wx.Button(bkg,size=(200,30),label=("Rename pictures in a folder"))
        readButtonFolder=wx.Button(bkg,size=(200,30),label=("Rename a single picture"))
        self.Bind(wx.EVT_BUTTON, self.renamePicturesInFolder, readButton)
        self.Bind(wx.EVT_BUTTON, self.renamePicture, readButtonFolder)
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.Add(introLabel,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=20)
        vbox.Add(readButton,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=10)
        vbox.Add(readButtonFolder,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=10)
        bkg.SetSizer(vbox)
        self.winRenameTool.Show()

    def renamePicture(self,evt):
        """A tool to rename pictures of a directory"""
        picture=wx.FileDialog(self)
        picture.ShowModal()
        picture.SetWildcard("*.JPG")
        self.pathPicture=picture.GetPath()
        self.winRenameTool.Close()
        if self.pathPicture !="" or None:
            wx.CallAfter(self.consolePrint,"\n"+("Beginning renaming..."))
            def rename():
                myPicture=GeoExif(self.pathPicture)
                string=myPicture.readDateTime()[0]+" "+myPicture.readDateTime()[1]
                string=string.replace(":","-")
                latlong=myPicture.readLatLong()
                if latlong==None: latlong=""
                if len(string)<5:
                    wx.CallAfter(self.consolePrint,"\n"+("Didn't find Original Time/Date for ")+self.pathPicture)
                else:
                    os.rename(self.pathPicture,os.path.dirname(self.pathPicture)+"/"+string+" "+latlong+".jpg")
                    wx.CallAfter(self.consolePrint,"\n"+("Renamed ")+os.path.basename(self.pathPicture)+" -> "+string+latlong+".jpg")
            start_new_thread(rename,())

    def renamePicturesInFolder(self,evt):
        self.stop=False
        self.winRenameTool.Close()
        openDir=wx.DirDialog(self)
        openDir.ShowModal()
        self.picDir=openDir.GetPath()
        if self.picDir!="" or None:
            wx.CallAfter(self.consolePrint,"\n"+("Beginning renaming..."))
            def rename():
                for fileName in os.listdir ( self.picDir ):
                        if self.stop==True:
                            wx.CallAfter(self.consolePrint,"\n"+("Interrupted by the user"))
                            self.stop=False
                            break
                        if fnmatch.fnmatch ( fileName, '*.JPG' )or \
                        fnmatch.fnmatch ( fileName, '*.jpg' ):
                            print (self.picDir+'/'+fileName)
                            myPicture=GeoExif(self.picDir+"/"+fileName)
                            string=myPicture.readDateTime()[0]+" "+myPicture.readDateTime()[1]
                            print (string, len(string))
                            if len(string)<5:
                                wx.CallAfter(self.consolePrint,"\n"+("Didn't find Original Time/Date for ")+fileName)
                                break
                            string=string.replace(":","-")
                            latlong=myPicture.readLatLong()
                            if latlong==None: latlong=""
                            print ("latlong= ",latlong)
                            os.rename(self.picDir+'/'+fileName,self.picDir+"/"+string+" "+latlong+".jpg")
                            wx.CallAfter(self.consolePrint,"\n"+("Renamed ")+fileName+" to "+string+" "+latlong+".jpg")
                wx.CallAfter(self.consolePrint,"\n"+("Finished"))
            start_new_thread(rename,())

    def kmzGeneratorFrame(self,evt):
        """A frame to generate a KMZ  file"""
        self.winKmzGenerator=wx.Frame(win,size=(280,180),title="KMZ Generator")
        bkg=wx.Panel(self.winKmzGenerator)
        text="\n"+("Create a kmz file archive")
        introLabel = wx.StaticText(bkg, -1,text)
        readButton=wx.Button(bkg,size=(150,30),label=("Create KMZ file !"))
        self.Bind(wx.EVT_BUTTON, self.kmzGenerator, readButton)
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.Add(introLabel,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=20)
        vbox.Add(readButton,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=20)
        bkg.SetSizer(vbox)
        if sys.platform == 'darwin':
          wx.CallAfter(self.consolePrint,"\n"+("Sorry this tool is not yet available for the MacOS X version")+" \n")
        else:
          self.winKmzGenerator.Show()

    def kmzGenerator(self,evt):
        """A tool to create a kmz file containing the geolocalized pictures"""
        print  ("kmz ordered ...")
        self.winKmzGenerator.Close()
        if self.picDir == None or self.picDir !="":
            wx.CallAfter(self.consolePrint,"\n"+("Creating a KMZ file in the pictures folder...")+"\n")
            zip = zipfile.ZipFile(self.picDir+'/'+os.path.basename(self.picDir)+".zip", 'w')
            zip.write(self.picDir+'/doc.kml','doc.kml',zipfile.ZIP_DEFLATED)
            wx.CallAfter(self.consolePrint,"\n"+("Adding doc.kml"))
            for fileName in os.listdir ( self.picDir ):
                if fnmatch.fnmatch ( fileName, '*.JPG' )or fnmatch.fnmatch ( fileName, '*.jpg' ):
                    zip.write(self.picDir+"/"+fileName,fileName.encode(),zipfile.ZIP_DEFLATED)
                    wx.CallAfter(self.consolePrint,"\n"+("Adding ")+fileName)
            if (self.iconsChoice.GetSelection() == 0):
              wx.CallAfter(self.consolePrint,"\n"+("Adding ") + "thumbs")
              for fileName in os.listdir ( self.picDir+'/thumbs' ):
                  zip.write(self.picDir+"/thumbs/"+fileName,'thumbs/' + fileName.encode(),zipfile.ZIP_DEFLATED)
                  wx.CallAfter(self.consolePrint,"\n"+("Adding ")+fileName)
            zip.close()
            try:
                os.rename(self.picDir+'/'+os.path.basename(self.picDir)+".zip",self.picDir+'/'+os.path.basename(self.picDir)+".kmz")
                wx.CallAfter(self.consolePrint,"\n"+("KMZ file created in pictures folder")+"\n")
            except WindowsError:
                wx.CallAfter(self.consolePrint,"\n"+("Couldn't rename the zip file to kmz (maybe a previous file already exist)")+"\n")
        else:
            text="\n --- \n"+("To create a Google Earth kmz file you must either:")+"\n\n"\
            +("- finish a synchronisation")+"\n"\
            +("- select a folder you've already synchronized then select the KMZ Generator tool")+"\n --- \n"
            wx.CallAfter(self.consolePrint,text)


    def gpxInspectorFrame(self,evt):
        """A frame to inspect a gpx file"""
        self.winGpxInspector=wx.Frame(win,size=(280,180),title=("GPX Inspector"))
        bkg=wx.Panel(self.winGpxInspector)
        text=("Inspect a gpx file and show tracklog data.")
        introLabel = wx.StaticText(bkg, -1,text)
        readButton=wx.Button(bkg,size=(150,30),label=("Select a gpx file"))
        self.Bind(wx.EVT_BUTTON, self.gpxInspector, readButton)
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.Add(introLabel,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=20)
        vbox.Add(readButton,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=20)
        bkg.SetSizer(vbox)
        self.winGpxInspector.Show()

    def gpxInspector(self,evt):
        """A tool to display data from a gpx file"""
        gpx=wx.FileDialog(self)
        gpx.ShowModal()
        gpx.SetWildcard("*.gpx")
        gpxPath=gpx.GetPath()
        self.winGpxInspector.Close()
        print ("gpxPath=", gpxPath)
        if gpxPath =="" or None:
            wx.CallAfter(self.consolePrint,"\n"+("Select a gpx file first."))
        else:
            gpxPath=[gpxPath]
            gpxObject = Gpx(gpxPath)
            myGpx=gpxObject.extract()
            wx.CallAfter(self.consolePrint,"\n"+("Looking at ")+gpxPath[0]+"\n")
            points_found_str = ("Number of valid track points found")+" : " + str(len(myGpx))
            check_console_msg = "\n\n" + ("Check the console logs to get help about the issues with your gpx file") if len(myGpx) == 0 else ""
            def warn_user():
                self.consolePrint(gpxObject.errors + points_found_str +"\n")
                dialog=wx.MessageDialog(self, message=points_found_str + check_console_msg, style=wx.OK | wx.ICON_INFORMATION)
                dialog.ShowModal()

            def inspect():
                for trkpt in myGpx:
                    wx.CallAfter(self.consolePrint,("Date")+": "+trkpt["date"]+"\t"+("Time")+": "\
                    +trkpt["time"]+"\t"+("Latitude")+": "+trkpt["lat"]
                    +"\t"+("Longitude")+": "+trkpt["lon"]
                    +"\t"+("Altitude")+": "+trkpt["ele"]+"\n")
            start_new_thread(inspect,())
            wx.CallAfter(warn_user)

    def tzMenuPopup(self, evt):
        """Show timezones menu"""
        self.tzButton.PopupMenu(self.tzMenu, (0,self.tzButton.GetSize().GetHeight()))

    def manualTZ(self, evt):
        self.timezone = None
        self.tzButton.SetLabel(("Manual UTC offset"))
        self.utcLabel.Enable()
        self.utcEntry.Enable()

    def selectTZ(self, evt):
        """Choose a selected timezone"""
        self.timezone = timezones[evt.GetId()-3000]
        self.tzButton.SetLabel(self.timezone)
        self.utcLabel.Disable()
        self.utcEntry.Disable()

app=wx.App(redirect=False)
win=GUI(None,title="GPicSync GUI")
win.Show()
app.MainLoop()
