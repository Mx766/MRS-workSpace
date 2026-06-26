@echo off
:: 把 DOCX 文件拖到这个 bat 上即可翻译
cd /d "%~dp0"
start pythonw translate_app.py "%~1"
