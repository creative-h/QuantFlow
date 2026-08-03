$ErrorActionPreference = 'Stop'
Push-Location "$PSScriptRoot\..\backend"
try {
    & ..\.venv\Scripts\python.exe -m ruff check .
    & ..\.venv\Scripts\python.exe -m black --check .
    & ..\.venv\Scripts\python.exe -m pytest
}
finally {
    Pop-Location
}
