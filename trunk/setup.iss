; InnoSetup setup file for GmailTray

; Miki Tebeka <miki.tebeka@gmail.com>
 
[Setup]
AppName = GmailTray
DefaultDirName = "{pf}\GmailTray"
DefaultGroupName = "GmailTray"
OutputDir = .

; This is created by the build system
#include "version.iss"

[Files]
Source: dist\*; DestDir: {app}

[Icons]
; Group
Name: "{group}\GmailTray"; Filename: "{app}\gmailtray.exe"
Name: "{group}\License"; Filename: "{app}\LICENSE.txt"
Name: "{group}\README"; Filename: "{app}\README.html"
Name: "{group}\Uninstall"; Filename: "{uninstallexe}"

; Also in startup
Name: "{userstartup}\GmailTray"; Filename: "{app}\gmailtray.exe"

[Run]
Filename: "{app}\gmailtray.exe"; Parameters: "--initialize"

[UninstallDelete]
Type: files; Name: "{app}\messages.db"
Type: files; Name: "{app}\gmailtray.exe.log"
