[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$current = & "$PSScriptRoot/Get-ProjectRecencyBucket.ps1" -ProjectYear 2021 -ReferenceYear 2026 | ConvertFrom-Json
$past = & "$PSScriptRoot/Get-ProjectRecencyBucket.ps1" -ProjectYear 2020 -ReferenceYear 2026 | ConvertFrom-Json
if ($current.bucket -ne 'Current Projects') { throw 'Expected 2021 to be current for reference year 2026.' }
if ($past.bucket -ne 'Past Projects') { throw 'Expected 2020 to be past for reference year 2026.' }
[pscustomobject]@{ reference_year=2026; current_start_year=2021; passed=$true } | ConvertTo-Json -Compress
