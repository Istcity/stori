@echo off
chcp 65001 >nul
title StoryTime Studio - AI 2D Storytime Animator
echo ==============================================================
echo       🎬 STORYTIME STUDIO - AI 2D STORYTIME ANIMATOR
echo ==============================================================
echo.
echo [1/3] Sanal ortam ve bilesenler kontrol ediliyor...
set VENV_PY=C:\Users\sinan.nergiz\.gemini\antigravity-ide\scratch\.venv\Scripts\python.exe

if not exist "%VENV_PY%" (
    echo [UYARI] Onerilen .venv bulunamadi, sistem python'i kullaniliyor.
    set VENV_PY=python
)

echo [2/3] StoryTime Studio arka plan sunucusu baslatiliyor (Port 8000)...
start "" http://127.0.0.1:8000

"%VENV_PY%" -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
pause
