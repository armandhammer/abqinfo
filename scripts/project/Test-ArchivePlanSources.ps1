[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$PlanPath,
  [Parameter(Mandatory)][string]$OutputPath,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'
$plan = Get-Content -Raw -Encoding UTF8 -LiteralPath $PlanPath | ConvertFrom-Json
$results = foreach ($item in @($plan.items)) {
  try {
    & "$PSScriptRoot/Test-Candidate.ps1" -Id $item.id -InventoryPath $InventoryPath | ConvertFrom-Json
  } catch {
    [pscustomobject]@{
      id = [string]$item.id
      title = [string]$item.title
      url = [string]$item.direct_file_url
      http_status = $null
      error = $_.Exception.Message
    }
  }
}
$passed = @($results | Where-Object { $_.http_status -ge 200 -and $_.http_status -lt 400 }).Count
$failed = $results.Count - $passed
[ordered]@{
  schema_version = 1
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  plan_path = $PlanPath
  total = $results.Count
  passed = $passed
  failed = $failed
  results = $results
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{Total=$results.Count;Passed=$passed;Failed=$failed;OutputPath=$OutputPath} | ConvertTo-Json -Compress
if ($failed) { exit 1 }
