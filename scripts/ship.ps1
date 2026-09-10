param(
    [Parameter(Mandatory=$true)]
    [string]$Message
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Run this script from the ResearchIntelligence project root."
}

Write-Host "Running tests..." -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" -m pytest
if ($LASTEXITCODE -ne 0) {
    throw "Tests failed. Nothing will be committed or pushed."
}

Write-Host "Staging changes..." -ForegroundColor Cyan
git add .

Write-Host "Creating commit..." -ForegroundColor Cyan
git commit -m $Message
if ($LASTEXITCODE -ne 0) {
    throw "Commit failed."
}

Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
git push
if ($LASTEXITCODE -ne 0) {
    throw "Push failed."
}

Write-Host "Checkpoint complete." -ForegroundColor Green
