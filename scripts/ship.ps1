param([Parameter(Mandatory=$true)][string]$Message)
$ErrorActionPreference='Stop'
if(-not(Test-Path '.\.venv\Scripts\python.exe')){throw 'Run from ResearchIntelligence project root.'}
& '.\.venv\Scripts\python.exe' -m pytest
if($LASTEXITCODE -ne 0){throw 'Tests failed. Nothing will be committed or pushed.'}
git add .
$pending=git diff --cached --name-only
if(-not $pending){Write-Host 'Tests passed. No changes to commit.' -ForegroundColor Green; exit 0}
git commit -m $Message
if($LASTEXITCODE -ne 0){throw 'Commit failed.'}
git push
if($LASTEXITCODE -ne 0){throw 'Push failed.'}
Write-Host 'Checkpoint complete.' -ForegroundColor Green
