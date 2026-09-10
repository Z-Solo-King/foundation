param(
    [string]$ProjectRoot = (Get-Location).Path,
    [string]$CommitMessage = "Add research intelligence core batch v2"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path (Join-Path $ProjectRoot ".git"))) {
    throw "Run this installer while your current directory is the ResearchIntelligence repository."
}

if (-not (Test-Path (Join-Path $ProjectRoot ".venv\Scripts\python.exe"))) {
    throw "ResearchIntelligence .venv not found."
}

$payload = Join-Path $PSScriptRoot "payload"

Get-ChildItem $payload -Recurse -File | ForEach-Object {
    $relative = $_.FullName.Substring($payload.Length).TrimStart('\')
    $destination = Join-Path $ProjectRoot $relative
    New-Item -ItemType Directory -Force -Path (Split-Path $destination -Parent) | Out-Null
    Copy-Item $_.FullName $destination -Force
}

Set-Location $ProjectRoot

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

git commit -m $CommitMessage
if ($LASTEXITCODE -ne 0) { throw "Commit failed." }

git push
if ($LASTEXITCODE -ne 0) { throw "Push failed." }

Write-Host "Batch installation complete." -ForegroundColor Green
