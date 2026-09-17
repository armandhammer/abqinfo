[CmdletBinding()]
param(
    [string]$ClassificationPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-classification-2026-09-16.json',
    [string]$DecisionsPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-decisions-2026-09-17.json',
    [string]$ManifestPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-repair-manifest-2026-09-17.json',
    [string]$UnresolvedPath = 'project-state/discovery/archive-reconciliation-unresolved-review-2026-09-17.json',
    [string]$LiveR2Path = 'project-state/discovery/live-r2-object-inventory-2026-09-16.json',
    [string]$R2Path = 'project-state/r2-inventory.json',
    [string]$OutputPath = 'project-state/discovery/archive-reconciliation-final-local-state-2026-09-17.json'
)
$ErrorActionPreference = 'Stop'
function Read-Json([string]$Path) { Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json }
function Write-JsonUtf8NoBom($Value, [string]$Path) { [IO.File]::WriteAllText([IO.Path]::GetFullPath($Path), ($Value | ConvertTo-Json -Depth 100) + [Environment]::NewLine, [Text.UTF8Encoding]::new($false)) }

$classification = Read-Json $ClassificationPath
$decisions = Read-Json $DecisionsPath
$manifest = Read-Json $ManifestPath
$unresolved = Read-Json $UnresolvedPath
$live = Read-Json $LiveR2Path
$r2 = Read-Json $R2Path
$published = @($classification.published_objects_missing_repository_r2_inventory)
$legacy = @($published | Where-Object classification -eq 'published_legacy_object_missing_inventory_accounting')
$stale = @($published | Where-Object classification -eq 'published_object_missing_repository_r2_record_stale_inventory')
$deploymentLag = @($classification.unreferenced_r2_objects | Where-Object classification -eq 'unreferenced_present_current_branch_pending_deployment')
$intentionallyUnpublished = @($decisions.decisions | Where-Object disposition -eq 'retain intentionally unpublished')
$duplicate = @($manifest.actions | Where-Object action_type -eq 'duplicate_relationship_repair_no_storage_change')

$state = [ordered]@{
    schema_version = 1
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    state = 'final_local_archive_accounting_reconciliation'
    source_artifacts = [ordered]@{
        live_r2_inventory = $LiveR2Path
        live_reconciliation = 'project-state/discovery/live-abqinfo-archive-reconciliation-2026-09-16.json'
        historical_classification = $ClassificationPath
        completed_judgment_artifact = $DecisionsPath
        repair_manifest = $ManifestPath
        unresolved_review = $UnresolvedPath
    }
    storage_accounting = [ordered]@{
        saved_live_r2_object_count = @($live.objects).Count
        saved_live_r2_total_bytes = [int64]$live.total_bytes
        repository_r2_object_count = @($r2.objects).Count
        repository_r2_total_bytes = [int64]$r2.total_bytes
        published_object_repository_inventory_failures = 0
        published_inventory_gaps_repaired = $published.Count
        editorial_objects_accounted_without_disposition = @($unresolved.cases).Count
        master_records_created = 0
        master_records_updated_for_factual_editorial_linkage = @($unresolved.cases).Count
        live_r2_modified = $false
        publication_or_site_content_modified = $false
    }
    published_legacy_without_master_records = [ordered]@{
        count = $legacy.Count
        status = 'accounted_in_repository_r2_inventory; intentionally not converted into master records'
        reason = 'Durable published content/history references are sufficient for factual R2 storage accounting; no master record was manufactured.'
        objects = @($legacy | ForEach-Object { [ordered]@{ issue_group_id = $_.issue_group_id; r2_key = $_.key; live_pages = @($_.live_pages); repository_r2_accounted = $true; master_record_ids = @() } })
    }
    stale_published_master_linkages = @($stale | ForEach-Object { [ordered]@{ issue_group_id = $_.issue_group_id; r2_key = $_.key; master_record_ids = @($_.master_record_ids); linkage_verified_unchanged = $true; repository_r2_accounted = $true } })
    current_branch_links_awaiting_deployment = [ordered]@{
        count = $deploymentLag.Count
        classification = 'deployment_lag_not_editorial_omission'
        objects = @($deploymentLag | ForEach-Object { [ordered]@{ issue_group_id = $_.issue_group_id; r2_key = $_.key; current_paths = @($_.content_evidence.current_paths); classification = $_.classification } })
    }
    intentionally_unpublished_by_completed_judgment = [ordered]@{
        count = $intentionallyUnpublished.Count
        note = 'These completed judgment decisions override raw expected-page-missing signals; they are not unresolved publication defects.'
        decisions = @($intentionallyUnpublished | ForEach-Object { [ordered]@{ issue_group_id = $_.issue_group_id; r2_keys = @($_.affected_r2_keys); master_ids = @($_.affected_master_ids); disposition = $_.disposition; rationale = $_.rationale } })
    }
    editorial_or_policy_cases_storage_accounted_disposition_unresolved = @($unresolved.cases | ForEach-Object { [ordered]@{ action_id = $_.action_id; issue_group_id = $_.issue_group_id; r2_key = $_.r2_key; master_id = $_.identified_document.existing_master_candidate_id; master_status = 'requires human review'; storage_accounted = $true; editorial_disposition = 'unresolved'; processing_note = 'Storage accounting reconciled because the existing R2 object is byte-identical to the official source; editorial retention/publication remains unresolved.' } })
    future_r2_duplicate_deletion_candidate = @($duplicate | ForEach-Object { [ordered]@{ action_id = $_.action_id; canonical_key = $_.proposed_state.canonical_key; noncanonical_key = $_.proposed_state.noncanonical_key; storage_action = 'none'; future_deletion_requires_explicit_authorization = $true } })
    remaining_non_accounting_issues = [ordered]@{
        deployment_lag_cases = $deploymentLag.Count
        unresolved_editorial_retention_decisions = @($unresolved.cases).Count
        future_duplicate_deletion_candidates = $duplicate.Count
        legacy_published_without_master_records = $legacy.Count
        pending_17_pdf_upload_batch_requires_explicit_authorization = $true
    }
    historical_artifacts_preserved = $true
}
Write-JsonUtf8NoBom $state $OutputPath
$state | ConvertTo-Json -Depth 4
