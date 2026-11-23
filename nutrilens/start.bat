@echo off
title NutriLens - Starting...
color 0A

echo.
echo  ============================================================
echo   NutriLens - Automated Food Label Analyser
echo  ============================================================
echo.
echo  Starting Backend (FastAPI + PaddleOCR)...
echo  Starting Frontend (React + Vite)...
echo.
echo  Backend  -^>  http://localhost:8000
echo  Frontend -^>  http://localhost:5173
echo.
echo  Press Ctrl+C to stop both servers.
echo  ============================================================
echo.

cd /d "%~dp0"
npm run dev
