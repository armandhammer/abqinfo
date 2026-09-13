[CmdletBinding()]
param(
  [string]$AuditPath = 'project-state/discovery/post-pr132-content-quality-audit-2026-09-13.json',
  [string]$ReportPath = 'project-state/discovery/post-pr132-content-quality-review-2026-09-13.md'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$audit = Get-Content -Raw -Encoding UTF8 -LiteralPath $AuditPath | ConvertFrom-Json

$archiveOnly = @{
  'src-089361e5a66d4fea' = 'Two-page visual with only 28 extractable words. It is valid source evidence, but the isolated design overview does not justify a public-facing record.'
  'src-4347bb9af15c89ba' = 'One-page request to initiate an investigation, without the investigation, findings, response, or resulting action. Preserve it in the archive but do not feature it alone.'
  'src-9642139286c8f411' = 'One-page, 38-word neighborhood stop-sign proposal without analysis, disposition, or implementation record. It does not provide enough context or substance alone.'
}

$borderline = @{
  'src-f0c76005377afd83' = 'A dated one-page organizational chart can answer a narrow historical question, but it becomes stale quickly and has limited durable public value.'
  'src-53f3375a9829dc10' = 'This 126-word regulation summary is a thin pointer to controlling requirements. Consider folding it into a curated drainage-review guide instead of retaining a separate entry.'
  'src-5e74a3b59f6ef58f' = 'A one-page 2024 fee sheet is operationally useful but time-sensitive and easily superseded. It needs a current-version maintenance rule to justify a standalone entry.'
  'src-fa4cf248a6dd7221' = 'The 99-word permit checklist is useful but slight and time-sensitive. Consider presenting it within a consolidated current development-submittal guide.'
  'src-7c27417fbd191fdf' = 'The one-page contractor notice has a concrete rule but little context. It may be better as part of a consolidated drainage construction requirements record.'
  'src-98563dab32c38b5c' = 'The one-page information and fee sheet is useful but volatile. It should remain standalone only with an explicit process for detecting supersession.'
  'src-6d08320245cacfbd' = 'This two-page procedure is visually encoded and may be useful, but the audit could not extract its substance. It needs renewed visual review before retention.'
}

$manualConsolidate = @{
  'src-047e8956baad212d' = 'A short departmental capital scope belongs with the applicable bond-cycle or capital-program master record rather than as an isolated entry.'
  'src-a58b458f5d0f5284' = 'The 97-word ballot question is useful context for the 2004 Street Bond, but it should be a section of a master 2004 program record.'
  'src-4f28a655d98c8ae3' = 'Topic 1 is one installment of a three-part Old Town task-force ranking exercise and lacks sufficient value as a separate site entry.'
  'src-3f866d2089b33926' = 'Topic 2 is one installment of a three-part Old Town task-force ranking exercise and should be combined with Topics 1 and 3.'
  'src-d866542fe3372c5e' = 'Topic 3 is one installment of a three-part Old Town task-force ranking exercise and should be combined with Topics 1 and 2.'
  'src-f70c337140899545' = 'The one-page program overview is context for the same 2010-2011 UETF award cycle and should lead a consolidated master record.'
  'src-b9402ce7e2e6c22f' = 'The 55-word funding summary has almost no standalone substance and should be incorporated into the 2010-2011 UETF master record.'
  'src-10edc718610865b0' = 'The funded-project list is substantive, but it is one part of the same UETF cycle and is clearer when combined with its overview and funding summary.'
}

function Get-WordCount([string]$Text) {
  if ([string]::IsNullOrWhiteSpace($Text)) { return 0 }
  return @($Text -split '\s+' | Where-Object { $_ }).Count
}

function Set-Review($Document, [string]$Status, [string]$Value, [string]$Density, [bool]$Aggregation, [string]$Recommendation, [string]$Rationale, [string]$MasterTitle = '') {
  $Document.quality_review.status = $Status
  $Document.quality_review.standalone_value = $Value
  $Document.quality_review.information_density = $Density
  $Document.quality_review.aggregation_candidate = $Aggregation
  $Document.quality_review.recommendation = $Recommendation
  $Document.quality_review.rationale = $Rationale
  if (-not $Document.quality_review.PSObject.Properties['proposed_master_record']) {
    $Document.quality_review | Add-Member -NotePropertyName proposed_master_record -NotePropertyValue $MasterTitle
  } else {
    $Document.quality_review.proposed_master_record = $MasterTitle
  }
}

foreach ($document in $audit.documents) {
  $id = [string]$document.candidate_id
  $title = [string]$document.title
  $measurement = $document.content_measurement
  $pages = if ($null -ne $measurement.pages) { [int]$measurement.pages } else { 0 }
  $words = [int]$measurement.extracted_words
  $density = if ($words -eq 0) { 'not text-extractable; visual inspection required' } elseif ($pages -le 2 -and $words -lt 250) { 'limited' } else { 'substantial or specialized visual/tabular content' }

  if ($archiveOnly.ContainsKey($id)) {
    Set-Review $document 'does not meet standalone standard' 'low' $density $false 'archive-only; remove public-facing entry after user approval' $archiveOnly[$id]
    continue
  }
  if ($borderline.ContainsKey($id)) {
    Set-Review $document 'questionable; user review requested' 'uncertain' $density $true 'retain only if user confirms standalone value or consolidation approach' $borderline[$id]
    continue
  }

  if ($title -match '^Development Process( Manual)? Executive Committee Minutes,') {
    Set-Review $document 'does not meet standalone standard' 'low individually' $density $true 'replace individual entry with a consolidated master record after user approval' 'This is one short installment in a homogeneous meeting series. Its decisions are more discoverable in a dated, chronological master record than through a separate link and repetitive description.' 'Development Process Manual Executive Committee Decisions, 2014-2018'
    continue
  }
  if ($measurement.aggregation_family -eq 'annual-listing-of-obligations') {
    Set-Review $document 'does not meet standalone standard' 'moderate as a series' $density $true 'replace individual entry with a consolidated master record after user approval' 'This is one annual installment in a four-document obligations series. A single 2006-2009 master record would preserve every table while avoiding repetitive standalone entries.' 'MRMPO Annual Listings of Obligations, FFY 2006-2009'
    continue
  }
  if ($manualConsolidate.ContainsKey($id)) {
    $master = if ($id -in @('src-4f28a655d98c8ae3','src-3f866d2089b33926','src-d866542fe3372c5e')) { 'Old Town Virtual Task Force Ranking Results, Topics 1-3' } elseif ($id -in @('src-f70c337140899545','src-b9402ce7e2e6c22f','src-10edc718610865b0')) { 'Urban Enhancement Trust Fund 2010-2011 Program and Funded Projects' } elseif ($id -eq 'src-a58b458f5d0f5284') { '2004 Street Bond Program History' } else { 'Applicable capital-program master record' }
    Set-Review $document 'does not meet standalone standard' 'moderate only with related records' $density $true 'replace individual entry with a consolidated master record after user approval' $manualConsolidate[$id] $master
    continue
  }

  if ($measurement.aggregation_family -eq 'general-obligation-bond-component') {
    $serialContext = $title -match '(Summary|Schedule|Introduction|Planning, Selection|Funding Allocation|Rehabilitation, Maintenance|Authorization|Initial Version)'
    $thinScope = (($pages -eq 1 -and $words -lt 400) -or ($pages -eq 2 -and $words -lt 250))
    if ($serialContext -or $thinScope) {
      $year = if ($title -match '(20\d{2})') { $Matches[1] } else { 'historical' }
      Set-Review $document 'does not meet standalone standard' 'low or context-dependent individually' $density $true 'replace individual entry with a bond-cycle master record after user approval' 'This component is brief, version-dependent, or meaningful primarily alongside the other records from the same bond cycle. It should not have received an independent site entry.' "$year General Obligation Bond Program Master Record"
      continue
    }
  }

  Set-Review $document 'meets standard on renewed review' 'high or distinct specialized use' $density $false 'retain' 'The document provides substantial legal, planning, engineering, geographic, historical, tabular, or operational content and has a distinct use that is not adequately represented by a thinner related fragment.'
}

$reviewed = @($audit.documents)
$failures = @($reviewed | Where-Object { $_.quality_review.status -eq 'does not meet standalone standard' })
$questions = @($reviewed | Where-Object { $_.quality_review.status -eq 'questionable; user review requested' })
$kept = @($reviewed | Where-Object { $_.quality_review.status -eq 'meets standard on renewed review' })
if ($reviewed.Count -ne ($failures.Count + $questions.Count + $kept.Count)) { throw 'Every audited document must receive exactly one review outcome.' }
foreach ($document in $reviewed) {
  if ((Get-WordCount ([string]$document.quality_review.rationale)) -lt 15) { throw "Quality rationale is too short for '$($document.candidate_id)'." }
}

$audit | Add-Member -Force -NotePropertyName quality_review_summary -NotePropertyValue ([pscustomobject][ordered]@{
  reviewed = $reviewed.Count
  does_not_meet_standalone_standard = $failures.Count
  questionable_user_review = $questions.Count
  meets_standard = $kept.Count
  site_edits_made = $false
})
$audit | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath $AuditPath -Encoding utf8

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# Post-PR 132 content quality review')
$lines.Add('')
$lines.Add("Reviewed all $($reviewed.Count) distinct static documents first introduced by merged PRs 132-147. This is an audit only: no site content was edited. Shortness alone was not treated as failure; maps, forms, legal records, dense tables, and current operational instructions can have distinct value.")
$lines.Add('')
$lines.Add("## Recommended not to remain as standalone entries ($($failures.Count))")
$lines.Add('')
$lines.Add('These originals should remain preserved in R2. Any removal, replacement, or consolidation requires a later site-content change after user review.')
$lines.Add('')
foreach ($group in ($failures | Group-Object { if ($_.quality_review.proposed_master_record) { $_.quality_review.proposed_master_record } else { 'Archive-only records' } } | Sort-Object Name)) {
  $lines.Add("### $($group.Name)")
  $lines.Add('')
  foreach ($document in ($group.Group | Sort-Object { $_.introducing_prs[0] },title)) {
    $m = $document.content_measurement
    $pageText = if ($m.pages) { "$($m.pages) page$(if ([int]$m.pages -ne 1) {'s'})" } else { [string]$document.file_type }
    $lines.Add("- **PR $($document.introducing_prs[0]) — $($document.title)** (ID $($document.candidate_id); $pageText; $($m.extracted_words) extracted words): $($document.quality_review.rationale)")
  }
  $lines.Add('')
}
$lines.Add("## Borderline records requiring your judgment ($($questions.Count))")
$lines.Add('')
foreach ($document in ($questions | Sort-Object { $_.introducing_prs[0] },title)) {
  $m = $document.content_measurement
  $lines.Add("- **PR $($document.introducing_prs[0]) — $($document.title)** (ID $($document.candidate_id); $($m.pages) page$(if ([int]$m.pages -ne 1) {'s'}); $($m.extracted_words) extracted words): $($document.quality_review.rationale)")
}
$lines.Add('')
$lines.Add("## Retained on renewed review ($($kept.Count))")
$lines.Add('')
$lines.Add('The complete machine-readable audit identifies every retained document and its evidence. These records passed because they contain substantial or distinctly useful legal, planning, engineering, geographic, historical, tabular, or operational material; page count alone was not decisive.')
$lines | Set-Content -LiteralPath $ReportPath -Encoding utf8

[pscustomobject]@{ Reviewed=$reviewed.Count; DoesNotMeetStandalone=$failures.Count; Questionable=$questions.Count; Meets=$kept.Count; AuditPath=$AuditPath; ReportPath=$ReportPath } | ConvertTo-Json -Compress
