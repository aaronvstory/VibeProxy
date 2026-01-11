@echo off
title VibeProxy Manager
cd /d "%~dp0"
powershell -NoExit -ExecutionPolicy Bypass -File "VibeProxy-Manager.ps1"
