@echo off
rem Double-click to play. Opens in Windows Terminal when it is installed.
rem %~dp0 ends with a backslash; strip it, or wt reads \" as an escaped quote.
set "HERE=%~dp0"
set "HERE=%HERE:~0,-1%"
cd /d "%HERE%"
where wt >nul 2>nul && (
    start "" wt -d "%HERE%" "%HERE%\.venv\Scripts\python.exe" -m squirrel_vim_quest
) || (
    "%HERE%\.venv\Scripts\python.exe" -m squirrel_vim_quest
)
