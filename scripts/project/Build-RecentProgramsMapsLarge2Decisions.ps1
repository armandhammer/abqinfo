[CmdletBinding()]
param(
  [string]$OutputPath = 'project-state/discovery/recent-programs-maps-large2-decisions.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$decisions = @(
  [pscustomobject][ordered]@{
    id = 'src-0c2d8157b7ae743b'
    title = 'MRMPO Annual Performance and Expenditure Report, FFY 2024'
    date = '2024'
    r2_key = 'transportation/transportation-plans/mrmpo-annual-performance-expenditure-report-ffy2024.pdf'
    canonical_page = 'content/transportation/transportation-plans.md'
    source_page = 'https://www.mrcog-nm.gov/310/Unified-Planning-Work-Program'
    direct_file_url = 'https://www.mrcog-nm.gov/DocumentCenter/View/6594/2024-Annual-Performance-and-Expenditue-Report-PDF'
    description = 'Documents MRMPO work and spending during FFY 2024, including the regional safety plan, traffic monitoring, development review, incident management, metropolitan planning, transit studies, ABQ RIDE planning, consultant work, staffing, and Title VI compliance.'
  }
  [pscustomobject][ordered]@{
    id = 'src-e440d0fcb2763709'
    title = 'MRMPO FFY 2024 Annual Listing of Obligations'
    date = '2024'
    r2_key = 'transportation/funding/mrmpo-ffy2024-annual-listing-obligations.pdf'
    canonical_page = 'content/transportation/transportation-plans.md'
    source_page = 'https://www.mrcog-nm.gov/278/Annual-Project-Listing-Obligation-Report'
    direct_file_url = 'https://www.mrcog-nm.gov/DocumentCenter/View/6454/FFY-2024-Annual-Listing-of-Obligations-PDF'
    description = 'Records federal transportation funds obligated in FFY 2024 for Albuquerque-area roadway, transit, bicycle, pedestrian, safety, and planning projects, distinguishing programmed amounts from actual obligations and identifying projects that advanced or remained unobligated.'
  }
  [pscustomobject][ordered]@{
    id = 'src-d4cc8f7b8355a863'
    title = 'MRMPO FFY 2023 Annual Listing of Obligations'
    date = '2023'
    r2_key = 'transportation/funding/mrmpo-ffy2023-annual-listing-obligations.pdf'
    canonical_page = 'content/transportation/transportation-plans.md'
    source_page = 'https://www.mrcog-nm.gov/278/Annual-Project-Listing-Obligation-Report'
    direct_file_url = 'https://www.mrcog-nm.gov/DocumentCenter/View/6116/FFY-2023-Annual-Listing-of-Obligations-PDF'
    description = 'Records federal transportation funds obligated in FFY 2023 for Albuquerque-area roadway, transit, bicycle, pedestrian, safety, and school projects, preserving programmed amounts, actual obligations, project phases, funding categories, and explanatory notes.'
  }
  [pscustomobject][ordered]@{
    id = 'src-3320d55997b148b0'
    title = 'Regional Transportation Safety Action Plan Area Safety Profiles'
    date = '2024'
    r2_key = 'transportation/roadway-projects/safety/mrmpo-rtsap-area-safety-profiles-2024.pdf'
    canonical_page = 'content/transportation/roadway-projects/speed-management.md'
    source_page = 'https://www.mrcog-nm.gov/638/Safety-Planning-Assistance'
    direct_file_url = 'https://www.mrcog-nm.gov/DocumentCenter/View/6465/Appendix-C-RTSAP-2024-Area-Safety-Profiles'
    description = 'Provides localized crash analyses for eleven communities, including Albuquerque''s International District, with fatal and serious-injury patterns, vulnerable-road-user findings, mapped concentrations, contributing factors, site observations, and recommended safety focus areas.'
  }
  [pscustomobject][ordered]@{
    id = 'src-29a1d22427148b89'
    title = 'Big I Approach Volumes, 1980-2024'
    date = '2024'
    r2_key = 'maps/mrmpo-big-i-approach-volumes-1980-2024.pdf'
    canonical_page = 'content/maps/maps.md'
    source_page = 'https://www.mrcog-nm.gov/623/Traffic-Flow-Maps-and-Busiest-Intersecti'
    direct_file_url = 'https://www.mrcog-nm.gov/DocumentCenter/View/6378/Big-I-Approach-Volumes-Historic-to-Current-2023-PDF'
    description = 'Charts observed average weekday traffic approaching Albuquerque''s Big I from 1980 through 2024, showing long-term growth, year-to-year variation, pandemic-era decline, recent recovery, and the fitted historical trend.'
    implementation_locations = @('content/maps/maps.md','content/transportation/roadway-projects/studies.md')
    cross_listing_approved = $true
  }
  [pscustomobject][ordered]@{
    id = 'src-36c8976c6dc16816'
    title = 'MRMPO Potential Road Diet Candidates Map'
    date = '2025'
    r2_key = 'maps/mrmpo-potential-road-diet-candidates-2025.pdf'
    canonical_page = 'content/transportation/roadway-projects/studies.md'
    source_page = 'https://www.mrcog-nm.gov/569/Road-Diet-Candidates-Map'
    direct_file_url = 'https://www.mrcog-nm.gov/DocumentCenter/View/6639/MRMPO_RoadDiets2023_Web20250523'
    description = 'Maps potential Albuquerque-area road-diet corridors using 2023 lane and traffic-volume data, grouping six-, eight-, and four-lane streets by preliminary priority while emphasizing that every candidate requires project-level engineering analysis.'
    implementation_locations = @('content/transportation/roadway-projects/studies.md','content/maps/maps.md')
    cross_listing_approved = $true
  }
  [pscustomobject][ordered]@{
    id = 'src-a814beef74b73265'
    title = 'New Mexico Transit Guide'
    date = '2023'
    r2_key = 'transportation/transit/nmdot-new-mexico-transit-guide-2023.pdf'
    canonical_page = 'content/transportation/transit/_index.md'
    source_page = 'https://www.dot.nm.gov/planning-research-multimodal-and-safety/modal/transit-rail/'
    direct_file_url = 'https://api.realfile.rtsclients.com/PublicFiles/f260a66b364d453e91ff9b3fedd494dc/35cf3c08-e0c8-42f3-8c65-412397ba8ab9/2023%20Transit%20Guide.pdf'
    description = 'Catalogs New Mexico transit providers, services, funding programs, regional districts, and connections, with dedicated Albuquerque, Rio Metro, Rail Runner, paratransit, university, veteran, and intercity information plus a statewide system map.'
  }
  [pscustomobject][ordered]@{
    id = 'src-c0f50c34651627f9'
    title = 'FY 2024 Section 5310, 5311, and 5339 Transit Budget Awards'
    date = '2024'
    r2_key = 'transportation/transit/nmdot-fy2024-fta-5310-5311-5339-budget-awards.pdf'
    canonical_page = 'content/transportation/transit/_index.md'
    source_page = 'https://www.dot.nm.gov/planning-research-multimodal-and-safety/modal/transit-rail/transit-bureau/'
    direct_file_url = 'https://api.realfile.rtsclients.com/PublicFiles/f260a66b364d453e91ff9b3fedd494dc/d3144877-9751-4ea0-8497-94c2fe4a60ab/FY%202024%20FTA%20Section%205310%205311%205339%20Budget%20Awards.pdf'
    description = 'Preserves FY 2024 federal transit award recommendations for Albuquerque mobility providers, Rio Metro, and statewide rural systems, including vehicle and equipment requests, operating support, applicant rankings, matching funds, and available balances.'
  }
  [pscustomobject][ordered]@{
    id = 'src-85e073f50952c5d2'
    title = 'FY 2023 Section 5310, 5311, and 5339 Transit Budget Awards'
    date = '2023'
    r2_key = 'transportation/transit/nmdot-fy2023-fta-5310-5311-5339-budget-awards.pdf'
    canonical_page = 'content/transportation/transit/_index.md'
    source_page = 'https://www.dot.nm.gov/planning-research-multimodal-and-safety/modal/transit-rail/transit-bureau/'
    direct_file_url = 'https://api.realfile.rtsclients.com/PublicFiles/f260a66b364d453e91ff9b3fedd494dc/91972cdd-0698-46c6-b201-a41dd629c5db/FY%202023%20FTA%20Section%205310%205311%205339%20Budget%20Awards.pdf'
    description = 'Preserves FY 2023 federal transit award recommendations for Albuquerque mobility providers and statewide systems, documenting vehicles, equipment, operating assistance, regional priorities, matching shares, procurement requirements, and program administration.'
  }
  [pscustomobject][ordered]@{
    id = 'src-8b49885f46b0b748'
    title = 'NMDOT FFY 2025-2026 Planning Work Program, as Amended'
    date = '2025-2026'
    r2_key = 'transportation/transportation-plans/nmdot-planning-work-program-ffy2025-2026-amended.pdf'
    canonical_page = 'content/transportation/transportation-plans.md'
    source_page = 'https://www.dot.nm.gov/planning-research-multimodal-and-safety/planning-division/'
    direct_file_url = 'https://api.realfile.rtsclients.com/PublicFiles/f260a66b364d453e91ff9b3fedd494dc/0eb13fa7-89c2-49cc-99f0-f0df1a5a1d17/Current%20FFY%202025-2026%20Planning%20Work%20Program%20As%20Amended.pdf'
    description = 'Defines NMDOT''s current statewide planning and research work, budgets, staffing, schedules, and deliverables, including Albuquerque-region coordination, Complete Streets implementation, bicycle-plan updates, safety programming, traffic data, freight, climate, and metropolitan planning support.'
  }
  [pscustomobject][ordered]@{
    id = 'src-639a0614f2314c1a'
    title = 'Isleta Boulevard Corridor Phase II Design Schedule'
    date = '2024-2027'
    r2_key = 'transportation/roadway-projects/current/bernco-isleta-boulevard-phase-2-design-schedule-2024-2027.pdf'
    canonical_page = 'content/transportation/roadway-projects/_index.md'
    source_page = 'https://www.bernco.gov/public-works/blog/2025/07/16/isleta-boulevard-reconstruction-phase-2-3/'
    direct_file_url = 'https://www.bernco.gov/public-works/wp-content/uploads/sites/76/2025/07/Isleta-Blvd-FINAL-DESIGN-PHASE-II-Schedule-MAR2024.pdf'
    description = 'Schedules design, environmental review, right-of-way acquisition, utility coordination, 60- and 90-percent reviews, final plans, bidding, and construction for Isleta Boulevard Phase II between Luchetti Road and Raymac Road.'
  }
  [pscustomobject][ordered]@{
    id = 'src-c6aad2951b9b5ab1'
    title = 'Second Street and Rio Bravo Intersection Construction Schedule'
    date = '2026-02-18'
    r2_key = 'transportation/roadway-projects/current/bernco-second-street-rio-bravo-construction-schedule-2026-02-18.pdf'
    canonical_page = 'content/transportation/roadway-projects/_index.md'
    source_page = 'https://www.bernco.gov/public-works/blog/2021/04/16/rio-bravo-2nd-st-intersection/'
    direct_file_url = 'https://www.bernco.gov/public-works/wp-content/uploads/sites/76/2026/02/A300942-2nd-and-Rio-Bravo-CPM-Pay-App-14-Schedule-Update.pdf'
    description = 'Provides the February 2026 contractor schedule for the Second Street and Rio Bravo intersection, tracking utility work, traffic control, paving, lighting, signals, drainage, bridge activities, milestones, completion percentages, and schedule constraints.'
  }
)

