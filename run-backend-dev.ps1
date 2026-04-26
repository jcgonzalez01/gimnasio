# GymSystem Pro - Backend Dev Server (Self-contained Python)
# Downloads embeddable Python if not present, then starts FastAPI.

$ErrorActionPreference = "Stop"
$root    = Split-Path -Parent $MyInvocation.MyCommand.Path
$pyDir   = Join-Path $root "backend\.python"
$pyExe   = Join-Path $pyDir "python.exe"
$backDir = Join-Path $root "backend"

# ── 1. Download embeddable Python if missing ──────────────────────────────────
if (-not (Test-Path $pyExe)) {
    Write-Host ">>> Descargando Python 3.12 embeddable (sin instalacion)..." -ForegroundColor Cyan
    $zipUrl  = "https://www.python.org/ftp/python/3.12.7/python-3.12.7-embed-amd64.zip"
    $zipPath = Join-Path $root "backend\_python_embed.zip"

    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
    Expand-Archive -Path $zipPath -DestinationPath $pyDir -Force
    Remove-Item $zipPath

    # Habilitar site-packages (descomentar "import site" en el ._pth)
    $pthFile = Get-ChildItem $pyDir -Filter "*._pth" | Select-Object -First 1
    if ($pthFile) {
        (Get-Content $pthFile.FullName) -replace "#import site", "import site" |
            Set-Content $pthFile.FullName
    }

    Write-Host ">>> Instalando pip..." -ForegroundColor Cyan
    $getPip = Join-Path $pyDir "get-pip.py"
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPip -UseBasicParsing
    & $pyExe $getPip --no-warn-script-location --quiet
    Remove-Item $getPip
}

# ── 2. Install requirements if not already installed ─────────────────────────
$uvicorn = Join-Path $pyDir "Scripts\uvicorn.exe"
if (-not (Test-Path $uvicorn)) {
    Write-Host ">>> Instalando dependencias Python..." -ForegroundColor Cyan
    & $pyExe -m pip install -r (Join-Path $backDir "requirements.txt") `
        --no-warn-script-location --quiet
}

# ── 3. Start FastAPI ──────────────────────────────────────────────────────────
Write-Host ""
Write-Host ">>> Iniciando FastAPI en http://localhost:8001" -ForegroundColor Green
Write-Host ">>> API Docs: http://localhost:8001/api/docs" -ForegroundColor Green
Write-Host ""
Set-Location $backDir
& $pyExe -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
