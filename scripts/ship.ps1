param(
    [Parameter(Mandatory=$true)]
    [string]$Message
)

Write-Host "Running tests..." -ForegroundColor Cyan
python -m pytest

if ($LASTEXITCODE -ne 0) {
    Write-Host "Tests failed. Nothing was committed or pushed." -ForegroundColor Red
    exit 1
}

Write-Host "Tests passed. Staging changes..." -ForegroundColor Green
git add .

Write-Host "Creating commit..." -ForegroundColor Cyan
git commit -m $Message

if ($LASTEXITCODE -ne 0) {
    Write-Host "Commit failed." -ForegroundColor Red
    exit 1
}

Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
git push

if ($LASTEXITCODE -ne 0) {
    Write-Host "Push failed." -ForegroundColor Red
    exit 1
}

Write-Host "Done." -ForegroundColor Green