foreach ($decision in $decisions) {
  $wordCount = @($decision.description -split '\s+' | Where-Object { $_ }).Count
  if ($wordCount -lt 20 -or $wordCount -gt 50) { throw "$($decision.id) description has $wordCount words." }
  $decision | Add-Member -NotePropertyName processing_notes -NotePropertyValue @(
    'Original authoritative PDF preserved without modification.',
    'Description reviewed against complete extracted text and representative visual inspection.',
    'Selected under the recent-first, high-value review policy.'
  )
}

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json

$large = @($inventory.candidates | Where-Object id -eq 'src-c7fcd58b9998999c')
if ($large.Count -ne 1) { throw 'Expected one FFY 2025 APER candidate.' }
$large[0].status = 'requires human review'
$large[0].title = 'MRMPO Annual Performance and Expenditure Report, FFY 2025'
$large[0].date = '2025'
$large[0].proposed_canonical_page = 'content/transportation/transportation-plans.md'
$large[0].description = 'Documents MRMPO work, deliverables, staffing, and expenditures during FFY 2025, including safety, traffic monitoring, metropolitan planning, development review, incident management, transit studies, ABQ RIDE activities, consultant work, and Title VI compliance.'
$large[0].description_word_count = @($large[0].description -split '\s+' | Where-Object { $_ }).Count
$large[0].validation_status = 'content reviewed; production archival requires explicit approval because the original is larger than 100 MB'
$large[0].processing_notes = @(@($large[0].processing_notes) + 'Exact source size is 135,951,095 bytes (129.65 MiB); original remains local and was not uploaded to R2.' | Sort-Object -Unique)
$large[0].updated_at = (Get-Date).ToUniversalTime().ToString('o')

$notice = @($inventory.candidates | Where-Object id -eq 'src-0867b997bbdfdd3e')
if ($notice.Count -ne 1) { throw 'Expected one Isleta sewer-lining notice candidate.' }
$notice[0].status = 'excluded'
$notice[0].exclusion_reason = 'Short-lived 2025 utility construction notice for completed sewer lining; it does not add durable planning, design, or project-history value beyond the maintained corridor and utility sources.'
$notice[0].validation_status = 'reviewed and excluded for low durable informational value'
$notice[0].processing_notes = @(@($notice[0].processing_notes) + 'Reviewed complete two-page notice; not archived or published.' | Sort-Object -Unique)
$notice[0].updated_at = (Get-Date).ToUniversalTime().ToString('o')

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
[IO.File]::WriteAllText([IO.Path]::GetFullPath($InventoryPath), ($inventory | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))

[ordered]@{
  schema_version = 1
  batch_id = 'recent-programs-maps-large2'
  decisions = $decisions
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8

[pscustomobject]@{ Decisions=$decisions.Count; RequiresHumanReview=1; Excluded=1; OutputPath=$OutputPath } | ConvertTo-Json -Compress
