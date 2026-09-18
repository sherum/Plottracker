$Root = Split-Path -Parent $PSScriptRoot

function Stop-App($name, $pidFile, $port) {
    if (Test-Path $pidFile) {
        $procId = Get-Content $pidFile
        taskkill /PID $procId /T /F 2>$null | Out-Null
        Remove-Item $pidFile -Force
        Write-Host "$name stopped (pid $procId)"
        return
    }
    $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($conn) {
        taskkill /PID $conn.OwningProcess /T /F 2>$null | Out-Null
        Write-Host "$name stopped (pid $($conn.OwningProcess))"
    } else {
        Write-Host "$name not running"
    }
}

Stop-App "Backend" (Join-Path $Root ".backend.pid") 8000
Stop-App "Frontend" (Join-Path $Root ".frontend.pid") 5173
