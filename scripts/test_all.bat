@echo off
echo Running Ruff Lint...
uv run ruff check .
if %errorlevel% neq 0 exit /b %errorlevel%

echo Running Type Check (basedpyright)...
uv run basedpyright
if %errorlevel% neq 0 exit /b %errorlevel%

echo Running Tests...
uv run pytest
if %errorlevel% neq 0 exit /b %errorlevel%

echo ALL CHECKS PASSED
