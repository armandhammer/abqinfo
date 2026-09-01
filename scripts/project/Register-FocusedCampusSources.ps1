[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$records = @(
  [ordered]@{
    SourceUrl = 'https://css.unm.edu/campus-planning/safe-mobility-action-plan.pdf'
    DirectFileUrl = 'https://css.unm.edu/campus-planning/safe-mobility-action-plan.pdf'
    Agency = 'University of New Mexico'
    Title = 'UNM Safe Mobility Action Plan'
    Date = '2025'
    FileType = 'PDF'
    ParentUrl = 'https://css.unm.edu/campus-planning/'
    DiscoveryMethod = 'user-supplied official source and authoritative campus-planning graph'
    CrawlDepth = 1
    SizeBytes = 23147270
    ChecksumSha256 = $null
    Notes = @(
      'High-value Albuquerque campus transportation and safety plan. Review for Transportation Plans, bicycling, pedestrian safety, transit, and Maps placement.',
      'The 216-page single-page edition is the preferred official archival candidate. Its extracted content is effectively equivalent to the 252,884,404-byte two-page-spread edition, so no source modification is needed.'
    )
  },
  [ordered]@{
    SourceUrl = 'https://css.unm.edu/campus-planning/adopted-unm_integrated_campus_plan.pdf'
    DirectFileUrl = 'https://css.unm.edu/campus-planning/adopted-unm_integrated_campus_plan.pdf'
    Agency = 'University of New Mexico'
    Title = 'UNM Integrated Campus Plan'
    Date = '2025'
    FileType = 'PDF'
    ParentUrl = 'https://css.unm.edu/campus-planning/'
    DiscoveryMethod = 'authoritative campus-planning graph'
    CrawlDepth = 1
    SizeBytes = 105645375
    ChecksumSha256 = $null
    Notes = @(
      'Review only Albuquerque-relevant chapters, maps, transportation systems, development proposals, and systemwide policies materially governing the Albuquerque campuses.',
      'The official file exceeds the project 100 MB production-upload threshold and must not be uploaded to R2 without explicit user approval.'
    )
  },
  [ordered]@{
    SourceUrl = 'https://sustainability.unm.edu/assets/unm-sustainability_strategic-plan_2025-30.pdf'
    DirectFileUrl = 'https://sustainability.unm.edu/assets/unm-sustainability_strategic-plan_2025-30.pdf'
    Agency = 'University of New Mexico'
    Title = 'UNM Sustainability Strategic Plan 2025-2030'
    Date = '2025'
    FileType = 'PDF'
    ParentUrl = 'https://sustainability.unm.edu/'
    DiscoveryMethod = 'official UNM plan cross-reference'
    CrawlDepth = 2
    SizeBytes = 13239037
    ChecksumSha256 = $null
    Notes = @('Transportation goals reference Safe Mobility Action Plan implementation, alternative commuting, bicycle and micromobility infrastructure, and City coordination.')
  },
  [ordered]@{
    SourceUrl = 'https://www.cnm.edu/locations/main-campus'
    DirectFileUrl = $null
    Agency = 'Central New Mexico Community College'
    Title = 'CNM Main Campus'
    Date = $null
    FileType = 'Web page'
    ParentUrl = $null
    DiscoveryMethod = 'user-requested official source scope'
    CrawlDepth = 0
    SizeBytes = $null
    ChecksumSha256 = $null
    Notes = @('Canonical CNM scope root. Follow only Main Campus planning, capital projects, maps, transportation, parking, bicycle, pedestrian, transit, accessibility, sustainability, and public-realm pathways.')
  },
  [ordered]@{
    SourceUrl = 'https://www.cnm.edu/depts/finance-operations/business-office/purchasing/documents/master-plan-project-list.pdf'
    DirectFileUrl = 'https://www.cnm.edu/depts/finance-operations/business-office/purchasing/documents/master-plan-project-list.pdf'
    Agency = 'Central New Mexico Community College'
    Title = 'CNM Fiscal Year 2025 Master Plan Projects List'
    Date = '2025'
    FileType = 'PDF'
    ParentUrl = 'https://www.cnm.edu/depts/finance-operations/business-office/purchasing/master-plan-projects-list'
    DiscoveryMethod = 'authoritative CNM planning graph'
    CrawlDepth = 1
    SizeBytes = 241789
    ChecksumSha256 = '346a07a77359c4c8427567606e46bacd88a89f1c6537f31bce50f918c3229f48'
    Notes = @('Five-page capital list includes Main Campus demolition, renovation, student-services, public-safety, trades, utility, landscape, and facility projects. Exclude unrelated campus entries during placement.')
  },
  [ordered]@{
    SourceUrl = 'https://www.cnm.edu/locations/documents/main-campus-map-may-2026'
    DirectFileUrl = 'https://www.cnm.edu/locations/documents/main-campus-map-may-2026'
    Agency = 'Central New Mexico Community College'
    Title = 'CNM Main Campus Map - May 2026'
    Date = '2026'
    FileType = 'PDF'
    ParentUrl = 'https://www.cnm.edu/locations/main-campus'
    DiscoveryMethod = 'authoritative CNM Main Campus page'
    CrawlDepth = 1
    SizeBytes = 566698
    ChecksumSha256 = 'e19a62e83910de18189705ef9f846f2c1773e3344ec0d3752db29483a57ee6a7'
    Notes = @('Current official map identifies buildings, parking, EV charging, ADA parking and entrances, crosswalks, the Wellness Path, bicycle racks, and future facilities.')
  },
  [ordered]@{
    SourceUrl = 'https://maps.cnm.edu/?id=1934'
    DirectFileUrl = $null
    Agency = 'Central New Mexico Community College'
    Title = 'CNM Interactive Campus Map'
    Date = $null
    FileType = 'Interactive map'
    ParentUrl = 'https://www.cnm.edu/locations/main-campus'
    DiscoveryMethod = 'authoritative CNM Main Campus page'
    CrawlDepth = 1
    SizeBytes = $null
    ChecksumSha256 = $null
    Notes = @('Rendered-browser validation is required before implementation; confirm that the direct user-facing view can be scoped to Main Campus.')
  },
  [ordered]@{
    SourceUrl = 'https://www.cnm.edu/depts/parking-and-fleet-services/parking-and-fleet-services'
    DirectFileUrl = $null
    Agency = 'Central New Mexico Community College'
    Title = 'CNM Parking and Fleet Services'
    Date = $null
    FileType = 'Web page'
    ParentUrl = 'https://www.cnm.edu/locations/main-campus'
    DiscoveryMethod = 'authoritative CNM Main Campus transportation pathway'
    CrawlDepth = 1
    SizeBytes = $null
    ChecksumSha256 = $null
    Notes = @('Review only durable Main Campus public-transport, EV-charging, bicycle-parking, accessibility, and parking-map information.')
  }
)

foreach ($record in $records) {
  $candidateArgs = @{
    SourceUrl = $record.SourceUrl
    Agency = $record.Agency
    Title = $record.Title
    FileType = $record.FileType
    DiscoveryMethod = $record.DiscoveryMethod
    CrawlDepth = $record.CrawlDepth
    InventoryPath = $InventoryPath
  }
  if ($record.DirectFileUrl) { $candidateArgs.DirectFileUrl = $record.DirectFileUrl }
  if ($record.Date) { $candidateArgs.Date = $record.Date }
  if ($record.ParentUrl) { $candidateArgs.ParentUrl = $record.ParentUrl }
  & "$PSScriptRoot/Add-InventoryCandidate.ps1" @candidateArgs | Out-Null
}

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
foreach ($record in $records) {
  $candidate = @($inventory.candidates | Where-Object source_url -eq $record.SourceUrl)
  if ($candidate.Count -ne 1) { throw "Expected one inventory record for $($record.SourceUrl); found $($candidate.Count)." }
  if ($null -ne $record.SizeBytes) { $candidate[0].size_bytes = $record.SizeBytes }
  if ($record.ChecksumSha256) { $candidate[0].checksum_sha256 = $record.ChecksumSha256 }
  $candidate[0].processing_notes = @($candidate[0].processing_notes) + @($record.Notes) | Select-Object -Unique
  $candidate[0].updated_at = '2026-09-01T00:00:00Z'
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) {
  $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count
}
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = '2026-09-01T00:00:00Z'
$json = $inventory | ConvertTo-Json -Depth 15
[IO.File]::WriteAllText([IO.Path]::GetFullPath($InventoryPath), $json, [Text.UTF8Encoding]::new($false))

[pscustomobject]@{
  registered = $records.Count
  pending_review = @($records | Where-Object { $_ }).Count
  cnm_records = @($records | Where-Object Agency -eq 'Central New Mexico Community College').Count
  unm_records = @($records | Where-Object Agency -eq 'University of New Mexico').Count
}
