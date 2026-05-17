' ATLAS Arka Plan Baslatici
' Bilgisayar acildiginda donanim hazir olana kadar bekle
WScript.Sleep 15000
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\LENOVO\Desktop\atlas-v8.2\sesli-asistan"
WshShell.Run "venv\Scripts\pythonw.exe main.py --arka-plan", 0, False
