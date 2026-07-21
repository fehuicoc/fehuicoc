# Pack 3 — local /health controlled_target probe (simulate + live + negative)
# Writes evidence under Factory_v3/runs/exercise-routine-002-change/layer2/integration_contracts/evidence/

[CmdletBinding()]
param(
    [string]$RepoRoot = '',
    [string]$RunId = 'exercise-routine-002-change',
    [int]$Port = 8765,
    [int]$NegativePort = 18765
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $RepoRoot) {
    $here = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
    $RepoRoot = (Resolve-Path (Join-Path $here '..\..\..')).Path
}

$workspace = Join-Path $RepoRoot 'generated-solutions\exercise-routine'
$evidenceDir = Join-Path $RepoRoot "Factory_v3\runs\$RunId\layer2\integration_contracts\evidence"
$mockPath = Join-Path $RepoRoot "Factory_v3\runs\$RunId\layer2\integration_contracts\mocks\er-health-response.json"
New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null

function Write-JsonFile([string]$Path, $Object) {
    $json = $Object | ConvertTo-Json -Depth 6
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $json, $utf8)
}

# --- Simulate ---
$mock = Get-Content -LiteralPath $mockPath -Raw | ConvertFrom-Json
if ($mock.status -ne 'ok' -or $mock.service -ne 'exercise-routine') {
    throw "SIMULATE_FAIL: mock shape mismatch at $mockPath"
}
Write-Host "SIMULATE_PASS mock=$mockPath"

# --- Start uvicorn ---
$python = (Get-Command python -ErrorAction Stop).Source
$uvicornArgs = @('-m', 'uvicorn', 'exercise_routine.app:app', '--app-dir', 'src', '--host', '127.0.0.1', '--port', "$Port")
$stdoutLog = Join-Path $evidenceDir 'uvicorn-stdout.log'
$stderrLog = Join-Path $evidenceDir 'uvicorn-stderr.log'
$proc = Start-Process -FilePath $python -ArgumentList $uvicornArgs -WorkingDirectory $workspace -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog

$session = [ordered]@{
    pid = $proc.Id
    port = $Port
    started_at = (Get-Date).ToUniversalTime().ToString('o')
    command = "$python $($uvicornArgs -join ' ')"
}
Write-JsonFile (Join-Path $evidenceDir 'uvicorn-session.json') $session

try {
    $ready = $false
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Milliseconds 500
        try {
            $probe = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/health" -UseBasicParsing -TimeoutSec 2
            if ($probe.StatusCode -eq 200) { $ready = $true; break }
        } catch { }
    }
    if (-not $ready) { throw "LIVE_START_FAIL: uvicorn did not become ready on port $Port" }

    $pos = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/health" -UseBasicParsing -TimeoutSec 5
    $posBody = $pos.Content
    $posEvidence = [ordered]@{
        outcome = 'pass'
        at = (Get-Date).ToUniversalTime().ToString('o')
        error = $null
        body = $posBody
        status_code = [int]$pos.StatusCode
        url = "http://127.0.0.1:$Port/health"
        probe = 'pkg3_health_parity_probe.ps1'
    }
    Write-JsonFile (Join-Path $evidenceDir 'live-health-positive.json') $posEvidence
    Write-Host "LIVE_PASS status=$($pos.StatusCode) body=$posBody"

    $negOutcome = 'pass_unreachable'
    $negError = $null
    $negStatus = $null
    $negBody = $null
    try {
        $neg = Invoke-WebRequest -Uri "http://127.0.0.1:$NegativePort/health" -UseBasicParsing -TimeoutSec 2
        $negOutcome = 'fail_unexpected_reachable'
        $negStatus = [int]$neg.StatusCode
        $negBody = $neg.Content
        throw "NEGATIVE_FAIL: port $NegativePort unexpectedly responded"
    } catch {
        if ($negOutcome -eq 'fail_unexpected_reachable') { throw }
        $negError = $_.Exception.Message
        Write-Host "NEGATIVE_PASS_UNREACHABLE port=$NegativePort err=$negError"
    }
    $negEvidence = [ordered]@{
        outcome = $negOutcome
        at = (Get-Date).ToUniversalTime().ToString('o')
        error = $negError
        body = $negBody
        status_code = $negStatus
        url = "http://127.0.0.1:$NegativePort/health"
        probe = 'pkg3_health_parity_probe.ps1'
    }
    Write-JsonFile (Join-Path $evidenceDir 'live-health-negative-wrong-port.json') $negEvidence

    $env:ER_REQUIRE_LIVE_HEALTH = '1'
    $env:ER_HEALTH_MOCK_PATH = $mockPath
    Push-Location $workspace
    try {
        & python -m pytest tests/test_health.py tests/test_health_env_parity.py -q --tb=line
        $pytestExit = $LASTEXITCODE
    } finally {
        Pop-Location
        Remove-Item Env:ER_REQUIRE_LIVE_HEALTH -ErrorAction SilentlyContinue
    }
    if ($pytestExit -ne 0) { throw "PYTEST_FAIL exit=$pytestExit" }
    Write-Host "PYTEST_PASS exit=0"
}
finally {
    if ($proc -and -not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        Write-Host "STOPPED uvicorn pid=$($proc.Id)"
    }
}

Write-Host 'PKG3_PROBE_COMPLETE'
