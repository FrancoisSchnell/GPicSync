#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

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

import wx,time
import os,sys,fnmatch
import win32com.client
from geoexif import *
from gpx import *
from gpicsync import *
from kmlGen import *
from thread import start_new_thread

class GUI(wx.Frame):
    """Main Frame of GPicSync"""
    def __init__(self,parent, title):
        """Initialize the main frame"""
        
        wx.Frame.__init__(self, parent, -1, title="GPicSync",size=(900,600))
        self.tcam_l="00:00:00"
        self.tgps_l="00:00:00"
        self.log=False
        self.stop=False
        
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
        menuBar.Append(menu2,"&Help")
        statusBar=self.CreateStatusBar()
        self.Bind(wx.EVT_MENU,self.localtimeFrame,timeShift)
        self.Bind(wx.EVT_MENU,self.aboutApp,about)
        self.Bind(wx.EVT_MENU,self.exifFrame,exifReader)
        self.Bind(wx.EVT_MENU,self.renameFrame,renameToolMenu)
        self.Bind(wx.EVT_MENU,self.gpxInspectorFrame,gpxInspectorMenu)
        
        dirButton=wx.Button(bkg,size=(150,-1),label="Pictures folder")
        gpxButton=wx.Button(bkg,size=(150,-1),label="GPS file (.gpx)")
        syncButton=wx.Button(bkg,size=(250,-1),label=" Synchronise ! ")
        quitButton=wx.Button(bkg,label="Quit",size=(100,-1))
        stopButton=wx.Button(bkg,label="Stop",size=(100,-1))
        clearButton=wx.Button(bkg,label="Clear",size=(100,-1))
        viewInGEButton=wx.Button(bkg,label="View result in Google Earth",size=(-1,-1))
        
        utcLabel = wx.StaticText(bkg, -1,"UTC Offset=")
        self.logFile=wx.CheckBox(bkg,-1,"Create a log file in picture folder")
        self.logFile.SetValue(True)
        self.dateCheck=wx.CheckBox(bkg,-1,"Dates must match")
        self.dateCheck.SetValue(True)
        self.geCheck=wx.CheckBox(bkg,-1,"Create a local Google Earth file")
        self.geCheck.SetValue(True)

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
        self.consoleEntry=wx.TextCtrl(bkg,style=wx.TE_MULTILINE | wx.HSCROLL)
        #self.consoleEntry.SetBackgroundColour("light grey")
        
        hbox=wx.BoxSizer()
        hbox.Add(dirButton,proportion=0,flag=wx.LEFT,border=5)
        hbox.Add(self.dirEntry,proportion=1,flag=wx.EXPAND)

        hbox2=wx.BoxSizer()
        hbox2.Add(gpxButton,proportion=0,flag=wx.LEFT,border=5)
        hbox2.Add(self.gpxEntry,proportion=1,flag=wx.EXPAND)
        
        hbox3=wx.BoxSizer()
        hbox3.Add(self.logFile,proportion=0,flag=wx.LEFT| wx.ALL,border=10)
        hbox3.Add(self.dateCheck,proportion=0,flag=wx.LEFT| wx.ALL,border=10)
        hbox3.Add(self.geCheck,proportion=0,flag=wx.EXPAND| wx.ALL,border=10)
        
        hbox4=wx.BoxSizer()
        hbox4.Add(utcLabel,proportion=0,flag=wx.LEFT,border=5)
        hbox4.Add(self.utcEntry,proportion=0,flag=wx.LEFT,border=5)
        hbox4.Add(syncButton,proportion=0,flag=wx.LEFT,border=5)
        hbox4.Add(stopButton,proportion=0,flag=wx.LEFT,border=5)
        hbox4.Add(clearButton,proportion=0,flag=wx.LEFT,border=5)
        hbox4.Add(viewInGEButton,proportion=0,flag=wx.LEFT,border=5)
        hbox4.Add(quitButton,proportion=0,flag=wx.LEFT,border=5)
        
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.Add(hbox,proportion=0,flag=wx.EXPAND | wx.ALL,border=5)
        vbox.Add(hbox2,proportion=0,flag=wx.EXPAND | wx.ALL,border=5)
        vbox.Add(hbox3,proportion=0,flag=wx.EXPAND | wx.ALL,border=5)
        vbox.Add(hbox4,proportion=0,flag=wx.EXPAND | wx.ALL,border=5)
        #vbox.Add(syncButton,proportion=0,flag=wx.EXPAND | wx.LEFT, border=5)
        vbox.Add(self.consoleEntry,proportion=1,flag=wx.EXPAND | wx.LEFT, border=5)
        #vbox.Add(quitButton,proportion=0,flag=wx.EXPAND | wx.LEFT, border=5)
        
        bkg.SetSizer(vbox)
        self.SetMenuBar(menuBar)
        
    def aboutApp(self,evt): 
        """An about message dialog"""
        text="""
        GPicSync version 0.7 - March 2007 
         
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
        googleEarth =win32com.client.Dispatch("GoogleEarth.ApplicationGE")
        #while not googleEarth.IsInitialized():
        #    print "waiting for Google Earth to initialize"
        path=self.picDir+'\\local-google-earth.kml'
        print "path=",path
        googleEarth.OpenKmlFile(path,True)
        #googleEarth.OpenKmlFile(r'C:/"Documents and Settings"/franz/Bureau/GE-Short-test/local-google-earth.kml')
        #googleEarth.OpenKmlFile("C:/Documents and Settings/franz/Bureau/GE-Short-test/local-google-earth.kml",True)
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
        self.stop=False
        utcOffset=int(self.utcEntry.GetValue())
        dateProcess=self.dateCheck.GetValue()
        self.log=self.logFile.GetValue()
        print "utcOffset= ",utcOffset
        geo=GpicSync(gpxFile=self.gpxFile,tcam_l=self.tcam_l,tgps_l=self.tgps_l,
        UTCoffset=utcOffset,dateProcess=dateProcess)
        if self.geCheck.GetValue()==True:
            self.consoleEntry.AppendText("\nCreating a Google Earth file in picture folder: local-google-earth.kml\n\n")
            localKml=KML(self.picDir+"/local-google-earth")
        def sync():
            self.consoleEntry.AppendText("Beginning synchronisation with "
            +"UTC Offset="+self.utcEntry.GetValue()+"\n")
            if self.log==True:
                f=open(self.picDir+'/gpicsync.log','w')
                f.write("Synchronisation with UTC Offset="+
                self.utcEntry.GetValue()+"\n")
                f.write("Pictures Folder: "+self.picDir+"\n")
                f.write("GPX file: "+self.gpxEntry.GetValue()+"\n\n")
                
            for fileName in os.listdir ( self.picDir ):
                if self.stop==True: break
                if fnmatch.fnmatch ( fileName, '*.JPG' )or fnmatch.fnmatch ( fileName, '*.jpg' ):
                    print "\nFound fileName ",fileName," Processing now ..."
                    self.consoleEntry.AppendText("\nFound "+fileName+" ")
                    print self.picDir+'/'+fileName
                    result=geo.syncPicture(self.picDir+'/'+fileName)
                    self.consoleEntry.AppendText(result+"\n")
                    if self.log==True:
                        f.write("Processed image "+fileName+" : "+result+"\n")
                    if self.geCheck.GetValue()==True:
                        localKml.placemark(self.picDir+"/"+fileName)
            if self.stop==False:
                self.consoleEntry.AppendText("\n *** FINISHED ***\n")
            if self.stop==True:
                self.consoleEntry.AppendText("\n *** Processing STOPPED bu the user ***\n")
            if self.log==True: f.close()
            if self.geCheck.GetValue()==True:
                localKml.close()
                self.consoleEntry.AppendText("\nAttempting to visualize data in Google Earth...\n")
                #try:
                #googleEarth =win32com.client.Dispatch("GoogleEarth.ApplicationGE")
                #while not googleEarth.IsInitialized():
                #    print "waiting for Google Earth to initialize"
                #time.sleep(5)
                #path=self.picDir+'\\local-google-earth.kml'
                #print "path=",path
                #googleEarth.OpenKmlFile(path)
                #except:
                #    self.consoleEntry.AppendText("\nCouldn't find or launch Google Earth...\n")
        start_new_thread(sync,())
        googleEarth =win32com.client.Dispatch("GoogleEarth.ApplicationGE")
        
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
        vbox.Add(self.gpsEntry,proportion=0,flag=wx.ALIGN_CENTER,border=5,
        border=5)
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
        print "Selected ",self.ExifReaderSelected
        self.winExifReader.Close()
        picture=wx.FileDialog(self)
        picture.SetWildcard("*.jpg")
        picture.ShowModal()
        pathPicture=picture.GetPath()
        if pathPicture !="" or None:
            myPicture=GeoExif(pathPicture)
            def read():
                self.consoleEntry.AppendText("\n\nSelected metada in the EXIF header of the picture : \n")
                self.consoleEntry.AppendText("---------------------------------------------------------------\n")
                if self.ExifReaderSelected=="All EXIF metadata":
                    self.consoleEntry.AppendText(myPicture.readExifAll())
                if self.ExifReaderSelected=="Date/Time/Lat./Long.":
                    dateTime=myPicture.readDateTime()
                    datetimeString=dateTime[0]+":"+dateTime[1]
                    if len(datetimeString)>5:
                        self.consoleEntry.AppendText(datetimeString)
                        self.consoleEntry.AppendText("    lat./long.="+str(myPicture.readLatLong()))
                    else:
                        self.consoleEntry.AppendText("None")
            start_new_thread(read,())
            self.winExifReader.Close()
            
    def renameFrame(self,evt):
        """A frame for the rename tool"""
        self.winRenameTool=wx.Frame(win,size=(280,220),title="Renaming tool")
        bkg=wx.Panel(self.winRenameTool)
        #bkg.SetBackgroundColour('White')
        text="This tool renames your pictures with the \noriginal time/date and lat./long.(if present)"
        introLabel = wx.StaticText(bkg, -1,text)
        readButton=wx.Button(bkg,size=(150,30),label="Rename pictures in a folder")
        readButtonFolder=wx.Button(bkg,size=(150,30),label="Rename a single picture")
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
        picture.SetWildcard("*.jpg")
        self.pathPicture=picture.GetPath()
        self.winRenameTool.Close()
        if self.pathPicture !="" or None:
            self.consoleEntry.AppendText("\nBeginning renaming...")
            def rename():
                myPicture=GeoExif(self.pathPicture)
                string=myPicture.readDateTime()[0]+" "+myPicture.readDateTime()[1]
                string=string.replace(":","-")
                latlong=myPicture.readLatLong()
                if latlong==None: latlong=""
                if len(string)<5:
                    self.consoleEntry.AppendText("\nDidn't find Original Time/Date for "+self.pathPicture)
                else:
                    os.rename(self.pathPicture,os.path.dirname(self.pathPicture)+"/"+string+" "+latlong+".jpg")
                    self.consoleEntry.AppendText("\nRenamed "+os.path.basename(self.pathPicture)+" to "+string+latlong+".jpg")
            start_new_thread(rename,())
            
    def renamePicturesInFolder(self,evt):
        self.stop=False        
        self.winRenameTool.Close()
        openDir=wx.DirDialog(self)
        openDir.ShowModal()
        self.picDir=openDir.GetPath()
        if self.picDir!="" or None:
            self.consoleEntry.AppendText("\nBeginning renaming...")
            def rename():
                for fileName in os.listdir ( self.picDir ):
                        if self.stop==True:
                            self.consoleEntry.AppendText("\nInterrupted by the user") 
                            self.stop=False
                            break
                        if fnmatch.fnmatch ( fileName, '*.JPG' )or \
                        fnmatch.fnmatch ( fileName, '*.jpg' ):
                            print self.picDir+'/'+fileName
                            myPicture=GeoExif(self.picDir+"/"+fileName)
                            string=myPicture.readDateTime()[0]+" "+myPicture.readDateTime()[1]
                            print string, len(string)
                            if len(string)<5:
                                self.consoleEntry.AppendText("\nDidn't find Original Time/Date for "+fileName)
                                break
                            string=string.replace(":","-")
                            latlong=myPicture.readLatLong()
                            if latlong==None: latlong=""
                            print "latlong= ",latlong
                            os.rename(self.picDir+'/'+fileName,self.picDir+"/"+string+" "+latlong+".jpg")
                            self.consoleEntry.AppendText("\nRenamed "+fileName+" to "+string+" "+latlong+".jpg")
                self.consoleEntry.AppendText("\nFinished")
            start_new_thread(rename,())
                    
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
            self.consoleEntry.AppendText("\nSelect a gpx file first.")
        else:
            myGpx=Gpx(gpxPath).extract()
            self.consoleEntry.AppendText("\nLooking at "+gpxPath+"\n")
            self.consoleEntry.AppendText("\nNumber of valid track points found : "+str(len(myGpx))+"\n\n")
            def inspect():
                for trkpt in myGpx:
                    self.consoleEntry.AppendText("Date: "+trkpt["date"]+"\tTime: "\
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
