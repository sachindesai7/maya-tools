@echo off
REM Launches Chrome with remote debugging on port 9222.
REM Close ALL Chrome windows first, then run this file.
REM The Figma Asset Exporter "Chrome" button reads the active tab URL from this port.

set CHROME="C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist %CHROME% set CHROME="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

start "" %CHROME% --remote-debugging-port=9222 --user-data-dir="%TEMP%\chrome_debug_profile"

echo Chrome started with debug port 9222.
echo Now open Figma in this Chrome window.
pause
