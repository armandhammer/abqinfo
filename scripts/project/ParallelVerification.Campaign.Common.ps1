Set-StrictMode -Version Latest
. "$PSScriptRoot/ParallelVerification.Common.ps1"

function Get-ParallelVerificationCampaignPayload {
  param([Parameter(Mandatory)]$Campaign)
  [ordered]@{
    schema_version = [int]$Campaign.schema_version
    campaign_id = [string]$Campaign.campaign_id
    created_at = [string]$Campaign.created_at
    base_commit = [string]$Campaign.base_commit
    inventory_path = [string]$Campaign.inventory_path
    inventory_sha256 = [string]$Campaign.inventory_sha256
    start_id = [string]$Campaign.start_id
    candidate_count = [int]$Campaign.candidate_count
    microbatch_size = [int]$Campaign.microbatch_size
    sharding = [string]$Campaign.sharding
    check_types = @($Campaign.check_types)
    update_field_allowlist = @($Campaign.update_field_allowlist)
    lanes = @($Campaign.lanes)
    batches = @($Campaign.batches)
  }
}

function Get-ParallelVerificationCandidateResultPayload {
  param([Parameter(Mandatory)]$Result)
  [ordered]@{
    schema_version = [int]$Result.schema_version
    campaign_id = [string]$Result.campaign_id
    campaign_sha256 = [string]$Result.campaign_sha256
    base_commit = [string]$Result.base_commit
    inventory_sha256 = [string]$Result.inventory_sha256
    lane_id = [string]$Result.lane_id
    batch_id = [string]$Result.batch_id
    batch_ordinal = [int]$Result.batch_ordinal
    candidate_ordinal = [int]$Result.candidate_ordinal
    candidate_id = [string]$Result.candidate_id
    input_fingerprint_sha256 = [string]$Result.input_fingerprint_sha256
    worker_provider = [string]$Result.worker_provider
    generated_at = [string]$Result.generated_at
    overall_status = [string]$Result.overall_status
    checks = $Result.checks
    proposed_updates = $Result.proposed_updates
    review_notes = $Result.review_notes
  }
}

function Get-ParallelVerificationIntegrationIntentPayload {
  param([Parameter(Mandatory)]$Intent)
  [ordered]@{
    schema_version = [int]$Intent.schema_version
    campaign_id = [string]$Intent.campaign_id
    campaign_sha256 = [string]$Intent.campaign_sha256
    candidate_id = [string]$Intent.candidate_id
    result_sha256 = [string]$Intent.result_sha256
    operation_id = [string]$Intent.operation_id
    created_at = [string]$Intent.created_at
    before_fingerprint_sha256 = [string]$Intent.before_fingerprint_sha256
    set = $Intent.set
  }
}

function Get-ParallelVerificationIntegrationReceiptPayload {
  param([Parameter(Mandatory)]$Receipt)
  [ordered]@{
    schema_version = [int]$Receipt.schema_version
    campaign_id = [string]$Receipt.campaign_id
    campaign_sha256 = [string]$Receipt.campaign_sha256
    candidate_id = [string]$Receipt.candidate_id
    result_sha256 = [string]$Receipt.result_sha256
    operation_id = [string]$Receipt.operation_id
    completed_at = [string]$Receipt.completed_at
    before_fingerprint_sha256 = [string]$Receipt.before_fingerprint_sha256
    after_fingerprint_sha256 = [string]$Receipt.after_fingerprint_sha256
    recovery = [bool]$Receipt.recovery
  }
}

function Get-ParallelVerificationCampaignEntries {
  param([Parameter(Mandatory)]$Campaign)
  @($Campaign.batches | Sort-Object ordinal | ForEach-Object {
    $batch = $_
    @($batch.candidates | Sort-Object ordinal | ForEach-Object {
      [pscustomobject][ordered]@{
        lane_id = [string]$batch.lane_id
        batch_id = [string]$batch.batch_id
        batch_ordinal = [int]$batch.ordinal
        candidate_ordinal = [int]$_.ordinal
        candidate_id = [string]$_.candidate_id
        input_fingerprint_sha256 = [string]$_.input_fingerprint_sha256
        result_path = [string]$_.result_path
      }
    })
  })
}

