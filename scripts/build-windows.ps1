param(
    [Parameter(Mandatory = $true)]
    [string]$ScAgentsCli,
    [switch]$ReplaceExisting
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$uvCommand = Get-Command uv -ErrorAction Stop
Push-Location $repoRoot
try {
    & $uvCommand.Source run --project $repoRoot --offline --no-sync python scripts/bundle.py precheck --cli $ScAgentsCli
    if ($LASTEXITCODE -ne 0) { throw 'Bundle pre-check failed.' }

    if ($ReplaceExisting) {
        & $uvCommand.Source run --project $repoRoot --offline --no-sync python scripts/bundle.py build --replace-existing
    }
    else {
        & $uvCommand.Source run --project $repoRoot --offline --no-sync python scripts/bundle.py build
    }
    if ($LASTEXITCODE -ne 0) { throw 'Windows bundle build failed.' }

    & $uvCommand.Source run --project $repoRoot --offline --no-sync python scripts/bundle.py postcheck --cli $ScAgentsCli
    if ($LASTEXITCODE -ne 0) { throw 'Bundle post-check failed.' }

    & $uvCommand.Source run --project $repoRoot --offline --no-sync python scripts/bundle.py local-test --cli $ScAgentsCli
    if ($LASTEXITCODE -ne 0) { throw 'Isolated AgentAI CLI install test failed.' }
}
finally {
    Pop-Location
}
