[CmdletBinding()]
param(
    [string]$MasterInventoryPath = 'project-state/master-inventory.json',
    [string]$OutputPath = 'project-state/discovery/dpm-executive-committee-consolidation-manifest-2026-09-17.json'
)

$ErrorActionPreference = 'Stop'

function Get-MeetingDate {
    param([object]$Candidate)

    if ($Candidate.id -eq 'src-030f7d2a680a31d4') { return '2014-11-19' }
    if ($Candidate.id -eq 'src-f6feb3549d055097') { return '2018-04-04' }
    if ($Candidate.id -eq 'src-48eb68305e18d8ad') { return '2018-03-07' }
    if ($Candidate.id -eq 'src-a8dda335fb901049') { return '2015-04-15' }
    if ($Candidate.id -eq 'src-f2716dd03961455e') { return '2015-05-20' }
    if ($Candidate.date) { return [string]$Candidate.date }
    throw "No deterministic meeting date is available for $($Candidate.id)."
}

$master = Get-Content -LiteralPath $MasterInventoryPath -Raw | ConvertFrom-Json
$years = 2014..2018
$additionalAgendaIds = @('src-a8dda335fb901049','src-f2716dd03961455e','src-48eb68305e18d8ad')
$components = @(
    $master.candidates |
        Where-Object {
            ($_.r2_key -match '^development-land-use/development-process/cabq-dpm-executive-committee-(minutes|agenda)-20(14|15|16|17|18)' -or $additionalAgendaIds -contains $_.id) -and
            $_.id -ne 'src-f6feb3549d055097'
        } |
        ForEach-Object {
            $date = Get-MeetingDate $_
            $isAgenda = $_.id -in $additionalAgendaIds -or $_.title -match '(?i)agenda' -or $_.direct_file_url -match '(?i)agenda'
            [pscustomobject][ordered]@{
                source_master_id = $_.id
                meeting_date = $date
                document_kind = if ($isAgenda) { 'agenda' } else { 'approved_minutes' }
                display_label = if ($isAgenda) { "Agenda - $date" } else { "Minutes - $date" }
                source_url = $_.direct_file_url
                existing_r2_key = $_.r2_key
                local_path = $_.local_path
                source_page_count = $null
                inclusion = 'include'
                notes = 'Existing City-source PDF and factual R2 object; inclusion in an annual packet does not alter the original record or its prior status.'
            }
        }
)

$aprilAgenda = $master.candidates | Where-Object id -eq 'src-f6feb3549d055097'
$components += [pscustomobject][ordered]@{
    source_master_id = $aprilAgenda.id
    meeting_date = '2018-04-04'
    document_kind = 'agenda_approved_minutes_not_located'
    display_label = 'Agenda - approved minutes not located - 2018-04-04'
    source_url = $aprilAgenda.direct_file_url
    existing_r2_key = $aprilAgenda.r2_key
    local_path = $null
    source_page_count = $null
    inclusion = 'include'
    notes = 'Official agenda. Its inclusion does not establish that the scheduled meeting occurred and is not a minutes substitute.'
}

$components += [pscustomobject][ordered]@{
    source_master_id = 'src-7e7af2af147d96d7'
    meeting_date = '2018-03-21'
    document_kind = 'agenda_approved_minutes_not_located'
    display_label = 'Agenda - approved minutes not located - 2018-03-21'
    source_url = 'https://documents.cabq.gov/planning/development-process-manual/development-process-manual-executive-committee-meeting-agenda-march-21-2018.pdf'
    existing_r2_key = $null
    local_path = $null
    source_page_count = $null
    inclusion = 'include'
    notes = 'Official agenda retained under the same missing-minutes rule; no individual R2 object exists and this campaign does not authorize one.'
}