function Test-ParallelVerificationCampaignObject {
  param([Parameter(Mandatory)]$Campaign)
  $errors = [Collections.Generic.List[string]]::new()
  if ([int]$Campaign.schema_version -ne 1) { $errors.Add('Campaign schema_version must be 1.') }
  if ([string]$Campaign.campaign_id -notmatch '^[a-z0-9][a-z0-9._-]{2,63}$') { $errors.Add('Campaign ID is invalid.') }
  if ([int]$Campaign.candidate_count -lt 1) { $errors.Add('Campaign must contain candidates.') }
  if ([int]$Campaign.microbatch_size -lt 1) { $errors.Add('Campaign microbatch_size must be positive.') }
  if ([string]$Campaign.sharding -ne 'sorted candidate IDs chunked into microbatches and batches assigned round-robin to lanes') { $errors.Add('Campaign sharding algorithm is not recognized.') }
  $lanes = @($Campaign.lanes | ForEach-Object { [string]$_ })
  if (-not $lanes.Count) { $errors.Add('Campaign must contain lanes.') }
  if (@($lanes | Group-Object | Where-Object Count -gt 1).Count) { $errors.Add('Campaign lanes are not unique.') }
  foreach ($lane in $lanes) { if ($lane -notmatch '^[a-z0-9][a-z0-9._-]{1,31}$') { $errors.Add("Invalid lane ID: $lane") } }
  $batches = @($Campaign.batches | Sort-Object ordinal)
  $entries = @(Get-ParallelVerificationCampaignEntries -Campaign $Campaign)
  if ($entries.Count -ne [int]$Campaign.candidate_count) { $errors.Add('Campaign candidate_count does not match its entries.') }
  if (@($entries.candidate_id | Group-Object | Where-Object Count -gt 1).Count) { $errors.Add('Candidate assignments overlap across campaign batches.') }
  if (@($entries.result_path | Group-Object | Where-Object Count -gt 1).Count) { $errors.Add('Candidate result paths are not unique.') }
  if (@($batches.batch_id | Group-Object | Where-Object Count -gt 1).Count) { $errors.Add('Campaign batch IDs are not unique.') }
  $sortedIds = @($entries.candidate_id | Sort-Object)
  for ($batchIndex = 0; $batchIndex -lt $batches.Count; $batchIndex++) {
    $batch = $batches[$batchIndex]
    $expectedOrdinal = $batchIndex + 1
    $expectedBatchId = 'batch-{0:d4}' -f $expectedOrdinal
    if ([int]$batch.ordinal -ne $expectedOrdinal -or [string]$batch.batch_id -ne $expectedBatchId) { $errors.Add("Non-deterministic batch identity at ordinal $expectedOrdinal.") }
    if ($lanes.Count -gt 0 -and [string]$batch.lane_id -ne $lanes[$batchIndex % $lanes.Count]) { $errors.Add("Non-deterministic lane assignment for $expectedBatchId.") }
    $start = $batchIndex * [int]$Campaign.microbatch_size
    $length = [Math]::Min([int]$Campaign.microbatch_size, [Math]::Max(0, $sortedIds.Count - $start))
    $expectedIds = if ($length -gt 0) { @($sortedIds[$start..($start + $length - 1)]) } else { @() }
    $actual = @($batch.candidates | Sort-Object ordinal | ForEach-Object { [string]$_.candidate_id })
    if (($expectedIds -join "`n") -ne ($actual -join "`n")) { $errors.Add("Batch $expectedBatchId does not contain its deterministic candidate slice.") }
    for ($candidateIndex = 0; $candidateIndex -lt @($batch.candidates).Count; $candidateIndex++) {
      $candidate = @($batch.candidates | Sort-Object ordinal)[$candidateIndex]
      if ([int]$candidate.ordinal -ne ($candidateIndex + 1)) { $errors.Add("Candidate ordinal is invalid in $expectedBatchId.") }
      $expectedPath = "results/$([string]$batch.lane_id)/$expectedBatchId/$([string]$candidate.candidate_id).json"
      if (([string]$candidate.result_path).Replace('\','/') -ne $expectedPath) { $errors.Add("Unexpected result path for candidate $($candidate.candidate_id).") }
    }
  }
  $expectedBatchCount = [int][Math]::Ceiling([double][int]$Campaign.candidate_count / [int]$Campaign.microbatch_size)
  if ($batches.Count -ne $expectedBatchCount) { $errors.Add('Campaign batch count is inconsistent with candidate_count and microbatch_size.') }
  $expectedHash = Get-ParallelVerificationObjectHash -Value (Get-ParallelVerificationCampaignPayload -Campaign $Campaign)
  if ([string]$Campaign.campaign_sha256 -ne $expectedHash) { $errors.Add('Campaign SHA-256 does not match its immutable payload.') }
  @($errors)
}

function Resolve-ParallelVerificationCampaignManifest {
  param([string]$ManifestPath, [string]$ActiveRunPath = 'project-state/active-run.json')
  if ($ManifestPath) { return [IO.Path]::GetFullPath($ManifestPath) }
  $pointer = Read-ParallelVerificationJson -Path ([IO.Path]::GetFullPath($ActiveRunPath))
  if ([string]$pointer.type -ne 'parallel-verification-campaign') { throw 'The active-run pointer is not a parallel verification campaign.' }
  $resolved = [IO.Path]::GetFullPath([string]$pointer.manifest_path)
  $campaign = Read-ParallelVerificationJson -Path $resolved
  if ([string]$pointer.campaign_id -ne [string]$campaign.campaign_id -or [string]$pointer.campaign_sha256 -ne [string]$campaign.campaign_sha256) { throw 'The active-run pointer does not match its campaign manifest.' }
  $resolved
}

function Test-ParallelVerificationCandidateResultObject {
  param([Parameter(Mandatory)]$Result, [Parameter(Mandatory)]$Campaign, [Parameter(Mandatory)]$Entry, [Parameter(Mandatory)][string]$ResultPath, [Parameter(Mandatory)][string]$ManifestDirectory)
  $errors = [Collections.Generic.List[string]]::new()
  if ([int]$Result.schema_version -ne 1) { $errors.Add('Candidate result schema_version must be 1.') }
  if ([string]$Result.campaign_id -ne [string]$Campaign.campaign_id -or [string]$Result.campaign_sha256 -ne [string]$Campaign.campaign_sha256) { $errors.Add('Candidate result campaign binding is invalid.') }
  foreach ($field in @('base_commit','inventory_sha256','lane_id','batch_id','candidate_id','input_fingerprint_sha256')) {
    $expected = switch ($field) { 'base_commit' { $Campaign.base_commit } 'inventory_sha256' { $Campaign.inventory_sha256 } default { $Entry.$field } }
    if ([string]$Result.$field -ne [string]$expected) { $errors.Add("Candidate result $field does not match its assignment.") }
  }
  if ([int]$Result.batch_ordinal -ne [int]$Entry.batch_ordinal -or [int]$Result.candidate_ordinal -ne [int]$Entry.candidate_ordinal) { $errors.Add('Candidate result ordinals do not match its assignment.') }
  $expectedPath = [IO.Path]::GetFullPath((Join-Path $ManifestDirectory ([string]$Entry.result_path)))
  if ([IO.Path]::GetFullPath($ResultPath) -ne $expectedPath) { $errors.Add('Candidate result is not at its manifest-assigned path.') }
  if (((Get-Item -LiteralPath $ResultPath).Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0) { $errors.Add('Candidate result is not read-only.') }
  $expectedHash = Get-ParallelVerificationObjectHash -Value (Get-ParallelVerificationCandidateResultPayload -Result $Result)
  if ([string]$Result.result_sha256 -ne $expectedHash) { $errors.Add('Candidate result SHA-256 is invalid.') }
  $statuses = [Collections.Generic.List[string]]::new()
  foreach ($checkType in @($Campaign.check_types)) {
    if (-not $Result.PSObject.Properties['checks'] -or -not $Result.checks.PSObject.Properties[[string]$checkType]) { $errors.Add("Candidate result is missing check: $checkType"); continue }
    $status = [string]$Result.checks.PSObject.Properties[[string]$checkType].Value.status
    if ($status -notin @('passed','failed','skipped','not_applicable')) { $errors.Add("Candidate result has invalid $checkType status: $status") }
    $statuses.Add($status)
  }
  $overall = if ('failed' -in $statuses) { 'failed' } elseif ('skipped' -in $statuses) { 'incomplete' } else { 'passed' }
  if ([string]$Result.overall_status -ne $overall) { $errors.Add('Candidate result overall_status does not match its checks.') }
  $fields = if ($Result.PSObject.Properties['proposed_updates'] -and $null -ne $Result.proposed_updates) { @($Result.proposed_updates.PSObject.Properties | ForEach-Object Name) } else { $errors.Add('Candidate result is missing proposed_updates.'); @() }
  foreach ($field in $fields) { if ($field -notin @($Campaign.update_field_allowlist)) { $errors.Add("Candidate result proposes disallowed field: $field") } }
  @($errors)
}

function Test-ParallelVerificationIntegrationIntentObject {
  param([Parameter(Mandatory)]$Intent,[Parameter(Mandatory)]$Campaign,[Parameter(Mandatory)]$Entry,[Parameter(Mandatory)]$Result,[Parameter(Mandatory)][string]$Path)
  $errors=[Collections.Generic.List[string]]::new()
  if([int]$Intent.schema_version-ne1){$errors.Add('Integration intent schema_version must be 1.')}
  if([string]$Intent.campaign_id-ne[string]$Campaign.campaign_id -or [string]$Intent.campaign_sha256-ne[string]$Campaign.campaign_sha256){$errors.Add('Integration intent campaign binding is invalid.')}
  if([string]$Intent.candidate_id-ne[string]$Entry.candidate_id -or [string]$Intent.result_sha256-ne[string]$Result.result_sha256){$errors.Add('Integration intent candidate/result binding is invalid.')}
  if([string]$Intent.before_fingerprint_sha256-ne[string]$Entry.input_fingerprint_sha256){$errors.Add('Integration intent input fingerprint is invalid.')}
  if(((Get-Item -LiteralPath $Path).Attributes -band [IO.FileAttributes]::ReadOnly)-eq0){$errors.Add('Integration intent is not read-only.')}
  if([string]$Intent.intent_sha256-ne(Get-ParallelVerificationObjectHash (Get-ParallelVerificationIntegrationIntentPayload $Intent))){$errors.Add('Integration intent SHA-256 is invalid.')}
  @($errors)
}

function Test-ParallelVerificationIntegrationReceiptObject {
  param([Parameter(Mandatory)]$Receipt,[Parameter(Mandatory)]$Campaign,[Parameter(Mandatory)]$Entry,[Parameter(Mandatory)]$Result,[Parameter(Mandatory)]$Intent,[Parameter(Mandatory)][string]$Path)
  $errors=[Collections.Generic.List[string]]::new()
  if([int]$Receipt.schema_version-ne1){$errors.Add('Integration receipt schema_version must be 1.')}
  if([string]$Receipt.campaign_id-ne[string]$Campaign.campaign_id -or [string]$Receipt.campaign_sha256-ne[string]$Campaign.campaign_sha256){$errors.Add('Integration receipt campaign binding is invalid.')}
  if([string]$Receipt.candidate_id-ne[string]$Entry.candidate_id -or [string]$Receipt.result_sha256-ne[string]$Result.result_sha256 -or [string]$Receipt.operation_id-ne[string]$Intent.operation_id){$errors.Add('Integration receipt operation binding is invalid.')}
  if([string]$Receipt.before_fingerprint_sha256-ne[string]$Entry.input_fingerprint_sha256 -or [string]::IsNullOrWhiteSpace([string]$Receipt.after_fingerprint_sha256)){$errors.Add('Integration receipt fingerprints are invalid.')}
  if(((Get-Item -LiteralPath $Path).Attributes -band [IO.FileAttributes]::ReadOnly)-eq0){$errors.Add('Integration receipt is not read-only.')}
  if([string]$Receipt.receipt_sha256-ne(Get-ParallelVerificationObjectHash (Get-ParallelVerificationIntegrationReceiptPayload $Receipt))){$errors.Add('Integration receipt SHA-256 is invalid.')}
  @($errors)
}

function Resolve-ParallelVerificationWorkerPath([string]$Path, [string]$Root) {
  if ([IO.Path]::IsPathRooted($Path)) { return [IO.Path]::GetFullPath($Path) }
  [IO.Path]::GetFullPath((Join-Path $Root $Path))
}

function Test-ParallelVerificationWorkerLink([string]$Url, [int]$TimeoutSeconds) {
  if ([string]::IsNullOrWhiteSpace($Url)) { return [pscustomobject][ordered]@{ status='not_applicable'; url=$null; http_status=$null; reason='No authoritative URL is recorded.' } }
  $parsed = $null
  if (-not [Uri]::TryCreate($Url,[UriKind]::Absolute,[ref]$parsed) -or $parsed.Scheme -notin @('http','https')) { return [pscustomobject][ordered]@{ status='failed'; url=$Url; http_status=$null; reason='URL is not an absolute HTTP(S) URL.' } }
  try {
    try { $response = Invoke-WebRequest -Uri $Url -Method Head -MaximumRedirection 8 -TimeoutSec $TimeoutSeconds -UserAgent 'ABQInfo parallel verification campaign/1.0' }
    catch { $response = Invoke-WebRequest -Uri $Url -Method Get -MaximumRedirection 8 -TimeoutSec $TimeoutSeconds -UserAgent 'ABQInfo parallel verification campaign/1.0' }
    $code = [int]$response.StatusCode
    [pscustomobject][ordered]@{ status=if($code -ge 200 -and $code -lt 400){'passed'}else{'failed'}; url=$Url; http_status=$code; reason="HTTP $code" }
  } catch {
    $code = if ($_.Exception.Response -and $_.Exception.Response.StatusCode) { [int]$_.Exception.Response.StatusCode } else { $null }
    [pscustomobject][ordered]@{ status='failed'; url=$Url; http_status=$code; reason=$_.Exception.Message }
  }
}

function Invoke-ParallelVerificationCandidateChecks {
  param([Parameter(Mandatory)]$Candidate,[Parameter(Mandatory)][string]$RepoRoot,[switch]$SkipLinkCheck,[int]$LinkTimeoutSeconds=30)
  $localPath = [string]$Candidate.local_path
  if ([string]::IsNullOrWhiteSpace($localPath)) { $fileCheck=[pscustomobject][ordered]@{status='not_applicable';path=$null;expected_size=$null;actual_size=$null;expected_sha256=$null;actual_sha256=$null;reason='No local file is recorded.'} }
  else {
    $full = Resolve-ParallelVerificationWorkerPath $localPath $RepoRoot
    if (-not (Test-Path -LiteralPath $full -PathType Leaf)) { $fileCheck=[pscustomobject][ordered]@{status='failed';path=$localPath;expected_size=$Candidate.size_bytes;actual_size=$null;expected_sha256=$Candidate.checksum_sha256;actual_sha256=$null;reason='Recorded local file is missing.'} }
    else {
      $size=(Get-Item -LiteralPath $full).Length; $hash=Get-ParallelVerificationFileHash $full
      $hasSize=$null -ne $Candidate.size_bytes -and [string]$Candidate.size_bytes -ne ''; $hasHash=-not [string]::IsNullOrWhiteSpace([string]$Candidate.checksum_sha256)
      $matches=$hasSize -and $hasHash -and [long]$Candidate.size_bytes -eq $size -and ([string]$Candidate.checksum_sha256).ToLowerInvariant() -eq $hash
      $fileCheck=[pscustomobject][ordered]@{status=if($matches){'passed'}else{'failed'};path=$localPath;expected_size=$Candidate.size_bytes;actual_size=$size;expected_sha256=$Candidate.checksum_sha256;actual_sha256=$hash;reason=if($matches){'Local file size and SHA-256 match inventory.'}elseif(-not $hasSize -or -not $hasHash){'Inventory lacks expected file size or SHA-256.'}else{'Local file size or SHA-256 does not match inventory.'}}
    }
  }
  $sourceUrl=if(-not [string]::IsNullOrWhiteSpace([string]$Candidate.source_url)){[string]$Candidate.source_url}else{[string]$Candidate.direct_file_url}
  $uri=$null; $sourceValid=[Uri]::TryCreate($sourceUrl,[UriKind]::Absolute,[ref]$uri) -and $uri.Scheme -in @('http','https') -and $uri.Host -ne 'files.abqinfo.com'
  $provenance=-not [string]::IsNullOrWhiteSpace([string]$Candidate.provenance_status) -and [string]$Candidate.provenance_status -notmatch '(?i)unknown|unresolved|pending'
  $sourceCheck=[pscustomobject][ordered]@{status=if($sourceValid -and $provenance){'passed'}else{'failed'};url=if($sourceUrl){$sourceUrl}else{$null};provenance_status=$Candidate.provenance_status;reason=if(-not $sourceValid){'No valid non-R2 authoritative HTTP(S) source is recorded.'}elseif(-not $provenance){'Provenance status is missing or unresolved.'}else{'Authoritative source and resolved provenance are recorded.'}}
  $linkUrl=if(-not [string]::IsNullOrWhiteSpace([string]$Candidate.direct_file_url) -and [string]$Candidate.direct_file_url -notmatch '^https?://files\.abqinfo\.com/'){[string]$Candidate.direct_file_url}else{$sourceUrl}
  $linkCheck=if($SkipLinkCheck){[pscustomobject][ordered]@{status='skipped';url=$linkUrl;http_status=$null;reason='Link check explicitly skipped.'}}else{Test-ParallelVerificationWorkerLink $linkUrl $LinkTimeoutSeconds}
  $statuses=@($fileCheck.status,$sourceCheck.status,$linkCheck.status)
  [pscustomobject][ordered]@{ overall_status=if('failed' -in $statuses){'failed'}elseif('skipped' -in $statuses){'incomplete'}else{'passed'}; checks=[pscustomobject][ordered]@{file_integrity=$fileCheck;source_provenance=$sourceCheck;link_reachability=$linkCheck} }
}
