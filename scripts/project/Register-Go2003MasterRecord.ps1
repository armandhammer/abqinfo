[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$BuildValidationPath = 'project-state/discovery/go2003-master-compilation-build-2026-09-13.json',
  [string]$VisualQaPath = 'project-state/discovery/go2003-master-compilation-visual-qa-2026-09-13.json',
  [string]$ResearchPath = 'project-state/discovery/claude-consolidation-2003-general-obligation-bond-program-master-record-2026-09-13.json',
  [string]$DecisionsPath = 'project-state/discovery/go2003-master-compilation-decisions-2026-09-13.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$buildArtifact = Get-Content -Raw -Encoding UTF8 -LiteralPath $BuildValidationPath | ConvertFrom-Json
$qa = Get-Content -Raw -Encoding UTF8 -LiteralPath $VisualQaPath | ConvertFrom-Json
$research = Get-Content -Raw -Encoding UTF8 -LiteralPath $ResearchPath | ConvertFrom-Json
$build = $buildArtifact.compilation
if (-not [bool]$qa.all_passed -or [string]$qa.checksum_sha256 -ne [string]$build.checksum_sha256) { throw 'Visual QA does not match the final compilation.' }
if ([int]$build.source_count -ne 21 -or [int]$buildArtifact.source_equivalence_validation.source_page_count -ne 92) { throw 'Compilation does not contain the complete reviewed source family.' }
if (-not [bool]$buildArtifact.source_equivalence_validation.rendered_source_pages_pixel_identical -or -not [bool]$buildArtifact.source_equivalence_validation.extracted_source_text_identical -or -not [bool]$buildArtifact.source_equivalence_validation.all_separator_provenance_links_present) { throw 'Source-equivalence validation is incomplete.' }
if ([string]$research.recommended_publication_form.form -ne 'consolidated_master') { throw 'Research does not recommend the master record.' }
$file = Get-Item -LiteralPath ([string]$build.output_path)
$hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
if ($file.Length -ne [int64]$build.size_bytes -or $hash -ne [string]$build.checksum_sha256) { throw 'Final compilation integrity mismatch.' }

$r2Key = 'city-data/capital-spending/cabq-2003-general-obligation-bond-program-master-record-abqinfo-compilation.pdf'
$publicUrl = "https://files.abqinfo.com/$r2Key"
$title = '2003 General Obligation Bond Program: Master Record - ABQInfo Historical Compilation'
$description = 'Combines 21 City records covering the governing resolutions, allocation and maintenance tables, Environmental Planning Commission recommendation, purpose-by-purpose project scopes, operating impacts, public FAQ, and Water Master Plan zone map for the 2003 bond program.'
$implementationLocations = @(
  'content/city-data/capital-spending.md',
  'content/city-data/public-safety-data.md',
  'content/public-works/parks-recreation.md',
  'content/transportation/transit/abq-ride.md',
  'content/public-works/stormwater-drainage.md',
  'content/transportation/transportation-plans.md'
)
$candidateJson = & "$PSScriptRoot/Add-InventoryCandidate.ps1" -SourceUrl $publicUrl -DirectFileUrl $publicUrl -Agency 'ABQInfo compilation of City of Albuquerque originals' -Title $title -Date '2003' -FileType PDF -ParentUrl 'https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2003-bond-doc' -DiscoveryMethod 'approved provenance-preserving ABQInfo annual program compilation' -InventoryPath $InventoryPath
$candidate = $candidateJson | ConvertFrom-Json
$memberIds = @($research.ordered_members | Sort-Object order | ForEach-Object candidate_id)
$notes = @(
  'ABQInfo-created browsing compilation; not a single publication issued by the City of Albuquerque.',
  "Contains 21 complete City originals in the research-approved order, each preceded by a provenance sheet; component inventory IDs: $($memberIds -join ', ').",
  'All components remain separately preserved with original source URLs, byte sizes, SHA-256 checksums, and inventory history.',
  "Final PDF source-equivalence and visual QA: $($VisualQaPath.Replace('\\','/'))."
)
& "$PSScriptRoot/Update-Candidate.ps1" -Id $candidate.id -Set @{
  status = 'approved for addition'
  source_url = $publicUrl
  direct_file_url = $publicUrl
  agency = 'ABQInfo compilation of City of Albuquerque originals'
  title = $title
  date = '2003'
  file_type = 'PDF'
  size_bytes = [int64]$file.Length
  checksum_sha256 = $hash
  parent_url = 'https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2003-bond-doc'
  provenance_status = 'ABQInfo compilation derived from separately archived and verified authoritative City originals; exact component provenance embedded in the PDF'
  proposed_canonical_page = 'content/city-data/capital-spending.md'
  description = $description
  processing_notes = @($notes)
  implementation_locations = $implementationLocations
  cross_listing_approved = $true
  validation_status = 'final compilation size, SHA-256, source-page equivalence, provenance links, and visual QA passed; R2 upload pending'
  local_path = $file.FullName.Substring((Get-Location).Path.Length + 1).Replace('\\','/')
} -InventoryPath $InventoryPath | Out-Null

$quality = [pscustomobject][ordered]@{
  reviewed_document_content = $true
  visual_inspection_completed = $true
  standalone_public_value = 'high'
  information_density = 'substantial'
  series_relationship = 'serial'
  publication_form = 'consolidated_master'
  rationale = 'The master record unifies the governing resolutions, project-selection evidence, allocations, public explanation, and purpose scopes needed to understand the complete 2003 bond program and its election outcome.'
  aggregation_rationale = 'The 21 short and interdependent records form one annual program history. Consolidating them eliminates sparse standalone listings while retaining direct provenance and byte-identical archive access for every original City file.'
  page_count = [int]$build.page_count
  extracted_word_count = 17825
}
$decision = [pscustomobject][ordered]@{
  id = [string]$candidate.id
  title = $title
  date = '2003'
  source_page = 'https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2003-bond-doc'
  direct_file_url = 'https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2003-bond-doc'
  agency = 'ABQInfo compilation of City of Albuquerque originals'
  canonical_page = 'content/city-data/capital-spending.md'
  description = $description
  r2_key = $r2Key
  provenance_status = 'ABQInfo compilation derived from separately archived and verified authoritative City originals; exact component provenance embedded in the PDF'
  processing_notes = @($notes)
  implementation_locations = $implementationLocations
  cross_listing_approved = $true
  quality_assessment = $quality
}
& "$PSScriptRoot/Test-ContentPublicationQuality.ps1" -Decision $decision -Context '2003 GO-bond annual master record' | Out-Null
$artifact = [pscustomobject][ordered]@{
  schema_version = 1
  created_at = (Get-Date).ToUniversalTime().ToString('o')
  batch_id = 'go2003-master-compilation-2026-09-13'
  purpose = 'Register the user-approved annual master only after all 21 component originals are separately archived and the final PDF passes integrity, provenance, source-equivalence, and visual QA.'
  decisions = @($decision)
}
$artifact | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $DecisionsPath -Encoding utf8
$artifact | Select-Object @{n='compilation_id';e={$_.decisions[0].id}},@{n='bytes';e={$file.Length}},@{n='sha256';e={$hash}},@{n='output_path';e={$DecisionsPath}} | ConvertTo-Json -Compress
