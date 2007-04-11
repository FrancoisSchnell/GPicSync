#####################################################
# WARNING : 
#
# - This Free Software comes without any warranty.
# - Always check the results on a map.
#
#####################################################

See the license.txt in the same folder.

For help and documentation: http://code.google.com/p/gpicsync/


WINDOWS:
--------

Launch the windows installer gpicsync-xx.exe


LINUX:
------

$ python gpicsync-GUI.py

version 0.5 requires:

- Python2.5
- exiftool
- wxpython for the GUI (2.8 but it could maybe work with a previous verion) 

I've tested GPicSync successfully on Linux Ubuntu "Feisty Fawn":
Python 2.5 is already installed as a default. 
In synaptic install exiftool and python-wgtk2.8

If you prefer the command-line version (or if you can't have the right wxpython for your distro):

$ python gpicsync.py --help
 

Thanks to Marc Nozell (marc@nozell.com) for his patch on geoexif.py,
gpicsync-GUI.py


--
francois.schnell@gmail.com