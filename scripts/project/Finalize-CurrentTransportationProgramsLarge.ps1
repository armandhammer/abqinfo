[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$R2InventoryPath = 'project-state/r2-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$updates = @(
  @{ id='src-1026d674bbbf2619'; title='NMDOT FY 2026 Section 5310, 5311, and 5339 Transit Budget Awards'; date='2025-05'; key='transportation/transit/nmdot-fy2026-fta-5310-5311-5339-budget-awards.pdf'; page='content/transportation/transit/_index.md'; locations=@('content/transportation/transit/_index.md'); description='Documents current federal transit award recommendations, including Albuquerque Section 5310 vehicles for disability and senior-service providers, Rio Metro capital awards, statewide rural-transit operating support, requests, rankings, matching funds, and program deadlines.' },
  @{ id='src-154dddf5a53708aa'; title='NMDOT FY 2025 Section 5310, 5311, and 5339 Transit Budget Awards'; date='2024-05'; key='transportation/transit/nmdot-fy2025-fta-5310-5311-5339-budget-awards.pdf'; page='content/transportation/transit/_index.md'; locations=@('content/transportation/transit/_index.md'); description='Preserves the preceding award cycle for Albuquerque mobility providers and Rio Metro, documenting requested and recommended vehicles, federal and local shares, applicant rankings, statewide rural-transit awards, capital history, and administrative requirements.' },
  @{ id='src-f65b90995cb80ae0'; title='NMDOT State Management Plan for Federal Transit Grants'; date='2025'; key='transportation/transit/nmdot-state-management-plan-transit-grants-2025.pdf'; page='content/transportation/transit/_index.md'; locations=@('content/transportation/transit/_index.md'); description='Defines how NMDOT administers federal transit funding, including program eligibility, project selection, coordination, procurement, financial controls, vehicles, property, oversight, civil rights, safety, drug-and-alcohol compliance, and grant closeout.' },
  @{ id='src-fafc18484f76379b'; title='MRMPO Unified Planning Work Program Progress Report, FFY 2026 Quarter 1'; date='2026-01'; key='transportation/transportation-plans/mrmpo-upwp-progress-report-ffy2026-q1.pdf'; page='content/transportation/transportation-plans.md'; locations=@('content/transportation/transportation-plans.md'); description='Tracks MRMPO work completed through December 2025 across TIP administration, data collection, safety, active transportation, regional planning, corridor studies, public engagement, ABQ RIDE planning, Rio Metro coordination, and the UNM/CNM transit study.' },
  @{ id='src-4985178a468a3575'; title='NMDOT Section 130 Highway-Rail Grade Crossing Safety Manual'; date='2025-11'; key='transportation/transit/rail-runner/nmdot-section-130-grade-crossing-safety-manual-2025.pdf'; page='content/transportation/transit/rail-runner.md'; locations=@('content/transportation/transit/rail-runner.md'); description='Defines the current statewide process for identifying, ranking, funding, designing, inspecting, and closing public highway-rail crossings, including crash history, train and roadway exposure, corridor projects, diagnostic reviews, agreements, and reporting.' },
  @{ id='src-787e833d60d98ea5'; title='NMDOT Transit and Rail Division Fact Sheet'; date='2026-02'; key='transportation/transit/nmdot-transit-rail-division-fact-sheet-2026.pdf'; page='content/transportation/transit/_index.md'; locations=@('content/transportation/transit/_index.md','content/transportation/transit/rail-runner.md'); description='Summarizes current NMDOT transit and rail programs with FY 2025 ridership, service, fleet, funding, Rail Runner, Park and Ride, Albuquerque paratransit-provider, regional-district, grade-crossing, and freight-rail statistics.' },
  @{ id='src-30975754bfb3814b'; title='NMDOT CMAQ and Carbon Reduction Program Guide, FFY 2026-2028'; date='2024-11'; key='transportation/transportation-plans/nmdot-cmaq-crp-program-guide-ffy2026-2028.pdf'; page='content/transportation/transportation-plans.md'; locations=@('content/transportation/transportation-plans.md'); description='Explains eligible emissions-reduction and carbon-reduction projects, available funding, local matches, federal requirements, application scoring, schedules, project delivery, and reimbursement for local and tribal agencies seeking FFY 2026-2028 awards.' },
  @{ id='src-7825ff6ffdb62504'; title='NMDOT Transportation Alternatives and Recreational Trails Program Guide, FFY 2026+'; date='2024-11'; key='transportation/transportation-plans/nmdot-tap-rtp-program-guide-ffy2026.pdf'; page='content/transportation/transportation-plans.md'; locations=@('content/transportation/transportation-plans.md'); description='Guides local agencies through funding for walking, bicycling, Safe Routes to School, trails, historic transportation facilities, streetscapes, and related projects, including eligibility, applications, scoring, matching funds, federal requirements, and project delivery.' },
  @{ id='src-0c0a09c86638f4c2'; title="Albuquerque Metropolitan Area's 25 Busiest Intersections"; date='2025-11'; key='maps/mrmpo-busiest-intersections-2024.pdf'; page='content/maps/maps.md'; locations=@('content/maps/maps.md'); description="Maps and ranks the region's 25 highest approach-volume intersections, reports 2024 counts, and compares each location's rank and volume with 2019-2023 data to show changing traffic patterns." },
  @{ id='src-21df738018b6a39f'; title='East Mountains Traffic Flows'; date='2025-09'; key='maps/mrmpo-east-mountains-traffic-flows-2024.pdf'; page='content/maps/maps.md'; locations=@('content/maps/maps.md'); description='Maps 2024 average annual weekday traffic on I-40, NM 14, NM 333, NM 337, NM 344, Frost Road, and local routes across eastern Bernalillo County, with a six-year vehicle-miles-traveled trend.' },
  @{ id='src-bc8bf8824f053ef6'; title='Greater Albuquerque Area Traffic Flows'; date='2025-09'; key='maps/mrmpo-greater-albuquerque-traffic-flows-2024.pdf'; page='content/maps/maps.md'; locations=@('content/maps/maps.md'); description='Maps 2024 average annual weekday traffic across Albuquerque and adjoining communities, with roadway-segment counts, volume categories, Uptown and Downtown insets, and a 2019-2024 metropolitan vehicle-miles-traveled trend.' },
  @{ id='src-6c78a9b8c3dc88b8'; title='NMDOT Green Stormwater Infrastructure Maintenance Manual'; date='2024-04'; key='public-works/stormwater-drainage/nmdot-green-stormwater-infrastructure-maintenance-manual-2024.pdf'; page='content/public-works/stormwater-drainage.md'; locations=@('content/public-works/stormwater-drainage.md','content/transportation/design-references.md'); description='Provides field-ready inspection and maintenance guidance for stormwater-harvesting basins and bioswales, addressing infiltration, sediment, erosion, vegetation, mulch, irrigation, roadway sight lines, worker safety, seasonal scheduling, remediation, and standardized checklists.' }
)

