GPicSync - 2007 - 2014

#####################################################
# WARNING : 
#
# - This Free GPL Software comes without any warranty.
# - Always check the results on a map.
# - See the license.txt in the same folder
#
#####################################################


For help and documentation: 
http://code.google.com/p/gpicsync/
https://github.com/notfrancois/GPicSync

GPicSync also embeds two great free free software tools (thanks to their authors):
- EXIFtool from Phil Harvey
- GPSBable from Robert Lipe 

WINDOWS:
--------

Download the latest executable at GPicSync website:
http://sourceforge.net/projects/gpicsync/files/

Launch the windows installer gpicsync-xx.exe


LINUX:
------

$ python gpicsync-GUI.py

GPicSync requires:

- Python2.5 or above
- exiftool
- wxpython for the GUI (2.8 but it could maybe work with a previous version)
- python-imaging (from version 0.93 of GPicSync)
- python-unidecode
- Google Earth (for Google Earth features). The Google-earth folder must in your home folder.

GPicSync was successfully on Linux Ubuntu "Feisty Fawn" 
(Python 2.5 is already installed as a default for this distribution and you can add wxpython and python-imaging from synaptic
for example). 
In synaptic install exiftool, python-wxgtk2.8 and python-imaging python-unidecode.

Note: On Mandrive 2007.1 Exiftool is known as perl-Image-ExifTool.

To install GoogleEarth on Ubuntu:
- fetch GoogleEarthLinux.bin on Google Earth website
- chmod +x GoogleEarthLinux.bin
- ./GoogleEarthLinux.bin

The first time you run the Linux version you won't have a configuration file. 
To generate one in your home folder quit GPicSync with the "Quit and save settings"
(this is userful if you want to fine tune Geonames for example)

If you prefer the command-line version (or if you can't have the right wxpython for your distro):

$ python gpicsync.py --help



Thanks and contributions:
-------------------------
https://code.google.com/p/gpicsync/wiki/Contributions


--
Contact at :
notfrancois AT gmail.com