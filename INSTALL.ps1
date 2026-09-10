param(
    [string]$ProjectRoot = (Get-Location).Path,
    [string]$CommitMessage = "Apply final research intelligence engine bundle"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path (Join-Path $ProjectRoot ".git"))) {
    throw "Run this installer from the ResearchIntelligence project root."
}

if (-not (Test-Path (Join-Path $ProjectRoot ".venv\Scripts\python.exe"))) {
    throw "ResearchIntelligence .venv was not found."
}

$payload = Join-Path $PSScriptRoot "payload"

Get-ChildItem $payload -Recurse -File | ForEach-Object {
    $relative = $_.FullName.Substring($payload.Length).TrimStart('\')
    $destination = Join-Path $ProjectRoot $relative
    $destinationDir = Split-Path $destination -Parent
    New-Item -ItemType Directory -Force -Path $destinationDir | Out-Null
    Copy-Item $_.FullName $destination -Force
}

Set-Location $ProjectRoot

Write-Host "Running complete test suite..." -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" -m pytest
if ($LASTEXITCODE -ne 0) {
    throw "Tests failed. Nothing will be committed or pushed."
}

git add .
$pending = git diff --cached --name-only

if (-not $pending) {
    Write-Host "Tests passed. No changes to commit." -ForegroundColor Green
    exit 0
}

Write-Host "Creating Git checkpoint..." -ForegroundColor Cyan
git commit -m $CommitMessage
if ($LASTEXITCODE -ne 0) {
    throw "Commit failed."
}

Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
git push
if ($LASTEXITCODE -ne 0) {
    throw "GitHub push failed."
}

Write-Host "FINAL BUNDLE INSTALLED AND PUSHED." -ForegroundColor Green
