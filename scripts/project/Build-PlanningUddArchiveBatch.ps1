[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$ResearchPath,
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$DecisionPath = 'project-state/discovery/planning-udd-archive-decisions-2026-09-12.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$research = Get-Content -Raw -Encoding UTF8 -LiteralPath $ResearchPath | ConvertFrom-Json
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$keys = @{
  'src-6d243844fe259b86' = 'public-works/city-facilities/cabq-sunport-airport-master-plan-executive-summary.pdf'
  'src-28418cab91a745a6' = 'development-land-use/redevelopment-plans/cabq-barelas-neighborhood-commercial-area-revitalization-plan.pdf'
  'src-33f990150811e7bb' = 'development-land-use/redevelopment-plans/cabq-south-broadway-sector-development-plan.pdf'
  'src-7a08bd24a1a9dcae' = 'development-land-use/development-process/cabq-silver-hill-historic-overlay-zone-design-guidelines.pdf'
  'src-bdf76c84223f82be' = 'development-land-use/development-process/cabq-official-plant-palette-sizing-list-2018.pdf'
  'src-87b92910cd99400d' = 'development-land-use/development-process/cabq-annexation-policies-resolution-r-54-1990.pdf'
  'src-6d08320245cacfbd' = 'development-land-use/development-process/cabq-facilitated-meetings-criteria-ido-2018.pdf'
  'src-6370c534dac0c540' = 'development-land-use/development-process/cabq-historic-protection-overlay-zones-citywide-map-2018.pdf'
  'src-ad7c091a07a0fb3f' = 'development-land-use/development-process/cabq-eighth-forrester-historic-protection-overlay-zone-map-2018.pdf'
  'src-ec6e7fdafdab0706' = 'development-land-use/development-process/cabq-fourth-ward-historic-protection-overlay-zone-map-2018.pdf'
  'src-75755583aa85c00c' = 'development-land-use/development-process/cabq-huning-highland-edo-historic-protection-overlay-zone-map-2018.pdf'
  'src-c74168a5ee95e044' = 'development-land-use/development-process/cabq-old-town-historic-protection-overlay-zone-map-2018.pdf'
  'src-7f1e53975e461d43' = 'development-land-use/development-process/cabq-silver-hill-historic-protection-overlay-zone-map-2018.pdf'
  'src-1ee4a0c5133aceda' = 'development-land-use/development-process/cabq-old-town-development-standards-guidelines-hpo-5-2018.pdf'
  'src-d42df0916d0d8a2b' = 'development-land-use/development-process/cabq-infrastructure-improvements-agreement-assignment-amendment.pdf'
}

$decisions = foreach ($row in @($research.approved_for_addition)) {
  $candidate = @($inventory.candidates | Where-Object id -eq $row.id)
  if ($candidate.Count -ne 1) { throw "Expected one candidate for $($row.id)." }
  if ([string]$candidate[0].status -ne 'downloaded') { throw "Candidate $($row.id) is not downloaded." }
  if (-not $keys.ContainsKey([string]$row.id)) { throw "Missing R2 key for $($row.id)." }
  $notes = @(
    if ($row.PSObject.Properties['why_retained']) { [string]$row.why_retained }
    if ($row.PSObject.Properties['evidence']) { [string]$row.evidence }
    'Original authoritative City PDF selected for byte-identical archival without modification.'
  ) | Where-Object { $_ }
  $decision = [ordered]@{
    id = [string]$row.id
    title = [string]$row.title
    date = if ($row.PSObject.Properties['date'] -and $row.date) { [string]$row.date } else { [string]$candidate[0].date }
    r2_key = [string]$keys[[string]$row.id]
    canonical_page = [string]$row.proposed_canonical_page
    implementation_locations = @([string]$row.proposed_canonical_page)
    cross_listing_approved = $false
    description = [string]$row.description
    direct_file_url = [string]$row.authoritative_url
    source_page = [string]$candidate[0].source_url
    agency = 'City of Albuquerque'
    provenance_status = 'official City of Albuquerque PDF fetched directly; exact byte size and SHA-256 matched the reviewed Planning UDD research artifact'
    processing_notes = $notes
  }
  if ([int64]$row.size_bytes -gt 25MB) {
    $decision.large_file_assessment = "The $($row.size_bytes)-byte original is image-rich and preserves the complete illustrated planning or design record. It is below the 100 MB archive limit; recompression could impair maps, photographs, or design details, so the authoritative original is retained unchanged."
  }
  [pscustomobject]$decision
}

if (@($decisions).Count -ne 15) { throw "Expected 15 archive decisions; found $(@($decisions).Count)." }
$result = [ordered]@{
  schema_version = 1
  batch_id = 'planning-udd-archive-2026-09-12'
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  research_artifact = 'project-state/discovery/planning-udd-cluster-research-2026-09-11.json'
  decisions = @($decisions)
}
$result | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8 -LiteralPath $DecisionPath
[pscustomobject]@{ decisions = @($decisions).Count; bytes = [int64](($research.approved_for_addition | Measure-Object size_bytes -Sum).Sum); output = $DecisionPath } | ConvertTo-Json -Compress
