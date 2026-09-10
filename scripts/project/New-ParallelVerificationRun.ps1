[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$RunId,
  [string[]]$WorkerIds = @('codex','claude'),
  [string[]]$CandidateIds,
  [string]$StartId,
  [int]$Count = 0,
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$RunRoot,
  [string]$BaseCommit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/ParallelVerification.Common.ps1"

if ($RunId -notmatch '^[a-z0-9][a-z0-9._-]{2,63}$') { throw 'RunId must be 3-64 lowercase letters, digits, dots, underscores, or hyphens.' }
$WorkerIds = @($WorkerIds | ForEach-Object { $_.Trim().ToLowerInvariant() })
if (-not $WorkerIds.Count -or @($WorkerIds | Group-Object | Where-Object Count -gt 1).Count) { throw 'WorkerIds must be non-empty and unique.' }
foreach ($worker in $WorkerIds) {
  if ($worker -notmatch '^[a-z0-9][a-z0-9._-]{1,31}$') { throw "Invalid worker ID: $worker" }
}
$inventoryFullPath = [IO.Path]::GetFullPath($InventoryPath)
$repositoryRoot = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE) { throw 'Unable to resolve the repository root.' }
$repositoryRoot = [IO.Path]::GetFullPath($repositoryRoot).TrimEnd('\','/')
if (-not $RunRoot) { $RunRoot = Join-Path (Split-Path -Parent ([IO.Path]::GetFullPath($repositoryRoot))) 'ABQinfo-verification-runs' }
$inventory = Read-ParallelVerificationJson -Path $inventoryFullPath
if ($CandidateIds -and ($StartId -or $Count)) { throw 'Use CandidateIds or StartId/Count, not both.' }
if (-not $CandidateIds) {
  if (-not $StartId -or $Count -lt 1) { throw 'Specify CandidateIds, or specify StartId with a positive Count.' }
  $CandidateIds = @($inventory.candidates | Where-Object { [string]$_.id -ge $StartId -and $_.status -eq 'pending review' } | Sort-Object id | Select-Object -First $Count -ExpandProperty id)
}
$CandidateIds = @($CandidateIds | ForEach-Object { [string]$_ } | Sort-Object -Unique)
if (-not $CandidateIds.Count) { throw 'The run contains no candidates.' }
$candidateMap = @{}
foreach ($candidate in @($inventory.candidates)) { $candidateMap[[string]$candidate.id] = $candidate }
foreach ($id in $CandidateIds) {
  if (-not $candidateMap.ContainsKey($id)) { throw "Candidate not found in inventory: $id" }
}
if (-not $BaseCommit) { $BaseCommit = 'HEAD' }
$BaseCommit = (& git rev-parse "$BaseCommit^{commit}").Trim()
if ($LASTEXITCODE) { throw 'Unable to resolve the manifest base commit.' }
$inventoryInsideRepository = $inventoryFullPath -eq $repositoryRoot -or $inventoryFullPath.StartsWith("$repositoryRoot\", [StringComparison]::OrdinalIgnoreCase)
if ($inventoryInsideRepository) {
  $inventoryRelativePath = [IO.Path]::GetRelativePath($repositoryRoot, $inventoryFullPath).Replace('\','/')
  & git ls-files --error-unmatch -- $inventoryRelativePath | Out-Null
  if ($LASTEXITCODE) { throw 'A repository-local inventory must be tracked by Git.' }
  & git diff --quiet $BaseCommit -- $inventoryRelativePath
  if ($LASTEXITCODE -eq 1) { throw 'Inventory content does not match the selected manifest base commit.' }
  if ($LASTEXITCODE -ne 0) { throw 'Unable to compare inventory content with the selected manifest base commit.' }
}
$manifestInventoryPath = if ($inventoryInsideRepository) { $inventoryRelativePath } else { $inventoryFullPath.Replace('\','/') }
$assignments = @{}
foreach ($worker in $WorkerIds) { $assignments[$worker] = [Collections.Generic.List[object]]::new() }
for ($index = 0; $index -lt $CandidateIds.Count; $index++) {
  $worker = $WorkerIds[$index % $WorkerIds.Count]
  $candidate = $candidateMap[$CandidateIds[$index]]
  $assignments[$worker].Add([pscustomobject][ordered]@{
    candidate_id = [string]$candidate.id
    input_fingerprint_sha256 = Get-ParallelVerificationCandidateFingerprint -Candidate $candidate
  })
}
$shards = foreach ($worker in $WorkerIds) {
  [pscustomobject][ordered]@{
    worker_id = $worker
    result_path = "results/$worker.json"
    candidates = @($assignments[$worker])
  }
}
$createdAt = (Get-Date).ToUniversalTime().ToString('o')
$payload = [ordered]@{
  schema_version = 1
  run_id = $RunId
  created_at = $createdAt
  base_commit = $BaseCommit
  inventory_path = $manifestInventoryPath
  inventory_sha256 = Get-ParallelVerificationFileHash -Path $inventoryFullPath
  sharding = 'sorted candidate IDs assigned round-robin'
  check_types = @('file_integrity','source_provenance','link_reachability')
  update_field_allowlist = @('status','title','date','description','proposed_canonical_page','exclusion_reason','validation_status','provenance_status','processing_notes_append')
  workers = $WorkerIds
  shards = @($shards)
}
$manifest = [ordered]@{}
foreach ($key in $payload.Keys) { $manifest[$key] = $payload[$key] }
$manifest.manifest_sha256 = Get-ParallelVerificationObjectHash -Value $payload
$manifestPath = Join-Path ([IO.Path]::GetFullPath($RunRoot)) "$RunId/manifest.json"
Write-ParallelVerificationJsonCreateNew -Value $manifest -Path $manifestPath -ReadOnly | Out-Null
[pscustomobject][ordered]@{
  run_id = $RunId
  manifest_path = $manifestPath
  manifest_sha256 = $manifest.manifest_sha256
  base_commit = $BaseCommit
  candidates = $CandidateIds.Count
  shards = @($shards | ForEach-Object { [pscustomobject]@{ worker_id=$_.worker_id; candidates=@($_.candidates).Count; result_path=$_.result_path } })
} | ConvertTo-Json -Depth 6
