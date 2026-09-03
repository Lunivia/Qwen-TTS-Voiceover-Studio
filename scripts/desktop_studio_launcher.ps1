Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$serviceScript = Join-Path $PSScriptRoot "start_studio.ps1"
$studioUrl = "http://127.0.0.1:7870"
$launcherLog = Join-Path $projectRoot "data\logs\desktop-launcher.log"

function Write-LauncherLog {
    param([string]$Message)
    try {
        $logDir = Split-Path -Parent $launcherLog
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        Add-Content -LiteralPath $launcherLog -Value ("{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message) -Encoding UTF8
    } catch {
        # Logging must never prevent the workbench from starting.
    }
}

function Show-LauncherError {
    param([string]$Message)
    Write-LauncherLog "ERROR $Message"
    try {
        Add-Type -AssemblyName PresentationFramework
        [System.Windows.MessageBox]::Show($Message, "Qwen3 TTS Voice Studio startup failed", "OK", "Error") | Out-Null
    } catch {
        # The desktop launcher is hidden; keep the failure available in the log.
    }
}

function Test-StudioPort {
    return [bool](Get-NetTCPConnection -LocalPort 7870 -State Listen -ErrorAction SilentlyContinue)
}

try {
    if (-not (Test-StudioPort)) {
        Write-LauncherLog "Starting service from $serviceScript"
        $serviceProcess = Start-Process powershell.exe `
            -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $serviceScript) `
            -WorkingDirectory $projectRoot `
            -WindowStyle Hidden `
            -PassThru

        $deadline = (Get-Date).AddSeconds(60)
        while (-not (Test-StudioPort) -and (Get-Date) -lt $deadline) {
            if ($serviceProcess.HasExited) {
                Write-LauncherLog "Service process exited early with code $($serviceProcess.ExitCode)"
                break
            }
            Start-Sleep -Milliseconds 500
        }
    }

    if (-not (Test-StudioPort)) {
        Show-LauncherError "Qwen3 TTS Voice Studio did not start within 60 seconds. Check data\logs\desktop-launcher.log."
        exit 1
    }

    Write-LauncherLog "Workbench is ready; opening $studioUrl"
    Start-Process -FilePath $studioUrl
} catch {
    Show-LauncherError ("Launcher error: {0}" -f $_.Exception.Message)
    exit 1
}
