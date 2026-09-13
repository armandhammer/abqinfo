[CmdletBinding()]
param(
  [string]$AuditPath = 'project-state/discovery/post-pr132-content-quality-audit-2026-09-13.json',
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OutputPath = 'project-state/discovery/claude-consolidation-research-queue-2026-09-13.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$audit = Get-Content -Raw -Encoding UTF8 -LiteralPath $AuditPath | ConvertFrom-Json
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$slices = [System.Collections.Generic.List[object]]::new()

function Add-Slice([string]$Id, [string]$Title, [string]$Kind, $Documents, [string]$CompletenessScope, [int]$Priority) {
  $docs = @($Documents | Sort-Object date,title,candidate_id)
  if (-not $docs.Count) { return }
  $slices.Add([pscustomobject][ordered]@{
    slice_id = $Id
    priority = $Priority
    title = $Title
    kind = $Kind
    assigned_documents = @($docs | ForEach-Object {
      [pscustomobject][ordered]@{
        candidate_id = [string]$_.candidate_id
        date = [string]$_.date
        title = [string]$_.title
        source_url = [string]$_.source_url
        archive_url = [string]$_.r2_url
      }
    })
    completeness_scope = $CompletenessScope
    per_document_checkpoint_directory = "research/staging/claude-consolidation-checkpoints/$Id/items"
    slice_result_path = "project-state/discovery/claude-consolidation-$Id-2026-09-13.json"
  })
}

$failures = @($audit.documents | Where-Object { $_.quality_review.status -eq 'does not meet standalone standard' })
$questions = @($audit.documents | Where-Object { $_.quality_review.status -like 'questionable*' })

$dpm = @($failures | Where-Object { $_.quality_review.proposed_master_record -eq 'Development Process Manual Executive Committee Decisions, 2014-2018' })
foreach ($year in 2014..2018) {
  Add-Slice "dpm-$year" "DPM Executive Committee Minutes $year" 'annual committee minutes compilation research' @($dpm | Where-Object { [string]$_.date -match "^$year" }) "Exhaustively review the official DPM source for every scheduled $year meeting; identify missing approved minutes, cancellations, no-quorum meetings, agendas eligible under the missing-minutes policy, exact chronological order, and total compilation pages." (10 + ($year - 2014))
}

$masterOrder = [ordered]@{
  '2003 General Obligation Bond Program Master Record' = 20
  '2004 Street Bond Program History' = 21
  '2009 General Obligation Bond Program Master Record' = 22
  '2011 General Obligation Bond Program Master Record' = 23
  '2013 General Obligation Bond Program Master Record' = 24
  '2017 General Obligation Bond Program Master Record' = 25
  'Applicable capital-program master record' = 26
  'MRMPO Annual Listings of Obligations, FFY 2006-2009' = 40
  'Old Town Virtual Task Force Ranking Results, Topics 1-3' = 41
  'Urban Enhancement Trust Fund 2010-2011 Program and Funded Projects' = 42
}
foreach ($master in $masterOrder.Keys) {
  $slug = ($master.ToLowerInvariant() -replace '[^a-z0-9]+','-').Trim('-')
  $members = @($failures | Where-Object { $_.quality_review.proposed_master_record -eq $master })
  Add-Slice $slug $master 'historical program compilation research' $members "Review the complete official source family, not only assigned members. Identify omitted components, final/initial version relationships, duplicates, governing resolutions, chronological or topical order, section titles, and whether the compilation should be split before 100-150 pages." $masterOrder[$master]
}

$committeePatterns = [ordered]@{
  'gaatc' = 'Greater Albuquerque Active Transportation Committee.*Meeting Minutes'
  'gabac' = 'Greater Albuquerque Bicycling Advisory Committee.*Meeting Minutes'
  'gartc' = 'Greater Albuquerque Recreational Trails Committee Minutes'
}
$committeePriority = 60
foreach ($committee in $committeePatterns.Keys) {
  $members = @($inventory.candidates | Where-Object { $_.status -eq 'validated' -and $_.title -match $committeePatterns[$committee] } | ForEach-Object {
    [pscustomobject]@{candidate_id=$_.id;date=$_.date;title=$_.title;source_url=$_.source_url;r2_url=$_.r2_url}
  })
  $years = @($members | ForEach-Object { if ([string]$_.date -match '^(20\d{2})') { $Matches[1] } } | Sort-Object -Unique)
  foreach ($year in $years) {
    Add-Slice "$committee-$year" "$($committee.ToUpperInvariant()) Minutes $year" 'annual committee minutes compilation research' @($members | Where-Object { [string]$_.date -match "^$year" }) "Exhaustively review the committee's official calendar, archive, and OnBase records for every scheduled $year meeting; distinguish approved minutes from agendas, cancellations, and no-quorum meetings and calculate the complete annual compilation." $committeePriority
    $committeePriority++
  }
}

Add-Slice 'borderline-current-records' 'Borderline current and procedural records' 'successor and public-value research' $questions 'For each item, locate any newer official version, controlling full document, parent procedure, or natural consolidation family; recommend retain, consolidate, supersede, or archive-only with concrete evidence.' 80

$orderedSlices = @($slices | Sort-Object priority,slice_id)
$candidateIds = @($orderedSlices.assigned_documents.candidate_id)
if (@($candidateIds | Group-Object | Where-Object Count -gt 1).Count) { throw 'A candidate appears in more than one Claude slice.' }

$queue = [pscustomobject][ordered]@{
  schema_version = 1
  created_at = (Get-Date).ToUniversalTime().ToString('o')
  source_commit = (& git rev-parse HEAD).Trim()
  purpose = 'Checkpointed research supporting sparse historical-document consolidation; research only, with no inventory, R2, site, Git, PR, merge, or deployment writes.'
  resume_rule = 'Always scan the immutable per-document checkpoint paths and completed slice-result paths. Resume at the first missing assigned document in the lowest-priority unfinished slice. Never repeat a valid completed checkpoint.'
  checkpoint_rule = 'Write one complete JSON result immediately after each document or official-source meeting check. Use a temporary sibling file and rename only after valid JSON is complete. After every slice, write its self-contained slice result before starting another slice.'
  required_document_result_fields = @('slice_id','candidate_id','reviewed_at','title_on_document','date_on_document','page_count','size_bytes','checksum_sha256','official_source_checked','official_source_url','archive_url','visual_inspection_completed','substantive_summary','series_relationship','version_relationship','recommended_compilation_section','quality_recommendation','evidence','unresolved_questions')
  required_slice_result_fields = @('slice_id','completed_at','assigned_ids','completed_checkpoint_paths','official_source_family_reviewed','missing_records_checked','missing_records_results','ordered_members','total_pages','total_bytes','proposed_compilation_title','proposed_table_of_contents','recommended_publication_form','provenance_notes','unresolved_questions')
  safeguards = @('Claude research lane only','preserve every original and inventory history','no static document approved merely because it is authoritative','no inventory edits','no checkpoint edits outside assigned checkpoint tree','no R2 writes','no content edits','no Git operations','no PR, merge, or deployment')
  slice_count = $orderedSlices.Count
  assigned_document_count = $candidateIds.Count
  slices = $orderedSlices
}
$queue | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $OutputPath -Encoding utf8
$queue | Select-Object slice_count,assigned_document_count,source_commit,purpose | ConvertTo-Json -Compress
