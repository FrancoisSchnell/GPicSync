#!/usr/bin/python

###############################################################################
#
# (c) francois.schnell  francois.schnell@gmail.com
#                       http://francois.schnell.free.fr  
#
# This script is released under the GPL license v2
#
# More informations and help can be found here: http://code.google.com/p/gpicsync/
#
###############################################################################

"""
GUI Part of GPicSync, a Free Software tool to geolocalize informations from:
- a GPS (.gpx file)
- pictures from a camera
The resulting pictures have latitude/longitude informations in their EXIF
meta-data and can be used with software or webservice which can read them
(like Flickr or Google Earth)
More informations at this URL:
http://code.google.com/p/gpicsync/
"""

import wx,time,decimal
import os,sys,fnmatch,zipfile
if sys.platform == 'win32':
    import win32com.client
from geoexif import *
from gpx import *
from gpicsync import *
from kmlGen import *
from geonames import *
from thread import start_new_thread
from PIL import Image
from PIL import JpegImagePlugin
from PIL import GifImagePlugin

class GUI(wx.Frame):
    """Main Frame of GPicSync"""
    def __init__(self,parent, title):
        """Initialize the main frame"""
        
        wx.Frame.__init__(self, parent, -1, title="GPicSync",size=(900,600))
        self.tcam_l="00:00:00"
        self.tgps_l="00:00:00"
        self.log=False
        self.stop=False
        self.picDir=""
                
        bkg=wx.Panel(self)
        #bkg.SetBackgroundColour('light blue steel')
        #toolbar=self.CreateToolBar()
        #toolbar.Realize()
        menuBar=wx.MenuBar()
        menu1=wx.Menu()
        timeShift=menu1.Append(wx.NewId(),"Local time correction")
        menuBar.Append(menu1,"&Options")
        menu2=wx.Menu()
        about=menu2.Append(wx.NewId(),"About...")
        menuTools=wx.Menu()
        menuBar.Append(menuTools,"&Tools")
        exifReader=menuTools.Append(wx.NewId(),"EXIF reader")
        renameToolMenu=menuTools.Append(wx.NewId(),"Geo-Rename pictures")
        gpxInspectorMenu=menuTools.Append(wx.NewId(),"GPX Inspector")
        kmzGeneratorMenu=menuTools.Append(wx.NewId(),"KMZ Generator")
        menuBar.Append(menu2,"&Help")
        statusBar=self.CreateStatusBar()
        self.Bind(wx.EVT_MENU,self.localtimeFrame,timeShift)
        self.Bind(wx.EVT_MENU,self.aboutApp,about)
        self.Bind(wx.EVT_MENU,self.exifFrame,exifReader)
        self.Bind(wx.EVT_MENU,self.renameFrame,renameToolMenu)
        self.Bind(wx.EVT_MENU,self.gpxInspectorFrame,gpxInspectorMenu)
        self.Bind(wx.EVT_MENU,self.kmzGeneratorFrame,kmzGeneratorMenu)
        
        dirButton=wx.Button(bkg,size=(150,-1),label="Pictures folder")
        gpxButton=wx.Button(bkg,size=(150,-1),label="GPS file (.gpx)")
        syncButton=wx.Button(bkg,size=(250,-1),label=" Synchronise ! ")
        quitButton=wx.Button(bkg,label="Quit",size=(100,-1))
        stopButton=wx.Button(bkg,label="Stop",size=(100,-1))
        clearButton=wx.Button(bkg,label="Clear",size=(100,-1))
        viewInGEButton=wx.Button(bkg,label="View in Google Earth",size=(-1,-1))
        
        utcLabel = wx.StaticText(bkg, -1,"UTC Offset=")
        timerangeLabel=wx.StaticText(bkg, -1,"Geocode picture only if time difference to nearest track point is below (seconds)=")
        self.logFile=wx.CheckBox(bkg,-1,"Create a log file in picture folder")
        self.logFile.SetValue(True)
        self.dateCheck=wx.CheckBox(bkg,-1,"Dates must match")
        self.dateCheck.SetValue(True)
        self.geCheck=wx.CheckBox(bkg,-1,"Create a Google Earth file")
        self.geCheck.SetValue(True)
        self.gmCheck=wx.CheckBox(bkg,-1,"Google Maps export, folder URL=")
        self.urlEntry=wx.TextCtrl(bkg,size=(300,-1))
        self.backupCheck=wx.CheckBox(bkg,-1,"backup pictures")
        self.backupCheck.SetValue(True)
        self.geonamesCheck=wx.CheckBox(bkg,-1,"add geonames and geotags")
        
        self.Bind(wx.EVT_BUTTON, self.findPictures, dirButton)
        self.Bind(wx.EVT_BUTTON, self.findGpx, gpxButton)
        self.Bind(wx.EVT_BUTTON, self.syncPictures, syncButton)
        self.Bind(wx.EVT_BUTTON, self.exitApp,quitButton)
        self.Bind(wx.EVT_BUTTON, self.stopApp,stopButton) 
        self.Bind(wx.EVT_BUTTON, self.clearConsole,clearButton)
        self.Bind(wx.EVT_BUTTON, self.viewInGE,viewInGEButton)
        
        self.dirEntry=wx.TextCtrl(bkg)
        self.gpxEntry=wx.TextCtrl(bkg)
        self.utcEntry=wx.TextCtrl(bkg,size=(40,-1))
        self.utcEntry.SetValue("0")
        self.timerangeEntry=wx.TextCtrl(bkg,size=(40,-1))
        self.timerangeEntry.SetValue("120")
        self.consoleEntry=wx.TextCtrl(bkg,style=wx.TE_MULTILINE | wx.HSCROLL)
        #self.consoleEntry.SetBackgroundColour("light grey")
        
        mapsbox=wx.BoxSizer()
        mapsbox.Add(self.geCheck,proportion=0,flag=wx.EXPAND| wx.ALL,border=10)
        mapsbox.Add(self.gmCheck,proportion=0,flag=wx.EXPAND| wx.ALL,border=10)
        mapsbox.Add(self.urlEntry,proportion=0,flag=wx.EXPAND| wx.ALL,border=5)
        
        hbox=wx.BoxSizer()
        hbox.Add(dirButton,proportion=0,flag=wx.LEFT,border=5)
        hbox.Add(self.dirEntry,proportion=1,flag=wx.EXPAND)
    
        hbox2=wx.BoxSizer()
        hbox2.Add(gpxButton,proportion=0,flag=wx.LEFT,border=5)
        hbox2.Add(self.gpxEntry,proportion=1,flag=wx.EXPAND)
        
        hbox3=wx.BoxSizer()
        hbox3.Add(self.logFile,proportion=0,flag=wx.LEFT| wx.ALL,border=10)
        hbox3.Add(self.dateCheck,proportion=0,flag=wx.LEFT| wx.ALL,border=10)
        hbox3.Add(self.backupCheck,proportion=0,flag=wx.EXPAND| wx.ALL,border=10)
        hbox3.Add(self.geonamesCheck,proportion=0,flag=wx.EXPAND| wx.ALL,border=10)
        
        hbox1=wx.BoxSizer()
        hbox1.Add(utcLabel,proportion=0,flag=wx.LEFT,border=10)
        hbox1.Add(self.utcEntry,proportion=0,flag=wx.LEFT,border=10)
        hbox1.Add(timerangeLabel,proportion=0,flag=wx.LEFT,border=10)
        hbox1.Add(self.timerangeEntry,proportion=0,flag=wx.LEFT,border=10)
        
        hbox4=wx.BoxSizer()
        hbox4.Add(syncButton,proportion=0,flag=wx.LEFT,border=5)
        hbox4.Add(stopButton,proportion=0,flag=wx.LEFT,border=5)
        hbox4.Add(clearButton,proportion=0,flag=wx.LEFT,border=5)
        hbox4.Add(viewInGEButton,proportion=0,flag=wx.LEFT,border=5)
        hbox4.Add(quitButton,proportion=0,flag=wx.LEFT,border=5)
        
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.Add(hbox,proportion=0,flag=wx.EXPAND | wx.ALL,border=5)
        vbox.Add(hbox2,proportion=0,flag=wx.EXPAND | wx.ALL,border=5)
        vbox.Add(mapsbox,proportion=0,flag=wx.EXPAND | wx.ALL,border=5)
        vbox.Add(hbox3,proportion=0,flag=wx.EXPAND | wx.ALL,border=5)
        vbox.Add(hbox1,proportion=0,flag=wx.EXPAND | wx.ALL,border=5)
        vbox.Add(hbox4,proportion=0,flag=wx.EXPAND | wx.ALL,border=5)
        vbox.Add(self.consoleEntry,proportion=1,flag=wx.EXPAND | wx.LEFT, border=5)
        
        bkg.SetSizer(vbox)
        self.SetMenuBar(menuBar)
        
        if sys.platform == 'win32':
            self.exifcmd = 'exiftool.exe'
        else:
            self.exifcmd = 'exiftool'
        
    def consolePrint(self,msg):
        """
        Print the given message in the console window 
        (GUI safe to call with a CallAfter in threads to avoid refresh problems)
        """
        self.consoleEntry.AppendText(msg)
        
    def aboutApp(self,evt): 
        """An about message dialog"""
        text="""
        GPicSync version 0.93 - 2007 
         
        GPicSync is Free Software (GPL v2)
        
        More informations and help:
        
        http://code.google.com/p/gpicsync/
        
        (c) 2007 - francois.schnell@gmail.com
        """ 
        dialog=wx.MessageDialog(self,message=text,
        style=wx.OK|wx.CANCEL|wx.ICON_INFORMATION)
        dialog.ShowModal()
        
    def viewInGE(self,evt):
        """View a local kml file in Google Earth"""
        if sys.platform == 'win32':
            googleEarth =win32com.client.Dispatch("GoogleEarth.ApplicationGE")
        if sys.platform.find("linux")!=-1:
            googleEarth= os.path.expanduser("~/google-earth/googleearth")
        try:
            path=self.picDir+'/doc.kml'
            print "path=",path
        except:
            text="""
---
To visualize the results in Google Earth you  must either:
            
- finish a synchronisation (message "*** FINISHED GEOCODING PROCESS ***)  in the main window then click "View in Google Earth"

- select a folder you've synchronized with the button "Pictures Folder" then click "View in Google Earth"
(the folder must contains a doc.kml file) 

Note that you can always look at your geolocalized pictures from Picassa then Google Earth (in Picassa: "Tools">"Geolocalize">"Display in Google Earth").
For help go to http://code.google.com/p/gpicsync/ or http://groups.google.com/group/gpicsync \n
---
"""
            wx.CallAfter(self.consolePrint,text)
        try:
            if sys.platform == 'win32':
                googleEarth.OpenKmlFile(path,True)
            if sys.platform.find("linux")!=-1:
                def goGELinux():
                    os.system(googleEarth +" "+path)
                start_new_thread(goGELinux,())
                
        except:
            wx.CallAfter(self.consolePrint,"\nCouldn't find or launch Google Earth\n")

    def exitApp(self,evt):
        """Quit properly the app"""
        print "Exiting the app..."
        self.Close()
        sys.exit(1)
    
    def stopApp(self,evt):
        """Stop current processing"""
        self.stop=True
        
    def clearConsole(self,evt):
        """clear the output console"""
        self.consoleEntry.Clear()
        
    def findGpx(self,evt):
        """Select the .gpx file to use"""
        openGpx=wx.FileDialog(self)
        openGpx.SetWildcard("*.gpx")
        openGpx.ShowModal()
        self.gpxFile=openGpx.GetPath()
        self.gpxEntry.SetValue(self.gpxFile)
        print self.gpxFile
    
    def findPictures(self,evt):
        """Select the folder pictures to use"""
        openDir=wx.DirDialog(self)
        openDir.ShowModal()
        self.picDir=openDir.GetPath()
        self.dirEntry.SetValue(self.picDir)
    
    def syncPictures(self,evt):
        """Sync. pictures with the .gpx file"""
        if self.dirEntry.GetValue()=="" or self.gpxEntry.GetValue=="":
                #wx.CallAfter(self.consolePrint,"You must first select a pictures folder and a GPX file\n")
                wx.CallAfter(self.consolePrint,"You must first select a pictures folder and a GPX file\n")
        else:
            pass
        self.stop=False
        utcOffset=int(self.utcEntry.GetValue())
        dateProcess=self.dateCheck.GetValue()
        self.log=self.logFile.GetValue()
        print "utcOffset= ",utcOffset

        def sync():
            wx.CallAfter(self.consolePrint,"\n------\nBeginning synchronization with "
            +"UTC Offset ="+self.utcEntry.GetValue()+
            " hours and maximum time difference = "+self.timerangeEntry.GetValue() +" seconds.\n")
            
            geo=GpicSync(gpxFile=self.gpxFile,tcam_l=self.tcam_l,tgps_l=self.tgps_l,
            UTCoffset=utcOffset,dateProcess=dateProcess,timerange=int(self.timerangeEntry.GetValue()),backup=self.backupCheck.GetValue())
            
            if self.geCheck.GetValue()==True:
                wx.CallAfter(self.consolePrint,"\nStarting to generate a Google Earth file (doc.kml) in the picture folder ... \n")
                localKml=KML(self.picDir+"/doc",os.path.basename(self.picDir))
            
            if self.gmCheck.GetValue()==True:
                wx.CallAfter(self.consolePrint,"\nStarting to generate a Google Map file (doc-web.kml) in the picture folder ... \n")
                webKml=KML(self.picDir+"/doc-web",os.path.basename(self.picDir),url=self.urlEntry.GetValue())
                webKml.path(self.gpxFile)
                webKml.writeInKml("\n<Folder>\n<name>Photos</name>")
                try:
                    os.mkdir(self.picDir+'/thumbs')
                except:
                    print "Couldn't create the thumbs folder, it maybe already exist"
                
            if self.log==True:
                f=open(self.picDir+'/gpicsync.log','w')
                f.write("Geocoded with UTC Offset= "+
                self.utcEntry.GetValue()+" and  Maximum time difference = "\
                +self.timerangeEntry.GetValue()+"\n")
                f.write("Pictures Folder: "+self.picDir+"\n")
                f.write("GPX file: "+self.gpxEntry.GetValue()+"\n\n")
                
            for fileName in os.listdir ( self.picDir ):
                if self.stop==True: break
                if fnmatch.fnmatch ( fileName, '*.JPG' )\
                or fnmatch.fnmatch ( fileName, '*.jpg' )\
                or fnmatch.fnmatch ( fileName, '*.CR2' )\
                or fnmatch.fnmatch ( fileName, '*.CRW' )\
                or fnmatch.fnmatch ( fileName, '*.NEF' )\
                or fnmatch.fnmatch ( fileName, '*.PEF' )\
                or fnmatch.fnmatch ( fileName, '*.SR2' )\
                or fnmatch.fnmatch ( fileName, '*.ARW' )\
                or fnmatch.fnmatch ( fileName, '*.RAF' ):
                    print "\nFound fileName ",fileName," Processing now ..."
                    wx.CallAfter(self.consolePrint,"\nFound "+fileName+" ...")
                    print self.picDir+'/'+fileName
                    result=geo.syncPicture(self.picDir+'/'+fileName)
                    wx.CallAfter(self.consolePrint,result[0]+"\n")
                    if self.log==True:
                        f.write("Processed image "+fileName+" : "+result[0]+"\n")
                        
                    if self.geCheck.GetValue()==True and result[1] !="" and result[2] !="":
                        localKml.placemark(self.picDir+'/'+fileName,lat=result[1],long=result[2],width=result[3],height=result[4])
                    
                    if self.gmCheck.GetValue()==True and result[1] !="" and result[2] !="":
                        webKml.placemark4Gmaps(self.picDir+'/'+fileName,lat=result[1],long=result[2],width=result[3],height=result[4])
                        im=Image.open(self.picDir+'/'+fileName)
                        width=int(result[3])
                        height=int(result[4])
                        if width>height:
                            max=width
                        else:
                            max=height
                        zoom=float(160.0/max)
                        im.thumbnail((int(width*zoom),int(height*zoom)))
                        im.save(self.picDir+"/thumbs/"+"thumb_"+fileName)
                        
                        
                    if self.geonamesCheck.GetValue()==True and result[1] !="" and result[2] !="":
                        try:
                            nearby=Geonames(lat=result[1],long=result[2])
                            gnPlace=nearby.findNearbyPlace()
                            gnDistance=nearby.findDistance()
                            gnRegion=nearby.findRegion()
                            gnCountry=nearby.findCountry()
                            gnSummary=gnDistance+"  Km to "+gnPlace+"  in "+gnRegion+", "+gnCountry
                            geotag="geotagged"
                            geotagLat="geo:lat="+str(decimal.Decimal(result[1]).quantize(decimal.Decimal('0.000001'))) 
                            geotagLon="geo:lon="+str(decimal.Decimal(result[2]).quantize(decimal.Decimal('0.000001'))) 
                            wx.CallAfter(self.consolePrint,gnSummary+" (writting geonames and geotags to keywords tag in picture EXIF).\n")
                            os.popen('%s -keywords="%s" -keywords="%s" -keywords="%s" \
                            -keywords="%s"  -overwrite_original -keywords="%s" -keywords="%s" -keywords="%s" "%s" '\
                            % (self.exifcmd,gnPlace,gnCountry,gnSummary,gnRegion,geotag,geotagLat,geotagLon,self.picDir+'/'+fileName))
                        except:
                            wx.CallAfter(self.consolePrint,"Couldn't retrieve geonames data...\n")
            if self.stop==False:
                wx.CallAfter(self.consolePrint,"\n*** FINISHED GEOCODING PROCESS ***\n")
            if self.stop==True:
                wx.CallAfter(self.consolePrint,"\n *** PROCESSING STOPPED BY THE USER ***\n")
            if self.log==True: f.close()
            
            if self.geCheck.GetValue()==True:
                wx.CallAfter(self.consolePrint,"\nAdding the GPS track log to the Google Earth kml file...\n")
                localKml.path(self.gpxFile)
                localKml.close()
                wx.CallAfter(self.consolePrint,"\nClick on the 'View in Google Earth' button if you want to visualize directly the track log and geocoded photos in Google Earth .\n")
                wx.CallAfter(self.consolePrint,"( A Google Earth doc.kml file has been created in your picture folder. You can also produce a kmz file with 'Tools'->'KMZ Generator' )\n")
            
            if self.gmCheck.GetValue()==True:
                #webKml.path(self.gpxFile)
                webKml.writeInKml("</Folder>\n")
                webKml.close()
                wx.CallAfter(self.consolePrint,"( A Google Maps doc-web.kml file has been created with the given url' )\n")
                
        start_new_thread(sync,())
        #googleEarth =win32com.client.Dispatch("GoogleEarth.ApplicationGE")
        
    def localtimeCorrection(self,evt):
            """ Local time correction if GPS and camera wasn't synchronized """
            self.winOpt.Close()
            self.tcam_l=self.camEntry.GetValue()
            self.tgps_l=self.gpsEntry.GetValue()
            print "tcam_l =",self.tcam_l
            print "tgps_l =",self.tgps_l
            
    def localtimeFrame(self,evt):
        """A frame for local time correction"""
        self.winOpt=wx.Frame(win,size=(440,280),title="Local time corrections")
        bkg=wx.Panel(self.winOpt)
        #bkg.SetBackgroundColour('White')
        text="\tUse this option ONLY if your camera local time is wrong.\
        \n\nIndicate here the local time now displayed by your camera and GPS (hh:mm:ss)" 
        utcLabel = wx.StaticText(bkg, -1,text)
        camLabel = wx.StaticText(bkg, -1,"Local time displayed now by the camera")
        self.camEntry=wx.TextCtrl(bkg,size=(100,-1))
        self.camEntry.SetValue("00:00:00")
        gpsLabel = wx.StaticText(bkg, -1,"Local time displayed now by the GPS")
        self.gpsEntry=wx.TextCtrl(bkg,size=(100,-1))
        self.gpsEntry.SetValue("00:00:00")
        applyButton=wx.Button(bkg,size=(130,30),label="Apply correction")
        self.Bind(wx.EVT_BUTTON, self.localtimeCorrection, applyButton)
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.Add(utcLabel,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=20)
        vbox.Add(camLabel,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=5)
        vbox.Add(self.camEntry,proportion=0,flag=wx.ALIGN_CENTER,border=5)
        vbox.Add(gpsLabel,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=5)
        vbox.Add(self.gpsEntry,proportion=0,flag=wx.ALIGN_CENTER,border=5)
        vbox.Add(applyButton,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,
        border=5,border=20)
        bkg.SetSizer(vbox)
        self.winOpt.Show()
    def exifFrame(self,evt):
        """A frame for the exifReader tool"""
        self.winExifReader=wx.Frame(win,size=(280,220),title="EXIF Reader")
        bkg=wx.Panel(self.winExifReader)
        #bkg.SetBackgroundColour('White')
        text="""
        Read the EXIF metadata of the selected picture."""
        introLabel = wx.StaticText(bkg, -1,text)
        self.ExifReaderSelected="All EXIF metadata"
        radio1=wx.RadioButton(bkg,-1,"All EXIF metadata")
        radio2=wx.RadioButton(bkg,-1,"Date/Time/Lat./Long.")
        def onRadio(evt):
            radioSelected=evt.GetEventObject()
            self.ExifReaderSelected=radioSelected.GetLabel()
        for eachRadio in [radio1,radio2]:
            self.Bind(wx.EVT_RADIOBUTTON ,onRadio,eachRadio)
        readButton=wx.Button(bkg,size=(130,30),label="Select a picture")
        self.Bind(wx.EVT_BUTTON, self.readEXIF, readButton)
        
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.Add(introLabel,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=20)
        vbox.Add(radio1,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=10)
        vbox.Add(radio2,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=10)
        vbox.Add(readButton,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=20)
        bkg.SetSizer(vbox)
        self.winExifReader.Show()
        
    def readEXIF(self,evt):
        """read the selected EXIF informations"""
        print "Selected ",self.ExifReaderSelected
        #self.winExifReader.Close()
        picture=wx.FileDialog(self)
        picture.SetWildcard("*.JPG")
        picture.ShowModal()
        pathPicture=picture.GetPath()
        if pathPicture !="" or None:
            myPicture=GeoExif(pathPicture)
            def read():
                wx.CallAfter(self.consolePrint,"\n\nSelected metada in the EXIF header of the picture : \n")
                wx.CallAfter(self.consolePrint,"---------------------------------------------------------------\n")
                if self.ExifReaderSelected=="All EXIF metadata":
                    wx.CallAfter(self.consolePrint,myPicture.readExifAll())
                    
                if self.ExifReaderSelected=="Date/Time/Lat./Long.":
                    dateTime=myPicture.readDateTime()
                    datetimeString=dateTime[0]+":"+dateTime[1]
                    if len(datetimeString)>5:
                        wx.CallAfter(self.consolePrint,datetimeString)
                        wx.CallAfter(self.consolePrint,"    lat./long.="+str(myPicture.readLatLong()))
                    else:
                        wx.CallAfter(self.consolePrint,"None")
            start_new_thread(read,())
            self.winExifReader.Close()
            
    def renameFrame(self,evt):
        """A frame for the rename tool"""
        self.winRenameTool=wx.Frame(win,size=(280,220),title="Renaming tool")
        bkg=wx.Panel(self.winRenameTool)
        #bkg.SetBackgroundColour('White')
        text="This tool renames your pictures with the \noriginal time/date and lat./long.(if present)"
        introLabel = wx.StaticText(bkg, -1,text)
        readButton=wx.Button(bkg,size=(200,30),label="Rename pictures in a folder")
        readButtonFolder=wx.Button(bkg,size=(200,30),label="Rename a single picture")
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
            wx.CallAfter(self.consolePrint,"\nBeginning renaming...")
            def rename():
                myPicture=GeoExif(self.pathPicture)
                string=myPicture.readDateTime()[0]+" "+myPicture.readDateTime()[1]
                string=string.replace(":","-")
                latlong=myPicture.readLatLong()
                if latlong==None: latlong=""
                if len(string)<5:
                    wx.CallAfter(self.consolePrint,"\nDidn't find Original Time/Date for "+self.pathPicture)
                else:
                    os.rename(self.pathPicture,os.path.dirname(self.pathPicture)+"/"+string+" "+latlong+".jpg")
                    wx.CallAfter(self.consolePrint,"\nRenamed "+os.path.basename(self.pathPicture)+" to "+string+latlong+".jpg")
            start_new_thread(rename,())
            
    def renamePicturesInFolder(self,evt):
        self.stop=False        
        self.winRenameTool.Close()
        openDir=wx.DirDialog(self)
        openDir.ShowModal()
        self.picDir=openDir.GetPath()
        if self.picDir!="" or None:
            wx.CallAfter(self.consolePrint,"\nBeginning renaming...")
            def rename():
                for fileName in os.listdir ( self.picDir ):
                        if self.stop==True:
                            wx.CallAfter(self.consolePrint,"\nInterrupted by the user") 
                            self.stop=False
                            break
                        if fnmatch.fnmatch ( fileName, '*.JPG' )or \
                        fnmatch.fnmatch ( fileName, '*.jpg' ):
                            print self.picDir+'/'+fileName
                            myPicture=GeoExif(self.picDir+"/"+fileName)
                            string=myPicture.readDateTime()[0]+" "+myPicture.readDateTime()[1]
                            print string, len(string)
                            if len(string)<5:
                                wx.CallAfter(self.consolePrint,"\nDidn't find Original Time/Date for "+fileName)
                                break
                            string=string.replace(":","-")
                            latlong=myPicture.readLatLong()
                            if latlong==None: latlong=""
                            print "latlong= ",latlong
                            os.rename(self.picDir+'/'+fileName,self.picDir+"/"+string+" "+latlong+".jpg")
                            wx.CallAfter(self.consolePrint,"\nRenamed "+fileName+" to "+string+" "+latlong+".jpg")
                wx.CallAfter(self.consolePrint,"\nFinished")
            start_new_thread(rename,())
    
    def kmzGeneratorFrame(self,evt):
        """A frame to generate a KMZ  file"""
        self.winKmzGenerator=wx.Frame(win,size=(280,180),title="KMZ Generator")
        bkg=wx.Panel(self.winKmzGenerator)
        text="\nCreate a kmz file to distribute to others"
        introLabel = wx.StaticText(bkg, -1,text)
        readButton=wx.Button(bkg,size=(150,30),label="Create KMZ file !")
        self.Bind(wx.EVT_BUTTON, self.kmzGenerator, readButton)
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.Add(introLabel,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=20)
        #vbox.Add(self.gpxInGECheck,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=10)
        vbox.Add(readButton,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=20)
        bkg.SetSizer(vbox)
        if sys.platform.find("linux")!=-1:
            wx.CallAfter(self.consolePrint,"\nSorry this tool is not yet available for the Linux version (soon)\n")
        else:
            self.winKmzGenerator.Show()
        
    def kmzGenerator(self,evt):
        """A tool to create a kmz file containing the geolocalized pictures"""
        print  "kmz ordered ..."
        self.winKmzGenerator.Close()
        if self.picDir == None or self.picDir !="":
            wx.CallAfter(self.consolePrint,"\nCreating a KMZ file in the pictures folder...\n")
            zip = zipfile.ZipFile(self.picDir+'/'+os.path.basename(self.picDir)+".zip", 'w')
            zip.write(self.picDir+'/doc.kml','doc.kml',zipfile.ZIP_DEFLATED)
            wx.CallAfter(self.consolePrint,"\nAdding doc.kml")
            for fileName in os.listdir ( self.picDir ):
                if fnmatch.fnmatch ( fileName, '*.JPG' )or fnmatch.fnmatch ( fileName, '*.jpg' ):
                    zip.write(self.picDir+"/"+fileName,fileName,zipfile.ZIP_DEFLATED)
                    wx.CallAfter(self.consolePrint,"\nAdding "+fileName)
            zip.close()
            try:
                os.rename(self.picDir+'/'+os.path.basename(self.picDir)+".zip",self.picDir+'/'+os.path.basename(self.picDir)+".kmz")
                wx.CallAfter(self.consolePrint,"\nKMZ file (which contains the geolocalized pictures) created in pictures folder\nYou can share this file with friends or put it on a webserver.\n")
            except WindowsError:
                wx.CallAfter(self.consolePrint,"\nCouldn't rename the zip file to kmz\n(Maybe a previous kmz file with the same name already exist, check first and retry)\n")
        else:
            text="""
---
To create a Google Earth kmz file you must either:
            
- finish a synchronisation (message "***FINISHED***) in the main window then select "KMZ Generator" in "Tools" menu

- select a folder you've synchronized with the button "Pictures Folder" then select "KMZ Generator" in "Tools" menu
(the folder must contains a doc.kml file) 

Note that you can always look at your geolocalized pictures from Picassa then Google Earth (in Picassa: "Tools">"Geolocalize">"Display in Google Earth").
For help go to http://code.google.com/p/gpicsync/ or http://groups.google.com/group/gpicsync \n
---
"""
            wx.CallAfter(self.consolePrint,text)
                
        
    def gpxInspectorFrame(self,evt):
        """A frame to inspect a gpx file"""
        self.winGpxInspector=wx.Frame(win,size=(280,180),title="GPX Inspector")
        bkg=wx.Panel(self.winGpxInspector)
        text="""
        Inspect a gpx file and show tracklog data ."""
        introLabel = wx.StaticText(bkg, -1,text)
        readButton=wx.Button(bkg,size=(150,30),label="Select a gpx file")
        self.Bind(wx.EVT_BUTTON, self.gpxInspector, readButton)
        #self.gpxInGECheck=wx.CheckBox(bkg,-1,"Show also path in GoogleEarth")
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.Add(introLabel,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=20)
        #vbox.Add(self.gpxInGECheck,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=10)
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
        print "gpxPath=", gpxPath
        if gpxPath =="" or None:
            wx.CallAfter(self.consolePrint,"\nSelect a gpx file first.")
        else:
            myGpx=Gpx(gpxPath).extract()
            wx.CallAfter(self.consolePrint,"\nLooking at "+gpxPath+"\n")
            wx.CallAfter(self.consolePrint,"\nNumber of valid track points found : "+str(len(myGpx))+"\n\n")
            def inspect():
                for trkpt in myGpx:
                    wx.CallAfter(self.consolePrint,"Date: "+trkpt["date"]+"\tTime: "\
                    +trkpt["time"]+"\tLatitude: "+trkpt["lat"]+"\tLongitude: "+trkpt["lon"]+"\n")
                """if self.gpxInGECheck.GetValue()==True:
                    print "trying to ..."
                    os.system("c:\\Program Files\\Google\\Google Earth\\googleearth.exe "+gpxPath)
                """
            start_new_thread(inspect,())
            
app=wx.App(redirect=False)
win=GUI(None,title="GPicSync GUI")
win.Show()

app.MainLoop()
