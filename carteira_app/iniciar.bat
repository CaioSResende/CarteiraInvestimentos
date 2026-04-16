@echo off
echo ============================================
echo   Carteira Financeira - Iniciando...
echo ============================================
echo.
echo Abrindo no navegador em instantes...
echo Para encerrar: feche esta janela ou Ctrl+C
echo.

:: Abre o navegador apos 2 segundos
start "" timeout /t 2 >nul
start "" "http://localhost:5000"

:: Inicia o servidor Python
python server.py

pause
