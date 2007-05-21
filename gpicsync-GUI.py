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

import wx,time, decimal,gettext,shutil,ConfigParser
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


# Try to get the OS language if possible and search for a translation 
"""
if sys.platform == 'win32':
    localedir= "locale"
    gettext.install("gpicsync-GUI", localedir)
"""

class GUI(wx.Frame):
    """Main Frame of GPicSync"""
    def __init__(self,parent, title):
        """Initialize the main frame"""
        
        wx.Frame.__init__(self, parent, -1, title="GPicSync",size=(900,600))
        self.tcam_l="00:00:00"
        self.tgps_l="00:00:00"
        self.log=False
        self.stop=False
        self.interpolation=False
        self.picDir=""
        self.utcOffset="0"
        self.backup=True
        self.picDirDefault=""
        self.GMaps=False
        self.urlGMaps=""
        self.geonamesTags=False
        self.datesMustMatch=True
        self.maxTimeDifference="120"
        self.language="English"
        
        # Search for an eventual gpicsync.conf file
        try:
            fconf=open("gpicsync.conf","r+")
            conf= ConfigParser.ConfigParser()
            conf.readfp(fconf) #parse the config file
            if conf.has_option("gpicsync","UTCOffset") == True:
                self.utcOffset=conf.get("gpicsync","UTCOffset")
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
            fconf.close()
            
        except:
            wx.CallAfter(self.consolePrint,"\n"
            +"Couldn't find or read configuration file."+"\n")
        try:
            print self.language
            if self.language=="French":
                langFr = gettext.translation('gpicsync-GUI', "locale",languages=['fr'])
                langFr.install()
            elif self.language=="Italian":
                langIt = gettext.translation('gpicsync-GUI', "locale",languages=['it'])
                langIt.install()
            else:
                gettext.install("gpicsync-GUI", "None")#a trick to go back to original
        except:
            print "Couldn't load translation."
                
        bkg=wx.Panel(self)
        #bkg.SetBackgroundColour('light blue steel')
        menuBar=wx.MenuBar()
        menu1=wx.Menu()
        timeShift=menu1.Append(wx.NewId(),_("Local time correction"))
        if sys.platform == 'win32':
            languageChoice=menu1.Append(wx.NewId(),_("Language"))
            self.Bind(wx.EVT_MENU,self.languageApp,languageChoice)
        menuBar.Append(menu1,_("&Options"))
        menu2=wx.Menu()
        about=menu2.Append(wx.NewId(),_("About..."))
        menuTools=wx.Menu()
        menuBar.Append(menuTools,_("&Tools"))
        exifReader=menuTools.Append(wx.NewId(),_("EXIF reader"))
        renameToolMenu=menuTools.Append(wx.NewId(),_("Geo-Rename pictures"))
        gpxInspectorMenu=menuTools.Append(wx.NewId(),_("GPX Inspector"))
        kmzGeneratorMenu=menuTools.Append(wx.NewId(),_("KMZ Generator"))
        menuBar.Append(menu2,_("&Help"))
        statusBar=self.CreateStatusBar()
        self.Bind(wx.EVT_MENU,self.localtimeFrame,timeShift)
        self.Bind(wx.EVT_MENU,self.aboutApp,about)
        self.Bind(wx.EVT_MENU,self.exifFrame,exifReader)
        self.Bind(wx.EVT_MENU,self.renameFrame,renameToolMenu)
        self.Bind(wx.EVT_MENU,self.gpxInspectorFrame,gpxInspectorMenu)
        self.Bind(wx.EVT_MENU,self.kmzGeneratorFrame,kmzGeneratorMenu)
        
        dirButton=wx.Button(bkg,size=(150,-1),label=_("Pictures folder"))
        gpxButton=wx.Button(bkg,size=(150,-1),label=_("GPS file (.gpx)"))
        syncButton=wx.Button(bkg,size=(250,-1),label=_(" Synchronise ! "))
        quitButton=wx.Button(bkg,label=_("Quit"),size=(100,-1))
        stopButton=wx.Button(bkg,label=_("Stop"),size=(100,-1))
        clearButton=wx.Button(bkg,label=_("Clear"),size=(100,-1))
        viewInGEButton=wx.Button(bkg,label=_("View in Google Earth"),size=(-1,-1))
        
        utcLabel = wx.StaticText(bkg, -1,_("UTC Offset="))
        timerangeLabel=wx.StaticText(bkg, -1,_("Geocode picture only if time difference to nearest track point is below (seconds)="))
        self.logFile=wx.CheckBox(bkg,-1,_("Create a log file in picture folder"))
        self.logFile.SetValue(self.log)
        self.dateCheck=wx.CheckBox(bkg,-1,_("Dates must match"))
        self.dateCheck.SetValue(self.datesMustMatch)
        self.geCheck=wx.CheckBox(bkg,-1,_("Create a Google Earth file"))
        self.geCheck.SetValue(True)
        self.gmCheck=wx.CheckBox(bkg,-1,_("Google Maps export, folder URL="))
        self.gmCheck.SetValue(self.GMaps)
        self.urlEntry=wx.TextCtrl(bkg,size=(300,-1))
        self.urlEntry.SetValue(self.urlGMaps)
        self.backupCheck=wx.CheckBox(bkg,-1,_("backup pictures"))
        self.backupCheck.SetValue(self.backup)
        self.interpolationCheck=wx.CheckBox(bkg,-1,_("interpolation"))
        self.interpolationCheck.SetValue(self.interpolation)
        self.geonamesCheck=wx.CheckBox(bkg,-1,_("add geonames and geotagged"))
        self.geonamesCheck.SetValue(self.geonamesTags)
        
        self.Bind(wx.EVT_BUTTON, self.findPictures, dirButton)
        self.Bind(wx.EVT_BUTTON, self.findGpx, gpxButton)
        self.Bind(wx.EVT_BUTTON, self.syncPictures, syncButton)
        self.Bind(wx.EVT_BUTTON, self.exitApp,quitButton)
        self.Bind(wx.EVT_BUTTON, self.stopApp,stopButton) 
        self.Bind(wx.EVT_BUTTON, self.clearConsole,clearButton)
        self.Bind(wx.EVT_BUTTON, self.viewInGE,viewInGEButton)
        #self.Bind(wx.EVT_CLOSE,self.exitApp,self)
        
        self.dirEntry=wx.TextCtrl(bkg)
        self.gpxEntry=wx.TextCtrl(bkg)
        self.utcEntry=wx.TextCtrl(bkg,size=(40,-1))
        self.utcEntry.SetValue(self.utcOffset)
        self.timerangeEntry=wx.TextCtrl(bkg,size=(40,-1))
        self.timerangeEntry.SetValue(self.maxTimeDifference)
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
        hbox3.Add(self.interpolationCheck,proportion=0,flag=wx.LEFT| wx.ALL,border=10)
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
        
    def languageApp(self,evt):
        """
        select a language to display the GUI with
        """
        choices = [ 'English', 'French','Italian']
        dialog=wx.SingleChoiceDialog(self,_("Choose a language"),_("languages choice"),choices)
        if dialog.ShowModal() == wx.ID_OK:
            choice=dialog.GetStringSelection()
            print "choice is : ", choice
            if choice=="French":
                fconf=open("gpicsync.conf","r+")
                conf= ConfigParser.ConfigParser()
                conf.readfp(fconf)
                conf.set("gpicsync","language","French")
                fconf.seek(0)
                conf.write(fconf)
                fconf.close()
                wx.CallAfter(self.consolePrint,"\n"+"Next time you launch GPicSync it will be in French."+"\n")
                #langFr = gettext.translation('gpicsync-GUI', "locale",languages=['fr'])
                #langFr.install()
            if choice=="Italian":
                fconf=open("gpicsync.conf","r+")
                conf= ConfigParser.ConfigParser()
                conf.readfp(fconf)
                conf.set("gpicsync","language","Italian")
                fconf.seek(0)
                conf.write(fconf)
                fconf.close()
                wx.CallAfter(self.consolePrint,"\n"+"Next time you launch GPicSync it will be in Italian."+"\n")
                #langFr = gettext.translation('gpicsync-GUI', "locale",languages=['fr'])
                #langFr.install()
            if choice=="English":
                fconf=open("gpicsync.conf","r+")
                conf= ConfigParser.ConfigParser()
                conf.readfp(fconf)
                conf.set("gpicsync","language","English")
                fconf.seek(0)
                conf.write(fconf)
                fconf.close()
                wx.CallAfter(self.consolePrint,"\n"+"Next time you launch GPicSync it will be in English."+"\n")
                #gettext.install("gpicsync-GUI", "None")#a trick to go back to original
            dialog.Destroy()
            #win.Destroy()
        else:
            dialog.Destroy()
                    
    def aboutApp(self,evt): 
        """An about message dialog"""
        text="GPicSync  0.98-2 - 2007 \n\n"\
        +"GPicSync is Free Software (GPL v2)\n\n"\
        +_("More informations and help:")+"\n\n"+\
        "http://code.google.com/p/gpicsync/"+"\n\n"\
        +"2007 - francois.schnell@gmail.com"
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
            text=_("To visualize the results in Google Earth you must either:")+"\n\n"\
            +_("- finish a synchronisation")+"\n"\
            +("- select a folder you've already synchronized or double-click on the kml file in his folder'")
            wx.CallAfter(self.consolePrint,text)
        try:
            if sys.platform == 'win32':
                googleEarth.OpenKmlFile(path,True)
            if sys.platform.find("linux")!=-1:
                def goGELinux():
                    os.system(googleEarth +" "+path)
                start_new_thread(goGELinux,())
                
        except:
            wx.CallAfter(self.consolePrint,"\n"+_("Couldn't find or launch Google Earth")+"\n")

    def exitApp(self,evt):
        """Quit properly the app"""
        print "Exiting the app..."
        self.Close()
        self.Destroy()
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
        if self.picDirDefault!="":
            openDir.SetPath(self.picDirDefault)
        openDir.ShowModal()
        self.picDir=openDir.GetPath()
        self.dirEntry.SetValue(self.picDir)
        self.picDirDefault=self.picDir
        
    
    def syncPictures(self,evt):
        """Sync. pictures with the .gpx file"""
        if self.dirEntry.GetValue()=="" or self.gpxEntry.GetValue=="":
                #wx.CallAfter(self.consolePrint,"You must first select a pictures folder and a GPX file\n")
                wx.CallAfter(self.consolePrint,_("You must first select a pictures folder and a GPX file.")+"\n")
        else:
            pass
        self.stop=False
        #utcOffset=int(self.utcEntry.GetValue())
        self.utcOffset=float(self.utcEntry.GetValue())#testing float for UTC
        dateProcess=self.dateCheck.GetValue()
        self.log=self.logFile.GetValue()
        self.interpolation=self.interpolationCheck.GetValue()
        print "self.utcOffset= ",self.utcOffset

        def sync():
            if self.dirEntry.GetValue()!="" and self.gpxEntry.GetValue!="":
                wx.CallAfter(self.consolePrint,_("\n------\n"+_("Beginning synchronization with "))
                +_("UTC Offset =")+self.utcEntry.GetValue()+
                _(" hours and maximum time difference = ")+self.timerangeEntry.GetValue() +_(" seconds"+"\n"))
            else:
                pass
            geo=GpicSync(gpxFile=self.gpxFile,tcam_l=self.tcam_l,tgps_l=self.tgps_l,
            UTCoffset=self.utcOffset,dateProcess=dateProcess,timerange=int(self.timerangeEntry.GetValue()),
            backup=False,interpolation=self.interpolation)
            
            if self.backupCheck.GetValue()==True:
                wx.CallAfter(self.consolePrint,"\n"+
                _("Creating an 'originals-backup' folder.")+"\n")
                try:
                    os.mkdir(self.picDir+'/originals-backup')
                except:
                    print "Couldn't create the backup folder, it maybe already exist"

            if self.geCheck.GetValue()==True:
                wx.CallAfter(self.consolePrint,"\n"+_("Starting to generate a Google Earth file (doc.kml) in the picture folder ...")+" \n")
                localKml=KML(self.picDir+"/doc",os.path.basename(self.picDir))
            
            if self.gmCheck.GetValue()==True:
                wx.CallAfter(self.consolePrint,"\n"+_("Starting to generate a Google Map file (doc-web.kml) in the picture folder")+" ... \n")
                webKml=KML(self.picDir+"/doc-web",os.path.basename(self.picDir),url=self.urlEntry.GetValue())
                webKml.path(self.gpxFile)
                webKml.writeInKml("\n<Folder>\n<name>Photos</name>")
                try:
                    os.mkdir(self.picDir+'/thumbs')
                except:
                    print "Couldn't create the thumbs folder, it maybe already exist"
                
            if self.log==True:
                f=open(self.picDir+'/gpicsync.log','w')
                f.write(_("Geocoded with UTC Offset= ")+
                self.utcEntry.GetValue()+_(" and  Maximum time difference = ")\
                +self.timerangeEntry.GetValue()+"\n")
                f.write(_("Pictures Folder: ")+self.picDir+"\n")
                f.write(_("GPX file: ")+self.gpxEntry.GetValue()+"\n\n")
                
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
                or fnmatch.fnmatch ( fileName, '*.DNG' )\
                or fnmatch.fnmatch ( fileName, '*.RAF' ):
                
                    print "\nFound fileName ",fileName," Processing now ..."
                    wx.CallAfter(self.consolePrint,"\n"+_("(Found ")+fileName+" ...")
                    print self.picDir+'/'+fileName
                    
                    if self.backupCheck.GetValue()==True:
                        shutil.copyfile(self.picDir+'/'+fileName,
                         self.picDir+'/originals-backup/'+fileName)
                        
                    result=geo.syncPicture(self.picDir+'/'+fileName)
                    wx.CallAfter(self.consolePrint,result[0]+"\n")
                        
                    if self.log==True:
                        f.write(_("Processed image ")+fileName+" : "+result[0]+"\n")
                        
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
                        except:
                            wx.CallAfter(self.consolePrint,_("Couldn't retrieve geonames data...")+"\n")
                        try:
                            gnPlace=nearby.findNearbyPlace()
                        except:
                            gnPlace=""
                        try:
                            gnDistance=nearby.findDistance()
                        except:
                            gnDistance=""
                        try:
                            gnRegion=nearby.findRegion()
                        except:
                            gnRegion=" "
                            print "hello ?"
                        try:
                            gnCountry=nearby.findCountry()
                        except:
                            gnCountry=""
                        try:
                            gnSummary=gnDistance+"  Km to "+gnPlace+"  in "+gnRegion+" "+gnCountry
                            geotag="geotagged"
                            geotagLat="geo:lat="+str(decimal.Decimal(result[1]).quantize(decimal.Decimal('0.000001'))) 
                            geotagLon="geo:lon="+str(decimal.Decimal(result[2]).quantize(decimal.Decimal('0.000001'))) 
                            wx.CallAfter(self.consolePrint,gnSummary+_(" (writting geonames and geotagged to keywords tag in picture EXIF)")+"\n")
                            os.popen('%s -keywords="%s" -keywords="%s" -keywords="%s" \
                            -keywords="%s"  -overwrite_original -keywords="%s" -keywords="%s" -keywords="%s" "%s" '\
                            % (self.exifcmd,gnPlace,gnCountry,gnSummary,gnRegion,geotag,geotagLat,geotagLon,self.picDir+'/'+fileName))
                        except:
                            pass
                            
            if self.stop==False:
                wx.CallAfter(self.consolePrint,"\n*** "+_("FINISHED GEOCODING PROCESS")+" ***\n")
            if self.stop==True:
                wx.CallAfter(self.consolePrint,"\n *** "+_("PROCESSING STOPPED BY THE USER")+" ***\n")
            if self.log==True: f.close()
            
            if self.geCheck.GetValue()==True:
                wx.CallAfter(self.consolePrint,"\n"+_("Adding the GPS track log to the Google Earth kml file")+"...\n")
                localKml.path(self.gpxFile)
                localKml.close()
                wx.CallAfter(self.consolePrint,"\n"+_("Click on the 'View in Google Earth' button to visualize the result")+".\n")
                wx.CallAfter(self.consolePrint,_("( A Google Earth doc.kml file has been created in your picture folder.)")+"\n")
            
            if self.gmCheck.GetValue()==True:
                #webKml.path(self.gpxFile)
                webKml.writeInKml("</Folder>\n")
                webKml.close()
                wx.CallAfter(self.consolePrint,_("( A Google Maps doc-web.kml file has been created with the given url )")+"\n")
                
        start_new_thread(sync,())
        #googleEarth =win32com.client.Dispatch("GoogleEarth.ApplicationGE")
        
    def localtimeCorrection(self,evt):
            """ Local time correction if GPS and camera wasn't synchronized """
            #self.winOpt.Close()
            self.tcam_l=self.camEntry.GetValue()
            self.tgps_l=self.gpsEntry.GetValue()
            wx.CallAfter(self.consolePrint,"\n"+"A time correction has been set : "+
            "Time camera= "+self.tcam_l+" Time GPS= "+self.tgps_l+" .\n")
            print "tcam_l =",self.tcam_l
            print "tgps_l =",self.tgps_l
    
    def quitLocaltimeCorrection(self,evt):
            self.winOpt.Close()
            
    def localtimeFrame(self,evt):
        """A frame for local time correction"""
        self.winOpt=wx.Frame(win,size=(440,280),title=_("Local time corrections"))
        bkg=wx.Panel(self.winOpt)
        #bkg.SetBackgroundColour('White')
        text=_("\t"+_("Use this option ONLY if your camera local time is wrong.")\
        +"\n\n"+_("Indicate here the local time now displayed by your camera and GPS (hh:mm:ss)"))
        utcLabel = wx.StaticText(bkg, -1,text)
        camLabel = wx.StaticText(bkg, -1,_("Local time displayed now by the camera"))
        self.camEntry=wx.TextCtrl(bkg,size=(100,-1))
        self.camEntry.SetValue(self.tcam_l)
        gpsLabel = wx.StaticText(bkg, -1,_("Local time displayed now by the GPS"))
        self.gpsEntry=wx.TextCtrl(bkg,size=(100,-1))
        self.gpsEntry.SetValue(self.tgps_l)
        applyButton=wx.Button(bkg,size=(130,30),label=_("Apply correction"))
        quitButton=wx.Button(bkg,size=(70,30),label=_("Quit"))
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
        self.winExifReader=wx.Frame(win,size=(280,220),title=_("EXIF Reader"))
        bkg=wx.Panel(self.winExifReader)
        #bkg.SetBackgroundColour('White')
        text=_("Read the EXIF metadata of the selected picture.")
        introLabel = wx.StaticText(bkg, -1,text)
        self.ExifReaderSelected=_("All EXIF metadata")
        radio1=wx.RadioButton(bkg,-1,_("All EXIF metadata"))
        radio2=wx.RadioButton(bkg,-1,_("Date/Time/Lat./Long."))
        def onRadio(evt):
            radioSelected=evt.GetEventObject()
            self.ExifReaderSelected=radioSelected.GetLabel()
        for eachRadio in [radio1,radio2]:
            self.Bind(wx.EVT_RADIOBUTTON ,onRadio,eachRadio)
        readButton=wx.Button(bkg,size=(130,30),label=_("Select a picture"))
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
        #picture.SetWildcard("*.JPG")
        picture.ShowModal()
        pathPicture=picture.GetPath()
        if pathPicture !="" or None:
            myPicture=GeoExif(pathPicture)
            def read():
                wx.CallAfter(self.consolePrint,"\n\n"+_("Selected metada ")+"\n")
                wx.CallAfter(self.consolePrint,"-------------------\n")
                if self.ExifReaderSelected==_("All EXIF metadata"):
                    wx.CallAfter(self.consolePrint,myPicture.readExifAll())
                    
                if self.ExifReaderSelected==_("Date/Time/Lat./Long."):
                    dateTime=myPicture.readDateTime()
                    datetimeString=dateTime[0]+":"+dateTime[1]
                    if len(datetimeString)>5:
                        wx.CallAfter(self.consolePrint,datetimeString)
                        wx.CallAfter(self.consolePrint,"    "+_("lat./long.")+"="+str(myPicture.readLatLong()))
                    else:
                        wx.CallAfter(self.consolePrint,_("None"))
            start_new_thread(read,())
            self.winExifReader.Close()
            
    def renameFrame(self,evt):
        """A frame for the rename tool"""
        self.winRenameTool=wx.Frame(win,size=(280,220),title=_("Renaming tool"))
        bkg=wx.Panel(self.winRenameTool)
        #bkg.SetBackgroundColour('White')
        text=_("This tool renames your pictures with the ")+"\n"+_("original time/date and lat./long.(if present)")
        introLabel = wx.StaticText(bkg, -1,text)
        readButton=wx.Button(bkg,size=(200,30),label=_("Rename pictures in a folder"))
        readButtonFolder=wx.Button(bkg,size=(200,30),label=_("Rename a single picture"))
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
            wx.CallAfter(self.consolePrint,"\n"+_("Beginning renaming..."))
            def rename():
                myPicture=GeoExif(self.pathPicture)
                string=myPicture.readDateTime()[0]+" "+myPicture.readDateTime()[1]
                string=string.replace(":","-")
                latlong=myPicture.readLatLong()
                if latlong==None: latlong=""
                if len(string)<5:
                    wx.CallAfter(self.consolePrint,"\n"+_("Didn't find Original Time/Date for ")+self.pathPicture)
                else:
                    os.rename(self.pathPicture,os.path.dirname(self.pathPicture)+"/"+string+" "+latlong+".jpg")
                    wx.CallAfter(self.consolePrint,"\n"+_("Renamed ")+os.path.basename(self.pathPicture)+" -> "+string+latlong+".jpg")
            start_new_thread(rename,())
            
    def renamePicturesInFolder(self,evt):
        self.stop=False        
        self.winRenameTool.Close()
        openDir=wx.DirDialog(self)
        openDir.ShowModal()
        self.picDir=openDir.GetPath()
        if self.picDir!="" or None:
            wx.CallAfter(self.consolePrint,"\n"+_("Beginning renaming..."))
            def rename():
                for fileName in os.listdir ( self.picDir ):
                        if self.stop==True:
                            wx.CallAfter(self.consolePrint,"\n"+_("Interrupted by the user")) 
                            self.stop=False
                            break
                        if fnmatch.fnmatch ( fileName, '*.JPG' )or \
                        fnmatch.fnmatch ( fileName, '*.jpg' ):
                            print self.picDir+'/'+fileName
                            myPicture=GeoExif(self.picDir+"/"+fileName)
                            string=myPicture.readDateTime()[0]+" "+myPicture.readDateTime()[1]
                            print string, len(string)
                            if len(string)<5:
                                wx.CallAfter(self.consolePrint,"\n"+_("Didn't find Original Time/Date for ")+fileName)
                                break
                            string=string.replace(":","-")
                            latlong=myPicture.readLatLong()
                            if latlong==None: latlong=""
                            print "latlong= ",latlong
                            os.rename(self.picDir+'/'+fileName,self.picDir+"/"+string+" "+latlong+".jpg")
                            wx.CallAfter(self.consolePrint,"\n"+_("Renamed ")+fileName+" to "+string+" "+latlong+".jpg")
                wx.CallAfter(self.consolePrint,"\n"+_("Finished"))
            start_new_thread(rename,())
    
    def kmzGeneratorFrame(self,evt):
        """A frame to generate a KMZ  file"""
        self.winKmzGenerator=wx.Frame(win,size=(280,180),title="KMZ Generator")
        bkg=wx.Panel(self.winKmzGenerator)
        text="\n"+_("Create a kmz file archive")
        introLabel = wx.StaticText(bkg, -1,text)
        readButton=wx.Button(bkg,size=(150,30),label=_("Create KMZ file !"))
        self.Bind(wx.EVT_BUTTON, self.kmzGenerator, readButton)
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.Add(introLabel,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=20)
        #vbox.Add(self.gpxInGECheck,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=10)
        vbox.Add(readButton,proportion=0,flag=wx.ALIGN_CENTER|wx.ALL,border=20)
        bkg.SetSizer(vbox)
        if sys.platform.find("linux")!=-1:
            wx.CallAfter(self.consolePrint,"\n"+_("Sorry this tool is not yet available for the Linux version")+" \n")
        else:
            self.winKmzGenerator.Show()
        
    def kmzGenerator(self,evt):
        """A tool to create a kmz file containing the geolocalized pictures"""
        print  "kmz ordered ..."
        self.winKmzGenerator.Close()
        if self.picDir == None or self.picDir !="":
            wx.CallAfter(self.consolePrint,"\n"+_("Creating a KMZ file in the pictures folder...")+"\n")
            zip = zipfile.ZipFile(self.picDir+'/'+os.path.basename(self.picDir)+".zip", 'w')
            zip.write(self.picDir+'/doc.kml','doc.kml',zipfile.ZIP_DEFLATED)
            wx.CallAfter(self.consolePrint,"\n"+_("Adding doc.kml"))
            for fileName in os.listdir ( self.picDir ):
                if fnmatch.fnmatch ( fileName, '*.JPG' )or fnmatch.fnmatch ( fileName, '*.jpg' ):
                    zip.write(self.picDir+"/"+fileName,fileName,zipfile.ZIP_DEFLATED)
                    wx.CallAfter(self.consolePrint,"\n"+_("Adding ")+fileName)
            zip.close()
            try:
                os.rename(self.picDir+'/'+os.path.basename(self.picDir)+".zip",self.picDir+'/'+os.path.basename(self.picDir)+".kmz")
                wx.CallAfter(self.consolePrint,"\n"+_("KMZ file created in pictures folder")+"\n")
            except WindowsError:
                wx.CallAfter(self.consolePrint,"\n"+_("Couldn't rename the zip file to kmz (maybe a previous file already exist)")+"\n")
        else:
            text="\n --- \n"+_("To create a Google Earth kmz file you must either:")+"\n\n"\
            +_("- finish a synchronisation")+"\n"\
            +_("- select a folder you've already synchronized then select the KMZ Generator tool")+"\n --- \n"
            wx.CallAfter(self.consolePrint,text)
                
        
    def gpxInspectorFrame(self,evt):
        """A frame to inspect a gpx file"""
        self.winGpxInspector=wx.Frame(win,size=(280,180),title=_("GPX Inspector"))
        bkg=wx.Panel(self.winGpxInspector)
        text=_("Inspect a gpx file and show tracklog data.")
        introLabel = wx.StaticText(bkg, -1,text)
        readButton=wx.Button(bkg,size=(150,30),label=_("Select a gpx file"))
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
            wx.CallAfter(self.consolePrint,"\n"+_("Select a gpx file first."))
        else:
            myGpx=Gpx(gpxPath).extract()
            wx.CallAfter(self.consolePrint,"\n"+_("Looking at ")+gpxPath+"\n")
            wx.CallAfter(self.consolePrint,"\n"+_("Number of valid track points found")+" : "+str(len(myGpx))+"\n\n")
            def inspect():
                for trkpt in myGpx:
                    wx.CallAfter(self.consolePrint,_("Date")+": "+trkpt["date"]+"\t"+_("Time")+": "\
                    +trkpt["time"]+"\t"+_("Latitude")+": "+trkpt["lat"]
                    +"\t"+_("Longitude")+": "+trkpt["lon"]
                    +"\t"+_("Altitude")+": "+trkpt["ele"]+"\n")
            start_new_thread(inspect,())
            
app=wx.App(redirect=False)
win=GUI(None,title="GPicSync GUI")
win.Show()
app.MainLoop()

# Reloads the GUI when language change
"""
while 0:
    win=GUI(None,title="GPicSync GUI")
    win.Show()
    app.MainLoop()
"""
