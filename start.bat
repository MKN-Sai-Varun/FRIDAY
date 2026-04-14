@echo off
echo Starting Friday VA FastAPI Backend...
start cmd /k "uvicorn backend.main:app --host 0.0.0.0 --port 8000"

echo Starting Next.js Web GUI...
cd frontend
start cmd /k "npm run dev"

echo FRIDAY is going online! Look for the browser window at http://localhost:3000
pause
