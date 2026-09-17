[CmdletBinding()]
param(
    [string]$ProvenancePath = 'project-state/discovery/archive-reconciliation-provenance-2026-09-17.json',
    [string]$MasterInventoryPath = 'project-state/master-inventory.json',
    [string]$R2InventoryPath = 'project-state/r2-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$provenance = Get-Content -Raw -Encoding UTF8 $ProvenancePath | ConvertFrom-Json
$master = Get-Content -Raw -Encoding UTF8 $MasterInventoryPath | ConvertFrom-Json
$r2 = Get-Content -Raw -Encoding UTF8 $R2InventoryPath | ConvertFrom-Json
$safe = @($provenance.cases | Where-Object result -eq 'provenance_reconstructed_safe_for_accounting')
if ($safe.Count -ne 24) { throw "Expected 24 safe provenance repairs, found $($safe.Count)." }
$masterById = @{}; foreach ($candidate in @($master.candidates)) { if ($masterById.ContainsKey([string]$candidate.id)) { throw "Duplicate master candidate ID '$($candidate.id)'." }; $masterById[[string]$candidate.id] = $candidate }
$r2ByKey = @{}; foreach ($object in @($r2.objects)) { if ($r2ByKey.ContainsKey([string]$object.key)) { throw "Duplicate R2 inventory key '$($object.key)'." }; $r2ByKey[[string]$object.key] = $object }
$requiredFields = @('key','size_bytes','last_modified','etag','storage_class','public_url')

foreach ($case in $safe) {
    $id = [string]$case.exact_proposed_local_accounting_action.master_candidate_id
    $key = [string]$case.r2_key
    $object = $case.exact_proposed_local_accounting_action.r2_object
    if (-not $masterById.ContainsKey($id)) { throw "Missing master candidate '$id' for $($case.action_id)." }
    if ($r2ByKey.ContainsKey($key)) { throw "R2 inventory already contains '$key'; refusing to overwrite or duplicate." }
    if (@(Compare-Object $requiredFields @($object.PSObject.Properties.Name | Sort-Object)).Count -ne 0) { throw "Proposed R2 object for $($case.action_id) has an invalid schema." }
    if ([string]$object.key -ne $key) { throw "Proposed R2 object key mismatch for $($case.action_id)." }
    $candidate = $masterById[$id]
    if ($candidate.r2_key -or $candidate.r2_url -or $candidate.r2_etag -or $candidate.r2_last_modified) { throw "Master candidate '$id' already has R2 linkage; refusing to overwrite." }
}

$note = 'Archive reconciliation accounting repair 2026-09-17: existing public R2 object was byte-identical to the authoritative City original; R2 linkage recorded without publication.'
foreach ($case in $safe) {
    $candidate = $masterById[[string]$case.exact_proposed_local_accounting_action.master_candidate_id]
    $object = $case.exact_proposed_local_accounting_action.r2_object
    $candidate.r2_key = [string]$object.key
    $candidate.r2_url = [string]$object.public_url
    $candidate.r2_etag = [string]$object.etag
    $candidate.r2_last_modified = [string]$object.last_modified
    if (@($candidate.processing_notes) -notcontains $note) { $candidate.processing_notes = @($candidate.processing_notes) + @($note) }
    $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
    $r2.objects += [pscustomobject][ordered]@{ key = [string]$object.key; size_bytes = [int64]$object.size_bytes; last_modified = [string]$object.last_modified; etag = [string]$object.etag; storage_class = [string]$object.storage_class; public_url = [string]$object.public_url }
}
$counts = [ordered]@{}; foreach ($status in @($master.allowed_statuses)) { $counts[$status] = @($master.candidates | Where-Object status -eq $status).Count }
$master.counts = [pscustomobject]$counts
$master.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$next = @($master.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | Sort-Object id | Select-Object -First 1)
$master.next_pending_id = if ($next.Count) { $next[0].id } else { $null }
$r2.objects = @($r2.objects | Sort-Object key)
$r2.object_count = @($r2.objects).Count
$r2.total_bytes = [int64](($r2.objects | Measure-Object -Property size_bytes -Sum).Sum)
$r2.generated_at = (Get-Date).ToUniversalTime().ToString('o')

function Write-Utf8Json($value, [string]$path, [int]$depth) {
    $fullPath = [IO.Path]::GetFullPath($path); $temporaryPath = "$fullPath.tmp-$PID"; [IO.File]::WriteAllText($temporaryPath, ($value | ConvertTo-Json -Depth $depth), [Text.UTF8Encoding]::new($false)); Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
}
Write-Utf8Json $master $MasterInventoryPath 14
Write-Utf8Json $r2 $R2InventoryPath 8
[pscustomobject]@{ master_records_updated = $safe.Count; r2_inventory_records_added = $safe.Count; r2_object_count = $r2.object_count; r2_total_bytes = $r2.total_bytes } | ConvertTo-Json -Compress
