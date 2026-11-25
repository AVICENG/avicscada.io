echo off
cls
rem D. Watson 12/07/2001
echo Stopping CrypKey License Service
net stop "crypkey license" 
echo CrypKey service has been stopped
echo Installing latest version of Crypkey
setupex
cls
echo Install complete.
type setupex.xco
echo :  setupex.xco code
echo PLEASE REBOOT YOUR COMPUTER!

