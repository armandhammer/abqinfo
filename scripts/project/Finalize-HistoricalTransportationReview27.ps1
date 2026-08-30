[CmdletBinding()]
param([string]$InventoryPath = 'project-state/master-inventory.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$openStatuses = @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned')
$now = (Get-Date).ToUniversalTime().ToString('o')
$changed = [System.Collections.Generic.List[object]]::new()

function Set-TerminalStatus {
  param([string]$Id,[string]$Status,[string]$Reason,[string]$SupersededBy = '')
  $candidate = @($inventory.candidates | Where-Object id -eq $Id)
  if ($candidate.Count -ne 1) { throw "Expected one candidate for '$Id'; found $($candidate.Count)." }
  if ($candidate[0].status -notin $openStatuses) { return }
  $candidate[0].status = $Status
  $candidate[0].exclusion_reason = $Reason
  $candidate[0].validation_status = "terminal review decision: $Status"
  $candidate[0].processing_notes = @($candidate[0].processing_notes) + @($Reason) | Sort-Object -Unique
  if ($SupersededBy) {
    if (-not $candidate[0].PSObject.Properties['superseded_by']) { $candidate[0] | Add-Member -NotePropertyName superseded_by -NotePropertyValue $SupersededBy }
    else { $candidate[0].superseded_by = $SupersededBy }
  }
  $candidate[0].updated_at = $now
  $changed.Add([pscustomobject]@{id=$Id;status=$Status;title=$candidate[0].title})
}

# Folder-catalog artifacts duplicate the authoritative records discovered from the project page.
$montanoDuplicates = @{
  'src-9b11ec353e6dfd38' = 'src-26532dcb33a27b7d'
  'src-ed8aff10c8d03211' = 'src-f93f8f11481c3c74'
  'src-53a33163e6fc47e9' = 'src-16b14a4f0b57f61e'
  'src-6c4f7a6d3f8edc7d' = 'src-16b14a4f0b57f61e'
  'src-bd137d3312489887' = 'src-203fb37e4964e658'
  'src-8e8f0fe6bb5b0c7a' = 'src-17d49e3ef030ed1a'
  'src-f8bc729b113fa5ab' = 'src-922fcd8ff3e7ab91'
  'src-0dca8d20d8314459' = 'src-1a82c77452c85991'
  'src-b9129498bd3de28e' = 'src-26532dcb33a27b7d'
}
foreach ($pair in $montanoDuplicates.GetEnumerator()) {
  Set-TerminalStatus $pair.Key 'duplicate' 'Folder-catalog link duplicates the authoritative project-page record; the substantive document is archived and validated.' $pair.Value
}
Set-TerminalStatus 'src-d0241152d91ff633' 'superseded' 'The separately published cover is preserved within the complete archived Wilson corridor study.' 'src-26532dcb33a27b7d'
Set-TerminalStatus 'src-64984794d0aec1ab' 'superseded' 'The separately published table of contents is preserved within the complete archived Wilson corridor study.' 'src-26532dcb33a27b7d'
Set-TerminalStatus 'src-b241a8bc662f76d9' 'superseded' 'The separately published cover is preserved within the complete archived Wilson corridor study.' 'src-26532dcb33a27b7d'
Set-TerminalStatus 'src-285faabe74599255' 'superseded' 'The separately published table of contents is preserved within the complete archived Wilson corridor study.' 'src-26532dcb33a27b7d'
Set-TerminalStatus 'src-08957b9de48d51cc' 'superseded' 'The presentation summarizes material preserved in the complete archived Hall transportation alternatives analysis.' 'src-16b14a4f0b57f61e'

# The City published North Fourth Street chapters separately; complete archived volumes preserve them in context.
Set-TerminalStatus 'src-218eeed4ce307c7f' 'duplicate' 'Folder-catalog page duplicates the authoritative North Fourth Street plan records already archived and validated.' 'src-6479e8efc5bcc2b6'
$northFourth = @($inventory.candidates | Where-Object {
  $_.status -in $openStatuses -and $_.parent_url -like 'https://www.cabq.gov/council/documents/north-fourth-street-plan*'
})
foreach ($candidate in $northFourth) {
  Set-TerminalStatus $candidate.id 'superseded' 'Separately published chapter, map, or cover is preserved in context within the complete archived North Fourth Street plan volumes.' 'src-6479e8efc5bcc2b6'
}

# Meeting logistics add little retrieval value after the final report and substantive evidence have been retained.
$taskForce = @($inventory.candidates | Where-Object {
  $_.status -in $openStatuses -and $_.parent_url -eq 'https://www.cabq.gov/council/projects/completed-projects/2008/21st-century-transportation-task-force'
})
foreach ($candidate in $taskForce) {
  if ($candidate.title -match '(?i)agenda|minutes') {
    Set-TerminalStatus $candidate.id 'excluded' 'Meeting agenda or minutes are lower-information administrative records; the final report and substantive technical evidence are retained.'
  } elseif ($candidate.title -match '(?i)streetcar.*(leland|hdr)') {
    Set-TerminalStatus $candidate.id 'superseded' 'Interim streetcar presentation is superseded by the archived comprehensive Streetcar Evaluation Summary, cost/ridership report, and appendices.' 'src-e5a9cf3e3195107d'
  } elseif ($candidate.id -eq 'src-9d33fe15a313fb8c') {
    Set-TerminalStatus $candidate.id 'superseded' 'Deadline-extension ordinance is procedural; the enabling ordinance and completed final report preserve the substantive task-force record.' 'src-5c9ad39184c0e9c3'
  }
}

# Preserve approved cross-listings for the two operational records.
foreach ($id in @('src-bdc584620c51dfa1','src-25c15ede0314ba7a')) {
  $candidate = @($inventory.candidates | Where-Object id -eq $id)[0]
  $candidate.implementation_locations = @('content/transportation/operations-data.md','content/transportation/transportation-plans.md')
  $candidate.processing_notes = @($candidate.processing_notes) + @('Cross-listed in the 2008 task-force record because it supplies historical planning context.') | Sort-Object -Unique
  $candidate.updated_at = $now
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = $now
$next = @($inventory.candidates | Where-Object {
  $_.status -in $openStatuses -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed')
} | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { $next[0].id } else { $null }

$json = $inventory | ConvertTo-Json -Depth 12
$fullPath = [IO.Path]::GetFullPath($InventoryPath)
$temporaryPath = "$fullPath.tmp-$PID"
[IO.File]::WriteAllText($temporaryPath, $json, [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force

[pscustomobject]@{
  terminal_decisions = $changed.Count
  excluded = @($changed | Where-Object status -eq 'excluded').Count
  duplicate = @($changed | Where-Object status -eq 'duplicate').Count
  superseded = @($changed | Where-Object status -eq 'superseded').Count
  next_pending = $inventory.next_pending_id
} | ConvertTo-Json -Compress
