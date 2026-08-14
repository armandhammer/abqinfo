[CmdletBinding()]
param(
  [Parameter(Mandatory)][int]$ProjectYear,
  [int]$ReferenceYear = (Get-Date).Year
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($ProjectYear -lt 1800 -or $ProjectYear -gt ($ReferenceYear + 20)) {
  throw "Project year '$ProjectYear' is outside the supported range."
}

$currentStartYear = $ReferenceYear - 5
[pscustomobject]@{
  project_year = $ProjectYear
  reference_year = $ReferenceYear
  current_start_year = $currentStartYear
  bucket = if ($ProjectYear -ge $currentStartYear) { 'Current Projects' } else { 'Past Projects' }
} | ConvertTo-Json -Compress
