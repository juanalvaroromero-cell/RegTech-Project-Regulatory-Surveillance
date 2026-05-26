@echo off
echo Iniciando RegTech Dashboard...

:: The following command moves the terminal to the exact folder where this file is located.
cd /d "%~dp0"

:: Comando para levantar Streamlit
streamlit run app.py

pause