#####################################################
# WARNING : 
#
# - This Free Software comes without any warranty.
# - Always check the results on a map.
#
#####################################################

GPicSync - 2007


See the license.txt in the same folder.

For help and documentation: http://code.google.com/p/gpicsync/


WINDOWS:
--------

Download the last executable at GPicSync website:
http://code.google.com/p/gpicsync/

Launch the windows installer gpicsync-xx.exe


LINUX:
------

$ python gpicsync-GUI.py

GPicSync requires:

- Python2.5
- exiftool
- wxpython for the GUI (2.8 but it could maybe work with a previous version)
- python-imaging (from version 0.93 of GPicSync)
- Google Earth (for Google Earth features). The Google-earth folder must in your home folder.

GPicSync was successfully on Linux Ubuntu "Feisty Fawn" 
(Python 2.5 is already installed as a default for this distribution and you can add wxpython and python-imaging from synaptic
for example). 
In synaptic install exiftool, python-wgtk2.8 and python-imaging.

Note: On Mandrive 2007.1 Exiftool is known as perl-Image-ExifTool.

To install GoogleEarth on Ubuntu:
- fetch GoogleEarthLinux.bin on Google Earth website
- chmod +x GoogleEarthLinux.bin
- ./GoogleEarthLinux.bin


If you prefer the command-line version (or if you can't have the right wxpython for your distro):

$ python gpicsync.py --help


Linux version issues:
---------------------

As time of writting (14 of april):
- the kmz tool in tools menu is not fuctionnal yet
- layout to improve

Still test to carry but main fuctionnalies are there. 
Don't hesitate to report any problem you may encounter.


Thanks and contributions:
-------------------------

Thanks to Marc Nozell for testing GPicSync on Linux before I had the time to do it
and for putting some specific Windows code behind a plateform check 
(changing  "exiftool.exe" to  "exiftool" for Linux in geoexif.py)

Big Thanks to all the users reporting bugs or asking for feature requests 
(see contributions page on the wiki project + issues page + dedicated Google Group). 


--
francois.schnell@gmail.com