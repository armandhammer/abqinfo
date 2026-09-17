[CmdletBinding()]
param(
    [string]$PacketPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-review-packet-2026-09-16.json',
    [string]$MasterInventoryPath = 'project-state/master-inventory.json',
    [string]$OutputPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-decisions-2026-09-17.json'
)

$ErrorActionPreference = 'Stop'
$packet = Get-Content $PacketPath -Raw | ConvertFrom-Json
$master = Get-Content $MasterInventoryPath -Raw | ConvertFrom-Json
$byId = @{}
foreach ($record in $master.candidates) { $byId[$record.id] = $record }
$canonicalMrmpo = 'transportation/transportation-plans/mrmpo-unified-planning-work-program-ffy-2027-2028.pdf'
$noncanonicalMrmppo = 'transportation/transportation-plans/mrmppo-unified-planning-work-program-ffy-2027-2028.pdf'

$decisions = foreach ($case in $packet.cases) {
    $ids = @($case.master_record_ids)
    $records = @($ids | ForEach-Object { $byId[$_] } | Where-Object { $_ })
    $pages = @($records | ForEach-Object { @($_.implementation_locations) + @($_.implementation_location) } | Where-Object { $_ } | Sort-Object -Unique)
    $evidence = @()
    foreach ($record in $records) {
        $evidence += [pscustomobject]@{
            master_id = $record.id
            status = $record.status
            title = $record.title
            source_url = $record.source_url
            direct_file_url = $record.direct_file_url
            validation_status = $record.validation_status
            implementation_locations = @($record.implementation_locations)
            processing_notes = @($record.processing_notes)
        }
    }

    if ($case.classification -eq 'unreferenced_storage_duplicate_of_other_r2_key') {
        $decision = 'duplicate/superseded - retain canonical object'
        $rationale = 'Both R2 keys have the same recorded SHA-256. MRMPO is the established acronym and the correctly spelled key recorded as the original authoritative upload; MRM PPO is explicitly labeled a mistyped duplicate master record.'
        $followup = 'Retain the canonical MRMPO key. Treat the MRM PPO key as a probable R2 deletion candidate only after a separately authorized storage cleanup and inventory reconciliation.'
        $canonical = $canonicalMrmpo
        $relatedKeys = @($canonicalMrmpo, $noncanonicalMrmppo)
    }
    elseif ($case.classification -in @('unreferenced_known_master_publication_intent_unresolved', 'expected_link_absent_from_repository_content')) {
        $decision = 'retain and publish'
        $rationale = 'The targeted master record is validated, uses an official City source, has an R2 key, and has an assigned implementation location. The saved processing notes describe a verified original suitable for the capital-spending batch.'
        $followup = 'In a future authorized content stage, add the archived and official links at the assigned page(s), reconcile r2-inventory accounting, and run normal page/build validation.'
        $canonical = $case.key
        $relatedKeys = @($case.key)
    }
    elseif ($case.key -like '*dpm-executive-committee-agenda-2018-04-04-approved-minutes-not-located.pdf') {
        $decision = 'retain and publish'
        $rationale = 'The filename preserves the missing-minutes qualification required by the agenda policy. It is a candidate for a clearly labeled official agenda record, not a substitute presented as minutes.'
        $followup = 'Before any visible use, create/reconcile a master record with the exhaustive minutes-search evidence, official source provenance, and the exact agenda label.'
        $canonical = $case.key
        $relatedKeys = @($case.key)
        $evidence += [pscustomobject]@{ artifact = 'project-state/discovery/dpm-draft-and-agenda-research-2026-09-11.json'; note = 'Saved DPM agenda/minutes research artifact.' }
    }
    else {
        $decision = 'retain but intentionally unpublished'
        $rationale = 'The live R2 object has no matching master or repository-inventory record and no current/origin content placement. Its filename indicates either a legacy DPM meeting record or a related 2003 capital-program source, but this review stage does not establish publishable provenance or placement.'
        $followup = 'Perform inventory/accounting repair and provenance confirmation before considering site placement. Do not delete based on this classification.'
        $canonical = $case.key
        $relatedKeys = @($case.key)
        if ($case.key -like '*dpm-executive-committee-*') {
            $evidence += [pscustomobject]@{ artifact = 'project-state/discovery/dpm-executive-committee-minutes-decisions-2026-09-11.json'; note = 'Use saved approved-minutes decisions and source validation to determine whether this legacy object belongs in a future inventory record.' }
        }
    }

    [pscustomobject]@{
        issue_group_id = $case.issue_group_id
        disposition = $decision
        rationale = $rationale
        affected_r2_keys = $relatedKeys
        canonical_r2_key = $canonical
        affected_master_ids = $ids
        affected_pages = $pages
        classifier_case = $case.classification
        classifier_reason = $case.review_reason
        content_evidence = $case.content_evidence
        targeted_master_evidence = $evidence
        proposed_follow_up = $followup
    }
}

$output = [pscustomobject]@{
    schema_version = '1.0'
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    source_review_packet = $PacketPath
    decision_counts = @($decisions | Group-Object disposition | ForEach-Object { [pscustomobject]@{ disposition = $_.Name; count = $_.Count } })
    decisions = @($decisions)
}
$json = $output | ConvertTo-Json -Depth 16
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText((Join-Path (Get-Location) $OutputPath), $json, $utf8NoBom)
Write-Output ("Recorded {0} decisions." -f @($decisions).Count)

