[CmdletBinding()]
param(
  [string]$PreparationPath = 'project-state/discovery/later-ms4-archive-preparation-2026-09-24.json',
  [string]$EvidencePath = 'project-state/discovery/later-ms4-archive-public-byte-verification-2026-09-25.json',
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$R2InventoryPath = 'project-state/r2-inventory.json',
  [string]$LivePath = 'tmp/later-ms4-live-postupload-2026-09-25.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$prepared = Get-Content -Raw -Encoding UTF8 -LiteralPath $PreparationPath | ConvertFrom-Json
$evidence = Get-Content -Raw -Encoding UTF8 -LiteralPath $EvidencePath | ConvertFrom-Json
$live = Get-Content -Raw -Encoding UTF8 -LiteralPath $LivePath | ConvertFrom-Json
if ($evidence.state -notin @('complete_all_six_public_byte_verified','complete_all_six_public_byte_verified_and_inventory_reconciled') -or @($prepared.records).Count -ne 6 -or @($evidence.results).Count -ne 6) { throw 'Later-MS4 six-object public-byte evidence is incomplete.' }
if ($evidence.summary.public_byte_verified -ne 6 -or $evidence.accounting.new_bytes -ne 426926738 -or $evidence.accounting.new_objects -ne 6) { throw 'Later-MS4 archive delta differs from authorized six originals.' }
if ($live.object_count -ne $evidence.after_r2.object_count -or $live.total_bytes -ne $evidence.after_r2.total_bytes) { throw 'Live R2 accounting differs from upload evidence.' }
if ($evidence.visitor_visible_content_changed) { throw 'Visible-content change is outside this stage.' }

# The authoritative saved inventory is the exact verified live listing, never
# a hand-edited aggregate or a partial object list.
Copy-Item -LiteralPath $LivePath -Destination $R2InventoryPath -Force
$saved = Get-Content -Raw -Encoding UTF8 -LiteralPath $R2InventoryPath | ConvertFrom-Json
if (($saved.objects | ConvertTo-Json -Depth 8 -Compress) -cne ($live.objects | ConvertTo-Json -Depth 8 -Compress) -or $saved.object_count -ne $live.object_count -or $saved.total_bytes -ne $live.total_bytes) { throw 'Saved R2 inventory does not match verified live listing.' }

$objects = @{}; foreach ($object in @($saved.objects)) { $objects[$object.key] = $object }
foreach ($record in @($prepared.records)) {
  $result = @($evidence.results | Where-Object id -eq $record.id)
  if ($result.Count -ne 1 -or -not $objects.ContainsKey($record.proposed_r2_key)) { throw "Missing exact record or R2 object: $($record.id)" }
  $result = $result[0]; $object = $objects[$record.proposed_r2_key]
  if (-not $result.byte_identical -or $result.http_public_get -ne 'passed' -or $result.public_size_bytes -ne $record.size_bytes -or $result.public_checksum_sha256 -ne $record.checksum_sha256 -or $object.size_bytes -ne $record.size_bytes -or $object.public_url -cne $record.proposed_future_archive_url) { throw "Public archive mismatch: $($record.id)" }
}

foreach ($record in @($prepared.records)) {
  $object = $objects[$record.proposed_r2_key]
  $inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json -DateKind String
  $candidate = @($inventory.candidates | Where-Object id -eq $record.id)
  if ($candidate.Count -ne 1) { throw "Missing inventory row: $($record.id)" }
  $candidate = $candidate[0]
  if ($candidate.status -notin @('approved for addition','placement assigned') -or $candidate.direct_file_url -cne $record.authoritative_source_url -or $candidate.local_path -cne $record.staged_original -or $candidate.size_bytes -ne $record.size_bytes -or $candidate.checksum_sha256 -ne $record.checksum_sha256 -or $candidate.proposed_canonical_page -cne 'content/public-works/stormwater-drainage.md') { throw "Inventory identity or scope mismatch: $($record.id)" }
  $note = "Later-MS4 R2 archival 2026-09-25: unchanged authoritative original at $($record.proposed_r2_key); public GET matched $($record.size_bytes) bytes and SHA-256 $($record.checksum_sha256). Stormwater and Drainage Hugo implementation remains separately gated."
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
  saved_object_count=[int]$saved.object_count;saved_total_bytes=[int64]$saved.total_bytes
  live_object_count=[int]$live.object_count;live_total_bytes=[int64]$live.total_bytes
  records_updated=6;inventory_status='placement assigned';public_content_changed=$false
}) -Force
$evidence.state = 'complete_all_six_public_byte_verified_and_inventory_reconciled'
$evidence.completed_at = (Get-Date).ToUniversalTime().ToString('o')
$full = [IO.Path]::GetFullPath($EvidencePath)
$temporary = "$full.tmp-$PID"
[IO.File]::WriteAllText($temporary, ($evidence | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporary -Destination $full -Force
$evidence.r2_inventory_accounting | ConvertTo-Json -Compress
