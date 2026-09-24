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

Adds one historical planning section for editorial review.

## Review this change

**Area & Sector Plans → Citywide Growth Strategy**

* Added: Citywide Growth Strategy, including Planned Growth Strategy Part 1 and the Part 2 chapter series.

**Preview:** https://example.abqinfo.pages.dev/development-land-use/area-sector-plans/#citywide-growth-strategy
'@ | Set-Content -LiteralPath $validPath -Encoding utf8NoBOM
  & $validator -Path $validPath

  foreach ($case in @(
    @{ Name = 'literal-newline'; Text = (Get-Content $validPath -Raw) -replace '## Review this change', '## Review this change\\n' },
    @{ Name = 'malformed-prefix'; Text = (Get-Content $validPath -Raw) -replace 'historical planning section', '\\requires planning section' },
    @{ Name = 'missing-section'; Text = (Get-Content $validPath -Raw) -replace '(?m)^## Summary$', '## Overview' },
    @{ Name = 'production-url'; Text = (Get-Content $validPath -Raw) -replace 'https://example.abqinfo.pages.dev/', 'https://abqinfo.com/' },
    @{ Name = 'preview-home'; Text = (Get-Content $validPath -Raw) -replace 'https://example.abqinfo.pages.dev/development-land-use/area-sector-plans/#citywide-growth-strategy', 'https://example.abqinfo.pages.dev/' }
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