$r2 = Get-Content -Raw -Encoding UTF8 -LiteralPath $R2InventoryPath | ConvertFrom-Json
foreach ($update in $updates) {
  $object = @($r2.objects | Where-Object key -eq $update.key)
  if ($object.Count -ne 1) { throw "Expected one R2 object for $($update.key); found $($object.Count)." }
  $candidate = (Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json).candidates | Where-Object id -eq $update.id
  if ($candidate.status -in @('implemented', 'validated') -and $candidate.r2_key -eq $update.key) { continue }
  $notes = @(
    "Downloaded exact size: $($candidate.size_bytes) bytes; SHA-256 $($candidate.checksum_sha256).",
    'PDF text and representative first, middle, and final pages were reviewed; no XFA placeholder or visual defect was found.',
    'Public R2 copy verified byte-identical to the authoritative download on 2026-09-02.'
  )
  if ([int64]$candidate.size_bytes -gt 25MB) {
    $notes += 'File exceeds 25 MB because it is a high-resolution print map with detailed cartography; no smaller authoritative edition was identified and no optimization was performed.'
  }
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $update.id -InventoryPath $InventoryPath -Set @{
    status = 'implemented'
    title = $update.title
    date = $update.date
    file_type = 'PDF'
    r2_key = $update.key
    r2_url = $object[0].public_url
    r2_etag = $object[0].etag
    r2_last_modified = $object[0].last_modified
    provenance_status = 'authoritative government source and byte-identical ABQInfo archive verified'
    proposed_canonical_page = $update.page
    description = $update.description
    implementation_location = $update.page
    implementation_locations = $update.locations
    cross_listing_approved = ($update.locations.Count -gt 1)
    validation_status = 'not run'
    processing_notes = $notes
  } | Out-Null
}

& "$PSScriptRoot/Update-Candidate.ps1" -Id 'src-02908d0d50d14467' -InventoryPath $InventoryPath -Set @{
  status = 'superseded'
  cited_successors = @('src-56302a72a506fb36')
  exclusion_reason = 'The statewide 2024 safety-target report is older than the validated 2026 regional performance-measures assessment already published on ABQInfo.'
  validation_status = 'superseded by current regional performance assessment'
  processing_notes = @('Reviewed locally; retained in staging but not archived or published because a newer Albuquerque-region assessment is already implemented.')
} | Out-Null

[pscustomobject]@{ implemented = $updates.Count; superseded = 1 }
