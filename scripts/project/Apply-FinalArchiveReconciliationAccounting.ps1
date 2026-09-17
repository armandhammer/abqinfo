[CmdletBinding()]
param(
    [string]$ClassificationPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-classification-2026-09-16.json',
    [string]$UnresolvedPath = 'project-state/discovery/archive-reconciliation-unresolved-review-2026-09-17.json',
    [string]$LiveR2Path = 'project-state/discovery/live-r2-object-inventory-2026-09-16.json',
    [string]$MasterPath = 'project-state/master-inventory.json',
    [string]$R2Path = 'project-state/r2-inventory.json'
)
$ErrorActionPreference = 'Stop'

function Read-Json([string]$Path) { Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json }
function Write-JsonUtf8NoBom($Value, [string]$Path) {
    $json = $Value | ConvertTo-Json -Depth 100
    [IO.File]::WriteAllText((Resolve-Path -LiteralPath $Path), $json + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
}
function Fail([string]$Message) { throw $Message }

$classification = Read-Json $ClassificationPath
$unresolved = Read-Json $UnresolvedPath
$live = Read-Json $LiveR2Path
$master = Read-Json $MasterPath
$inventory = Read-Json $R2Path

$published = @($classification.published_objects_missing_repository_r2_inventory)
if ($published.Count -ne 116) { Fail "Expected 116 published accounting gaps; found $($published.Count)." }
if (@($published | Where-Object classification -eq 'published_legacy_object_missing_inventory_accounting').Count -ne 111) { Fail 'Expected 111 legacy published gaps.' }
if (@($published | Where-Object classification -eq 'published_object_missing_repository_r2_record_stale_inventory').Count -ne 5) { Fail 'Expected 5 stale-inventory published gaps.' }
$editorial = @($unresolved.cases)
if ($editorial.Count -ne 3) { Fail "Expected 3 unresolved editorial cases; found $($editorial.Count)." }

$liveByKey = @{}
foreach ($object in @($live.objects)) {
    if ($liveByKey.ContainsKey([string]$object.key)) { Fail "Duplicate live-R2 key: $($object.key)" }
    $liveByKey[[string]$object.key] = $object
}
$currentByKey = @{}
foreach ($object in @($inventory.objects)) {
    if ($currentByKey.ContainsKey([string]$object.key)) { Fail "Duplicate repository R2 key before repair: $($object.key)" }
    $currentByKey[[string]$object.key] = $object
}
$masterById = @{}
foreach ($record in @($master.candidates)) {
    if ($masterById.ContainsKey([string]$record.id)) { Fail "Duplicate master ID before repair: $($record.id)" }
    $masterById[[string]$record.id] = $record
}

$toAdd = [ordered]@{}
foreach ($item in $published) {
    if (-not $liveByKey.ContainsKey([string]$item.key)) { Fail "Published gap absent from saved live inventory: $($item.key)" }
    if ($currentByKey.ContainsKey([string]$item.key)) { Fail "Published gap already exists in repository inventory: $($item.key)" }
    $toAdd[[string]$item.key] = $liveByKey[[string]$item.key]
    if (@($item.master_record_ids).Count -gt 0) {
        foreach ($id in @($item.master_record_ids)) {
            if (-not $masterById.ContainsKey([string]$id)) { Fail "Stale published gap references missing master: $id" }
            $record = $masterById[[string]$id]
            if ([string]$record.r2_key -ne [string]$item.key) { Fail "Existing master linkage changed/mismatched for $id." }
            $liveObject = $liveByKey[[string]$item.key]
            if ([string]$record.r2_url -ne [string]$liveObject.public_url -or [int64]$record.size_bytes -ne [int64]$liveObject.size_bytes) { Fail "Existing master linkage is not exact for $id." }
        }
    }
}

$editorialNote = 'Archive reconciliation storage accounting 2026-09-17: the existing R2 object was verified byte-identical to the authoritative City source; factual R2 linkage was recorded, while editorial retention/publication remains unresolved.'
foreach ($item in $editorial) {
    if (-not $liveByKey.ContainsKey([string]$item.r2_key)) { Fail "Editorial object absent from saved live inventory: $($item.r2_key)" }
    if ($currentByKey.ContainsKey([string]$item.r2_key)) { Fail "Editorial object already exists in repository inventory: $($item.r2_key)" }
    $toAdd[[string]$item.r2_key] = $liveByKey[[string]$item.r2_key]
    $id = [string]$item.identified_document.existing_master_candidate_id
    if (-not $masterById.ContainsKey($id)) { Fail "Editorial case references missing master: $id" }
    $record = $masterById[$id]
    if ([string]$record.status -ne 'requires human review') { Fail "Editorial master status changed for $id." }
    $liveObject = $liveByKey[[string]$item.r2_key]
    $record.r2_key = $liveObject.key
    $record.r2_url = $liveObject.public_url
    $record.r2_etag = $liveObject.etag
    $record.r2_last_modified = $liveObject.last_modified
    if ($null -eq $record.processing_notes) { $record.processing_notes = @() }
    $notes = @($record.processing_notes)
    if (-not ($notes -contains $editorialNote)) { $record.processing_notes = @($notes + $editorialNote) }
}

if ($toAdd.Count -ne 119) { Fail "Expected 119 new inventory objects; found $($toAdd.Count)." }
$newObjects = @($inventory.objects) + @($toAdd.Values)
$seen = @{}
foreach ($object in $newObjects) {
    $key = [string]$object.key
    if ($seen.ContainsKey($key)) { Fail "Duplicate repository R2 key after repair: $key" }
    $seen[$key] = $true
}
$inventory.objects = @($newObjects | Sort-Object key)
$inventory.object_count = $inventory.objects.Count
$inventory.total_bytes = [int64](($inventory.objects | Measure-Object -Property size_bytes -Sum).Sum)
if ($inventory.object_count -ne 1180 -or $inventory.total_bytes -ne 8614076524) { Fail "Unexpected final inventory totals: $($inventory.object_count) / $($inventory.total_bytes)." }

$masterJson = $master | ConvertTo-Json -Depth 100
$r2Json = $inventory | ConvertTo-Json -Depth 100
$masterFull = (Resolve-Path -LiteralPath $MasterPath).Path
$r2Full = (Resolve-Path -LiteralPath $R2Path).Path
$masterTmp = "$masterFull.final-accounting.tmp"
$r2Tmp = "$r2Full.final-accounting.tmp"
[IO.File]::WriteAllText($masterTmp, $masterJson + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText($r2Tmp, $r2Json + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $masterTmp -Destination $masterFull -Force
Move-Item -LiteralPath $r2Tmp -Destination $r2Full -Force

[pscustomobject]@{
    published_inventory_gaps_accounted = $published.Count
    published_legacy_objects_accounted = @($published | Where-Object classification -eq 'published_legacy_object_missing_inventory_accounting').Count
    stale_published_linkages_verified = @($published | Where-Object classification -eq 'published_object_missing_repository_r2_record_stale_inventory').Count
    editorial_objects_accounted = $editorial.Count
    master_records_updated = $editorial.Count
    master_records_created = 0
    r2_inventory_records_added = $toAdd.Count
    final_object_count = $inventory.object_count
    final_total_bytes = $inventory.total_bytes
} | ConvertTo-Json
