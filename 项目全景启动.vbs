Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "C:\Users\nicou\AppData\Local\Programs\Python\Python314\python.exe D:\建网站\mojing-docs\项目全景进度.py", 0, False
WScript.Sleep 2000
WshShell.Run "http://localhost:8899"
