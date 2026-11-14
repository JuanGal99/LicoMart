@echo off
chcp 65001 >nul 2>&1
:: ============================================================
::  LicoMart - Arranque completo con un solo comando
::  Uso:  iniciar.bat              (carga datos demo por defecto)
::        iniciar.bat --no-seed    (conserva datos existentes)
:: ============================================================

set "SEED_ON_START=true"
if "%~1"=="--no-seed" (
    set "SEED_ON_START=false"
    echo.
    echo   Se conservaran los datos existentes ^(sin recarga demo^).
    echo.
)

echo.
echo   Construyendo e iniciando LicoMart...
echo.

docker compose up --build -d

echo.
echo   Esperando a que los servicios esten listos...

set RETRIES=40
:wait_loop
curl -sf http://localhost:5173/ >nul 2>&1
if %errorlevel%==0 goto :ready
set /a RETRIES-=1
if %RETRIES% LEQ 0 (
    echo.
    echo   ERROR: Timeout esperando los servicios. Revisa: docker compose logs
    pause
    exit /b 1
)
timeout /t 3 /nobreak >nul
goto :wait_loop

:ready
echo.
echo ========================================================
echo   LicoMart esta corriendo
echo ========================================================
echo.
echo   URL:  http://localhost:5173
echo.
echo   CREDENCIALES:
echo   ----------------------------------------
echo   Rol: admin       Usuario: admin       Clave: Admin2026!
echo   Rol: usuario     Usuario: usuario     Clave: Usuario2026!
echo   ----------------------------------------
echo.
echo   Logs:   docker compose logs -f
echo   Parar:  docker compose down
echo ========================================================
echo.
pause
