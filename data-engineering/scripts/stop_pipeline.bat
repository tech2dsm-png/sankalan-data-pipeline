@echo off
echo ============================================
echo  Stopping Sankalan Real-Time Pipeline
echo ============================================

cd /d "%~dp0.."

echo [1/3] Stopping Docker services...
docker-compose down

echo.
echo [2/3] Stopping FastAPI...
taskkill /F /IM cmd.exe /FI "WINDOWTITLE eq FastAPI"

echo.
echo [3/3] Stopping Kafka Producer...
taskkill /F /IM cmd.exe /FI "WINDOWTITLE eq Kafka Producer"

echo.
echo ============================================
echo  All services stopped.
echo ============================================
pause