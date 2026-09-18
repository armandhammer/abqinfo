[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$ResearchPath = 'project-state/discovery/paseo-del-volcan-cluster-research-2026-09-11.json',
  [string]$DecisionPath = 'project-state/discovery/paseo-del-volcan-publication-decisions-2026-09-17.json',
  [string]$PlanPath = 'project-state/discovery/paseo-del-volcan-r2-archive-plan-2026-09-17.json',
  [string]$DownloadDirectory = 'research/staging/queue'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$research = Get-Content -Raw -Encoding UTF8 -LiteralPath $ResearchPath | ConvertFrom-Json -DateKind String
$approved = @($research.approved_for_addition | Sort-Object id)
if ($approved.Count -ne 11 -or [int]$research.counts.reviewed -ne 20) { throw 'Unexpected saved Paseo del Volcan research scope.' }

$parent = 'https://www.cabq.gov/council/documents/paseo-del-volcan-documents'
$keys = @{
  'src-05705d25113d3f2e' = 'transportation/paseo-del-volcan/cabq-paseo-del-volcan-steering-committee-agenda-2013-11-20.pdf'
  'src-189c0a45bb72113c' = 'transportation/paseo-del-volcan/cabq-paseo-del-volcan-steering-committee-minutes-2014-01-15.pdf'
  'src-2f75875ce1c5cf27' = 'transportation/paseo-del-volcan/cabq-double-eagle-ii-long-range-development-plans-2014-06-27.pdf'
  'src-3924fb39a476b0a7' = 'transportation/paseo-del-volcan/cabq-paseo-del-volcan-steering-committee-minutes-2014-04-04.pdf'
  'src-4aaa2a918146e21c' = 'transportation/paseo-del-volcan/cabq-paseo-del-volcan-right-of-way-acquisition-status-map-2013-12.pdf'
  'src-625f2a5f3f04d910' = 'transportation/paseo-del-volcan/cabq-paseo-del-volcan-long-term-perspective-brochure.pdf'
  'src-8043e1de7031af50' = 'transportation/paseo-del-volcan/cabq-paseo-del-volcan-economic-development-opportunities-technical-appendices-2014-09.pdf'
  'src-b1816c40babc0546' = 'transportation/paseo-del-volcan/cabq-paseo-del-volcan-funding-financing-workshop-2014-04-04.pdf'
  'src-bdb03a2b53786b9a' = 'public-works/parks-recreation/cabq-major-public-open-space-west-side-steering-committee-presentation.pdf'
  'src-e04cf778f5a04ae9' = 'transportation/paseo-del-volcan/cabq-paseo-del-volcan-economic-opportunity-implementation-summary-2014-11-07.pdf'
  'src-fd2c4ff2f2681189' = 'transportation/paseo-del-volcan/cabq-paseo-del-volcan-steering-committee-meeting-notes-2014-06-27.pdf'
}

function Get-Quality($row) {
  $id = [string]$row.id
  $isMeeting = $id -in @('src-05705d25113d3f2e','src-189c0a45bb72113c','src-3924fb39a476b0a7','src-fd2c4ff2f2681189')
  $isVisual = $id -in @('src-4aaa2a918146e21c','src-bdb03a2b53786b9a')
  $isThin = [int]$row.pages -le 3 -and -not $isVisual
  $quality = [ordered]@{
    reviewed_document_content = $true
    visual_inspection_completed = $true
    standalone_public_value = if ($id -eq 'src-05705d25113d3f2e') { 'medium' } else { 'high' }
    information_density = if ($isVisual) { 'visual_or_tabular' } elseif ($isThin) { 'limited' } else { 'substantial' }
    series_relationship = if ($isMeeting) { 'serial' } else { 'standalone' }
    publication_form = 'standalone'
    rationale = if ($row.PSObject.Properties['why_retained'] -and $row.why_retained) { [string]$row.why_retained } else { 'This dated official meeting record documents a distinct part of the Paseo del Volcan corridor process and supplies context for the related studies, financing materials, and right-of-way records.' }
    page_count = [int]$row.pages
    extracted_word_count = 0
  }
  if ($isMeeting) {
    $quality.aggregation_rationale = 'The Paseo del Volcan Corridor subsection presents the committee record chronologically with its related studies and handouts, while keeping each dated agenda, minutes, or meeting-notes original separately available and accurately labelled.'
    $quality.standalone_exception = 'Each meeting record supplies a distinct dated account of the corridor effort. The agenda is explicitly qualified because approved minutes were not located, and the June record remains labelled meeting notes rather than minutes.'
  }
  if ($isThin) {
    $quality.limited_content_exception = 'Although brief, this dated meeting record or agenda supplies unique evidence about the corridor process and is presented inside a contextual family subsection rather than as an isolated administrative document.'
  }
  [pscustomobject]$quality
}

$decisions = [System.Collections.Generic.List[object]]::new()
foreach ($row in $approved) {
  $id = [string]$row.id
  if (-not $keys.ContainsKey($id)) { throw "No R2 key defined for $id." }
  $inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json -DateKind String
  $candidate = @($inventory.candidates | Where-Object id -eq $id)
  if ($candidate.Count -ne 1) { throw "Expected exactly one candidate for $id." }
  $candidate = $candidate[0]
  if ($candidate.r2_url) { throw "$id already has an R2 archive; this plan must not overwrite it." }
  $hasVerifiedLocalFile = $candidate.local_path -and (Test-Path -LiteralPath $candidate.local_path)
  if ($hasVerifiedLocalFile) {
    $localFile = Get-Item -LiteralPath $candidate.local_path
    $localHash = (Get-FileHash -LiteralPath $localFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $hasVerifiedLocalFile = $localFile.Length -eq [int64]$row.size_bytes -and $localHash -eq [string]$row.checksum_sha256
  }
  if (-not $hasVerifiedLocalFile) {
    & "$PSScriptRoot/Update-Candidate.ps1" -Id $id -Set @{ status='pending review'; source_url=[string]$row.authoritative_url; direct_file_url=[string]$row.authoritative_url } -InventoryPath $InventoryPath | Out-Null
    & "$PSScriptRoot/Download-Candidate.ps1" -Id $id -InventoryPath $InventoryPath -DownloadDirectory $DownloadDirectory | Out-Null
    $inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json -DateKind String
    $candidate = @($inventory.candidates | Where-Object id -eq $id)[0]
  }
  $file = Get-Item -LiteralPath $candidate.local_path
  $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($file.Length -ne [int64]$row.size_bytes -or $hash -ne [string]$row.checksum_sha256) { throw "Official-source integrity mismatch for $id." }
  $quality = Get-Quality $row
  $decision = [pscustomobject][ordered]@{
    id = $id; title = [string]$row.title; date = $row.date; source_url = [string]$row.authoritative_url; direct_file_url = [string]$candidate.direct_file_url; parent_url = $parent
    agency = 'City of Albuquerque (official source)'; file_type = 'PDF'; size_bytes = [int64]$file.Length; checksum_sha256 = $hash; r2_key = $keys[$id]
    proposed_canonical_page = [string]$row.proposed_canonical_page; cross_listings = @($row.cross_listings); description = [string]$row.description
    provenance_status = 'Official City-hosted source re-fetched; exact size and SHA-256 match the saved complete Paseo del Volcan cluster research.'
    processing_notes = @('Original official PDF preserved without modification.', 'Paseo del Volcan complete-cluster research: project-state/discovery/paseo-del-volcan-cluster-research-2026-09-11.json.', 'Actual authorship is described in the public context where the City hosts but did not author a record.')
    quality_assessment = $quality
  }
  & "$PSScriptRoot/Test-ContentPublicationQuality.ps1" -Decision $decision -Context "Paseo del Volcan decision '$id'" | Out-Null
  if ($candidate.status -ne 'approved for addition' -or $candidate.validation_status -ne 'local exact size and SHA-256 match the saved complete-cluster research; R2 upload pending') {
    & "$PSScriptRoot/Update-Candidate.ps1" -Id $id -Set @{
      status='approved for addition'; source_url=$decision.source_url; direct_file_url=$decision.direct_file_url; agency=$decision.agency; title=$decision.title; date=$decision.date; file_type='PDF'; size_bytes=$decision.size_bytes; checksum_sha256=$decision.checksum_sha256; parent_url=$parent; local_path=$candidate.local_path; proposed_canonical_page=$decision.proposed_canonical_page; description=$decision.description; provenance_status=$decision.provenance_status; validation_status='local exact size and SHA-256 match the saved complete-cluster research; R2 upload pending'; processing_notes=@($candidate.processing_notes)+@($decision.processing_notes)|Select-Object -Unique; exclusion_reason=$null
    } -InventoryPath $InventoryPath | Out-Null
  }
  $decisions.Add($decision)
}

$terminal = @($research.duplicate) + @($research.excluded)
foreach ($row in $terminal) {
  $id = [string]$row.id
  $status = [string]$row.recommended_status
  $reason = if ($status -eq 'duplicate') { "Duplicate delivery; canonical record is $($row.canonical_id). $($row.basis)" } else { [string]$row.exclusion_reason }
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $id -Set @{ status=$status; source_url=[string]$row.authoritative_url; direct_file_url=[string]$row.authoritative_url; exclusion_reason=$reason; processing_notes=@('Paseo del Volcan complete-cluster research: project-state/discovery/paseo-del-volcan-cluster-research-2026-09-11.json.') } -InventoryPath $InventoryPath | Out-Null
}

$archive = [pscustomobject][ordered]@{ schema_version=1; created_at=(Get-Date).ToUniversalTime().ToString('o'); batch_id='paseo-del-volcan-public-history-2026-09-17'; purpose='Archive the eleven independently valuable official-source records selected by the complete Paseo del Volcan family review before any visible publication.'; research_artifact=$ResearchPath; decisions=@($decisions | Sort-Object id); terminal_classifications=@($terminal | Sort-Object id) }
$archive | ConvertTo-Json -Depth 14 | Set-Content -LiteralPath $DecisionPath -Encoding utf8
$currentR2 = (Get-Content -Raw -Encoding UTF8 -LiteralPath 'project-state/r2-inventory.json' | ConvertFrom-Json -DateKind String).total_bytes
$items = @($decisions | Sort-Object id | ForEach-Object { [pscustomobject][ordered]@{ id=$_.id; source_url=$_.source_url; direct_file_url=$_.direct_file_url; parent_url=$_.parent_url; agency=$_.agency; title=$_.title; date=$_.date; file_type=$_.file_type; size_bytes=$_.size_bytes; checksum_sha256=$_.checksum_sha256; r2_key=$_.r2_key; proposed_canonical_page=$_.proposed_canonical_page; description=$_.description; provenance_status=$_.provenance_status; processing_notes=$_.processing_notes; size_warning_over_25mb=($_.size_bytes -gt 25MB); implementation_locations=@($_.proposed_canonical_page)+@($_.cross_listings | ForEach-Object { $_.page }); cross_listing_approved=(@($_.cross_listings).Count -gt 0); already_present=$false } })
$added = [int64](@($items | Measure-Object -Property size_bytes -Sum).Sum)
$plan = [pscustomobject][ordered]@{ schema_version=1; created_at=(Get-Date).ToUniversalTime().ToString('o'); batch_id='paseo-del-volcan-public-history-2026-09-17'; current_r2_bytes=[int64]$currentR2; maximum_object_bytes=100000000; maximum_projected_r2_bytes=10000000000; batch_bytes=$added; added_bytes=$added; projected_r2_bytes=([int64]$currentR2+$added); items=$items }
$plan | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $PlanPath -Encoding utf8
[pscustomobject]@{ approved=$decisions.Count; terminal=$terminal.Count; bytes=$added; decision_path=$DecisionPath; plan_path=$PlanPath } | ConvertTo-Json -Compress
