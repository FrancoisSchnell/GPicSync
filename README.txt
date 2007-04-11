#####################################################
# WARNING : 
#
# - This Free Software comes without any warranty.
# - Always check the results on a map.
#
#####################################################

GPicSync 0.85 - April 2007


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
- wxpython for the GUI (2.8 but it could maybe work with a previous verion)
- Google Earth (for Google Earth features)

GPicSync was tested successfully on Linux Ubuntu "Feisty Fawn" 
(Python 2.5 is already installed as a default for this distribution). 

In synaptic install exiftool and python-wgtk2.8

If you prefer the command-line version (or if you can't have the right wxpython for your distro):

$ python gpicsync.py --help
 

Thanks to Marc Nozell (marc@nozell.com) for his patch on geoexif.py,
gpicsync-GUI.py (Windows-specific code behind a platform check)


--
francois.schnell@gmail.com