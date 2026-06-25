Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "C:\Users\nicou\AppData\Roaming\npm\openclaw.cmd gateway run", 0, False
WScript.Sleep 8000
WshShell.Run "http://127.0.0.1:18789"
