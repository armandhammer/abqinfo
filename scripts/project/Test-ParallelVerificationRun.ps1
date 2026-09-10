[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$ManifestPath,
  [string]$InventoryPath,
  [string[]]$ResultPaths,
  [switch]$AllowIncomplete
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/ParallelVerification.Common.ps1"

$parameters = @{ ManifestPath = $ManifestPath; AllowIncomplete = $AllowIncomplete }
if ($InventoryPath) { $parameters.InventoryPath = $InventoryPath }
if ($ResultPaths) { $parameters.ResultPaths = $ResultPaths }
$report = Test-ParallelVerificationRunData @parameters
$report | Select-Object passed,run_id,inventory_path,result_files,candidates,errors | ConvertTo-Json -Depth 8
if (-not $report.passed) { throw "Parallel verification run failed validation with $(@($report.errors).Count) error(s)." }
