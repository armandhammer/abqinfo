[CmdletBinding()]
param(
    [string]$PacketPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-review-packet-2026-09-16.json',
    [string]$DecisionPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-decisions-2026-09-17.json',
    [string]$ManifestPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-repair-manifest-2026-09-17.json',
    [string]$R2InventoryPath = 'project-state/r2-inventory.json'
)
$ErrorActionPreference = 'Stop'
$packet = Get-Content $PacketPath -Raw | ConvertFrom-Json
$decision = Get-Content $DecisionPath -Raw | ConvertFrom-Json
$manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$r2 = Get-Content $R2InventoryPath -Raw | ConvertFrom-Json
$liveR2 = Get-Content 'project-state/discovery/live-r2-object-inventory-2026-09-16.json' -Raw | ConvertFrom-Json
$liveByKey = @{}; foreach ($o in $liveR2.objects) { $liveByKey[$o.key.ToLowerInvariant()] = $o }
$expected = @($packet.cases.issue_group_id | Sort-Object -Unique)
$decided = @($decision.decisions.issue_group_id | Sort-Object -Unique)
$covered = @($manifest.coverage.covered_by_actions | Sort-Object -Unique)
$bad = @($expected + $decided + $covered | Where-Object { $_ -notmatch '^issue-\d{4}$' } | Sort-Object -Unique)
if ($bad.Count) { throw "Malformed issue IDs: $($bad -join ', ')" }
if ((Compare-Object $expected $decided).Count -ne 0 -or (Compare-Object $decided $covered).Count -ne 0) { throw 'Packet, decision, and manifest issue-ID sets do not match exactly.' }
if ($manifest.summary.decision_groups -ne 44 -or $manifest.coverage.missing.Count -ne 0 -or $manifest.coverage.duplicated_coverage.Count -ne 0) { throw 'Manifest coverage is incomplete or duplicated.' }
if ((Compare-Object $expected @($manifest.coverage.decision_group_ids | Sort-Object -Unique)).Count -ne 0) { throw 'Manifest decision-group identity set does not match the packet.' }
if (-not $manifest.dry_run -or $manifest.execution_performed) { throw 'Manifest is not dry-run only.' }
foreach ($a in @($manifest.actions | Where-Object safety_gate -eq 'safe_local_bookkeeping')) {
    $required = @('key','size_bytes','last_modified','etag','storage_class','public_url')
    if (@($a.affected_master_ids).Count -eq 0 -or @($a.source_master_ids).Count -eq 0 -or (Compare-Object @($a.affected_master_ids | Sort-Object -Unique) @($a.source_master_ids | Sort-Object -Unique)).Count -ne 0) { throw "Safe backfill $($a.action_id) lacks separately recorded master linkage." }
    if ($null -eq $a.proposed_r2_object -or (Compare-Object $required @($a.proposed_r2_object.PSObject.Properties.Name | Sort-Object)).Count -ne 0) { throw "Safe backfill $($a.action_id) does not contain exactly the six R2 inventory object fields." }
    $live = $liveByKey[$a.proposed_r2_object.key.ToLowerInvariant()]
    if ($null -eq $live) { throw "Safe backfill $($a.action_id) has no matching saved live-R2 object." }
    foreach ($field in $required) { if ([string]$a.proposed_r2_object.$field -ne [string]$live.$field) { throw "Safe backfill $($a.action_id) does not exactly match live-R2 field $field." } }
    if ($a.proposed_r2_object.size_bytes -isnot [int] -and $a.proposed_r2_object.size_bytes -isnot [long] -and $a.proposed_r2_object.size_bytes -isnot [double]) { throw "Safe backfill $($a.action_id) has invalid size_bytes type." }
}
Write-Output 'Repair manifest validation passed: exact identity coverage, dry-run safety, metadata completeness, and R2 schema fields are valid.'
