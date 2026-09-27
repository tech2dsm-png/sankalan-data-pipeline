@echo off
echo ============================================
echo  Sankalan Real-Time Pipeline
echo  Starting Kafka, Spark, PostgreSQL
echo ============================================

cd /d "%~dp0.."

echo [1/4] Starting Docker services...
docker-compose up -d

echo.
echo [2/4] Waiting for services to be ready...
timeout /t 10 /nobreak > nul

echo.
echo [3/4] Starting FastAPI...
start "FastAPI" cmd /k "uvicorn api.app:app --reload --host 0.0.0.0 --port 5000"

echo.
echo [4/4] Starting Kafka Producer (for testing)...
start "Kafka Producer" cmd /k "python kafka\producer.py"

echo.
echo ============================================
echo  Pipeline is running!
echo  FastAPI: http://localhost:5000
echo  API Docs: http://localhost:5000/docs
echo  Spark UI: http://localhost:8080
echo  PostgreSQL: localhost:5432
echo ============================================
pause