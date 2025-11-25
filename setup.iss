[Setup]
AppName=Password Manager
AppVersion=1.0
AppPublisher=K1T Tech.
DefaultDirName={localappdata}\Password Manager
DefaultGroupName=Password Manager
OutputDir=.
OutputBaseFilename=Setup
SetupIconFile=info.ico
UninstallDisplayIcon={app}\info.ico

[Files]
Source: "dist\Password Manager.dist\Password Manager.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Password Manager.dist\*.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Password Manager.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "info.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userdesktop}\Password Manager"; Filename: "{app}\Password Manager.exe"

[Registry]
; ปิดโหมดความเข้ากันได้
Root: HKLM; Subkey: "Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"; ValueType: string; ValueName: "{app}\MARINE CONNECT.exe"; ValueData: ""; Flags: uninsdeletevalue
