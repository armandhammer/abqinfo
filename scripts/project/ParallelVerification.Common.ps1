Set-StrictMode -Version Latest

function ConvertTo-ParallelVerificationJson {
  param([Parameter(Mandatory)]$Value)
  return ($Value | ConvertTo-Json -Depth 30 -Compress)
}

function Get-ParallelVerificationTextHash {
  param([Parameter(Mandatory)][string]$Text)
  $algorithm = [Security.Cryptography.SHA256]::Create()
  try {
    $bytes = [Text.Encoding]::UTF8.GetBytes($Text)
    return (-join ($algorithm.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') }))
  } finally {
    $algorithm.Dispose()
  }
}

function Get-ParallelVerificationObjectHash {
  param([Parameter(Mandatory)]$Value)
  return Get-ParallelVerificationTextHash -Text (ConvertTo-ParallelVerificationJson -Value $Value)
}

function Get-ParallelVerificationFileHash {
  param([Parameter(Mandatory)][string]$Path)
  return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-ParallelVerificationCandidateFingerprint {
  param([Parameter(Mandatory)]$Candidate)
  return Get-ParallelVerificationObjectHash -Value $Candidate
}

function Get-ParallelVerificationManifestPayload {
  param([Parameter(Mandatory)]$Manifest)
  return [ordered]@{
    schema_version = [int]$Manifest.schema_version
    run_id = [string]$Manifest.run_id
    created_at = [string]$Manifest.created_at
    base_commit = [string]$Manifest.base_commit
    inventory_path = [string]$Manifest.inventory_path
    inventory_sha256 = [string]$Manifest.inventory_sha256
    sharding = [string]$Manifest.sharding
    check_types = @($Manifest.check_types)
    update_field_allowlist = @($Manifest.update_field_allowlist)
    workers = @($Manifest.workers)
    shards = @($Manifest.shards)
  }
}

function Get-ParallelVerificationResultPayload {
  param([Parameter(Mandatory)]$Result)
  return [ordered]@{
    schema_version = [int]$Result.schema_version
    run_id = [string]$Result.run_id
    manifest_sha256 = [string]$Result.manifest_sha256
    base_commit = [string]$Result.base_commit
    inventory_sha256 = [string]$Result.inventory_sha256
    worker_id = [string]$Result.worker_id
    generated_at = [string]$Result.generated_at
    results = @($Result.results)
  }
}

function Write-ParallelVerificationJsonCreateNew {
  param(
    [Parameter(Mandatory)]$Value,
    [Parameter(Mandatory)][string]$Path,
    [switch]$ReadOnly
  )
  $fullPath = [IO.Path]::GetFullPath($Path)
  $parent = Split-Path -Parent $fullPath
  if (-not (Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
  }
  $json = $Value | ConvertTo-Json -Depth 30
  $bytes = [Text.UTF8Encoding]::new($false).GetBytes($json)
  $stream = [IO.File]::Open($fullPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
  try {
    $stream.Write($bytes, 0, $bytes.Length)
  } finally {
    $stream.Dispose()
  }
  if ($ReadOnly) {
    [IO.File]::SetAttributes($fullPath, [IO.FileAttributes]::ReadOnly)
  }
  return $fullPath
}

function Read-ParallelVerificationJson {
  param([Parameter(Mandatory)][string]$Path)
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "JSON file not found: $Path" }
  return Get-Content -Raw -Encoding UTF8 -LiteralPath $Path | ConvertFrom-Json -DateKind String
}

function Test-ParallelVerificationManifestObject {
  param([Parameter(Mandatory)]$Manifest)
  $errors = [Collections.Generic.List[string]]::new()
  if ([int]$Manifest.schema_version -ne 1) { $errors.Add('Manifest schema_version must be 1.') }
  if ([string]$Manifest.run_id -notmatch '^[a-z0-9][a-z0-9._-]{2,63}$') { $errors.Add('Manifest run_id is invalid.') }
  if ([string]$Manifest.sharding -ne 'sorted candidate IDs assigned round-robin') { $errors.Add('Manifest sharding algorithm is not recognized.') }
  $workers = @($Manifest.workers | ForEach-Object { [string]$_ })
  if (-not $workers.Count) { $errors.Add('Manifest must contain at least one worker.') }
  if (@($workers | Group-Object | Where-Object Count -gt 1).Count) { $errors.Add('Manifest workers are not unique.') }
  foreach ($worker in $workers) {
    if ($worker -notmatch '^[a-z0-9][a-z0-9._-]{1,31}$') { $errors.Add("Invalid worker ID: $worker") }
  }
  $shards = @($Manifest.shards)
  if ($shards.Count -ne $workers.Count) { $errors.Add('Manifest must contain exactly one shard per worker.') }
  $seenWorkers = @($shards | ForEach-Object { [string]$_.worker_id })
  if (@($seenWorkers | Group-Object | Where-Object Count -gt 1).Count) { $errors.Add('A worker has more than one shard.') }
  if (@($seenWorkers | Where-Object { $_ -notin $workers }).Count) { $errors.Add('A shard names an unknown worker.') }
  $candidateIds = @($shards | ForEach-Object { @($_.candidates) } | ForEach-Object { [string]$_.candidate_id })
  if (@($candidateIds | Group-Object | Where-Object Count -gt 1).Count) { $errors.Add('Candidate assignments overlap across shards.') }
  $sortedCandidateIds = @($candidateIds | Sort-Object)
  for ($index = 0; $workers.Count -gt 0 -and $index -lt $sortedCandidateIds.Count; $index++) {
    $candidateId = $sortedCandidateIds[$index]
    $assignedShard = @($shards | Where-Object { $candidateId -in @($_.candidates | ForEach-Object { [string]$_.candidate_id }) })
    if ($assignedShard.Count -eq 1) {
      $expectedWorker = $workers[$index % $workers.Count]
      if ([string]$assignedShard[0].worker_id -ne $expectedWorker) { $errors.Add("Candidate assignment is not deterministic round-robin: $candidateId") }
    }
  }
  $resultPaths = @($shards | ForEach-Object { [string]$_.result_path })
  if (@($resultPaths | Group-Object | Where-Object Count -gt 1).Count) { $errors.Add('Shard result paths are not unique.') }
  foreach ($shard in $shards) {
    $expected = "results/$([string]$shard.worker_id).json"
    if (([string]$shard.result_path).Replace('\','/') -ne $expected) { $errors.Add("Unexpected result path for worker $($shard.worker_id).") }
  }
  $expectedHash = Get-ParallelVerificationObjectHash -Value (Get-ParallelVerificationManifestPayload -Manifest $Manifest)
  if ([string]$Manifest.manifest_sha256 -ne $expectedHash) { $errors.Add('Manifest SHA-256 does not match its immutable payload.') }
  return @($errors)
}

function Test-ParallelVerificationRunData {
  param(
    [Parameter(Mandatory)][string]$ManifestPath,
    [string]$InventoryPath,
    [string[]]$ResultPaths,
    [switch]$AllowIncomplete
  )
  $errors = [Collections.Generic.List[string]]::new()
  $manifest = Read-ParallelVerificationJson -Path $ManifestPath
  foreach ($errorText in @(Test-ParallelVerificationManifestObject -Manifest $manifest)) { $errors.Add($errorText) }
  if (((Get-Item -LiteralPath $ManifestPath).Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0) { $errors.Add('Manifest file is not read-only.') }

  $manifestDirectory = Split-Path -Parent ([IO.Path]::GetFullPath($ManifestPath))
  if (-not $InventoryPath) { $InventoryPath = [string]$manifest.inventory_path }
  if (-not [IO.Path]::IsPathRooted($InventoryPath)) {
    $InventoryPath = [IO.Path]::GetFullPath((Join-Path (Get-Location).Path $InventoryPath))
  }
  if (-not (Test-Path -LiteralPath $InventoryPath -PathType Leaf)) {
    $errors.Add("Inventory file not found: $InventoryPath")
    return [pscustomobject][ordered]@{ passed=$false; run_id=[string]$manifest.run_id; manifest=$manifest; inventory_path=$InventoryPath; result_files=0; candidates=0; errors=@($errors); results=@() }
  }
  $inventory = Read-ParallelVerificationJson -Path $InventoryPath
  $inventoryMap = @{}
  foreach ($candidate in @($inventory.candidates)) { $inventoryMap[[string]$candidate.id] = $candidate }

  $manifestCandidates = @($manifest.shards | ForEach-Object { @($_.candidates) })
  foreach ($entry in $manifestCandidates) {
    $id = [string]$entry.candidate_id
    if (-not $inventoryMap.ContainsKey($id)) {
      $errors.Add("Manifest candidate is missing from current inventory: $id")
      continue
    }
    $currentFingerprint = Get-ParallelVerificationCandidateFingerprint -Candidate $inventoryMap[$id]
    if ($currentFingerprint -ne [string]$entry.input_fingerprint_sha256) {
      $errors.Add("Stale candidate input: $id")
    }
  }

  if (-not $ResultPaths) {
    $resultDirectory = Join-Path $manifestDirectory 'results'
    $ResultPaths = if (Test-Path -LiteralPath $resultDirectory) {
      @(Get-ChildItem -LiteralPath $resultDirectory -Filter '*.json' -File | Sort-Object Name | Select-Object -ExpandProperty FullName)
    } else { @() }
  }
  $loadedResults = [Collections.Generic.List[object]]::new()
  $seenResultWorkers = [Collections.Generic.List[string]]::new()
  $seenResultCandidates = [Collections.Generic.List[string]]::new()
  foreach ($resultPath in @($ResultPaths | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) })) {
    $result = Read-ParallelVerificationJson -Path $resultPath
    $workerId = [string]$result.worker_id
    if ([int]$result.schema_version -ne 1) { $errors.Add("Result schema_version must be 1: $resultPath") }
    if ($workerId -in $seenResultWorkers) { $errors.Add("Multiple result files found for worker: $workerId") }
    $seenResultWorkers.Add($workerId)
    if ([string]$result.run_id -ne [string]$manifest.run_id) { $errors.Add("Result run_id mismatch: $resultPath") }
    if ([string]$result.manifest_sha256 -ne [string]$manifest.manifest_sha256) { $errors.Add("Result manifest hash mismatch: $resultPath") }
    if ([string]$result.base_commit -ne [string]$manifest.base_commit) { $errors.Add("Result base commit mismatch: $resultPath") }
    if ([string]$result.inventory_sha256 -ne [string]$manifest.inventory_sha256) { $errors.Add("Result inventory hash mismatch: $resultPath") }
    $expectedResultHash = Get-ParallelVerificationObjectHash -Value (Get-ParallelVerificationResultPayload -Result $result)
    if ([string]$result.result_sha256 -ne $expectedResultHash) { $errors.Add("Result SHA-256 mismatch: $resultPath") }
    if (((Get-Item -LiteralPath $resultPath).Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0) { $errors.Add("Result file is not read-only: $resultPath") }
    $shard = @($manifest.shards | Where-Object worker_id -eq $workerId)
    if ($shard.Count -ne 1) {
      $errors.Add("Result names unknown worker: $workerId")
    } else {
      $expectedPath = [IO.Path]::GetFullPath((Join-Path $manifestDirectory ([string]$shard[0].result_path)))
      if ([IO.Path]::GetFullPath($resultPath) -ne $expectedPath) { $errors.Add("Result file is not at its manifest-assigned path for worker: $workerId") }
      $expectedIds = @($shard[0].candidates | ForEach-Object { [string]$_.candidate_id } | Sort-Object)
      $actualIds = @($result.results | ForEach-Object { [string]$_.candidate_id } | Sort-Object)
      if (($expectedIds -join "`n") -ne ($actualIds -join "`n")) { $errors.Add("Result candidate set does not match shard for worker: $workerId") }
    }
    foreach ($candidateResult in @($result.results)) {
      $id = [string]$candidateResult.candidate_id
      if ($id -in $seenResultCandidates) { $errors.Add("Candidate appears in multiple result files: $id") }
      $seenResultCandidates.Add($id)
      $manifestEntry = @($manifestCandidates | Where-Object candidate_id -eq $id)
      if ($manifestEntry.Count -eq 1 -and [string]$candidateResult.input_fingerprint_sha256 -ne [string]$manifestEntry[0].input_fingerprint_sha256) {
        $errors.Add("Result input fingerprint does not match manifest: $id")
      }
      $checkStatuses = [Collections.Generic.List[string]]::new()
      foreach ($checkType in @($manifest.check_types)) {
        if (-not $candidateResult.PSObject.Properties['checks'] -or -not $candidateResult.checks.PSObject.Properties[[string]$checkType]) {
          $errors.Add("Candidate $id is missing check result: $checkType")
          continue
        }
        $checkObject = $candidateResult.checks.PSObject.Properties[[string]$checkType].Value
        $checkStatus = if ($checkObject.PSObject.Properties['status']) { [string]$checkObject.status } else { '' }
        if ($checkStatus -notin @('passed','failed','skipped','not_applicable')) { $errors.Add("Candidate $id has invalid $checkType status: $checkStatus") }
        $checkStatuses.Add($checkStatus)
      }
      $derivedOverall = if ('failed' -in $checkStatuses) { 'failed' } elseif ('skipped' -in $checkStatuses) { 'incomplete' } else { 'passed' }
      if ([string]$candidateResult.overall_status -ne $derivedOverall) { $errors.Add("Candidate $id overall_status does not match its checks.") }
      if (-not $candidateResult.PSObject.Properties['proposed_updates'] -or $null -eq $candidateResult.proposed_updates) {
        $errors.Add("Candidate $id is missing proposed_updates.")
        $proposedFields = @()
      } else {
        $proposedFields = @($candidateResult.proposed_updates.PSObject.Properties | ForEach-Object { $_.Name })
      }
      foreach ($field in $proposedFields) {
        if ($field -notin @($manifest.update_field_allowlist)) { $errors.Add("Candidate $id proposes disallowed update field: $field") }
      }
    }
    $loadedResults.Add([pscustomobject]@{ path=[IO.Path]::GetFullPath($resultPath); data=$result })
  }

  $expectedWorkers = @($manifest.workers | ForEach-Object { [string]$_ })
  if (-not $AllowIncomplete) {
    foreach ($worker in $expectedWorkers) {
      if ($worker -notin $seenResultWorkers) { $errors.Add("Missing result file for worker: $worker") }
    }
  }
  return [pscustomobject][ordered]@{
    passed = ($errors.Count -eq 0)
    run_id = [string]$manifest.run_id
    manifest = $manifest
    inventory_path = $InventoryPath
    result_files = $loadedResults.Count
    candidates = $seenResultCandidates.Count
    errors = @($errors)
    results = @($loadedResults)
  }
}
