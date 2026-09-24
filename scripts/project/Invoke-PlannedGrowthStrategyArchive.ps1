[CmdletBinding()]
param(
  [string]$PreparationPath = 'project-state/discovery/planned-growth-strategy-archive-preparation-2026-09-23.json',
  [string]$EvidencePath = 'project-state/discovery/planned-growth-strategy-archive-public-byte-verification-2026-09-23.json',
  [string]$PreLivePath = 'tmp/pgs-live-r2-preupload-2026-09-23.json',
  [string]$PostLivePath = 'tmp/pgs-live-r2-postupload-2026-09-23.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $EvidencePath) {
  $priorEvidence = Get-Content -Raw -Encoding UTF8 -LiteralPath $EvidencePath | ConvertFrom-Json
  if ([string]$priorEvidence.state -like 'complete_all_13_*') {
    throw 'The completed PGS public-byte evidence already exists; refusing to replace it.'
  }
}

function Save-Evidence($value) {
  $full = [IO.Path]::GetFullPath($EvidencePath)
  $temporary = "$full.tmp-$PID"
  [IO.File]::WriteAllText($temporary, ($value | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporary -Destination $full -Force
}

$prepared = Get-Content -Raw -Encoding UTF8 -LiteralPath $PreparationPath | ConvertFrom-Json
$records = @($prepared.records)
$expectedIds = @(
  'src-9aeb5f621800da58','src-08b6b68b53336462','src-3efa72bc100374a1',
  'src-aee98d2ab382de65','src-44dedde405c00c2c','src-bc069f52331eb293',
  'src-c8e6f10731a478e6','src-cd72192082580abe','src-765624191ba169bd',
  'src-d15bbc358aeaec4d','src-8188148b0cd6c40d','src-0e133db868401e77',
  'src-c771ae9e41b9905c'
)
if ($records.Count -ne 13 -or (@($records.id) -join ',') -cne ($expectedIds -join ',')) { throw 'PGS batch is not the exact approved 13-record order.' }
if (($records | Measure-Object -Property size_bytes -Sum).Sum -ne 109212492) { throw 'PGS prepared total differs from 109,212,492 bytes.' }
if (@($records.proposed_r2_key | ForEach-Object ToLowerInvariant | Select-Object -Unique).Count -ne 13) { throw 'PGS keys are not unique.' }

$preflight = @()
foreach ($record in $records) {
  $path = [IO.Path]::GetFullPath($record.staged_original)
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Staged original absent: $($record.id)" }
  $size = [int64](Get-Item -LiteralPath $path).Length
  $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($size -ne [int64]$record.size_bytes -or $hash -ne [string]$record.checksum_sha256) { throw "Staged original differs from preparation: $($record.id)" }
  if ($record.proposed_future_archive_url -cne "https://files.abqinfo.com/$($record.proposed_r2_key)") { throw "Approved public URL differs from key: $($record.id)" }
  $preflight += [pscustomobject][ordered]@{id=$record.id;staged_original=$record.staged_original;size_bytes=$size;checksum_sha256=$hash;source_url=$record.authoritative_original_url;r2_key=$record.proposed_r2_key;public_url=$record.proposed_future_archive_url}
}

& "$PSScriptRoot/Get-R2Inventory.ps1" -OutputPath $PreLivePath | Out-Null
$before = Get-Content -Raw -Encoding UTF8 -LiteralPath $PreLivePath | ConvertFrom-Json
$liveKeys = @{}
foreach ($object in @($before.objects)) { $liveKeys[$object.key.ToLowerInvariant()] = $object }
$alreadyPresent = @{}
foreach ($check in $preflight) {
  $folded = $check.r2_key.ToLowerInvariant()
  if ($liveKeys.ContainsKey($folded)) {
    if ($liveKeys[$folded].key -cne $check.r2_key) { throw "Case-insensitive R2 key collision: $($check.r2_key)" }
    if ([int64]$liveKeys[$folded].size_bytes -ne $check.size_bytes) { throw "Different-sized R2 key collision: $($check.r2_key)" }
    $public = & "$PSScriptRoot/Test-R2PublicObject.ps1" -SourcePath $check.staged_original -PublicUrl ([uri]$check.public_url)
    if (-not $public.byte_identical -or $public.checksum_sha256 -ne $check.checksum_sha256) { throw "Nonidentical existing R2 object: $($check.r2_key)" }
    $alreadyPresent[$check.id] = $public
  }
}

$evidence = [ordered]@{
  schema_version=1;artifact_type='planned_growth_strategy_archive_public_byte_verification'
  started_at=(Get-Date).ToUniversalTime().ToString('o');state='running'
  preparation_artifact=$PreparationPath;authorized_scope='exactly 13 unchanged City originals; R2 upload and public-byte verification only'
  family_presentation_limit=$prepared.family_presentation_limit
  before_r2=[ordered]@{object_count=[int]$before.object_count;total_bytes=[int64]$before.total_bytes;generated_at=$before.generated_at}
  preflight=$preflight;results=@();summary=[ordered]@{intended=13;uploaded_now=0;already_present_identical=0;public_byte_verified=0;added_bytes=0}
  next_stage='Hugo/editorial implementation remains separately gated; no public content, PR, merge, or deployment in this stage.'
}
Save-Evidence $evidence

try {
  foreach ($check in $preflight) {
    $action = 'already_present_identical'
    if ($alreadyPresent.ContainsKey($check.id)) {
      $public = $alreadyPresent[$check.id]
    } else {
      $output = @(& "$PSScriptRoot/../upload-r2-document.ps1" -SourcePath $check.staged_original -ObjectKey $check.r2_key)
      if (@($output | Where-Object { $_.PSObject.Properties.Name -contains 'R2Metadata' }).Count -ne 1) { throw "Uploader did not confirm R2 metadata: $($check.id)" }
      $action = 'uploaded_now'
      $public = & "$PSScriptRoot/Test-R2PublicObject.ps1" -SourcePath $check.staged_original -PublicUrl ([uri]$check.public_url)
    }
    if (-not $public.byte_identical -or [int64]$public.size_bytes -ne $check.size_bytes -or $public.checksum_sha256 -ne $check.checksum_sha256 -or $public.public_url -cne $check.public_url) { throw "Public byte verification differs from preparation: $($check.id)" }
    $evidence.results += [pscustomobject][ordered]@{id=$check.id;source_url=$check.source_url;r2_key=$check.r2_key;public_url=$check.public_url;action=$action;http_public_get='passed';expected_size_bytes=$check.size_bytes;public_size_bytes=[int64]$public.size_bytes;expected_checksum_sha256=$check.checksum_sha256;public_checksum_sha256=$public.checksum_sha256;byte_identical=$true;verified_at=$public.verified_at}
    if ($action -eq 'uploaded_now') { $evidence.summary.uploaded_now++; $evidence.summary.added_bytes += $check.size_bytes } else { $evidence.summary.already_present_identical++ }
    $evidence.summary.public_byte_verified++
    Save-Evidence $evidence
    Write-Host "PGS public bytes verified: $($evidence.summary.public_byte_verified)/13 $($check.id)"
  }

  & "$PSScriptRoot/Get-R2Inventory.ps1" -OutputPath $PostLivePath | Out-Null
  $after = Get-Content -Raw -Encoding UTF8 -LiteralPath $PostLivePath | ConvertFrom-Json
  $expectedCount = [int]$before.object_count + [int]$evidence.summary.uploaded_now
  $expectedBytes = [int64]$before.total_bytes + [int64]$evidence.summary.added_bytes
  if ($after.object_count -ne $expectedCount -or $after.total_bytes -ne $expectedBytes) { throw 'Post-upload live R2 count/bytes differ from the intended delta.' }
  $afterKeys = @{}; foreach ($object in @($after.objects)) { $afterKeys[$object.key] = $object }
  foreach ($object in @($before.objects)) {
    if (-not $afterKeys.ContainsKey($object.key) -or $afterKeys[$object.key].size_bytes -ne $object.size_bytes -or $afterKeys[$object.key].etag -ne $object.etag) { throw "Existing unrelated R2 object changed or disappeared: $($object.key)" }
  }
  foreach ($check in $preflight) {
    if (-not $afterKeys.ContainsKey($check.r2_key) -or [int64]$afterKeys[$check.r2_key].size_bytes -ne $check.size_bytes) { throw "Intended R2 key absent or sized incorrectly: $($check.id)" }
  }
  $evidence.after_r2 = [ordered]@{object_count=[int]$after.object_count;total_bytes=[int64]$after.total_bytes;generated_at=$after.generated_at}
  $evidence.completed_at = (Get-Date).ToUniversalTime().ToString('o')
  $evidence.state = 'complete_all_13_public_byte_verified'
  Save-Evidence $evidence
  $evidence.summary | ConvertTo-Json -Compress
} catch {
  $evidence.state = 'blocked_incomplete'
  $evidence.blocker = [string]$_.Exception.Message
  Save-Evidence $evidence
  throw
}
