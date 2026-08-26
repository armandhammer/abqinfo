[CmdletBinding()]
param(
  [string]$CrawlPath = 'project-state/discovery/retained-unser-paseo-2026-08-25-crawl.json',
  [string]$OutputPath = 'project-state/retained-source-expansion-6d-decisions-2026-08-25.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$crawl = Get-Content -Raw -Encoding UTF8 -LiteralPath $CrawlPath | ConvertFrom-Json
$definitions = @{
  'src-f827e747d14f6216' = @{ key='transportation/roadway-projects/current/cabq-unser-paseo-phase-1-construction-fact-sheet-english-2025.pdf'; pages=2 }
  'src-3ff7d0de5c42b98d' = @{ key='transportation/roadway-projects/current/cabq-unser-paseo-phase-1-construction-fact-sheet-spanish-2025.pdf'; pages=2 }
  'src-863499b79dab41c0' = @{ key='transportation/roadway-projects/current/cabq-unser-paseo-public-meeting-presentation-2022.pdf'; pages=22; large='The 49,245,276-byte PDF is unusually large because the official 22-slide presentation contains high-resolution roadway design media and was published as a with-video presentation. No smaller authoritative version was found. Optimization could remove or reduce embedded media, but would alter the source and is not proposed.' }
  'src-b422c2535de83efc' = @{ key='transportation/roadway-projects/current/cabq-unser-widening-biological-evaluation-2022.pdf'; pages=92 }
  'src-d8e7dd2c390c5ac5' = @{ key='transportation/roadway-projects/current/cabq-paseo-del-norte-widening-biological-evaluation-2022.pdf'; pages=80 }
  'src-68e69a0015fc4cdd' = @{ key='public-works/stormwater-drainage/amafca-upper-piedras-marcadas-watershed-plan-volume-1-literature-review-2017.pdf'; pages=373; large='The 74,125,379-byte PDF is unusually large because the 373-page official volume preserves three decades of source plans, as-builts, maps, plates, figures, and appendices. The source filename already identifies it as compressed, and no smaller authoritative version was found. Further optimization could reduce map or scan legibility and is not proposed.' }
  'src-e6c483a6440f5a01' = @{ key='public-works/stormwater-drainage/amafca-upper-piedras-marcadas-watershed-plan-volume-2-existing-conditions-2017.pdf'; pages=147; large='The 65,777,461-byte PDF is unusually large because the 147-page official report contains detailed watershed maps, hydrologic modeling, infrastructure exhibits, calculations, and appendices. No smaller authoritative version was found. Recompression or downsampling could reduce map and engineering-detail usefulness and is not proposed.' }
  'src-fd224fd0694e0bc3' = @{ key='public-works/stormwater-drainage/amafca-upper-piedras-marcadas-watershed-plan-volume-3-developed-conditions-2017.pdf'; pages=225; large='The 60,536,110-byte PDF is unusually large because the 225-page official report contains developed-condition models, alternatives, cost estimates, plates, calculations, and extensive appendices. No smaller authoritative version was found. Recompression or downsampling could reduce map and engineering-detail usefulness and is not proposed.' }
}

$decisions = foreach ($candidate in @($crawl.candidates)) {
  $definition = $definitions[[string]$candidate.id]
  if (-not $definition) { throw "No archive definition for $($candidate.id)." }
  $decision = [ordered]@{
    id = [string]$candidate.id
    title = [string]$candidate.title
    date = [string]$candidate.date
    r2_key = [string]$definition.key
    canonical_page = [string]$candidate.proposed_canonical_page
    source_page = 'https://www.upgradeunserpaseo.com/resources/'
    direct_file_url = [string]$candidate.direct_file_url
    agency = [string]$candidate.agency
    description = [string]$candidate.description
    provenance_status = [string]$candidate.provenance_status
    processing_notes = @(
      "Original authoritative $($definition.pages)-page PDF preserved without modification.",
      'Exact size and SHA-256 recorded; extracted title, date, scope, and representative content reviewed.',
      'The project resources page remains linked as the source of truth for updates.'
    )
  }
  if ($definition.ContainsKey('large')) { $decision.large_file_assessment = [string]$definition.large }
  [pscustomobject]$decision
}

$output = [ordered]@{
  batch_id = 'retained-source-expansion-6d-2026-08-25'
  decisions = @($decisions)
}
$json = $output | ConvertTo-Json -Depth 10
[IO.File]::WriteAllText([IO.Path]::GetFullPath($OutputPath), $json, [Text.UTF8Encoding]::new($false))
[pscustomobject]@{ decisions = @($decisions).Count; output = $OutputPath } | ConvertTo-Json -Compress