$annualPackets = foreach ($year in $years) {
    $yearComponents = @($components | Where-Object { $_.meeting_date -like "$year-*" } | Sort-Object meeting_date, @{ Expression = { if ($_.document_kind -match '^agenda') { 0 } else { 1 } } }, source_master_id)
    [pscustomobject][ordered]@{
        year = $year
        proposed_filename = "cabq-dpm-executive-committee-agendas-minutes-$year.pdf"
        proposed_r2_key = "development-land-use/development-process/cabq-dpm-executive-committee-agendas-minutes-$year.pdf"
        proposed_public_url = "https://files.abqinfo.com/development-land-use/development-process/cabq-dpm-executive-committee-agendas-minutes-$year.pdf"
        component_count = $yearComponents.Count
        components = $yearComponents
        packet_policy = 'Chronological annual compilation. Original pages are preserved; a minimal generated contents page identifies each component. Agenda-only components remain explicitly labeled and do not establish meeting occurrence.'
    }
}

$excluded = @(
    [pscustomobject][ordered]@{ source_master_id = 'src-2448a4409efca23b'; source_url = 'https://documents.cabq.gov/planning/development-process-manual/DPM-2015April15DPExecMinutes.pdf'; disposition = 'exclude_duplicate_source'; reason = 'Duplicate delivery of the included April 15, 2015 minutes.' },
    [pscustomobject][ordered]@{ source_master_id = 'src-28ce1d8748abb9a2'; source_url = 'https://documents.cabq.gov/planning/development-process-manual/Development%20Process%20Manual%20Executive%20Committee%20Agenda_February-25-2025.pdf'; disposition = 'outside_legacy_consolidation_scope'; reason = 'Later unaccounted record; no accounting or editorial decision is authorized in this campaign.' },
    [pscustomobject][ordered]@{ source_master_id = 'src-89d7a6448976c52e'; source_url = 'https://documents.cabq.gov/planning/development-process-manual/DPM%20Executive%20Committee%20Agenda%20%2012-4-2025.pdf'; disposition = 'outside_legacy_consolidation_scope'; reason = 'Later unaccounted record; no accounting or editorial decision is authorized in this campaign.' },
    [pscustomobject][ordered]@{ source_master_id = 'src-04dfcbe1dcde70f8'; source_url = 'https://documents.cabq.gov/planning/development-process-manual/DPM%20Executive%20Committee%20Agenda%20%2012-11-2025.pdf'; disposition = 'outside_legacy_consolidation_scope'; reason = 'Later unaccounted record; no accounting or editorial decision is authorized in this campaign.' },
    [pscustomobject][ordered]@{ source_master_id = 'src-100dcafff14a7b22'; source_url = 'https://documents.cabq.gov/planning/development-process-manual/December%204%20and%20December%2011%202025%20DPM%20Executive%20Committee%20Meeting%20Minutes.pdf'; disposition = 'outside_legacy_consolidation_scope'; reason = 'Later unaccounted record remains requires human review; no new decision is authorized in this campaign.' },
    [pscustomobject][ordered]@{ source_master_id = 'src-dc3a192d194d3d65'; source_url = 'https://documents.cabq.gov/planning/development-process-manual/DPM%20Executive%20Committee%20Agenda%205-4-2026.pdf'; disposition = 'outside_legacy_consolidation_scope'; reason = 'Later unaccounted record remains requires human review; no new decision is authorized in this campaign.' }
)

$manifest = [pscustomobject][ordered]@{
    artifact_type = 'dpm_executive_committee_annual_consolidation_manifest'
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    scope = 'Already represented 2014-2018 Development Process Manual Executive Committee records, including distinct agenda and approved-minutes records for the same meeting date, plus the March 21, 2018 official agenda needed to complete the year under the approved missing-minutes policy.'
    source_inventory = [pscustomobject][ordered]@{
        master_inventory_path = $MasterInventoryPath
        existing_accounted_component_count = 40
        external_read_only_component_count = 0
    }
    annual_packets = $annualPackets
    excluded_or_out_of_scope_records = $excluded
    prohibitions = @('No R2 upload', 'No live R2 mutation', 'No individual original-object deletion', 'No deployment')
}

$directory = Split-Path -Parent $OutputPath
if ($directory) { New-Item -ItemType Directory -Force -Path $directory | Out-Null }
$json = $manifest | ConvertTo-Json -Depth 12
[System.IO.File]::WriteAllText([System.IO.Path]::GetFullPath($OutputPath), "$json`r`n", [System.Text.UTF8Encoding]::new($false))
Write-Output "Wrote $OutputPath with $($annualPackets.Count) annual packet(s) and $($components.Count) included component(s)."
