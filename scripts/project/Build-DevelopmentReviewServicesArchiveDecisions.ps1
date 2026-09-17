[CmdletBinding()]
param(
  [string]$ResearchPath = 'project-state/discovery/development-review-services-cluster-research-2026-09-11.json',
  [string]$OutputPath = 'project-state/discovery/development-review-services-archive-decisions-2026-09-11.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$research = Get-Content -Raw -Encoding UTF8 -LiteralPath $ResearchPath | ConvertFrom-Json
$keys = @{
  'src-d74108ddea65eb7d' = 'public-works/stormwater/cabq-npdes-storm-water-management-manual-revision-2-2012.pdf'
  'src-28372ac121eeb0ba' = 'public-works/stormwater/cabq-enacted-ordinance-o-2018-020-drainage-runoff-best-practices.pdf'
  'src-e5b815c2a314724a' = 'development-land-use/zoning/cabq-enacted-ordinance-o-2014-024-wireless-telecommunications.pdf'
  'src-85425ef5e82d7493' = 'development-land-use/zoning/cabq-zoning-code-14-16-3-17-wireless-telecommunications.pdf'
  'src-db74fbcfb6e04b9e' = 'city-data/capital-spending/cabq-enacted-resolution-r-2012-100-impact-fee-ccip-2012-2022.pdf'
  'src-f0d6744711099a88' = 'city-data/capital-spending/cabq-enacted-resolution-r-2013-115-impact-fee-credits.pdf'
  'src-49533d311cc95fe9' = 'city-data/capital-spending/cabq-impact-fee-credit-holder-summary-2020-02-18.pdf'
  'src-16030da9139693a5' = 'development-land-use/development-process/cabq-drc-jurisdiction-memorandum-2026-08-25.pdf'
  'src-7c27417fbd191fdf' = 'transportation/design-references/cabq-special-order-19-private-drainage-facilities-2022.pdf'
  'src-53f3375a9829dc10' = 'public-works/stormwater/cabq-drainage-flood-erosion-governing-regulations-summary.pdf'
  'src-567244356665a527' = 'development-land-use/development-process/cabq-infrastructure-improvements-agreement-procedure-c.pdf'
  'src-fa4cf248a6dd7221' = 'development-land-use/development-process/cabq-revocable-permit-submittal-requirements-2020.pdf'
  'src-7f0d4c4f77185c6f' = 'public-works/stormwater/cabq-erosion-sediment-control-plan-permit-drc-process-2018.pdf'
  'src-a066bb85795d81d4' = 'public-works/stormwater/cabq-construction-stormwater-quality-submittal-process-2025.pdf'
  'src-98563dab32c38b5c' = 'public-works/stormwater/cabq-stormwater-quality-plan-fee-schedule.pdf'
  'src-5e74a3b59f6ef58f' = 'development-land-use/development-process/cabq-hydrology-review-fees-2024.pdf'
  'src-f3389ee4d757562d' = 'public-works/stormwater/cabq-fema-three-processes-remove-structure-flood-hazard-area.pdf'
  'src-42070e2d53434fef' = 'public-works/stormwater/cabq-special-flood-hazard-areas-explainer.pdf'
  'src-64ad8d6862df1b52' = 'transportation/design-references/cabq-subdivision-plat-drainage-easement-language-2018.pdf'
}

$decisions = foreach ($item in $research.approved_for_addition) {
  $id = [string]$item.id
  if (-not $keys.ContainsKey($id)) { throw "Missing R2 key for $id." }
  $locations = @([string]$item.proposed_canonical_page)
  foreach ($cross in @($item.cross_listings)) { if ($cross.page) { $locations += [string]$cross.page } }
  [ordered]@{
    id = $id
    title = [string]$item.title
    date = if ($item.PSObject.Properties.Name -contains 'date') { [string]$item.date } else { $null }
    source_page = [string]$item.authoritative_url
    direct_file_url = [string]$item.authoritative_url
    r2_key = [string]$keys[$id]
    canonical_page = [string]$item.proposed_canonical_page
    implementation_locations = @($locations)
    cross_listing_approved = [bool]($locations.Count -gt 1)
    description = [string]$item.description
    provenance_status = 'official City of Albuquerque file fetched directly; exact byte size and SHA-256 verified against the reviewed research artifact'
    large_file_assessment = if ($id -eq 'src-d74108ddea65eb7d') {
      'The 586-page regional manual is a substantive official reference incorporated by related City guidance. Its 35.42 MiB size is intrinsic to the original PDF, remains below the 100,000,000-byte object limit, and requires no transformation.'
    } else { $null }
    processing_notes = @(
      [string]$item.evidence,
      'Original authoritative PDF selected for byte-identical archival without modification.'
    )
  }
}

if (@($decisions).Count -ne 19) { throw "Expected 19 archive decisions; found $(@($decisions).Count)." }
[ordered]@{
  schema_version = 1
  batch_id = 'development-review-services-archive-2026-09-11'
  created_at = (Get-Date).ToUniversalTime().ToString('o')
  source_research = $ResearchPath
  decisions = @($decisions)
} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $OutputPath -Encoding utf8

[pscustomobject]@{ Items = @($decisions).Count; OutputPath = $OutputPath } | ConvertTo-Json -Compress
