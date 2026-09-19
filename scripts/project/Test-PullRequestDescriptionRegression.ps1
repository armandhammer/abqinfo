[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$validator = Join-Path $PSScriptRoot 'Test-PullRequestDescription.ps1'
$tempRoot = Join-Path ([IO.Path]::GetTempPath()) ('abqinfo-pr-body-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null

try {
  $validPath = Join-Path $tempRoot 'valid.md'
  @'
## Summary

Records a research-only decision.

## What changed

* Added the durable decision artifact.

## Archive / inventory / provenance

No R2 change; source evidence remains preserved.

## Visible site changes

None.

No `content/` pages or public archive objects changed.

## Validation

* Focused regression passed.

## Deferred / not included

Archive and publication remain gated.
'@ | Set-Content -LiteralPath $validPath -Encoding utf8NoBOM
  & $validator -Path $validPath

  foreach ($case in @(
    @{ Name = 'literal-newline'; Text = (Get-Content $validPath -Raw) -replace "## What changed", "## What changed\\n" },
    @{ Name = 'malformed-prefix'; Text = (Get-Content $validPath -Raw) -replace 'Records a research-only decision\.', 'Records a \\requires review decision.' },
    @{ Name = 'missing-section'; Text = (Get-Content $validPath -Raw) -replace '(?ms)## Deferred / not included.*$', '' }
  )) {
    $path = Join-Path $tempRoot ($case.Name + '.md')
    Set-Content -LiteralPath $path -Value $case.Text -Encoding utf8NoBOM
    $failedAsExpected = $false
    try { & $validator -Path $path } catch { $failedAsExpected = $true }
    if (-not $failedAsExpected) { throw "Regression case did not fail: $($case.Name)" }
  }
} finally {
  Remove-Item -LiteralPath $tempRoot -Recurse -Force
}

Write-Output 'Pull-request description regression passed.'
