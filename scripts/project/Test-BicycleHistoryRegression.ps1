[CmdletBinding()]
param(
  [string]$BenchmarkPath = 'project-state/discovery/bicycle-history-benchmarks.json',
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OutputPath = 'project-state/discovery/bicycle-history-regression-report.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$benchmarks = Get-Content -Raw -LiteralPath $BenchmarkPath | ConvertFrom-Json
$inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json
$excluded = @{}
$exclusionsPath = 'project-state/discovery/import-exclusions.json'
if (Test-Path -LiteralPath $exclusionsPath) {
  foreach ($item in (Get-Content -Raw -LiteralPath $exclusionsPath | ConvertFrom-Json)) { $excluded[[string]$item.file] = $true }
}

$crawlCandidates = @()
foreach ($file in Get-ChildItem -LiteralPath 'project-state/discovery' -Filter '*-crawl.json' -File) {
  if ($excluded.ContainsKey($file.Name)) { continue }
  $state = Get-Content -Raw -LiteralPath $file.FullName | ConvertFrom-Json
  foreach ($candidate in @($state.candidates)) {
    $crawlCandidates += [pscustomobject]@{
      state_file = $file.Name
      url = [string]$candidate.url
      discovery_method = [string]$candidate.discovery_method
      discovery_path = @($candidate.discovery_path)
      crawl_depth = $candidate.discovery_depth
    }
  }
}

$results = @(foreach ($benchmark in $benchmarks) {
  $record = @($inventory.candidates | Where-Object id -eq $benchmark.inventory_id | Select-Object -First 1)
  $pattern = [string]$benchmark.authoritative_url_pattern
  $blindMatches = if ($pattern) { @($crawlCandidates | Where-Object { $_.url -match $pattern -and $_.discovery_method -notmatch '(?i)exact.title|web search' }) } else { @() }
  $inventoryRecord = $record | Select-Object -First 1
  $blindCount = ($blindMatches | Measure-Object).Count
  [ordered]@{
    id = $benchmark.id
    title = $benchmark.title
    inventory_id = $benchmark.inventory_id
    blind_graph_recovered = ($blindCount -gt 0)
    blind_matches = @($blindMatches)
    authoritative_source_url = if ($inventoryRecord) { $inventoryRecord.source_url } else { $null }
    authoritative_direct_file_url = if ($inventoryRecord) { $inventoryRecord.direct_file_url } else { $null }
    provenance_status = if ($inventoryRecord) { $inventoryRecord.provenance_status } else { 'inventory record missing' }
    inventory_status = if ($inventoryRecord) { $inventoryRecord.status } else { 'missing' }
    regression_pass = ($blindCount -gt 0)
  }
})

$eligibleStates = @(Get-ChildItem -LiteralPath 'project-state/discovery' -Filter '*-crawl.json' -File | Where-Object { -not $excluded.ContainsKey($_.Name) })
$output = [ordered]@{
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  rule = 'A benchmark passes only when an eligible crawl state recovers its authoritative file without an exact-title or general web-search discovery method.'
  eligible_crawl_states = @($eligibleStates.Name)
  passed = (@($results | Where-Object regression_pass)).Count
  total = $results.Count
  benchmarks = @($results)
}
$output | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $OutputPath -Encoding utf8
$output | ConvertTo-Json -Depth 5 -Compress
