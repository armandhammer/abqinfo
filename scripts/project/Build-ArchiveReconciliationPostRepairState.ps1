[CmdletBinding()]
param(
    [string]$ManifestPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-repair-manifest-2026-09-17.json',
    [string]$ProvenancePath = 'project-state/discovery/archive-reconciliation-provenance-2026-09-17.json',
    [string]$MasterInventoryPath = 'project-state/master-inventory.json',
    [string]$R2InventoryPath = 'project-state/r2-inventory.json',
    [string]$ReportPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-2026-09-16.json',
    [string]$OutputPath = 'project-state/discovery/archive-reconciliation-post-repair-state-2026-09-17.json',
    [string]$UnresolvedOutputPath = 'project-state/discovery/archive-reconciliation-unresolved-review-2026-09-17.json'
)

$ErrorActionPreference = 'Stop'
$manifest = Get-Content -Raw -Encoding UTF8 $ManifestPath | ConvertFrom-Json
$provenance = Get-Content -Raw -Encoding UTF8 $ProvenancePath | ConvertFrom-Json
$master = Get-Content -Raw -Encoding UTF8 $MasterInventoryPath | ConvertFrom-Json
$r2 = Get-Content -Raw -Encoding UTF8 $R2InventoryPath | ConvertFrom-Json
$report = Get-Content -Raw -Encoding UTF8 $ReportPath | ConvertFrom-Json
$masterById = @{}; foreach ($candidate in @($master.candidates)) { $masterById[[string]$candidate.id] = $candidate }
$r2ByKey = @{}; foreach ($object in @($r2.objects)) { $r2ByKey[[string]$object.key] = $object }
$cases = @($provenance.cases | Sort-Object action_id)
if ($cases.Count -ne 27) { throw 'Expected 27 provenance cases.' }

$stateCases = foreach ($case in $cases) {
    $id = [string]$case.identified_document.existing_master_candidate_id
    $candidate = $masterById[$id]
    $object = $r2ByKey[[string]$case.r2_key]
    $safe = $case.result -eq 'provenance_reconstructed_safe_for_accounting'
    $linkageExact = $safe -and $candidate -and $object -and $candidate.r2_key -eq $case.r2_key -and $candidate.r2_url -eq $object.public_url -and $candidate.r2_etag -eq $object.etag -and $candidate.r2_last_modified -eq $object.last_modified
    [ordered]@{ action_id = [string]$case.action_id; issue_group_id = [string]$case.issue_group_id; r2_key = [string]$case.r2_key; provenance_result = [string]$case.result; master_candidate_id = $id; repository_r2_record_present = [bool]$object; master_r2_linkage_exact = [bool]$linkageExact; no_longer_unaccounted = [bool]$linkageExact; unresolved_reason = if ($safe) { $null } else { [string]$case.limitations } }
}
$priorSafe = @($manifest.actions | Where-Object safety_gate -eq 'safe_local_bookkeeping')
$priorIntact = @($priorSafe | Where-Object { $r2ByKey.ContainsKey([string]$_.proposed_r2_object.key) }).Count
if ($priorSafe.Count -ne 14 -or $priorIntact -ne 14) { throw 'Previously completed 14 safe bookkeeping repairs are not intact.' }
$unresolved = @($cases | Where-Object result -ne 'provenance_reconstructed_safe_for_accounting' | ForEach-Object { [ordered]@{ action_id = [string]$_.action_id; issue_group_id = [string]$_.issue_group_id; r2_key = [string]$_.r2_key; identified_document = $_.identified_document; result = [string]$_.result; reason = [string]$_.limitations; required_next_decision = 'Editorial or policy judgment; no local inventory mutation is authorized for this case.'; external_storage_action_requires_explicit_authorization = $true } })
$state = [ordered]@{ schema_version = 1; generated_at = (Get-Date).ToUniversalTime().ToString('o'); source_manifest = $ManifestPath; source_provenance = $ProvenancePath; source_reconciliation_report = $ReportPath; repository_totals = [ordered]@{ r2_object_count = [int]$r2.object_count; r2_total_bytes = [int64]$r2.total_bytes; live_objects_without_master = [int]$report.summary.live_objects_without_master }; safe_provenance_repairs_completed = @($stateCases | Where-Object no_longer_unaccounted).Count; unresolved_provenance_cases = $unresolved.Count; previously_completed_safe_bookkeeping_repairs_intact = $priorIntact; cases = $stateCases }
$review = [ordered]@{ schema_version = 1; generated_at = $state.generated_at; source_provenance = $ProvenancePath; unresolved_count = $unresolved.Count; cases = $unresolved }
function Write-Utf8Json($value, [string]$path) { $fullPath = [IO.Path]::GetFullPath($path); $temporaryPath = "$fullPath.tmp-$PID"; [IO.File]::WriteAllText($temporaryPath, ($value | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false)); Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force }
Write-Utf8Json $state $OutputPath
Write-Utf8Json $review $UnresolvedOutputPath
Write-Output ("Created post-repair state: {0} safe repairs complete, {1} unresolved." -f $state.safe_provenance_repairs_completed, $state.unresolved_provenance_cases)
