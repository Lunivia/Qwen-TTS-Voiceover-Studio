Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv/Scripts/python.exe"
if (-not (Test-Path $python)) {
    throw "Virtual environment not found: $python"
}

$localBypass = "127.0.0.1,localhost,::1"
$env:NO_PROXY = if ($env:NO_PROXY) { "$localBypass,$env:NO_PROXY" } else { $localBypass }
$env:no_proxy = $env:NO_PROXY
$env:PYTHONUTF8 = "1"

if (-not (Get-Command sox -ErrorAction SilentlyContinue)) {
    $wingetPackages = Join-Path $env:LOCALAPPDATA "Microsoft/WinGet/Packages"
    $soxExe = Get-ChildItem $wingetPackages -Recurse -Filter "sox.exe" -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -like "*ChrisBagwell.SoX*" } |
        Select-Object -First 1
    if ($soxExe) {
        $env:Path = "$($soxExe.DirectoryName);$env:Path"
    }
}

# Share the same mutex as the two official standalone launchers. Keeping the
# studio open blocks those services from accidentally claiming the 8 GB GPU.
$gpuMutex = [System.Threading.Mutex]::new($false, "Local\QwenTTS-1.7B-GPU")
$hasMutex = $false
try {
    $hasMutex = $gpuMutex.WaitOne(0)
    if (-not $hasMutex) {
        throw "Another QwenTTS service is already running. Stop it with Ctrl+C before opening the studio."
    }
    Write-Host "Starting Qwen3 TTS Voice Studio" -ForegroundColor Cyan
    Write-Host "Open: http://127.0.0.1:7870" -ForegroundColor Green
    Write-Host "Stop: Ctrl+C"
    Push-Location $projectRoot
    try {
        & $python -m studio --host 127.0.0.1 --port 7870
        if ($LASTEXITCODE -ne 0) {
            throw "Voice Studio exited with code $LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}
finally {
    if ($hasMutex) {
        $gpuMutex.ReleaseMutex()
    }
    $gpuMutex.Dispose()
}
