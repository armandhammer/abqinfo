[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OutputPath = 'project-state/near-complete-review-decisions-2026-08-20.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Set-TerminalCandidate {
  param([string]$Id, [string]$Status, [string]$Reason, [string]$Note)
  $set = @{
    status = $Status
    exclusion_reason = $Reason
    validation_status = "terminal review decision recorded: $Status"
  }
  if ($Note) { $set.processing_notes = @($Note) }
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $Id -Set $set -InventoryPath $InventoryPath | Out-Null
}

$duplicates = @(
  @{ id='src-970dd55000ab7143'; canonical='src-16cf913dd9c6f11c'; note='Exact byte-for-byte duplicate of the existing R2-preserved Coal Avenue to MLK Avenue 90% plan set (9,422,283 bytes; matching SHA-256).' },
  @{ id='src-901a34f2e690948f'; canonical='src-7d1f0aa7fd43ecd7'; note='Exact byte-for-byte duplicate of the existing R2-preserved MLK Avenue to Lomas Boulevard draft 60% plan set (24,126,866 bytes; matching SHA-256).' },
  @{ id='src-09f5a299fc442e74'; canonical='src-860035d463be9d48'; note='Exact byte-for-byte duplicate of the existing R2-preserved MLK Avenue to Lomas Boulevard 60% cost estimate (145,319 bytes; matching SHA-256).' },
  @{ id='src-5062443b09866b08'; canonical='src-48a2030163390b5b'; note='Exact byte-for-byte duplicate of the existing R2-preserved signed July 2, 2025 Broadway Road Diet traffic evaluation (9,449,902 bytes; matching SHA-256).' },
  @{ id='src-1afac09e7e1653a8'; canonical='src-6ba7c575abb1ac19'; note='The 48,765,881-byte high-resolution file has the same normalized text on all 46 pages as the authoritative 4,661,965-byte City version already archived; it adds resolution but no substantive content.' }
)
foreach ($item in $duplicates) {
  Set-TerminalCandidate -Id $item.id -Status 'duplicate' -Reason "Duplicate of $($item.canonical)." -Note $item.note
}

Set-TerminalCandidate -Id 'src-b3e13fdc634d23d0' -Status 'superseded' -Reason 'The May 23, 2025 draft is superseded by the signed July 2, 2025 Broadway Road Diet traffic evaluation already archived.' -Note 'The 206-page draft was retained locally for audit history but is not separately published.'
Set-TerminalCandidate -Id 'src-0fb71091e519f961' -Status 'superseded' -Reason 'The February 2025 draft appendix is superseded by the complete March 2025 final Lead and Coal report and appendices already archived.' -Note 'The 67,842,414-byte draft appendix was retained locally for audit history but is not separately published.'
Set-TerminalCandidate -Id 'src-c6a954c08b541b43' -Status 'excluded' -Reason 'Generic international bus-corridor safety guide; not Albuquerque-specific and available from its original publisher.' -Note 'Reviewed because it appeared in the ART research folder; excluded under the project relevance standard.'

$lowValueAdvocacy = @(
  @{id='src-2e92cb18380275f6'; reason='One-page advocacy summary is substantially represented by the more detailed preserved ART public-comment records.'},
  @{id='src-4a62be61984d63f8'; reason='Short letter to a design consultant adds little unique information beyond the selected annotated design comments.'},
  @{id='src-65c9d6df022a6502'; reason='Two-page intervention request is a low-information advocacy fragment and is not needed beside the selected detailed opposition record.'},
  @{id='src-f8b73d7feeaa0f82'; reason='Short participatory-governance excerpt is secondary commentary and adds little unique project evidence.'}
)
foreach ($item in $lowValueAdvocacy) {
  Set-TerminalCandidate -Id $item.id -Status 'excluded' -Reason $item.reason -Note 'Curated out to preserve a concise, representative ART planning-history collection.'
}

