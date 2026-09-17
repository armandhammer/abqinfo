[CmdletBinding()]
param(
    [string]$ProvenancePath = 'project-state/discovery/archive-reconciliation-provenance-2026-09-17.json',
    [string]$MasterInventoryPath = 'project-state/master-inventory.json',
    [string]$R2InventoryPath = 'project-state/r2-inventory.json'
)

$ErrorActionPreference = 'Stop'
$provenance = Get-Content -Raw -Encoding UTF8 $ProvenancePath | ConvertFrom-Json
$master = Get-Content -Raw -Encoding UTF8 $MasterInventoryPath | ConvertFrom-Json
$r2 = Get-Content -Raw -Encoding UTF8 $R2InventoryPath | ConvertFrom-Json
$safe = @($provenance.cases | Where-Object result -eq 'provenance_reconstructed_safe_for_accounting')
$unresolved = @($provenance.cases | Where-Object result -eq 'requires_user_or_higher_judgment')
if ($safe.Count -ne 24 -or $unresolved.Count -ne 3) { throw 'Unexpected provenance repair classification counts.' }
$masterById = @{}; foreach ($candidate in @($master.candidates)) { if ($masterById.ContainsKey([string]$candidate.id)) { throw "Duplicate master candidate ID '$($candidate.id)'." }; $masterById[[string]$candidate.id] = $candidate }
$r2ByKey = @{}; foreach ($object in @($r2.objects)) { if ($r2ByKey.ContainsKey([string]$object.key)) { throw "Duplicate R2 key '$($object.key)'." }; $r2ByKey[[string]$object.key] = $object }
$fields = @('key','size_bytes','last_modified','etag','storage_class','public_url')
foreach ($case in $safe) {
    $candidate = $masterById[[string]$case.exact_proposed_local_accounting_action.master_candidate_id]
    $object = $r2ByKey[[string]$case.r2_key]
    if ($null -eq $candidate -or $null -eq $object) { throw "Missing safe repair linkage for $($case.action_id)." }
    if ($candidate.r2_key -ne $case.r2_key -or $candidate.r2_url -ne $object.public_url -or $candidate.r2_etag -ne $object.etag -or $candidate.r2_last_modified -ne $object.last_modified) { throw "Master linkage mismatch for $($case.action_id)." }
    foreach ($field in $fields) { if ([string]$object.$field -ne [string]$case.exact_proposed_local_accounting_action.r2_object.$field) { throw "R2 object mismatch for $($case.action_id), field $field." } }
}
foreach ($case in $unresolved) {
    $object = $r2ByKey[[string]$case.r2_key]
    $id = [string]$case.identified_document.existing_master_candidate_id
    $candidate = $masterById[$id]
    if ($null -eq $object -or $null -eq $candidate) { throw "Final factual accounting is missing for unresolved case $($case.action_id)." }
    if ($candidate.status -ne 'requires human review' -or $candidate.r2_key -ne $case.r2_key -or $candidate.r2_url -ne $object.public_url -or $candidate.r2_etag -ne $object.etag -or $candidate.r2_last_modified -ne $object.last_modified) { throw "Unresolved case $($case.action_id) changed status or has incorrect factual linkage." }
    if (-not (@($candidate.processing_notes) -match 'storage accounting.*byte-identical.*editorial retention/publication remains unresolved')) { throw "Unresolved case $($case.action_id) is missing its processing note." }
}
if ([int]$r2.object_count -ne @($r2.objects).Count -or [int64]$r2.total_bytes -ne [int64](($r2.objects | Measure-Object -Property size_bytes -Sum).Sum)) { throw 'R2 inventory aggregate metadata is inconsistent.' }
Write-Output 'Archive-reconciliation provenance repairs validation passed: 24 safe links/objects exact and 3 editorial cases factually accounted with human-review status preserved.'
