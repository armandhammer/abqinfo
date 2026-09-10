[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$ManifestPath,
  [Parameter(Mandatory)][string]$WorkerId,
  [string]$InventoryPath,
  [string]$RepoRoot = (Get-Location).Path,
  [string]$ProposalPath,
  [switch]$SkipLinkCheck,
  [int]$LinkTimeoutSeconds = 30
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/ParallelVerification.Common.ps1"

function Resolve-VerificationPath([string]$Path, [string]$Root) {
  if ([IO.Path]::IsPathRooted($Path)) { return [IO.Path]::GetFullPath($Path) }
  return [IO.Path]::GetFullPath((Join-Path $Root $Path))
}

function Test-VerificationLink([string]$Url, [int]$TimeoutSeconds) {
  if ([string]::IsNullOrWhiteSpace($Url)) {
    return [pscustomobject][ordered]@{ status='not_applicable'; url=$null; http_status=$null; reason='No authoritative URL is recorded.' }
  }
  $parsed = $null
  if (-not [Uri]::TryCreate($Url, [UriKind]::Absolute, [ref]$parsed) -or $parsed.Scheme -notin @('http','https')) {
    return [pscustomobject][ordered]@{ status='failed'; url=$Url; http_status=$null; reason='URL is not an absolute HTTP(S) URL.' }
  }
  try {
    try {
      $response = Invoke-WebRequest -Uri $Url -Method Head -MaximumRedirection 8 -TimeoutSec $TimeoutSeconds -UserAgent 'ABQInfo parallel verification/1.0'
    } catch {
      $response = Invoke-WebRequest -Uri $Url -Method Get -MaximumRedirection 8 -TimeoutSec $TimeoutSeconds -UserAgent 'ABQInfo parallel verification/1.0'
    }
    $statusCode = [int]$response.StatusCode
    $status = if ($statusCode -ge 200 -and $statusCode -lt 400) { 'passed' } else { 'failed' }
    return [pscustomobject][ordered]@{ status=$status; url=$Url; http_status=$statusCode; reason="HTTP $statusCode" }
  } catch {
    $statusCode = $null
    if ($_.Exception.Response -and $_.Exception.Response.StatusCode) { $statusCode = [int]$_.Exception.Response.StatusCode }
    return [pscustomobject][ordered]@{ status='failed'; url=$Url; http_status=$statusCode; reason=$_.Exception.Message }
  }
}

$manifestFullPath = [IO.Path]::GetFullPath($ManifestPath)
$manifest = Read-ParallelVerificationJson -Path $manifestFullPath
$manifestErrors = @(Test-ParallelVerificationManifestObject -Manifest $manifest)
if ($manifestErrors.Count) { throw "Manifest validation failed: $($manifestErrors -join '; ')" }
$WorkerId = $WorkerId.Trim().ToLowerInvariant()
$shard = @($manifest.shards | Where-Object worker_id -eq $WorkerId)
if ($shard.Count -ne 1) { throw "Expected exactly one shard for worker '$WorkerId'; found $($shard.Count)." }

$repoFullPath = [IO.Path]::GetFullPath($RepoRoot)
if (-not $InventoryPath) { $InventoryPath = [string]$manifest.inventory_path }
$inventoryFullPath = Resolve-VerificationPath -Path $InventoryPath -Root $repoFullPath
if ((Get-ParallelVerificationFileHash -Path $inventoryFullPath) -ne [string]$manifest.inventory_sha256) {
  throw 'Worker inventory does not match the manifest snapshot. Recreate the worktree at the manifest base commit.'
}
$inventory = Read-ParallelVerificationJson -Path $inventoryFullPath
$candidateMap = @{}
foreach ($candidate in @($inventory.candidates)) { $candidateMap[[string]$candidate.id] = $candidate }

$proposalMap = @{}
if ($ProposalPath) {
  $proposal = Read-ParallelVerificationJson -Path (Resolve-VerificationPath -Path $ProposalPath -Root $repoFullPath)
  if ([string]$proposal.run_id -ne [string]$manifest.run_id) { throw 'Proposal run_id does not match the manifest.' }
  if ([string]$proposal.worker_id -ne $WorkerId) { throw 'Proposal worker_id does not match the selected shard.' }
  foreach ($item in @($proposal.proposals)) {
    $id = [string]$item.candidate_id
    if ($proposalMap.ContainsKey($id)) { throw "Duplicate proposal candidate: $id" }
    $proposalMap[$id] = $item
  }
  $shardIds = @($shard[0].candidates | ForEach-Object { [string]$_.candidate_id })
  foreach ($id in @($proposalMap.Keys)) {
    if ($id -notin $shardIds) { throw "Proposal contains candidate outside worker shard: $id" }
  }
}

$resultItems = [Collections.Generic.List[object]]::new()
foreach ($entry in @($shard[0].candidates)) {
  $id = [string]$entry.candidate_id
  if (-not $candidateMap.ContainsKey($id)) { throw "Candidate is missing from worker inventory: $id" }
  $candidate = $candidateMap[$id]
  $fingerprint = Get-ParallelVerificationCandidateFingerprint -Candidate $candidate
  if ($fingerprint -ne [string]$entry.input_fingerprint_sha256) { throw "Stale candidate input: $id" }

  $localPath = [string]$candidate.local_path
  if ([string]::IsNullOrWhiteSpace($localPath)) {
    $fileCheck = [pscustomobject][ordered]@{ status='not_applicable'; path=$null; expected_size=$null; actual_size=$null; expected_sha256=$null; actual_sha256=$null; reason='No local file is recorded.' }
  } else {
    $localFullPath = Resolve-VerificationPath -Path $localPath -Root $repoFullPath
    if (-not (Test-Path -LiteralPath $localFullPath -PathType Leaf)) {
      $fileCheck = [pscustomobject][ordered]@{ status='failed'; path=$localPath; expected_size=$candidate.size_bytes; actual_size=$null; expected_sha256=$candidate.checksum_sha256; actual_sha256=$null; reason='Recorded local file is missing.' }
    } else {
      $actualSize = (Get-Item -LiteralPath $localFullPath).Length
      $actualHash = Get-ParallelVerificationFileHash -Path $localFullPath
      $hasExpectedSize = $null -ne $candidate.size_bytes -and [string]$candidate.size_bytes -ne ''
      $hasExpectedHash = -not [string]::IsNullOrWhiteSpace([string]$candidate.checksum_sha256)
      $matches = $hasExpectedSize -and $hasExpectedHash -and ([long]$candidate.size_bytes -eq $actualSize) -and ([string]$candidate.checksum_sha256).ToLowerInvariant() -eq $actualHash
      $fileCheck = [pscustomobject][ordered]@{
        status = if ($matches) { 'passed' } else { 'failed' }
        path = $localPath
        expected_size = $candidate.size_bytes
        actual_size = $actualSize
        expected_sha256 = $candidate.checksum_sha256
        actual_sha256 = $actualHash
        reason = if ($matches) { 'Local file size and SHA-256 match inventory.' } elseif (-not $hasExpectedSize -or -not $hasExpectedHash) { 'Inventory lacks expected file size or SHA-256.' } else { 'Local file size or SHA-256 does not match inventory.' }
      }
    }
  }

  $sourceUrl = if (-not [string]::IsNullOrWhiteSpace([string]$candidate.source_url)) { [string]$candidate.source_url } else { [string]$candidate.direct_file_url }
  $sourceUri = $null
  $sourceValid = [Uri]::TryCreate($sourceUrl, [UriKind]::Absolute, [ref]$sourceUri) -and $sourceUri.Scheme -in @('http','https') -and $sourceUri.Host -ne 'files.abqinfo.com'
  $provenanceRecorded = -not [string]::IsNullOrWhiteSpace([string]$candidate.provenance_status) -and [string]$candidate.provenance_status -notmatch '(?i)unknown|unresolved|pending'
  $sourceCheck = [pscustomobject][ordered]@{
    status = if ($sourceValid -and $provenanceRecorded) { 'passed' } else { 'failed' }
    url = if ($sourceUrl) { $sourceUrl } else { $null }
    provenance_status = $candidate.provenance_status
    reason = if (-not $sourceValid) { 'No valid non-R2 authoritative HTTP(S) source is recorded.' } elseif (-not $provenanceRecorded) { 'Provenance status is missing or unresolved.' } else { 'Authoritative source and resolved provenance are recorded.' }
  }

  $linkUrl = if (-not [string]::IsNullOrWhiteSpace([string]$candidate.direct_file_url) -and [string]$candidate.direct_file_url -notmatch '^https?://files\.abqinfo\.com/') { [string]$candidate.direct_file_url } else { $sourceUrl }
  $linkCheck = if ($SkipLinkCheck) {
    [pscustomobject][ordered]@{ status='skipped'; url=$linkUrl; http_status=$null; reason='Link check explicitly skipped.' }
  } else {
    Test-VerificationLink -Url $linkUrl -TimeoutSeconds $LinkTimeoutSeconds
  }
  $statuses = @($fileCheck.status, $sourceCheck.status, $linkCheck.status)
  $overallStatus = if ('failed' -in $statuses) { 'failed' } elseif ('skipped' -in $statuses) { 'incomplete' } else { 'passed' }

  $updates = [pscustomobject]@{}
  $reviewNotes = $null
  if ($proposalMap.ContainsKey($id)) {
    $proposalItem = $proposalMap[$id]
    if ($proposalItem.PSObject.Properties['proposed_updates'] -and $null -ne $proposalItem.proposed_updates) {
      foreach ($field in @($proposalItem.proposed_updates.PSObject.Properties | ForEach-Object { $_.Name })) {
        if ($field -notin @($manifest.update_field_allowlist)) { throw "Candidate $id proposes disallowed update field: $field" }
      }
      $updates = $proposalItem.proposed_updates
    }
    if ($proposalItem.PSObject.Properties['review_notes']) { $reviewNotes = [string]$proposalItem.review_notes }
  }
  $resultItems.Add([pscustomobject][ordered]@{
    candidate_id = $id
    input_fingerprint_sha256 = $fingerprint
    overall_status = $overallStatus
    checks = [pscustomobject][ordered]@{ file_integrity=$fileCheck; source_provenance=$sourceCheck; link_reachability=$linkCheck }
    proposed_updates = $updates
    review_notes = $reviewNotes
  })
}

$payload = [ordered]@{
  schema_version = 1
  run_id = [string]$manifest.run_id
  manifest_sha256 = [string]$manifest.manifest_sha256
  base_commit = [string]$manifest.base_commit
  inventory_sha256 = [string]$manifest.inventory_sha256
  worker_id = $WorkerId
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  results = @($resultItems)
}
$result = [ordered]@{}
foreach ($key in $payload.Keys) { $result[$key] = $payload[$key] }
$result.result_sha256 = Get-ParallelVerificationObjectHash -Value $payload
$outputPath = Join-Path (Split-Path -Parent $manifestFullPath) ([string]$shard[0].result_path)
Write-ParallelVerificationJsonCreateNew -Value $result -Path $outputPath -ReadOnly | Out-Null
[pscustomobject][ordered]@{ run_id=$manifest.run_id; worker_id=$WorkerId; result_path=$outputPath; candidates=$resultItems.Count; passed=@($resultItems | Where-Object overall_status -eq 'passed').Count; incomplete=@($resultItems | Where-Object overall_status -eq 'incomplete').Count; failed=@($resultItems | Where-Object overall_status -eq 'failed').Count } | ConvertTo-Json -Depth 4
