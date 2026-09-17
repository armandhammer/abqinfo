[CmdletBinding()]
param(
    [string]$ManifestPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-repair-manifest-2026-09-17.json',
    [string]$VerificationPath = 'project-state/discovery/archive-reconciliation-provenance-verification-2026-09-17.json',
    [string]$InventoryPath = 'project-state/master-inventory.json',
    [string]$OutputPath = 'project-state/discovery/archive-reconciliation-provenance-2026-09-17.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$requiresJudgment = @{
    'repair-001' = 'The official EPC hearing-notification packet is byte-identical, but its saved 2003 bond research requires an editorial decision on preserving EPC decision notifications as a document class.'
    'repair-017' = 'The official WIZ map is byte-identical, but its saved 2003 bond research identifies it as appendix page B-6 of an unlocated parent plan and requires an editorial decision on preserving the standalone map.'
    'repair-020' = 'The official April 4, 2018 agenda is byte-identical, but the saved DPM research requires an exhaustive missing-minutes review and a missing-minutes-policy decision before accounting or preservation.'
}
$titles = @{
    'repair-001' = '2003 Environmental Planning Commission Hearing Recommendations and Decision Notifications'; 'repair-007' = '2003 General Obligation Bond Program Frequently Asked Questions'; 'repair-008' = '2003 General Obligation Bond Summary by Purpose'; 'repair-017' = 'Water Master Plan Infrastructure Zone Map'; 'repair-019' = '2003 General Obligation Bond Operating and Maintenance Cost Impacts'; 'repair-020' = 'Development Process Manual Executive Committee Agenda, April 4, 2018'
}

$manifest = Get-Content -Raw -Encoding UTF8 $ManifestPath | ConvertFrom-Json
$verification = Get-Content -Raw -Encoding UTF8 $VerificationPath | ConvertFrom-Json
$inventory = Get-Content -Raw -Encoding UTF8 $InventoryPath | ConvertFrom-Json
$actions = @($manifest.actions | Where-Object safety_gate -eq 'blocked_on_provenance_research' | Sort-Object action_id)
if ($actions.Count -ne 27 -or @($verification.results).Count -ne 27) { throw 'Expected exactly 27 provenance actions and verification results.' }
$verificationByAction = @{}; foreach ($result in @($verification.results)) { $verificationByAction[[string]$result.action_id] = $result }
$masterById = @{}; foreach ($candidate in @($inventory.candidates)) { $masterById[[string]$candidate.id] = $candidate }

$cases = foreach ($action in $actions) {
    $verificationResult = $verificationByAction[[string]$action.action_id]
    if ($null -eq $verificationResult -or -not $verificationResult.byte_identical) { throw "No byte-identical verification for $($action.action_id)." }
    $candidate = $masterById[[string]$verificationResult.master_candidate_id]
    if ($null -eq $candidate) { throw "Missing master candidate for $($action.action_id)." }
    $isJudgment = $requiresJudgment.ContainsKey([string]$action.action_id)
    $identifiedTitle = if ($titles.ContainsKey([string]$action.action_id)) { $titles[[string]$action.action_id] } elseif ([string]$candidate.date -match '^\d{4}-\d{2}-\d{2}$') { 'Development Process Manual Executive Committee Minutes, ' + ([datetime]$candidate.date).ToString('MMMM d, yyyy') } else { [string]$candidate.title }
    $conclusion = if ($isJudgment) { 'Byte-identical official City original is identified, but the existing master record remains requires human review for the stated editorial/policy reason.' } else { 'Existing public R2 object is byte-identical to the official City original already represented by the identified master record; deterministic accounting linkage is safe and does not authorize publication.' }
    $canonical = if ($isJudgment) { 'Official original identified; canonical publication/preservation relationship remains unresolved.' } elseif ($candidate.status -eq 'excluded') { 'Canonical official original for accounting; intentionally excluded from publication under the recorded review decision.' } else { 'Canonical official original represented by the existing master record.' }
    [ordered]@{
        action_id = [string]$action.action_id
        issue_group_id = [string](@($action.covered_issue_group_ids)[0])
        r2_key = [string](@($action.affected_r2_keys)[0])
        identified_document = [ordered]@{ title = $identifiedTitle; date_or_version = [string]$candidate.date; issuing_organization = 'City of Albuquerque'; existing_master_candidate_id = [string]$candidate.id; existing_master_status = [string]$candidate.status }
        authoritative_source_url = [string]$candidate.source_url
        authoritative_direct_file_url = [string]$candidate.direct_file_url
        repository_evidence_used = @('project-state/master-inventory.json', 'project-state/discovery/live-abqinfo-archive-reconciliation-repair-manifest-2026-09-17.json', 'project-state/discovery/live-r2-object-inventory-2026-09-16.json', 'case-specific prior DPM or 2003 bond research artifact recorded in the manifest')
        external_read_only_evidence_used = [ordered]@{ verification_artifact = $VerificationPath; official_and_public_r2_byte_identical = $true; official_size_bytes = [int64]$verificationResult.official_file.size_bytes; official_sha256 = [string]$verificationResult.official_file.checksum_sha256; public_r2_size_bytes = [int64]$verificationResult.public_r2_file.size_bytes; public_r2_sha256 = [string]$verificationResult.public_r2_file.checksum_sha256 }
        provenance_conclusion = $conclusion
        confidence = if ($isJudgment) { 'high for source-object identity; unresolved for editorial/policy disposition' } else { 'high' }
        limitations = if ($isJudgment) { $requiresJudgment[[string]$action.action_id] } else { 'No publication decision is implied by local accounting repair.' }
        canonical_noncanonical_relationship = $canonical
        result = if ($isJudgment) { 'requires_user_or_higher_judgment' } else { 'provenance_reconstructed_safe_for_accounting' }
        exact_proposed_local_accounting_action = if ($isJudgment) { [ordered]@{ action = 'none'; reason = $requiresJudgment[[string]$action.action_id] } } else { [ordered]@{ action = 'update_existing_master_r2_linkage_and_add_r2_inventory_object'; master_candidate_id = [string]$candidate.id; r2_object = $verificationResult.saved_live_r2_object; publication = 'no-op' } }
        later_external_or_storage_action_requires_explicit_authorization = $true
    }
}
$counts = [ordered]@{ provenance_reconstructed_safe_for_accounting = @($cases | Where-Object result -eq 'provenance_reconstructed_safe_for_accounting').Count; provenance_reconstructed_but_noncanonical = @($cases | Where-Object result -eq 'provenance_reconstructed_but_noncanonical').Count; provenance_incomplete = @($cases | Where-Object result -eq 'provenance_incomplete').Count; requires_user_or_higher_judgment = @($cases | Where-Object result -eq 'requires_user_or_higher_judgment').Count }
$output = [ordered]@{ schema_version = 1; generated_at = (Get-Date).ToUniversalTime().ToString('o'); source_manifest = $ManifestPath; source_verification = $VerificationPath; case_count = @($cases).Count; result_counts = $counts; cases = @($cases) }
$fullPath = [IO.Path]::GetFullPath($OutputPath); $temporaryPath = "$fullPath.tmp-$PID"; [IO.File]::WriteAllText($temporaryPath, ($output | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false)); Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
Write-Output ("Created provenance artifact for {0} cases: {1} safe, {2} judgment required." -f $output.case_count, $counts.provenance_reconstructed_safe_for_accounting, $counts.requires_user_or_higher_judgment)
