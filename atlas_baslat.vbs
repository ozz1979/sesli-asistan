' ATLAS Arka Plan Başlatıcı
' Bilgisayar açıldığında ATLAS'ı sessizce başlatır
' Komut penceresi göstermez

Set WshShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strPath
WshShell.Run "pythonw main.py --arka-plan", 0, False
