' Opus Translate — Tray Launcher
' pythonw.exe ile calistirir, hic konsol penceresi acmaz.

Dim fso, scriptDir, shell
Set fso       = CreateObject("Scripting.FileSystemObject")
Set shell     = CreateObject("WScript.Shell")
scriptDir     = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = scriptDir

shell.Run "venv\Scripts\pythonw.exe tray.py", 0, False