$centralProvenance = 'requires review: City-branded September 2017 draft supplied from the project research archive; exact government-hosted source URL has not been recovered'
$centralNotes = @(
  'Original City-branded source file will be preserved without modification.',
  'September 2017 Draft for Comment / Potential Amendment to the Route 66 Action Plan; do not represent as an adopted plan.',
  'Exact government-hosted provenance remains unreconciled, so implementation must remain requires human review.'
)
$decisions = @(
  @{id='src-c1d5a2b0b33b331a';title='Central Avenue Station-Area Planning Draft — Introduction and Action Plan';date='2017-09';key='development-land-use/area-sector-plans/central-route-66-station-area-draft-2017-01-introduction.pdf';description='Introduces the 2017 draft station-area planning framework for Central Avenue, connecting ART investment with corridor development, public-realm improvements, implementation priorities, and a potential Route 66 Action Plan amendment.'},
  @{id='src-5f3ea18d2262dd4e';title='Central Avenue Station-Area Planning Draft — Station Types';date='2017-09';key='development-land-use/area-sector-plans/central-route-66-station-area-draft-2017-02-station-types.pdf';description='Defines draft station types and related land-use, public-space, access, parking, and development strategies intended to tailor transit-oriented investment to different Central Avenue contexts.';large='The 27,559,335-byte PDF is unusually large because it is a graphics-intensive planning chapter with maps, diagrams, and photographs. No smaller authoritative version was found; optimization would alter the source.'},
  @{id='src-80ee860e3cfa60bf';title='Central Avenue Station-Area Planning Draft — West Central';date='2017-09';key='development-land-use/area-sector-plans/central-route-66-station-area-draft-2017-03-west-central.pdf';description='Presents draft station-area strategies for West Central, including development opportunities, public-realm improvements, access, land use, and implementation concepts from Unser Boulevard toward the Rio Grande.';large='The 36,527,625-byte PDF is unusually large because it contains detailed maps, aerials, renderings, and photographs. No smaller authoritative version was found; optimization would alter the source.'},
  @{id='src-bad7cd0818045625';title='Central Avenue Station-Area Planning Draft — Old Town';date='2017-09';key='development-land-use/area-sector-plans/central-route-66-station-area-draft-2017-04-old-town.pdf';description='Presents draft station-area strategies for Old Town and nearby Central Avenue, addressing historic context, redevelopment opportunities, walking access, public space, and connections across the corridor.'},
  @{id='src-2641b5b13214d7ee';title='Central Avenue Station-Area Planning Draft — Downtown';date='2017-09';key='development-land-use/area-sector-plans/central-route-66-station-area-draft-2017-05-downtown.pdf';description='Presents draft Downtown Central Avenue strategies for development, streetscape, transit access, public space, parking, and connections among civic, cultural, employment, and residential destinations.';large='The 28,352,903-byte PDF is unusually large because it contains detailed maps, aerials, renderings, and photographs. No smaller authoritative version was found; optimization would alter the source.'},
  @{id='src-5ade756c56baac45';title='Central Avenue Station-Area Planning Draft — East Downtown';date='2017-09';key='development-land-use/area-sector-plans/central-route-66-station-area-draft-2017-06-edo.pdf';description='Presents draft East Downtown station-area strategies addressing redevelopment sites, neighborhood connections, pedestrian access, public space, parking, and growth around Central Avenue transit service.'},
  @{id='src-ed916e54f80ece6f';title='Central Avenue Station-Area Planning Draft — University Area';date='2017-09';key='development-land-use/area-sector-plans/central-route-66-station-area-draft-2017-07-university.pdf';description='Presents draft University-area strategies for Central Avenue, including campus and hospital access, development opportunities, pedestrian connections, public space, parking, and transit-supportive land use.';large='The 45,987,813-byte PDF is unusually large because it contains detailed maps, aerials, renderings, and photographs. No smaller authoritative version was found; optimization would alter the source.'},
  @{id='src-863e82803d9e7cac';title='Central Avenue Station-Area Planning Draft — Nob Hill';date='2017-09';key='development-land-use/area-sector-plans/central-route-66-station-area-draft-2017-08-nob-hill.pdf';description='Presents draft Nob Hill station-area strategies addressing corridor businesses, redevelopment, pedestrian access, streetscape, parking, historic character, and transit-supportive growth along Central Avenue.';large='The 29,848,895-byte PDF is unusually large because it contains detailed maps, aerials, renderings, and photographs. No smaller authoritative version was found; optimization would alter the source.'},
  @{id='src-c070ab7e5a4a2622';title='Central Avenue Station-Area Planning Draft — International District';date='2017-09';key='development-land-use/area-sector-plans/central-route-66-station-area-draft-2017-09-international-district.pdf';description='Presents draft International District station-area strategies for redevelopment, community services, pedestrian access, public space, economic opportunity, and transit-supportive investment along Central Avenue.';large='The 35,293,658-byte PDF is unusually large because it contains detailed maps, aerials, renderings, and photographs. No smaller authoritative version was found; optimization would alter the source.'},
  @{id='src-2bbfb64ecf6455b3';title='Central Avenue Station-Area Planning Draft — Equity and Inclusion';date='2017-09';key='development-land-use/area-sector-plans/central-route-66-station-area-draft-2017-10-equity-inclusion.pdf';description='Examines draft equity and inclusion strategies for Central Avenue investment, including displacement risks, community benefits, affordable housing, local businesses, access, and implementation considerations.'},
  @{id='src-d7b006f3aceaa405';title='Central Avenue Station-Area Planning Draft — Finance';date='2017-09';key='development-land-use/area-sector-plans/central-route-66-station-area-draft-2017-11-finance.pdf';description='Outlines potential financing and implementation tools for Central Avenue station-area improvements, redevelopment, infrastructure, public-private partnerships, incentives, and coordinated public investment.'},
  @{id='src-61107c696c0e35b5';title='Central Avenue Station-Area Planning Draft — Infrastructure';date='2017-09';key='development-land-use/area-sector-plans/central-route-66-station-area-draft-2017-12-infrastructure.pdf';description='Reviews infrastructure considerations supporting Central Avenue station-area development, including utilities, streets, public space, stormwater, access, planning, and coordinated capital improvements.'},
  @{id='src-e0748ccf7ebc1a77';title='Impact of Transit: Forecasting Future Value Along Central Avenue';date='2017';key='development-land-use/area-sector-plans/central-avenue-impact-of-transit-forecasting-future-value-2017.pdf';description='Models the fiscal and development value of Central Avenue transit investment, illustrating how land-use intensity and station-area growth could affect Albuquerque''s public-sector return on infrastructure.'}
)

