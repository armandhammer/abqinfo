[CmdletBinding()]
param(
  [string]$PreparationPath = 'project-state/discovery/planned-growth-strategy-archive-preparation-2026-09-23.json',
  [string]$EvidencePath = 'project-state/discovery/planned-growth-strategy-archive-public-byte-verification-2026-09-23.json',
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$R2InventoryPath = 'project-state/r2-inventory.json',
  [string]$LivePath = 'tmp/pgs-live-r2-postupload-2026-09-23.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$prepared = Get-Content -Raw -Encoding UTF8 -LiteralPath $PreparationPath | ConvertFrom-Json
$evidence = Get-Content -Raw -Encoding UTF8 -LiteralPath $EvidencePath | ConvertFrom-Json
$r2 = Get-Content -Raw -Encoding UTF8 -LiteralPath $R2InventoryPath | ConvertFrom-Json
$live = Get-Content -Raw -Encoding UTF8 -LiteralPath $LivePath | ConvertFrom-Json
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json -DateKind String
if ($evidence.state -ne 'complete_all_13_public_byte_verified' -or @($prepared.records).Count -ne 13 -or @($evidence.results).Count -ne 13) { throw 'PGS 13/13 public-byte evidence is incomplete.' }
if ($evidence.summary.uploaded_now -ne 13 -or $evidence.summary.public_byte_verified -ne 13 -or $evidence.summary.added_bytes -ne 109212492) { throw 'PGS archive delta differs from expected 13 originals.' }
if ($r2.object_count -ne 1231 -or $r2.total_bytes -ne 8791355104 -or $live.object_count -ne $r2.object_count -or $live.total_bytes -ne $r2.total_bytes) { throw 'Saved/live R2 totals differ from verified completion.' }
if ((@($r2.objects | ForEach-Object { "$($_.key)|$($_.size_bytes)|$($_.etag)" }) -join "`n") -cne (@($live.objects | ForEach-Object { "$($_.key)|$($_.size_bytes)|$($_.etag)" }) -join "`n")) { throw 'Saved R2 inventory differs from live post-upload listing.' }

foreach ($record in @($prepared.records)) {
  $result = @($evidence.results | Where-Object id -eq $record.id)
  $object = @($r2.objects | Where-Object key -eq $record.proposed_r2_key)
  $candidate = @($inventory.candidates | Where-Object id -eq $record.id)
  if ($result.Count -ne 1 -or $object.Count -ne 1 -or $candidate.Count -ne 1) { throw "Incomplete exact PGS record match: $($record.id)" }
  $result = $result[0]; $object = $object[0]; $candidate = $candidate[0]
  if (-not $result.byte_identical -or $result.http_public_get -ne 'passed' -or $result.public_size_bytes -ne $record.size_bytes -or $result.public_checksum_sha256 -ne $record.checksum_sha256) { throw "Unverified public bytes: $($record.id)" }
  if ($result.public_url -cne $record.proposed_future_archive_url -or $object.public_url -cne $result.public_url -or $object.size_bytes -ne $record.size_bytes) { throw "R2 destination mismatch: $($record.id)" }
  if ($candidate.direct_file_url -cne $record.authoritative_original_url -or $candidate.size_bytes -ne $record.size_bytes -or $candidate.checksum_sha256 -ne $record.checksum_sha256) { throw "Authoritative source or inventory metadata mismatch: $($record.id)" }
  if ($candidate.status -notin @('approved for addition','placement assigned')) { throw "Unexpected PGS status: $($record.id)" }
}

foreach ($record in @($prepared.records)) {
  $object = @($r2.objects | Where-Object key -eq $record.proposed_r2_key)[0]
  $candidate = @($inventory.candidates | Where-Object id -eq $record.id)[0]
  $note = "PGS R2 archival 2026-09-23: unchanged official City original at $($record.proposed_r2_key); public GET matched $($record.size_bytes) bytes and SHA-256 $($record.checksum_sha256). Hugo/editorial implementation remains separately gated."
  $notes = @($candidate.processing_notes)
  if ($note -notin $notes) { $notes += $note }
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $record.id -InventoryPath $InventoryPath -Set @{
    status='placement assigned';r2_key=$record.proposed_r2_key;r2_url=$record.proposed_future_archive_url
    r2_etag=$object.etag;r2_last_modified=$object.last_modified
    validation_status='authoritative source and public R2 bytes match exact size and SHA-256; Hugo/editorial implementation separately gated'
    processing_notes=$notes
  } | Out-Null
}

$evidence | Add-Member -NotePropertyName r2_inventory_accounting -NotePropertyValue ([pscustomobject][ordered]@{
  saved_object_count=[int]$r2.object_count;saved_total_bytes=[int64]$r2.total_bytes
  live_object_count=[int]$live.object_count;live_total_bytes=[int64]$live.total_bytes
  records_updated=13;inventory_status='placement assigned';public_content_changed=$false
}) -Force
$evidence.state = 'complete_all_13_public_byte_verified_and_inventory_reconciled'
$evidence.completed_at = (Get-Date).ToUniversalTime().ToString('o')
$full = [IO.Path]::GetFullPath($EvidencePath)
$temporary = "$full.tmp-$PID"
[IO.File]::WriteAllText($temporary, ($evidence | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporary -Destination $full -Force
$evidence.r2_inventory_accounting | ConvertTo-Json -Compress
