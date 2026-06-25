@echo off
start /B "" openclaw gateway run >nul 2>&1
timeout /t 8 /nobreak >nul
start http://127.0.0.1:18789
