[CmdletBinding()]
param(
    [string]$DecisionPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-decisions-2026-09-17.json',
    [string]$ClassificationPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-classification-2026-09-16.json',
    [string]$LiveR2Path = 'project-state/discovery/live-r2-object-inventory-2026-09-16.json',
    [string]$R2InventoryPath = 'project-state/r2-inventory.json',
    [string]$OutputPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-repair-manifest-2026-09-17.json'
)
$ErrorActionPreference = 'Stop'
$decisions = (Get-Content $DecisionPath -Raw | ConvertFrom-Json).decisions
$classification = Get-Content $ClassificationPath -Raw | ConvertFrom-Json
$liveInventory = Get-Content $LiveR2Path -Raw | ConvertFrom-Json
$r2 = Get-Content $R2InventoryPath -Raw | ConvertFrom-Json
$r2ByKey = @{}; foreach ($o in $r2.objects) { $r2ByKey[$o.key] = $o }
$classByKey = @{}; foreach ($section in @($classification.unreferenced_r2_objects, $classification.expected_but_not_live, $classification.published_objects_missing_repository_r2_inventory)) { foreach ($x in $section) { if ($x.key) { $classByKey[$x.key] = $x } } }
$liveByKey = @{}; foreach ($o in $liveInventory.objects) { $liveByKey[$o.key.ToLowerInvariant()] = $o }

$actions = [System.Collections.Generic.List[object]]::new()
$normalGroups = $decisions | Group-Object { ($_.affected_r2_keys | Select-Object -First 1).ToLowerInvariant() }
foreach ($group in $normalGroups) {
    $items = @($group.Group); $keys = @($items | ForEach-Object { $_.affected_r2_keys } | Sort-Object -Unique); $ids = @($items | ForEach-Object { $_.affected_master_ids } | Sort-Object -Unique); $key = $keys[0]; $c = $classByKey[$key]; $live = $liveByKey[$key.ToLowerInvariant()]; if (-not $live -and $c) { $live = [pscustomobject]@{ size_bytes = $c.size_bytes; etag = $c.etag; public_url = $c.public_url } }
    if ($items[0].disposition -eq 'duplicate/superseded - retain canonical') { continue }
    if ($items[0].disposition -eq 'accounting/inventory repair only') {
        $actionType = 'provenance_reconstruction_required'; $gate = 'blocked_on_provenance_research'; $target = @('project-state/master-inventory.json','project-state/r2-inventory.json'); $current = 'Live R2 object exists, but no authoritative master record or repository R2 accounting record is present.'; $proposed = 'After provenance is reconstructed, add one authoritative master record and reconcile one matching R2 inventory record; do not publish.'
        if ($ids.Count -gt 0) { $actionType = 'safe_r2_inventory_backfill'; $gate = 'safe_local_bookkeeping'; $target = @('project-state/r2-inventory.json'); $current = 'Validated master record exists and the live R2 object is absent from repository R2 inventory.'; $proposed = [pscustomobject]@{ key = $key; size_bytes = $live.size_bytes; etag = $live.etag; public_url = $live.public_url; source_master_ids = $ids } }
    } else {
        if ($ids.Count -gt 0 -and $c -and -not $c.repository_r2_record_present) {
            $actionType = 'safe_r2_inventory_backfill_without_publication'; $gate = 'safe_local_bookkeeping'; $target = @('project-state/r2-inventory.json'); $current = 'Validated master record and live R2 object exist, but the repository R2 inventory record is absent; the decision explicitly withholds publication.'; $proposed = [pscustomobject]@{ key = $key; size_bytes = $live.size_bytes; etag = $live.etag; public_url = $live.public_url; source_master_ids = $ids; publication = 'no-op' }
        } else { $actionType = 'no_op_retain_intentionally_unpublished'; $gate = 'no_action'; $target = @(); $current = 'Decision explicitly retains the object unpublished; no publication action is authorized.'; $proposed = 'No local publication change.' }
    }
    $actions.Add([pscustomobject]@{ action_id = ('repair-' + ($actions.Count + 1).ToString('000')); action_type = $actionType; safety_gate = $gate; covered_issue_group_ids = @($items.issue_group_id); affected_master_ids = $ids; affected_r2_keys = $keys; target_files = $target; current_state = $current; proposed_state = $proposed; evidence = @($items | ForEach-Object { $_.case_specific_evidence; $_.rationale }); proposed_follow_up = @($items.proposed_follow_up) })
}

