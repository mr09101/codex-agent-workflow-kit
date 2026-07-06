@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Run codex-multi-agent-workflow-kit

echo.
echo [codex-multi-agent-workflow-kit] CLI help
echo This project is a command-line toolkit. The help screen will be printed below.
echo.

where python >nul 2>nul
if %errorlevel%==0 (
  python -m codex_multi_agent_workflow_kit.cli --help
  goto done
)

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m codex_multi_agent_workflow_kit.cli --help
  goto done
)

echo Python was not found. Please install Python 3.10+ and run this file again.

:done
echo.
echo Example:
echo   python -m codex_multi_agent_workflow_kit.cli check "D:\AI PROJECT\some-project"
echo.
pause
