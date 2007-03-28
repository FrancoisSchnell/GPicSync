; Install file for GPicSync
; (C)2007 francois schnell
;

[Setup]
AppName=GPicSync
AppId=GPicSync
AppVerName=GPicSync 0.6
AppVersion=0.6
AppPublisher=francois schnell
AppPublisherURL=http://francois.schnell.free.fr
AppSupportURL=http://code.google.com/p/gpicsync/
AppUpdatesURL=http://code.google.com/p/gpicsync/
DefaultDirName={pf}\GPicSync
DefaultGroupName=GPicSync
OutputDir=Output
LicenseFile=license.txt

[Dirs]

[Files]

Source: dist\_controls_.pyd; DestDir:{app}
Source: dist\_core_.pyd; DestDir:{app}
Source: dist\_gdi_.pyd; DestDir:{app}
Source: dist\_misc_.pyd; DestDir:{app}
Source: dist\_windows_.pyd; DestDir:{app}
Source: dist\bz2.pyd; DestDir:{app}
Source: dist\exiftool.exe; DestDir:{app}
Source: dist\gpicsync-GUI.exe; DestDir:{app}
Source: dist\library.zip; DestDir:{app}
Source: dist\license.txt; DestDir:{app}
Source: dist\MSVCR71.dll; DestDir:{app}
Source: dist\pyexpat.pyd; DestDir:{app}
Source: dist\python25.dll; DestDir:{app}
Source: dist\README.txt; DestDir:{app}
Source: dist\unicodedata.pyd; DestDir:{app}
Source: dist\w9xpopen.exe; DestDir:{app}
Source: dist\wxbase28h_net_vc.dll; DestDir:{app}
Source: dist\wxbase28h_vc.dll; DestDir:{app}
Source: dist\wxmsw28h_adv_vc.dll; DestDir:{app}
Source: dist\wxmsw28h_core_vc.dll; DestDir:{app}
Source: dist\wxmsw28h_html_vc.dll; DestDir:{app}
Source: dist\test.ico; DestDir:{app}
;Source: dist\Website; DestDir:{app}

[Run]

[Languages]
Name: Anglais; MessagesFile: compiler:Default.isl
Name: Francais; MessagesFile: compiler:Languages\French.isl
Name: Allemand; MessagesFile: compiler:Languages\German.isl

[Icons]
Name: {group}\GPicSync.exe; Filename: {app}\gpicsync-GUI.exe; IconIndex: 0; WorkingDir: {app};IconFilename: {app}\test.ico
;Name: {group}\Website; Filename: {app}\Website; IconIndex: 0; WorkingDir: {app}
Name: {commondesktop}\GPicSync; Filename: {app}\Gpicsync-GUI.exe; IconIndex: 0; WorkingDir: {app};IconFilename: {app}\test.ico

[Registry]

[InstallDelete]
Name: {tmp}; Type: filesandordirs

[UninstallDelete]

[Code]