$duplicateItems = @($decisions | Where-Object disposition -eq 'duplicate/superseded - retain canonical')
if ($duplicateItems.Count) {
    $keys = @($duplicateItems | ForEach-Object affected_r2_keys | Sort-Object -Unique); $canonical = 'transportation/transportation-plans/mrmpo-unified-planning-work-program-ffy-2027-2028.pdf'; $noncanonical = 'transportation/transportation-plans/mrmppo-unified-planning-work-program-ffy-2027-2028.pdf'
    $actions.Add([pscustomobject]@{ action_id = ('repair-' + ($actions.Count + 1).ToString('000')); action_type = 'duplicate_relationship_repair_no_storage_change'; safety_gate = 'no_action_until_explicit_storage_authorization'; covered_issue_group_ids = @($duplicateItems.issue_group_id); affected_master_ids = @($duplicateItems.affected_master_ids | Sort-Object -Unique); affected_r2_keys = $keys; target_files = @('project-state/master-inventory.json','project-state/r2-inventory.json'); current_state = [pscustomobject]@{ sha256_duplicate = $true; references = @($keys | ForEach-Object { [pscustomobject]@{ key = $_; live_r2 = $r2ByKey[$_]; repository_r2_inventory = [bool]($r2ByKey[$_]); master_records = @($duplicateItems | Where-Object { $_.affected_r2_keys -contains $_ } | ForEach-Object affected_master_ids) } }) }; proposed_state = [pscustomobject]@{ canonical_key = $canonical; noncanonical_key = $noncanonical; canonical_action = 'no-op retain'; noncanonical_action = 'label as exact future R2 deletion candidate only'; deletion_requires_explicit_authorization = $true }; evidence = @($duplicateItems.rationale); proposed_follow_up = 'Reconcile duplicate/superseded metadata locally only after authorization; never delete during this dry run.' })
}

$allGroupIds = @($decisions.issue_group_id | Sort-Object -Unique); $manifest = [pscustomobject]@{ schema_version = '1.0'; generated_at = (Get-Date).ToUniversalTime().ToString('o'); dry_run = $true; execution_performed = $false; source_decision_artifact = $DecisionPath; source_classification_artifact = $ClassificationPath; source_r2_inventory = $R2InventoryPath; summary = [pscustomobject]@{ decision_groups = $allGroupIds.Count; consolidated_actions = $actions.Count; safe_local_bookkeeping_repairs = @($actions | Where-Object safety_gate -eq 'safe_local_bookkeeping').Count; provenance_reconstruction_cases = @($actions | Where-Object safety_gate -eq 'blocked_on_provenance_research').Count; no_action_retained_objects = @($actions | Where-Object safety_gate -eq 'no_action').Count; duplicate_noncanonical_objects = 1; exact_future_r2_deletion_candidates = 1; unexpected_editorial_judgment_cases = @($actions | Where-Object safety_gate -eq 'requires_editorial_judgment').Count }; coverage = [pscustomobject]@{ decision_group_ids = $allGroupIds; covered_by_actions = @($actions.covered_issue_group_ids | Sort-Object -Unique); missing = @($allGroupIds | Where-Object { @($actions.covered_issue_group_ids) -notcontains $_ }); duplicated_coverage = @($actions.covered_issue_group_ids | Group-Object | Where-Object Count -gt 1 | ForEach-Object Name) }; actions = @($actions) }
$enc = New-Object System.Text.UTF8Encoding($false); [IO.File]::WriteAllText((Join-Path (Get-Location) $OutputPath), ($manifest | ConvertTo-Json -Depth 20), $enc); Write-Output ("Generated dry-run manifest with {0} consolidated actions covering {1} decision groups." -f $actions.Count,$allGroupIds.Count)

