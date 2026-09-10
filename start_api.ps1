$ErrorActionPreference = 'Stop'
$projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw "Project Python not found: $projectPython"
}
Push-Location $PSScriptRoot
try {
    & $projectPython -m uvicorn api.api_main:app --host 127.0.0.1 --port 8000 @args
    $resultCode = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $resultCode
