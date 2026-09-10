[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/ParallelVerification.Common.ps1"

function Assert-VerificationTest([bool]$Condition, [string]$Message) {
  if (-not $Condition) { throw "Parallel verification workflow test failed: $Message" }
}

function Set-TestJson([object]$Value, [string]$Path, [switch]$ReadOnly) {
  if (Test-Path -LiteralPath $Path) { [IO.File]::SetAttributes($Path, [IO.FileAttributes]::Normal) }
  $json = $Value | ConvertTo-Json -Depth 30
  [IO.File]::WriteAllText($Path, $json, [Text.UTF8Encoding]::new($false))
  if ($ReadOnly) { [IO.File]::SetAttributes($Path, [IO.FileAttributes]::ReadOnly) }
}

function New-TestCandidate([string]$Id, [string]$Title, [string]$LocalPath, [Nullable[long]]$Size, [string]$Hash) {
  return [pscustomobject][ordered]@{
    id=$Id; status='pending review'; source_url="https://www.cabq.gov/test/$Id"; direct_file_url=$null
    r2_url=$null; r2_key=$null; r2_etag=$null; r2_last_modified=$null; agency='City of Albuquerque'
    title=$Title; date='2026-09-10'; file_type=if ($LocalPath) { 'Text' } else { 'Web page' }
    size_bytes=$Size; checksum_sha256=$Hash; parent_url='https://www.cabq.gov/test'; referring_urls=@('https://www.cabq.gov/test')
    discovery_path=@('fixture'); discovery_method='parallel verification fixture'; crawl_depth=0; cited_predecessors=@(); cited_successors=@()
    provenance_status='verified official source'; proposed_canonical_page=$null; description=$null; description_word_count=0
    processing_notes=@('Fixture candidate.'); implementation_location=$null; implementation_locations=@(); cross_listing_approved=$false
    validation_status='pending'; exclusion_reason=$null; local_path=$LocalPath; discovered_at='2026-09-10T00:00:00Z'; updated_at='2026-09-10T00:00:00Z'
  }
}

$repositoryRoot = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE) { throw 'Unable to resolve repository root for workflow tests.' }
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ("abqinfo-parallel-verification-tests-" + [guid]::NewGuid().ToString('N'))
$inventoryPath = Join-Path $testRoot 'master-inventory.json'
$runRoot = Join-Path $testRoot 'runs'
$localRelative = 'files/fixture.txt'
$localPath = Join-Path $testRoot $localRelative
$tests = [Collections.Generic.List[string]]::new()

