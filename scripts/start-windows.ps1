$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$BackendPid = Join-Path $Root ".backend.pid"
$FrontendPid = Join-Path $Root ".frontend.pid"

foreach ($tool in "uv", "npm") {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        Write-Host "$tool is required but not installed"
        exit 1
    }
}

$envFile = Join-Path $Root ".env"
if (-not ((Test-Path $envFile) -and (Select-String -Path $envFile -Pattern '^[A-Z_]+_API_KEY=.+' -Quiet))) {
    Write-Host "No API key found. Run: copy .env.example .env  then add your key to .env"
    exit 1
}

if (-not (Test-Path (Join-Path $Root "frontend\node_modules"))) {
    Push-Location (Join-Path $Root "frontend"); npm install; Pop-Location
}

function Start-App($name, $pidFile, $workDir, $command, $url) {
    if ((Test-Path $pidFile) -and (Get-Process -Id (Get-Content $pidFile) -ErrorAction SilentlyContinue)) {
        Write-Host "$name already running (pid $(Get-Content $pidFile))"
        return
    }
    $log = Join-Path $Root ".$($name.ToLower()).log"
    $p = Start-Process -FilePath "cmd.exe" -ArgumentList "/c $command > `"$log`" 2>&1" `
        -WorkingDirectory $workDir -WindowStyle Hidden -PassThru
    $p.Id | Set-Content $pidFile
    Write-Host "$name started (pid $($p.Id)) - $url"
}

Start-App "Backend" $BackendPid (Join-Path $Root "backend") "uv run uvicorn app.main:app --port 8000" "http://localhost:8000"
Start-App "Frontend" $FrontendPid (Join-Path $Root "frontend") "npm run dev" "http://localhost:5173"
