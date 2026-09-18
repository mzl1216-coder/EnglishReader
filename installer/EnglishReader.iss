#define MyAppName "English Reader"
#define MyAppVersion "1.0.0"
[Setup]
AppId={{EC3B9173-6919-430D-A811-D6F6B8C9CA6E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=mzl1216-coder
AppPublisherURL=https://github.com/mzl1216-coder/EnglishReader
DefaultDirName={autopf}\English Reader
DefaultGroupName=English Reader
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=EnglishReader-Setup-x64
SetupIconFile=..\assets\icons\app.ico
UninstallDisplayIcon={app}\EnglishReader.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
PrivilegesRequired=admin
LicenseFile=..\LICENSE
CloseApplications=yes
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked
[Files]
Source: "..\dist\EnglishReader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\English Reader"; Filename: "{app}\EnglishReader.exe"
Name: "{autodesktop}\English Reader"; Filename: "{app}\EnglishReader.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\EnglishReader.exe"; Description: "Launch English Reader"; Flags: nowait postinstall skipifsilent runasoriginaluser