try {
  New-Item -ItemType Directory -Path (Split-Path -Parent $localPath) -Force | Out-Null
  [IO.File]::WriteAllText($localPath, 'fixture source file', [Text.UTF8Encoding]::new($false))
  $localHash = Get-ParallelVerificationFileHash -Path $localPath
  $localSize = (Get-Item -LiteralPath $localPath).Length
  $inventory = [pscustomobject][ordered]@{
    schema_version=1; generated_at='2026-09-10T00:00:00Z'; next_pending_id='src-0000000000000001'
    allowed_statuses=@('pending review','approved for addition','downloading','downloaded','parsed','description drafted','placement assigned','implemented','validated','excluded','duplicate','superseded','blocked','requires human review')
    counts=[pscustomobject]@{'pending review'=2}
    candidates=@(
      (New-TestCandidate -Id 'src-0000000000000001' -Title 'Fixture File' -LocalPath $localRelative -Size $localSize -Hash $localHash),
      (New-TestCandidate -Id 'src-0000000000000002' -Title 'Fixture Page' -LocalPath $null -Size $null -Hash $null)
    )
  }
  New-Item -ItemType Directory -Path $testRoot -Force | Out-Null
  Set-TestJson -Value $inventory -Path $inventoryPath

  $runId = 'fixture-parallel-run'
  $headCommit = (& git rev-parse HEAD).Trim()
  $createOutput = & "$PSScriptRoot/New-ParallelVerificationRun.ps1" -RunId $runId -WorkerIds @('codex','claude') -CandidateIds @('src-0000000000000002','src-0000000000000001') -InventoryPath $inventoryPath -RunRoot $runRoot -BaseCommit $headCommit | ConvertFrom-Json
  $manifestPath = [string]$createOutput.manifest_path
  $manifest = Read-ParallelVerificationJson -Path $manifestPath
  Assert-VerificationTest ($manifest.shards[0].candidates[0].candidate_id -eq 'src-0000000000000001') 'sorted round-robin sharding did not assign the first ID to the first worker.'
  Assert-VerificationTest ($manifest.shards[1].candidates[0].candidate_id -eq 'src-0000000000000002') 'sorted round-robin sharding did not assign the second ID to the second worker.'
  Assert-VerificationTest (((Get-Item -LiteralPath $manifestPath).Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0) 'manifest is not read-only.'
  $tests.Add('deterministic-sharding-and-immutable-manifest')

  $externalWorktreeRoot = Join-Path ([IO.Path]::GetTempPath()) ("abqinfo-verification-worktrees-" + [guid]::NewGuid().ToString('N'))
  $worktreePlan = & "$PSScriptRoot/Initialize-ParallelVerificationWorktrees.ps1" -ManifestPath $manifestPath -WorktreeRoot $externalWorktreeRoot -PlanOnly | ConvertFrom-Json
  Assert-VerificationTest ($worktreePlan.worktrees.Count -eq 2 -and @($worktreePlan.worktrees | Where-Object mode -ne 'detached read-only worker checkout').Count -eq 0) 'detached worktree plan was not created for each worker.'
  $tests.Add('separate-detached-worktree-plan')

  $incompleteRun = Test-ParallelVerificationRunData -ManifestPath $manifestPath -InventoryPath $inventoryPath -AllowIncomplete
  Assert-VerificationTest ($incompleteRun.passed -and $incompleteRun.result_files -eq 0) 'an incomplete run could not be inspected before workers finished.'
  $tests.Add('incomplete-run-inspection')

  & "$PSScriptRoot/Invoke-ParallelVerificationShard.ps1" -ManifestPath $manifestPath -WorkerId codex -InventoryPath $inventoryPath -RepoRoot $testRoot -SkipLinkCheck | Out-Null
  & "$PSScriptRoot/Invoke-ParallelVerificationShard.ps1" -ManifestPath $manifestPath -WorkerId claude -InventoryPath $inventoryPath -RepoRoot $testRoot -SkipLinkCheck | Out-Null
  $resultPaths = @(
    (Join-Path (Split-Path -Parent $manifestPath) 'results/codex.json'),
    (Join-Path (Split-Path -Parent $manifestPath) 'results/claude.json')
  )
  $duplicateWriteBlocked = $false
  try { & "$PSScriptRoot/Invoke-ParallelVerificationShard.ps1" -ManifestPath $manifestPath -WorkerId codex -InventoryPath $inventoryPath -RepoRoot $testRoot -SkipLinkCheck | Out-Null } catch { $duplicateWriteBlocked = $true }
  Assert-VerificationTest $duplicateWriteBlocked 'a worker was able to overwrite an existing result artifact.'
  $tests.Add('unique-create-once-worker-results')

  $baseline = Test-ParallelVerificationRunData -ManifestPath $manifestPath -InventoryPath $inventoryPath -ResultPaths $resultPaths
  Assert-VerificationTest $baseline.passed 'baseline result artifacts did not validate.'

  $originalResult = [IO.File]::ReadAllText($resultPaths[0])
  $tampered = $originalResult | ConvertFrom-Json
  $tampered.worker_id = 'claude'
  Set-TestJson -Value $tampered -Path $resultPaths[0] -ReadOnly
  $tamperReport = Test-ParallelVerificationRunData -ManifestPath $manifestPath -InventoryPath $inventoryPath -ResultPaths $resultPaths
  Assert-VerificationTest (-not $tamperReport.passed -and (@($tamperReport.errors | Where-Object { $_ -match 'SHA-256 mismatch' }).Count -gt 0)) 'tampered result was not rejected.'
  [IO.File]::SetAttributes($resultPaths[0], [IO.FileAttributes]::Normal)
  [IO.File]::WriteAllText($resultPaths[0], $originalResult, [Text.UTF8Encoding]::new($false))
  [IO.File]::SetAttributes($resultPaths[0], [IO.FileAttributes]::ReadOnly)
  $tests.Add('result-tamper-detection')

  $originalInventory = [IO.File]::ReadAllText($inventoryPath)
  $staleInventory = $originalInventory | ConvertFrom-Json
  $staleInventory.candidates[0].title = 'Changed after manifest creation'
  Set-TestJson -Value $staleInventory -Path $inventoryPath
  $staleReport = Test-ParallelVerificationRunData -ManifestPath $manifestPath -InventoryPath $inventoryPath -ResultPaths $resultPaths
  Assert-VerificationTest (-not $staleReport.passed -and (@($staleReport.errors | Where-Object { $_ -match 'Stale candidate input' }).Count -gt 0)) 'stale candidate input was not rejected.'
  [IO.File]::WriteAllText($inventoryPath, $originalInventory, [Text.UTF8Encoding]::new($false))
  $tests.Add('stale-input-detection')

  $originalManifest = [IO.File]::ReadAllText($manifestPath)
  $overlapManifest = $originalManifest | ConvertFrom-Json
  $overlapManifest.shards[1].candidates = @($overlapManifest.shards[1].candidates) + @($overlapManifest.shards[0].candidates[0])
  $overlapManifest.manifest_sha256 = Get-ParallelVerificationObjectHash -Value (Get-ParallelVerificationManifestPayload -Manifest $overlapManifest)
  Set-TestJson -Value $overlapManifest -Path $manifestPath -ReadOnly
  $overlapErrors = @(Test-ParallelVerificationManifestObject -Manifest $overlapManifest)
  Assert-VerificationTest (@($overlapErrors | Where-Object { $_ -match 'overlap' }).Count -gt 0) 'overlapping shard assignments were not rejected.'
  [IO.File]::SetAttributes($manifestPath, [IO.FileAttributes]::Normal)
  [IO.File]::WriteAllText($manifestPath, $originalManifest, [Text.UTF8Encoding]::new($false))
  [IO.File]::SetAttributes($manifestPath, [IO.FileAttributes]::ReadOnly)
  $tests.Add('shard-overlap-detection')

  foreach ($resultPath in $resultPaths) {
    $result = Read-ParallelVerificationJson -Path $resultPath
    $result.results[0].checks.link_reachability.status = 'passed'
    $result.results[0].checks.link_reachability.http_status = 200
    $result.results[0].checks.link_reachability.reason = 'Fixture link result.'
    $result.results[0].overall_status = 'passed'
    $result.results[0].proposed_updates = [pscustomobject][ordered]@{ validation_status='passed: fixture parallel verification'; processing_notes_append='Fixture worker verification accepted.' }
    $result.result_sha256 = Get-ParallelVerificationObjectHash -Value (Get-ParallelVerificationResultPayload -Result $result)
    Set-TestJson -Value $result -Path $resultPath -ReadOnly
  }
  $passing = Test-ParallelVerificationRunData -ManifestPath $manifestPath -InventoryPath $inventoryPath -ResultPaths $resultPaths
  Assert-VerificationTest $passing.passed 'passing fixture results did not validate.'

  $inventoryHashBeforeDryRun = Get-ParallelVerificationFileHash -Path $inventoryPath
  $dryRun = & "$PSScriptRoot/Merge-ParallelVerificationRun.ps1" -ManifestPath $manifestPath -InventoryPath $inventoryPath -ResultPaths $resultPaths -AcceptedCandidateIds @('src-0000000000000001','src-0000000000000002') -UpdateCandidateScript "$PSScriptRoot/Update-Candidate.ps1" -LeasePath (Join-Path $testRoot 'integration.lock') | ConvertFrom-Json
  Assert-VerificationTest ($dryRun.mode -eq 'dry-run') 'integrator did not default to dry-run.'
  Assert-VerificationTest ((Get-ParallelVerificationFileHash -Path $inventoryPath) -eq $inventoryHashBeforeDryRun) 'dry-run modified the inventory.'
  $tests.Add('single-writer-dry-run')

  $leasePath = Join-Path $testRoot 'integration.lock'
  [IO.File]::WriteAllText($leasePath, 'existing writer', [Text.UTF8Encoding]::new($false))
  $contentionBlocked = $false
  try { & "$PSScriptRoot/Merge-ParallelVerificationRun.ps1" -ManifestPath $manifestPath -InventoryPath $inventoryPath -ResultPaths $resultPaths -AcceptedCandidateIds @('src-0000000000000001') -Apply -UpdateCandidateScript "$PSScriptRoot/Update-Candidate.ps1" -LeasePath $leasePath | Out-Null } catch { $contentionBlocked = $true }
  Assert-VerificationTest ($contentionBlocked -and (Test-Path -LiteralPath $leasePath)) 'an existing writer lease was not preserved and rejected.'
  Remove-Item -LiteralPath $leasePath -Force
  $tests.Add('repository-wide-writer-contention')

  $apply = & "$PSScriptRoot/Merge-ParallelVerificationRun.ps1" -ManifestPath $manifestPath -InventoryPath $inventoryPath -ResultPaths $resultPaths -AcceptedCandidateIds @('src-0000000000000001','src-0000000000000002') -Apply -UpdateCandidateScript "$PSScriptRoot/Update-Candidate.ps1" -LeasePath $leasePath | ConvertFrom-Json
  $updated = Read-ParallelVerificationJson -Path $inventoryPath
  Assert-VerificationTest (@($updated.candidates | Where-Object validation_status -eq 'passed: fixture parallel verification').Count -eq 2) 'accepted updates were not applied through Update-Candidate.ps1.'
  Assert-VerificationTest (-not (Test-Path -LiteralPath $leasePath)) 'integration lease was not released.'
  Assert-VerificationTest (Test-Path -LiteralPath ([string]$apply.receipt_path)) 'immutable integration receipt was not created.'
  Assert-VerificationTest (((Get-Item -LiteralPath ([string]$apply.receipt_path)).Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0) 'integration receipt is not read-only.'
  $tests.Add('accepted-apply-through-update-candidate')

  [pscustomobject][ordered]@{ passed=$true; tests=@($tests); test_count=$tests.Count } | ConvertTo-Json -Depth 5
} finally {
  if (Test-Path -LiteralPath $testRoot) {
    Get-ChildItem -LiteralPath $testRoot -Recurse -Force -File | ForEach-Object { $_.Attributes = [IO.FileAttributes]::Normal }
    Remove-Item -LiteralPath $testRoot -Recurse -Force
  }
}
