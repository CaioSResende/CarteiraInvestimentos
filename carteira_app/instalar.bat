@echo off
echo ============================================
echo   Instalando Carteira Financeira...
echo ============================================
echo.

:: Verifica se Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo.
    echo Por favor, instale o Python em:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANTE: Marque a opcao "Add Python to PATH"
    echo durante a instalacao!
    pause
    exit /b 1
)

echo [OK] Python encontrado.
echo.
echo Instalando dependencias...
pip install flask --quiet
echo [OK] Flask instalado.
echo.
echo ============================================
echo   Tudo pronto! Para iniciar o app, execute:
echo   iniciar.bat
echo ============================================
pause
