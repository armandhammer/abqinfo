[CmdletBinding()]
param(
    [string]$FinalStatePath = 'project-state/discovery/archive-reconciliation-final-local-state-2026-09-17.json',
    [string]$LiveR2Path = 'project-state/discovery/live-r2-object-inventory-2026-09-16.json',
    [string]$R2Path = 'project-state/r2-inventory.json',
    [string]$MasterPath = 'project-state/master-inventory.json',
    [string]$UnresolvedPath = 'project-state/discovery/archive-reconciliation-unresolved-review-2026-09-17.json'
)
$ErrorActionPreference = 'Stop'
function Read-Json([string]$Path) { Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json }
function Fail([string]$Message) { throw $Message }
$state = Read-Json $FinalStatePath
$live = Read-Json $LiveR2Path
$r2 = Read-Json $R2Path
$master = Read-Json $MasterPath
$unresolved = Read-Json $UnresolvedPath
if (@($live.objects).Count -ne 1180 -or [int64]$live.total_bytes -ne 8614076524) { Fail 'Saved live-R2 baseline changed unexpectedly.' }
if (@($r2.objects).Count -ne 1180 -or [int64]$r2.total_bytes -ne 8614076524) { Fail 'Repository R2 totals are not final expected totals.' }
$liveByKey = @{}
foreach ($o in @($live.objects)) { if ($liveByKey.ContainsKey([string]$o.key)) { Fail "Duplicate live key: $($o.key)" }; $liveByKey[[string]$o.key] = $o }
$repoByKey = @{}
foreach ($o in @($r2.objects)) { if ($repoByKey.ContainsKey([string]$o.key)) { Fail "Duplicate repository key: $($o.key)" }; $repoByKey[[string]$o.key] = $o }
if ($liveByKey.Count -ne $repoByKey.Count) { Fail 'Live/repository key counts differ.' }
foreach ($key in $liveByKey.Keys) {
    if (-not $repoByKey.ContainsKey($key)) { Fail "Repository missing live key: $key" }
    $a = $liveByKey[$key]; $b = $repoByKey[$key]
    foreach ($field in @('key','size_bytes','last_modified','etag','storage_class','public_url')) { if ([string]$a.$field -ne [string]$b.$field) { Fail "Metadata mismatch for $key field $field." } }
}
$ids = @{}
foreach ($record in @($master.candidates)) { if ($ids.ContainsKey([string]$record.id)) { Fail "Duplicate master ID: $($record.id)" }; $ids[[string]$record.id] = $true }
if ($state.storage_accounting.published_object_repository_inventory_failures -ne 0) { Fail 'Published inventory failures are nonzero.' }
if ($state.published_legacy_without_master_records.count -ne 111) { Fail 'Legacy published-without-master count is not 111.' }
if ($state.current_branch_links_awaiting_deployment.count -ne 53) { Fail 'Deployment-lag count is not 53.' }
if (@($unresolved.cases).Count -ne 3 -or @($state.editorial_or_policy_cases_storage_accounted_disposition_unresolved).Count -ne 3) { Fail 'Editorial unresolved count is not 3.' }
foreach ($case in @($unresolved.cases)) {
    $id = [string]$case.identified_document.existing_master_candidate_id
    $record = @($master.candidates | Where-Object id -eq $id)
    if ($record.Count -ne 1 -or $record[0].status -ne 'requires human review' -or [string]$record[0].r2_key -ne [string]$case.r2_key) { Fail "Editorial factual linkage/status invalid for $id." }
}
if (@($state.future_r2_duplicate_deletion_candidate).Count -ne 1) { Fail 'Expected exactly one future duplicate-deletion candidate.' }
if ($state.storage_accounting.live_r2_modified -ne $false -or $state.storage_accounting.publication_or_site_content_modified -ne $false) { Fail 'External/content mutation flag is incorrect.' }
[pscustomobject]@{ passed = $true; live_and_repository_keys = $repoByKey.Count; total_bytes = [int64]$r2.total_bytes; legacy_without_master = $state.published_legacy_without_master_records.count; deployment_lag = $state.current_branch_links_awaiting_deployment.count; unresolved_editorial = @($state.editorial_or_policy_cases_storage_accounted_disposition_unresolved).Count } | ConvertTo-Json
