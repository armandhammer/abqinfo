[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$ResearchPath = 'project-state/discovery/claude-consolidation-2003-general-obligation-bond-program-master-record-2026-09-13.json',
  [string]$FamilyCheckpointPath = 'research/staging/claude-consolidation-checkpoints/2003-general-obligation-bond-program-master-record/items/family-2003-bond-doc.json',
  [string]$DownloadDirectory = 'research/staging/queue',
  [string]$DecisionsPath = 'project-state/discovery/go2003-master-original-components-decisions-2026-09-13.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$research = Get-Content -Raw -Encoding UTF8 -LiteralPath $ResearchPath | ConvertFrom-Json
$family = Get-Content -Raw -Encoding UTF8 -LiteralPath $FamilyCheckpointPath | ConvertFrom-Json
if ([string]$research.slice_id -ne '2003-general-obligation-bond-program-master-record') { throw 'Unexpected research slice.' }
if ([string]$research.recommended_publication_form.form -ne 'consolidated_master') { throw 'Research does not approve a consolidated master.' }
$members = @($research.ordered_members)
if ($members.Count -ne 21 -or [int]$research.total_pages -ne 92) { throw 'Expected the reviewed 21-source, 92-page program family.' }
$familyById = @{}
foreach ($item in @($family.files_reviewed)) { $familyById[[string]$item.candidate_id] = $item }

$metadata = @{
  'src-7405cfc41e5500c4' = @{
    title = '2003 General Obligation Bond Program Purpose Allocation Summary'
    description = 'Shows the dollar amount and percentage assigned to each of the ten 2003 general-obligation bond purposes, including streets, parks, public facilities, storm sewers, transit, public safety, libraries, and community centers.'
    r2_key = 'city-data/capital-spending/cabq-2003-go-bond-program-purpose-allocation-summary.pdf'
    extracted_words = 0
  }
  'src-6735737588d294e0' = @{
    title = '2003-2012 Capital Improvements Decade Plan: Environmental Planning Commission Recommendations'
    description = "Records the Environmental Planning Commission decision and findings recommending approval of the Mayor's proposed 2003-2012 capital-improvements decade plan after its January 16, 2003 public hearing."
    r2_key = 'city-data/capital-spending/cabq-2003-2012-capital-improvements-epc-recommendations.pdf'
    extracted_words = 7997
  }
  'src-bd084d192e7b78ce' = @{
    title = '2003 General Obligation Bond Program Frequently Asked Questions'
    description = "Explains general-obligation bond financing, property-tax effects, eligible capital improvements, project selection, debt-service policy, and the City's public process for assembling the 2003 bond program."
    r2_key = 'city-data/capital-spending/cabq-2003-go-bond-program-frequently-asked-questions.pdf'
    extracted_words = 0
  }
  'src-3c9907796a0cfaf3' = @{
    title = '2003 Water Master Plan Infrastructure Zone Map'
    description = 'Maps the Water Master Plan Infrastructure Zone against Albuquerque streets, landmarks, the municipal boundary, and major transportation corridors. The official sheet is labeled page B-6; its parent document was not located.'
    r2_key = 'city-data/capital-spending/cabq-2003-water-master-plan-infrastructure-zone-map.pdf'
    extracted_words = 0
  }
}

$decisions = [System.Collections.Generic.List[object]]::new()
foreach ($id in $metadata.Keys) {
  if (-not $familyById.ContainsKey($id)) { throw "Family checkpoint lacks $id." }
  $review = $familyById[$id]
  $inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
  $candidate = @($inventory.candidates | Where-Object id -eq $id)
  if ($candidate.Count -ne 1) { throw "Expected one inventory candidate for $id." }
  $candidate = $candidate[0]
  if ($candidate.r2_url) { throw "$id already has an R2 archive; do not plan a second object." }

  $localPath = if ($candidate.local_path) { [string]$candidate.local_path } else { Join-Path $DownloadDirectory "$id.pdf" }
  if (-not (Test-Path -LiteralPath $localPath)) {
    $sharedPath = Join-Path 'C:\Users\ben\Documents\ABQinfo' $localPath
    if (Test-Path -LiteralPath $sharedPath) {
      New-Item -ItemType Directory -Force -Path (Split-Path -Parent $localPath) | Out-Null
      Copy-Item -LiteralPath $sharedPath -Destination $localPath
    }
  }
  if (-not (Test-Path -LiteralPath $localPath)) {
    & "$PSScriptRoot/Update-Candidate.ps1" -Id $id -Set @{
      status = 'pending review'
      source_url = [string]$review.official_url
      direct_file_url = [string]$review.official_url
    } -InventoryPath $InventoryPath | Out-Null
    & "$PSScriptRoot/Download-Candidate.ps1" -Id $id -InventoryPath $InventoryPath -DownloadDirectory $DownloadDirectory | Out-Null
    $inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
    $candidate = @($inventory.candidates | Where-Object id -eq $id)[0]
    $localPath = [string]$candidate.local_path
  }

  $file = Get-Item -LiteralPath $localPath
  $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($file.Length -ne [int64]$review.size_bytes -or $hash -ne [string]$review.checksum_sha256) {
    throw "Official-source integrity mismatch for $id."
  }
  $meta = $metadata[$id]
  $quality = [pscustomobject][ordered]@{
    reviewed_document_content = $true
    visual_inspection_completed = $true
    standalone_public_value = 'low'
    information_density = if ($id -in @('src-7405cfc41e5500c4','src-3c9907796a0cfaf3')) { 'visual_or_tabular' } else { 'substantial' }
    series_relationship = 'component'
    publication_form = 'consolidated_master'
    rationale = 'This official record contributes substantive evidence to the complete 2003 bond-program history, but its context depends on the governing resolutions, allocation records, selection materials, and related purpose scopes.'
    aggregation_rationale = 'The user-approved annual program master combines the complete reviewed source family into one coherent browsing record while retaining this byte-identical original, its authoritative source URL, size, and checksum separately.'
    page_count = [int]$review.pages
    extracted_word_count = [int]$meta.extracted_words
  }
  $decision = [pscustomobject][ordered]@{
    id = $id
    title = [string]$meta.title
    date = '2003'
    source_page = 'https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2003-bond-doc'
    direct_file_url = [string]$review.official_url
    agency = 'City of Albuquerque'
    canonical_page = 'content/city-data/capital-spending.md'
    description = [string]$meta.description
    r2_key = [string]$meta.r2_key
    provenance_status = 'official City source fetched and visually reviewed; exact size and SHA-256 match the exhaustive source-family checkpoint'
    processing_notes = @(
      'Preserved as a byte-identical source component of the 2003 annual bond-program master record; not approved as a standalone visible site entry.',
      "Claude official-family checkpoint: $($FamilyCheckpointPath.Replace('\\','/'))."
    )
    implementation_locations = @()
    cross_listing_approved = $false
    quality_assessment = $quality
  }
  & "$PSScriptRoot/Test-ContentPublicationQuality.ps1" -Decision $decision -Context "2003 GO-bond source component '$id'" | Out-Null
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $id -Set @{
    status = 'approved for addition'
    source_url = [string]$review.official_url
    direct_file_url = [string]$review.official_url
    agency = 'City of Albuquerque'
    title = [string]$meta.title
    date = '2003'
    file_type = 'PDF'
    size_bytes = [int64]$file.Length
    checksum_sha256 = $hash
    local_path = $localPath.Replace('\\','/')
    parent_url = 'https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2003-bond-doc'
    proposed_canonical_page = 'content/city-data/capital-spending.md'
    description = [string]$meta.description
    provenance_status = [string]$decision.provenance_status
    validation_status = 'local exact size and SHA-256 match the official-source family checkpoint; R2 upload pending'
    processing_notes = @($candidate.processing_notes) + @($decision.processing_notes) | Select-Object -Unique
    exclusion_reason = $null
  } -InventoryPath $InventoryPath | Out-Null
  $decisions.Add($decision)
}

$artifact = [pscustomobject][ordered]@{
  schema_version = 1
  created_at = (Get-Date).ToUniversalTime().ToString('o')
  batch_id = 'go2003-master-original-components-2026-09-13'
  purpose = 'Archive the four previously unarchived authoritative source components required by the complete 2003 General Obligation Bond Program master record; no component is approved as a standalone visible entry.'
  decisions = @($decisions | Sort-Object id)
}
$artifact | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $DecisionsPath -Encoding utf8
$artifact | Select-Object @{n='planned_original_archives';e={@($_.decisions).Count}},@{n='added_bytes';e={(@($_.decisions | ForEach-Object { $familyById[$_.id].size_bytes }) | Measure-Object -Sum).Sum}},@{n='output_path';e={$DecisionsPath}} | ConvertTo-Json -Compress
