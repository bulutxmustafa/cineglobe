# Starts CINEGLOB locally: API on :8000 (local SQLite file) and website on :3000.
# Usage (PowerShell, repo root):  .\start-dev.ps1
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")

$env:DATABASE_URL = "sqlite:///dev_local.sqlite3"
$env:CACHE_BACKEND = "locmem"
$env:CSRF_TRUSTED_ORIGINS = "http://localhost:3000"
Push-Location "$root\backend"
& "$root\.venv\Scripts\python.exe" manage.py migrate -v 0
Start-Process -FilePath "$root\.venv\Scripts\python.exe" -ArgumentList "manage.py runserver localhost:8000 --noreload" -WindowStyle Minimized
Pop-Location

Push-Location "$root\web"
if (-not (Test-Path node_modules)) { npm install }
Write-Host "Site: http://localhost:3000/tr   (API: http://127.0.0.1:8000/api/schema/swagger-ui/)"
npm run dev
Pop-Location