foreach ($item in $decisions) {
  $item.agency = 'City of Albuquerque'
  $item.canonical = 'content/development-land-use/area-sector-plans.md'
  $item.provenance = $centralProvenance
  $item.notes = $centralNotes
}

$artDecisions = @(
  @{id='src-e80e0b49a4723c9a';title='The Scale of the Prize: Community Benefits of Bus Rapid Transit';date='2014';key='transportation/transit/art/the-scale-of-the-prize-community-benefits-of-brt-final.pdf';source='https://www.cabq.gov/economicdevelopment/the-scale-of-the-prize-community-benefits-of-transit-oriented-development';agency='City of Albuquerque / Center for Neighborhood Technology';description='Estimates the economic, household-cost, development, and community benefits of bus rapid transit along Central Avenue, providing an early City-commissioned case for the investment that became ART.';provenance='partial: City-commissioned final report; official City landing page preserves a marked draft, while the exact final-file URL remains unreconciled';notes=@('The supplied 42-page final report differs from the 41-page City-hosted copy marked DRAFT NOT FOR RELEASE.','Original final source file will be preserved without modification; exact final-file provenance remains requires human review.')},
  @{id='src-e88f5a097091c5db';title='ART Corridor Building Permits, October 2022–September 2023';date='2023';key='transportation/transit/art/art-corridor-building-permits-2022-2023.pdf';agency='City of Albuquerque';description='Maps building permits and reported construction value along the ART corridor from October 2022 through September 2023, preserving a concise snapshot of post-project development activity.';provenance='requires review: City-branded GIS map supplied from the project research archive; exact government-hosted source URL has not been recovered';notes=@('One-page City-branded GIS map visually reviewed.','Original source file will be preserved without modification; exact government-hosted provenance remains unreconciled.')},
  @{id='src-671b4bd36e11e0d9';title='ART Design Comments Submitted to the Transit Department';date='2015-12-02';key='transportation/transit/art/history/art-design-comments-to-transit-department-2015.pdf';agency='Coalition of Concerned Citizens';description='Preserves detailed public comments and annotations submitted during ART design, documenting concerns about alignment, access, medians, intersections, business effects, and proposed changes before construction.';provenance='requires review: historical public-comment file supplied from the project research archive; original submission URL has not been recovered';notes=@('Representative 14-page public-comment record selected from a larger advocacy folder.','Authorship is identified explicitly; original file will be preserved without modification.')},
  @{id='src-8903198f1d3c22e1';title='Coalition Response to City ART Mythbusters';date='2016-08-04';key='transportation/transit/art/history/coalition-response-to-art-mythbusters-2016.pdf';agency='Coalition of Concerned Citizens';description='Records a detailed contemporary opposition response to City claims about ART, preserving the project debate over ridership, safety, design, construction, business effects, funding, and public process.';provenance='requires review: historical advocacy file supplied from the project research archive; original publication URL has not been recovered';notes=@('Representative 17-page opposition record selected from a larger advocacy folder.','Authorship is identified explicitly; original file will be preserved without modification.')},
  @{id='src-aab5517438784db7';title='Summary of ART Meeting with the Transit Department';date='2015-12-02';key='transportation/transit/art/history/art-transit-department-meeting-summary-2015.pdf';agency='Coalition of Concerned Citizens';description='Summarizes a December 2015 meeting between ART opponents and the Transit Department, documenting questions, agency responses, disputed assumptions, design concerns, and the contemporary public process.';provenance='requires review: historical meeting summary supplied from the project research archive; original publication URL has not been recovered';notes=@('Representative six-page meeting record selected from a larger advocacy folder.','Authorship is identified explicitly; original file will be preserved without modification.')}
)
foreach ($item in $artDecisions) {
  $item.canonical = 'content/transportation/transit/abq-ride.md'
  $decisions += $item
}

$output = [ordered]@{
  batch_id = '2026-08-20-central-avenue-and-art-history'
  decisions = @($decisions | ForEach-Object {
    $record = [ordered]@{
      id = $_.id
      title = $_.title
      date = $_.date
      r2_key = $_.key
      canonical_page = $_.canonical
      source_page = if ($_.ContainsKey('source')) { $_.source } else { '' }
      agency = $_.agency
      description = $_.description
      decision = 'approved for addition'
      provenance_status = $_.provenance
      processing_notes = @($_.notes)
    }
    if ($_.ContainsKey('large')) { $record.large_file_assessment = $_.large }
    [pscustomobject]$record
  })
}

$output | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{ Decisions=$output.decisions.Count; Terminalized=12; OutputPath=$OutputPath } | ConvertTo-Json -Compress
