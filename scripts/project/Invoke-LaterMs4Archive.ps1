[CmdletBinding()]
param(
  [string]$PreparationPath = 'project-state/discovery/later-ms4-archive-preparation-2026-09-24.json',
  [string]$EvidencePath = 'project-state/discovery/later-ms4-archive-public-byte-verification-2026-09-25.json',
  [string]$PreLivePath = 'tmp/later-ms4-live-preupload-2026-09-25.json',
  [string]$PostLivePath = 'tmp/later-ms4-live-postupload-2026-09-25.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
function Save-Evidence($value) {
  $full = [IO.Path]::GetFullPath($EvidencePath)
  $temporary = "$full.tmp-$PID"
  [IO.File]::WriteAllText($temporary, ($value | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporary -Destination $full -Force
}
function Get-ObjectManifestSha256($objects) {
  $lines = @($objects | ForEach-Object { "$($_.key)|$($_.size_bytes)|$($_.etag)" } | Sort-Object -CaseSensitive)
  $bytes = [Text.Encoding]::UTF8.GetBytes(($lines -join "`n"))
  $hasher = [Security.Cryptography.SHA256]::Create()
  try { return ([BitConverter]::ToString($hasher.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() }
  finally { $hasher.Dispose() }
}

$prepared = Get-Content -Raw -Encoding UTF8 -LiteralPath $PreparationPath | ConvertFrom-Json
$records = @($prepared.records)
$ids = @('src-5cdb4d5491c3a02d','src-975528e01439f6df','src-fdc66c5b8de48584','src-7c1a063b817989bd','src-eda3280085776f61','src-e531466aed7f5387')
if ($records.Count -ne 6 -or (@($records.id) -join ',') -cne ($ids -join ',')) { throw 'Later-MS4 batch must contain the exact six authorized records in order.' }
if (($records | Measure-Object -Property size_bytes -Sum).Sum -ne 426926738) { throw 'Later-MS4 staged total differs from 426,926,738 bytes.' }

$preflight = @()
foreach ($record in $records) {
  $path = [IO.Path]::GetFullPath($record.staged_original)
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Staged original absent: $($record.id)" }
  $size = [int64](Get-Item -LiteralPath $path).Length
  $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($size -ne [int64]$record.size_bytes -or $hash -ne [string]$record.checksum_sha256) { throw "Staged original differs from preparation: $($record.id)" }
  if ($record.proposed_future_archive_url -cne "https://files.abqinfo.com/$($record.proposed_r2_key)") { throw "Approved public URL differs from key: $($record.id)" }
  $preflight += [pscustomobject][ordered]@{id=$record.id;staged_original=$record.staged_original;size_bytes=$size;checksum_sha256=$hash;source_url=$record.authoritative_source_url;r2_key=$record.proposed_r2_key;public_url=$record.proposed_future_archive_url}
}
if (@($preflight.r2_key | ForEach-Object ToLowerInvariant | Select-Object -Unique).Count -ne 6) { throw 'Later-MS4 keys are not unique.' }

# A new listing is required on every invocation. Existing keys are accepted only
# after exact public-byte verification, permitting safe interruption recovery.
& "$PSScriptRoot/Get-R2Inventory.ps1" -OutputPath $PreLivePath | Out-Null
$before = Get-Content -Raw -Encoding UTF8 -LiteralPath $PreLivePath | ConvertFrom-Json
$liveKeys = @{}; foreach ($object in @($before.objects)) { $liveKeys[$object.key.ToLowerInvariant()] = $object }
$present = @{}
foreach ($check in $preflight) {
  $folded = $check.r2_key.ToLowerInvariant()
  if ($liveKeys.ContainsKey($folded)) {
    if ($liveKeys[$folded].key -cne $check.r2_key -or [int64]$liveKeys[$folded].size_bytes -ne $check.size_bytes) { throw "R2 key collision: $($check.r2_key)" }
    $public = & "$PSScriptRoot/Test-R2PublicObject.ps1" -SourcePath $check.staged_original -PublicUrl ([uri]$check.public_url)
    if (-not $public.byte_identical -or $public.checksum_sha256 -ne $check.checksum_sha256) { throw "Nonidentical existing R2 object: $($check.r2_key)" }
    $present[$check.id] = $public
  } elseif (@($before.objects | Where-Object { $_.size_bytes -eq $check.size_bytes }).Count -gt 0) {
    throw "Possible same-size existing R2 object for $($check.id); investigate before upload."
  }
}

$prior = $null
if (Test-Path -LiteralPath $EvidencePath) { $prior = Get-Content -Raw -Encoding UTF8 -LiteralPath $EvidencePath | ConvertFrom-Json }
if ($null -ne $prior -and [string]$prior.state -like 'complete_all_six_*') { throw 'Completed later-MS4 public-byte evidence already exists.' }
$initialBefore = if ($null -ne $prior) { $prior.before_r2 } else { [pscustomobject]@{object_count=[int]$before.object_count;total_bytes=[int64]$before.total_bytes;generated_at=$before.generated_at} }
$initialManifest = if ($null -ne $prior) { [string]$prior.initial_pre_existing_manifest_sha256 } else { Get-ObjectManifestSha256 @($before.objects) }
if ([string]::IsNullOrWhiteSpace($initialManifest)) { throw 'Resume evidence lacks original R2 object manifest signature.' }
$plannedKeys = @($preflight.r2_key)
$currentPriorObjects = @($before.objects | Where-Object { $_.key -notin $plannedKeys })
if ((Get-ObjectManifestSha256 $currentPriorObjects) -ne $initialManifest) { throw 'Pre-existing R2 object manifest changed before or during this batch.' }
$presentBytes = [int64](@($preflight | Where-Object { $present.ContainsKey($_.id) } | Measure-Object -Property size_bytes -Sum)[0].Sum)
if ([int]$before.object_count -ne ([int]$initialBefore.object_count + $present.Count) -or [int64]$before.total_bytes -ne ([int64]$initialBefore.total_bytes + $presentBytes)) { throw 'R2 baseline changed outside the authorized six keys.' }
$evidence = [ordered]@{
  schema_version=1;artifact_type='later_ms4_archive_public_byte_verification'
  started_at=(Get-Date).ToUniversalTime().ToString('o');state='running'
  authorized_scope='exactly six unchanged prepared originals; R2 upload and exact public-byte verification only'
  max_object_bytes=150000000;max_projected_storage_bytes=10000000000
  preparation_artifact=$PreparationPath;preflight_artifact='project-state/discovery/later-ms4-r2-upload-preflight-2026-09-24.json'
  before_r2=$initialBefore;initial_pre_existing_manifest_sha256=$initialManifest
  preflight=$preflight;results=@()
  summary=[ordered]@{intended=6;uploaded_now=0;exact_existing_after_interrupted_resume=0;public_byte_verified=0;added_bytes=0}
  visitor_visible_content_changed=$false
}
if ($null -ne $prior) {
  foreach ($result in @($prior.results)) {
    if ($result.id -notin $ids -or -not $present.ContainsKey($result.id)) { throw "Prior result missing or invalid on resume: $($result.id)" }
    $evidence.results += $result
    if ($result.action -eq 'uploaded_now') { $evidence.summary.uploaded_now++ } else { $evidence.summary.exact_existing_after_interrupted_resume++ }
    $evidence.summary.added_bytes += [int64]$result.expected_size_bytes
    $evidence.summary.public_byte_verified++
  }
}
Save-Evidence $evidence

try {
  foreach ($check in $preflight) {
    if (@($evidence.results | Where-Object { $_.id -eq $check.id }).Count -gt 0) { continue }
    $action = 'exact_existing_after_interrupted_resume'
    if ($present.ContainsKey($check.id)) {
      $public = $present[$check.id]
    } else {
      $upload = @(& "$PSScriptRoot/../upload-r2-document.ps1" -SourcePath $check.staged_original -ObjectKey $check.r2_key -MaxObjectBytes 150000000 -MaxProjectedStorageBytes 10000000000)
      if (@($upload | Where-Object { $_.PSObject.Properties.Name -contains 'R2Metadata' }).Count -ne 1) { throw "Uploader did not confirm R2 metadata: $($check.id)" }
      $action = 'uploaded_now'
      $public = & "$PSScriptRoot/Test-R2PublicObject.ps1" -SourcePath $check.staged_original -PublicUrl ([uri]$check.public_url)
    }
    if (-not $public.byte_identical -or [int64]$public.size_bytes -ne $check.size_bytes -or $public.checksum_sha256 -ne $check.checksum_sha256 -or $public.public_url -cne $check.public_url) { throw "Public bytes differ from preparation: $($check.id)" }
    $evidence.results += [pscustomobject][ordered]@{id=$check.id;staged_original=$check.staged_original;source_url=$check.source_url;r2_key=$check.r2_key;public_url=$check.public_url;action=$action;http_public_get='passed';expected_size_bytes=$check.size_bytes;public_size_bytes=[int64]$public.size_bytes;expected_checksum_sha256=$check.checksum_sha256;public_checksum_sha256=$public.checksum_sha256;byte_identical=$true;verified_at=$public.verified_at}
    if ($action -eq 'uploaded_now') { $evidence.summary.uploaded_now++ } else { $evidence.summary.exact_existing_after_interrupted_resume++ }
    $evidence.summary.added_bytes += $check.size_bytes
    $evidence.summary.public_byte_verified++
    Save-Evidence $evidence
    Write-Host "Later-MS4 public bytes verified: $($evidence.summary.public_byte_verified)/6 $($check.id)"
  }
  & "$PSScriptRoot/Get-R2Inventory.ps1" -OutputPath $PostLivePath | Out-Null
  $after = Get-Content -Raw -Encoding UTF8 -LiteralPath $PostLivePath | ConvertFrom-Json
  $newCount = 6
  $newBytes = [int64]426926738
  if ($after.object_count -ne ([int]$initialBefore.object_count + $newCount) -or $after.total_bytes -ne ([int64]$initialBefore.total_bytes + $newBytes)) { throw 'Post-upload R2 count/bytes differ from intended delta.' }
  $afterKeys = @{}; foreach ($object in @($after.objects)) { $afterKeys[$object.key] = $object }
  foreach ($object in @($before.objects)) {
    if (-not $afterKeys.ContainsKey($object.key) -or $afterKeys[$object.key].size_bytes -ne $object.size_bytes -or $afterKeys[$object.key].etag -ne $object.etag) { throw "Pre-existing R2 object changed or disappeared: $($object.key)" }
  }
  foreach ($check in $preflight) {
    if (-not $afterKeys.ContainsKey($check.r2_key) -or [int64]$afterKeys[$check.r2_key].size_bytes -ne $check.size_bytes) { throw "Intended R2 object missing or mis-sized: $($check.id)" }
  }
  $beforeManifest = $initialManifest
  $afterPriorManifest = Get-ObjectManifestSha256 @($after.objects | Where-Object { $_.key -notin $plannedKeys })
  if ($beforeManifest -ne $afterPriorManifest) { throw 'Pre-existing object manifest signature changed.' }
  $evidence.after_r2 = [ordered]@{object_count=[int]$after.object_count;total_bytes=[int64]$after.total_bytes;generated_at=$after.generated_at}
  $evidence.accounting = [ordered]@{new_objects=$newCount;new_bytes=$newBytes;pre_existing_object_count=[int]$initialBefore.object_count;pre_existing_manifest_sha256_before=$beforeManifest;pre_existing_manifest_sha256_after=$afterPriorManifest;pre_existing_objects_unchanged=$true;unexpected_objects_added=$false}
  $evidence.completed_at = (Get-Date).ToUniversalTime().ToString('o')
  $evidence.state = 'complete_all_six_public_byte_verified'
  Save-Evidence $evidence
  $evidence.summary | ConvertTo-Json -Compress
} catch {
  $evidence.state = 'blocked_incomplete'
  $evidence.blocker = [string]$_.Exception.Message
  Save-Evidence $evidence
  throw
}
