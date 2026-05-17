' ATLAS Arka Plan Baslatici
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\LENOVO\Desktop\atlas-v8.2\sesli-asistan"
WshShell.Run "venv\Scripts\pythonw.exe main.py --arka-plan", 0, False
