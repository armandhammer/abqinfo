[CmdletBinding()]
param(
  [Parameter(Mandatory)][string[]]$ResearchPaths,
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$DecisionPath = 'project-state/discovery/council-records-archive-decisions-2026-09-12.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$keys = @{
  'src-9f5ac56df8c6cbb8' = 'development-land-use/projects/cabq-rail-yards-uli-advisory-panel-report-2008.pdf'
  'src-a3afa3078e7351a7' = 'development-land-use/development-process/cabq-neighborhood-task-force-final-report-2007.pdf'
  'src-42032f0eef57807c' = 'city-data/city-progress-surveys/cabq-small-business-resource-fair-report-2019.pdf'
  'src-f164513208041ca0' = 'city-data/city-progress-surveys/cabq-small-business-resource-fair-report-appendices-2019.pdf'
  'src-baf2db7aea5be0d2' = 'city-data/city-progress-surveys/cabq-african-american-advisory-board-minutes-2026-07-07.pdf'
  'src-c8618de9cd7384e7' = 'city-data/city-progress-surveys/cabq-african-american-advisory-board-minutes-2026-06-02.pdf'
  'src-f6f982e95a648dd7' = 'city-data/city-progress-surveys/cabq-african-american-advisory-board-minutes-2026-05-05.pdf'
  'src-f0c76005377afd83' = 'city-data/city-progress-surveys/cabq-city-council-services-organizational-chart-2026.pdf'
  'src-9642139286c8f411' = 'transportation/operations-data/cabq-raynolds-barelas-stop-sign-reconfiguration-proposal-2008.pdf'
  'src-4f28a655d98c8ae3' = 'development-land-use/zoning-ido/cabq-old-town-task-force-ranking-outdoor-displays.pdf'
  'src-3f866d2089b33926' = 'development-land-use/zoning-ido/cabq-old-town-task-force-ranking-signs.pdf'
  'src-d866542fe3372c5e' = 'development-land-use/zoning-ido/cabq-old-town-task-force-ranking-outdoor-demonstrations.pdf'
  'src-fc250f15df2ab028' = 'city-data/budget-spending/cabq-eclipse-aerospace-leda-ordinance-o-2014-005.pdf'
  'src-77ded92dfd05478c' = 'transportation/roadway-projects/cabq-rainbow-universe-safety-project-resolution-r-2010-056.pdf'
  'src-4347bb9af15c89ba' = 'transportation/safety-crash-data/cabq-redflex-contract-investigation-request-2014.pdf'
}

$rows = foreach ($path in $ResearchPaths) {
  $artifact = Get-Content -Raw -Encoding UTF8 -LiteralPath $path | ConvertFrom-Json
  @($artifact.approved_for_addition)
}
$decisions = foreach ($row in $rows) {
  $candidate = @($inventory.candidates | Where-Object id -eq $row.id)
  if ($candidate.Count -ne 1) { throw "Expected one candidate for $($row.id)." }
  if ([string]$candidate[0].status -ne 'parsed') { throw "Candidate $($row.id) is not parsed." }
  if (-not $keys.ContainsKey([string]$row.id)) { throw "Missing R2 key for $($row.id)." }
  $locations = @([string]$row.proposed_canonical_page)
  foreach ($cross in @($row.cross_listings)) {
    if ($cross.page) { $locations += [string]$cross.page }
  }
  $notes = @(
    if ($row.PSObject.Properties['why_retained']) { [string]$row.why_retained }
    if ($row.PSObject.Properties['evidence']) { [string]$row.evidence }
    'Original authoritative City record selected for byte-identical archival without modification.'
  ) | Where-Object { $_ }
  [pscustomobject][ordered]@{
    id = [string]$row.id
    title = if ([string]$row.id -eq 'src-9f5ac56df8c6cbb8') { "Albuquerque Rail Yards: Redeveloping the City's Historic Rail Yards, an Urban Land Institute Advisory Services Panel Report (February 2008)" } else { [string]$row.title }
    date = if ($row.PSObject.Properties['date'] -and $row.date) { [string]$row.date } else { [string]$candidate[0].date }
    r2_key = [string]$keys[[string]$row.id]
    canonical_page = [string]$row.proposed_canonical_page
    implementation_locations = @($locations | Sort-Object -Unique)
    cross_listing_approved = @($locations | Sort-Object -Unique).Count -gt 1
    description = [string]$row.description
    direct_file_url = ([string]$row.authoritative_url -replace '/view$','')
    source_page = [string]$row.authoritative_url
    agency = 'City of Albuquerque'
    provenance_status = 'official City of Albuquerque record fetched directly; exact byte size and SHA-256 matched the reviewed Council research artifact'
    processing_notes = $notes
  }
}
if (@($decisions).Count -ne 15) { throw "Expected 15 archive decisions; found $(@($decisions).Count)." }
[ordered]@{
  schema_version = 1
  batch_id = 'council-records-archive-2026-09-12'
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  research_artifacts = @('project-state/discovery/council-documents-cluster-research-2026-09-11.json','project-state/discovery/councilor-district-5-cluster-research-2026-09-11.json')
  decisions = @($decisions)
} | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8 -LiteralPath $DecisionPath
[pscustomobject]@{ decisions = @($decisions).Count; bytes = [int64](($rows | Measure-Object size_bytes -Sum).Sum); output = $DecisionPath } | ConvertTo-Json -Compress
