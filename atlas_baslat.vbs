' ATLAS Arka Plan Baslatici
' Bilgisayar acildiginda sessizce baslar

Set WshShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strPath
WshShell.Run strPath & "\venv\Scripts\pythonw.exe main.py --arka-plan", 0, False
