[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$ManifestPath,
  [string]$InventoryPath,
  [string[]]$ResultPaths,
  [Parameter(Mandatory)][string[]]$AcceptedCandidateIds,
  [switch]$Apply,
  [string]$UpdateCandidateScript = (Join-Path $PSScriptRoot 'Update-Candidate.ps1'),
  [string]$LeasePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/ParallelVerification.Common.ps1"

$manifestFullPath = [IO.Path]::GetFullPath($ManifestPath)
$manifest = Read-ParallelVerificationJson -Path $manifestFullPath
$acceptedInput = @($AcceptedCandidateIds | ForEach-Object { [string]$_ })
if (@($acceptedInput | Group-Object | Where-Object Count -gt 1).Count) { throw 'AcceptedCandidateIds contains duplicates.' }
$AcceptedCandidateIds = @($acceptedInput | Sort-Object)
if (-not $AcceptedCandidateIds.Count) { throw 'Specify at least one accepted candidate ID.' }
if (-not $InventoryPath) { $InventoryPath = [string]$manifest.inventory_path }
$inventoryFullPath = if ([IO.Path]::IsPathRooted($InventoryPath)) { [IO.Path]::GetFullPath($InventoryPath) } else { [IO.Path]::GetFullPath((Join-Path (Get-Location).Path $InventoryPath)) }

if (-not $LeasePath) {
  $gitCommon = (& git rev-parse --git-common-dir).Trim()
  if ($LASTEXITCODE) { throw 'Unable to resolve the shared Git directory for the integration lease.' }
  if (-not [IO.Path]::IsPathRooted($gitCommon)) { $gitCommon = [IO.Path]::GetFullPath((Join-Path (Get-Location).Path $gitCommon)) }
  $LeasePath = Join-Path (Join-Path $gitCommon 'abqinfo-verification-locks') 'inventory-writer.lock'
}
$leaseFullPath = [IO.Path]::GetFullPath($LeasePath)
$leaseStream = $null
$leaseAcquired = $false

try {
  if ($Apply) {
    & git symbolic-ref --quiet HEAD | Out-Null
    if ($LASTEXITCODE) { throw 'Apply mode must run from the coordinator branch, not a detached worker worktree.' }
    $leaseParent = Split-Path -Parent $leaseFullPath
    if (-not (Test-Path -LiteralPath $leaseParent)) { New-Item -ItemType Directory -Path $leaseParent -Force | Out-Null }
    try {
      $leaseStream = [IO.File]::Open($leaseFullPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
      $leaseBytes = [Text.UTF8Encoding]::new($false).GetBytes("run=$($manifest.run_id)`npid=$PID`nstarted=$((Get-Date).ToUniversalTime().ToString('o'))`n")
      $leaseStream.Write($leaseBytes, 0, $leaseBytes.Length)
      $leaseStream.Flush()
      $leaseAcquired = $true
    } catch {
      throw "Another integrator holds the run lease or a stale lease needs review: $leaseFullPath"
    }
  }

  $validationParameters = @{ ManifestPath=$manifestFullPath; InventoryPath=$inventoryFullPath }
  if ($ResultPaths) { $validationParameters.ResultPaths = $ResultPaths }
  $report = Test-ParallelVerificationRunData @validationParameters
  if (-not $report.passed) { throw "Run validation failed: $($report.errors -join '; ')" }

  $resultByCandidate = @{}
  foreach ($resultFile in @($report.results)) {
    foreach ($item in @($resultFile.data.results)) { $resultByCandidate[[string]$item.candidate_id] = $item }
  }
  foreach ($id in $AcceptedCandidateIds) {
    if (-not $resultByCandidate.ContainsKey($id)) { throw "Accepted candidate has no validated result: $id" }
    if ([string]$resultByCandidate[$id].overall_status -ne 'passed') { throw "Accepted candidate did not pass all worker checks: $id" }
  }

  $inventory = Read-ParallelVerificationJson -Path $inventoryFullPath
  $inventoryMap = @{}
  foreach ($candidate in @($inventory.candidates)) { $inventoryMap[[string]$candidate.id] = $candidate }
  $operations = [Collections.Generic.List[object]]::new()
  foreach ($id in $AcceptedCandidateIds) {
    $candidate = $inventoryMap[$id]
    $item = $resultByCandidate[$id]
    $set = @{}
    foreach ($property in @($item.proposed_updates.PSObject.Properties)) {
      if ($property.Name -eq 'processing_notes_append') { continue }
      $set[$property.Name] = $property.Value
    }
    if (-not $set.ContainsKey('validation_status')) { $set.validation_status = "passed: parallel verification run $($manifest.run_id)" }
    $notes = [Collections.Generic.List[string]]::new()
    foreach ($existingNote in @($candidate.processing_notes)) {
      if (-not [string]::IsNullOrWhiteSpace([string]$existingNote)) { $notes.Add(([string]$existingNote).Trim()) }
    }
    if ($item.proposed_updates.PSObject.Properties['processing_notes_append'] -and -not [string]::IsNullOrWhiteSpace([string]$item.proposed_updates.processing_notes_append)) {
      foreach ($proposedNote in @($item.proposed_updates.processing_notes_append)) {
        $append = ([string]$proposedNote).Trim()
        if ($append -and $append -notin $notes) { $notes.Add($append) }
      }
    }
    $integrationNote = "Accepted from immutable parallel verification run $($manifest.run_id) (manifest $($manifest.manifest_sha256))."
    if ($integrationNote -notin $notes) { $notes.Add($integrationNote) }
    $set.processing_notes = @($notes)
    $operations.Add([pscustomobject][ordered]@{
      candidate_id = $id
      before_fingerprint_sha256 = Get-ParallelVerificationCandidateFingerprint -Candidate $candidate
      set = [pscustomobject]$set
    })
  }

  if ($Apply) {
    foreach ($operation in $operations) {
      $setHashtable = @{}
      foreach ($property in @($operation.set.PSObject.Properties)) { $setHashtable[$property.Name] = $property.Value }
      & $UpdateCandidateScript -Id $operation.candidate_id -Set $setHashtable -InventoryPath $inventoryFullPath | Out-Null
      if ($LASTEXITCODE) { throw "Update-Candidate.ps1 failed for $($operation.candidate_id)." }
    }
    $updatedInventory = Read-ParallelVerificationJson -Path $inventoryFullPath
    $updatedMap = @{}
    foreach ($candidate in @($updatedInventory.candidates)) { $updatedMap[[string]$candidate.id] = $candidate }
    foreach ($operation in $operations) {
      Add-Member -InputObject $operation -NotePropertyName after_fingerprint_sha256 -NotePropertyValue (Get-ParallelVerificationCandidateFingerprint -Candidate $updatedMap[$operation.candidate_id])
    }
  }

  $receiptPayload = [ordered]@{
    schema_version = 1
    run_id = [string]$manifest.run_id
    manifest_sha256 = [string]$manifest.manifest_sha256
    mode = if ($Apply) { 'applied' } else { 'dry-run' }
    integrated_at = (Get-Date).ToUniversalTime().ToString('o')
    inventory_path = $inventoryFullPath
    accepted_candidate_ids = $AcceptedCandidateIds
    operations = @($operations)
  }
  $receipt = [ordered]@{}
  foreach ($key in $receiptPayload.Keys) { $receipt[$key] = $receiptPayload[$key] }
  $receipt.receipt_sha256 = Get-ParallelVerificationObjectHash -Value $receiptPayload
  $receiptPath = $null
  if ($Apply) {
    $receiptName = "$((Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ'))-$([guid]::NewGuid().ToString('N')).json"
    $receiptPath = Join-Path (Join-Path (Split-Path -Parent $manifestFullPath) 'integration') $receiptName
    Write-ParallelVerificationJsonCreateNew -Value $receipt -Path $receiptPath -ReadOnly | Out-Null
  }
  [pscustomobject][ordered]@{ run_id=$manifest.run_id; mode=$receipt.mode; candidates=$AcceptedCandidateIds.Count; receipt_path=$receiptPath; operations=@($operations) } | ConvertTo-Json -Depth 12
} finally {
  if ($leaseStream) { $leaseStream.Dispose() }
  if ($leaseAcquired -and (Test-Path -LiteralPath $leaseFullPath)) { Remove-Item -LiteralPath $leaseFullPath -Force }
}
