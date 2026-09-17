[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$MetaPath,
  [string]$OutputPath = 'project-state/discovery/early-go-bond-cluster-research-2026-09-11.json'
)

# Research lane only. Reads the inventory and a scratch metadata file and writes
# one dated decision artifact. It never modifies master-inventory.json or checkpoint.json.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$capital = 'content/city-data/capital-spending.md'
$streets = 'content/transportation/transportation-plans.md'
$parks = 'content/public-works/parks-recreation.md'
$transit = 'content/transportation/transit/abq-ride.md'
$safety = 'content/city-data/public-safety-data.md'
$devproc = 'content/development-land-use/development-process.md'

$approved = @(
  [ordered]@{id='src-cae140d675779242';title='2003 Capital Improvements Plan Priorities and Criteria Resolution R-02-30';date='2002';pages=16;page=$capital;cross=@();description='Establishes Albuquerque priorities for the 2003 capital improvements plan, defines the criteria used to rate project proposals, assigns weights to those criteria, and allocates amounts among purposes within the 2003 general obligation bond program.';evidence='Enactment 34-2002. Directly parallel to resolutions R-2006-089 and R-2008-017 already published on the capital-spending page.'}
  [ordered]@{id='src-93085b1bc76f4709';title='2003-2012 Decade Plan and 2003 Two-Year Capital Budget Resolution R-03-215';date='2003';pages=19;page=$capital;cross=@();description='Approves the programming of funds and projects for the 2003-2012 decade plan for capital improvements, including the 2003 two-year capital budget, with category, project-title, and amount tables adopted by the City Council.';evidence='Enactment 49-2003. Amended by R-03-265 (src-d86965da6d5d26f2), which must be presented alongside it.'}
  [ordered]@{id='src-d86965da6d5d26f2';title='2003 Capital Budget Amendment Resolution R-03-265';date='2003';pages=2;page=$capital;cross=@();description='Amends resolution R-03-215 to add the Paseo del Norte extension from Golf Course Road to Kimmick, programming $11.5 million and restating the total general obligation bond capital budget at $156,838,460.';evidence='Enactment 79-2003. An enacted amending resolution, not an isolated floor amendment; it revises the adopted totals in R-03-215.'}
  [ordered]@{id='src-57a1e412247c863d';title='2003 General Obligation Bond Funding Allocation Chart';date='2003';pages=1;page=$capital;cross=@();description='Compares the percentage allocated under resolution R-02-30, the approved amount, and the share of the approved program for each department and division, totaling $155,478,730 across streets, hydrology, transit, parks, public safety, community facilities, and neighborhood set-asides.';evidence='Visually reviewed: a detailed allocation comparison table, unlike the one-page percentage pie chart src-7405cfc41e5500c4 that was excluded. Parallel to the 2009 funding allocation chart already published.'}
  [ordered]@{id='src-3dfd629f27870dc1';title='2003 General Obligation Bond Rehabilitation, Maintenance, and Deficiency Remediation Summary';date='2003';pages=1;page=$capital;cross=@();description='Breaks the $155,478,730 approved 2003 bond program into rehabilitation and deficiency-remediation shares by funding category, reporting that 88.98 percent of the program addressed existing rehabilitation and deficiency needs.';evidence='Visually reviewed: a detailed seven-category funding table with percentages, not a summary graphic.'}
  [ordered]@{id='src-6fc996f849849028';title='2003 Street General Obligation Bond Project Scopes';date='2003';pages=7;page=$capital;cross=@($streets);description='Details the 2003 street bond scopes, including Fourth Street corridor improvements, public infrastructure rebuilding, paving rehabilitation, intersection and signal work, bridges, sidewalks, trails, and named corridor projects across the City.';evidence='Seven-page project-scope table with 54 dollar figures; the same document class as the already-validated 2003 storm sewer scopes src-e28f489ec0fba72f.'}
  [ordered]@{id='src-96e217080e84c14e';title='2003 Parks and Recreation General Obligation Bond Project Scopes';date='2003';pages=5;page=$capital;cross=@($parks);description='Details 2003 parks and recreation bond scopes, including a velodrome developed with the Southwest Velodrome Association, park and open-space improvements, recreation facilities, trails, and related equipment purchases.';evidence='Five-page project-scope table with 46 dollar figures.'}
  [ordered]@{id='src-321df68eff322421';title='2003 Senior, Family, and Community Center General Obligation Bond Project Scopes';date='2003';pages=2;page=$capital;cross=@();description='Details 2003 bond scopes for senior, family, and community centers, including Bear Canyon Senior Center, Wells Park and McKinley community centers, and related facility improvements and equipment purchases.';evidence='Two-page project-scope table with 19 dollar figures.'}
  [ordered]@{id='src-3c7653f64815b4ad';title='2003 Zoo, Biological Park, and Museum General Obligation Bond Project Scopes';date='2003';pages=2;page=$capital;cross=@();description='Details 2003 bond scopes for the Albuquerque Museum, Biological Park, and Zoo, covering facility improvements, exhibit and collection work, heavy equipment and vehicle replacement, and related equipment purchases.';evidence='Two-page project-scope table with 14 dollar figures.'}
  [ordered]@{id='src-a24b9d451e022e8f';title='2003 Public Facilities, Equipment, and System Modernization General Obligation Bond Project Scopes';date='2003';pages=2;page=$capital;cross=@();description='Details 2003 bond scopes for computerized mapping and geographic records, hardware, software and consulting, City facility improvements, equipment replacement, and other system-modernization investments across departments.';evidence='Two-page project-scope table with 21 dollar figures.'}
  [ordered]@{id='src-e7cd892adf805950';title='2003 Public Transportation General Obligation Bond Project Scopes';date='2003';pages=1;page=$capital;cross=@($transit);description='Details 2003 transit bond scopes, including the Alvarado Transportation Center depot joint-use facility, bus storage and maintenance equipment, and related transit vehicle and facility investments.';evidence='One-page project-scope table with 11 dollar figures.'}
  [ordered]@{id='src-ea516f826e5da86a';title='2003 Police General Obligation Bond Project Scopes';date='2003';pages=1;page=$capital;cross=@($safety);description='Details 2003 police bond scopes, including improvements and equipment at the John Carrillo Memorial Substation, replacement of marked police vehicles at the end of their useful life, and related equipment purchases.';evidence='One-page project-scope table with 10 dollar figures.'}
  [ordered]@{id='src-724dd13839ecb166';title='2003 Fire Protection General Obligation Bond Project Scopes';date='2003';pages=1;page=$capital;cross=@($safety);description='Details $6,039,565 in 2003 fire protection bond scopes, covering emergency response apparatus replacement, renovation of Fire Stations 1, 10, 12, 16, 2, and 4, a heavy technical rescue vehicle, new Fire Station 21, and public art.';evidence='Visually reviewed because the PDF uses glyph-encoded text that defeats extraction; the rendered page is a detailed project-scope table totaling $6,039,565.'}
  [ordered]@{id='src-888427a6abc5edf0';title='2003 Library General Obligation Bond Project Scopes';date='2003';pages=1;page=$capital;cross=@();description='Details 2003 library bond scopes for purchasing books, periodicals, audiovisual materials, and electronic resources to meet customer demand, replace outdated materials, and provide educational and informational materials across all City libraries.';evidence='One-page project-scope table with 7 dollar figures.'}
  [ordered]@{id='src-230753126ba3bbf7';title='Rules and Regulations Governing Compensation for Consulting Engineers, Architects, and Landscape Architects';date='2003';pages=12;page=$devproc;cross=@();description='Sets City rules adopted under Revised Ordinances Section 7-20-5 for negotiating consultant compensation as a percentage of estimated construction cost, covering negotiation limits, scope definition, special studies, alternative methods, and biennial percentage review.';evidence='Visually reviewed twelve-page policy document; fits the Public Infrastructure Cost Estimating section alongside the City Engineer unit-price schedules.'}
  [ordered]@{id='src-8c5d2888cc22b991';title='2004 Street General Obligation Bond Project Titles, Amounts, and Scopes';date='2004';pages=10;page=$capital;cross=@($streets);description='Lists each 2004 street bond project with its title, amount, and scope, covering advance right-of-way acquisition, paving rehabilitation, intersections, bridges, sidewalks, trails, traffic management, and named corridor improvements.';evidence='Ten-page project title, amount, and scope table with 47 dollar figures.'}
  [ordered]@{id='src-f1a9e4e7e1d84e9e';title='2004 Capital Programming Amendment Resolution R-04-109';date='2004';pages=5;page=$capital;cross=@();description='Amends the approval of programming of funds and projects for the capital improvements decade plan, adjusting adopted project allocations through enacted City Council action with bracketed additions and deletions shown.';evidence='Five-page enacted resolution text with 43 dollar figures.'}
  [ordered]@{id='src-6ebb9f0834bce393';title='2004 Street Bond Program Summary of Planning Process';date='2004';pages=5;page=$capital;cross=@();description='Summarizes how the 2004 street project program was created during the 2002-2003 planning period and reviewed under the Capital Improvement Program ordinance, describing the capital implementation program and the required review steps.';evidence='Five-page process narrative; parallel to the already-published 2007 Capital Program Policies and Project-Selection Criteria.'}
  [ordered]@{id='src-a58b458f5d0f5284';title='2004 Street Bond Ballot Question';date='2004-11-02';pages=1;page=$capital;cross=@($streets);description='Preserves the exact street bond question placed before Albuquerque voters on November 2, 2004, authorizing $52,514,950 in general obligation bonds to study, design, construct, rehabilitate, landscape, and otherwise improve streets and acquire land and equipment.';evidence='Voter-facing ballot text; parallel to the published voter-facing 2021 General Obligation Bond Program by Purpose companion.'}
)

$excluded = @(
  [ordered]@{id='src-bd084d192e7b78ce';item='2003 bond frequently asked questions';reason='Voter-education question-and-answer sheet explaining what general obligation bonds are and how tax rates work. It carries no project list, scope, schedule, or allocation detail, matching the reasoning already applied to src-7405cfc41e5500c4.'}
  [ordered]@{id='src-fc8f89e3581f75f9';item='2004 frequently asked questions and answers';reason='Voter-education question-and-answer sheet on general obligation bond mechanics and property-tax effects, with no capital-program detail.'}
  [ordered]@{id='src-1fc92434d9abc641';item='2004 dollar amounts and percentages by purpose';reason='One-page percentage-and-dollar breakdown by bond purpose with no project lists, locations, schedules, or scopes. This is the same document class as src-7405cfc41e5500c4, which was already excluded for exactly this reason.'}
  [ordered]@{id='src-85c6a14af1cfa182';item='2004 bond program staff contacts';reason='Internal staff telephone directory listing department directors and contact persons from 2004. The repository item-specific contact policy covers current project contacts, not a stale general staff roster, and it carries no capital-program content.'}
)

$humanReview = @(
  [ordered]@{id='src-3c9907796a0cfaf3';item='Water Master Plan Infrastructure Zone (WIZ) map';reason='A self-contained official City map showing the Water Master Plan Infrastructure Zone boundary, but paginated "B-6", indicating it is an appendix page of a larger parent document that was not located in the 2003 bond directory. Decide whether to publish the standalone map or first locate and archive the parent plan.'}
  [ordered]@{id='src-6735737588d294e0';item='2003 Environmental Planning Commission hearing recommendations and decision notifications';reason='Fifteen pages of official EPC notification-of-decision letters on the 2003 capital improvements program. The Environmental Planning Commission hearing is a required step in the capital ordinance process, so the record is substantive governance, but its form is procedural notification rather than a plan or scope document. Needs an editorial decision on whether ABQInfo preserves EPC decision notifications as a class.'}
)

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$index = @{}
foreach ($candidate in @($inventory.candidates)) { $index[[string]$candidate.id] = $candidate }

$meta = @{}
if ($MetaPath -and (Test-Path -LiteralPath $MetaPath)) {
  foreach ($row in @(Get-Content -Raw -LiteralPath $MetaPath | ConvertFrom-Json)) { $meta[[string]$row.id] = $row }
}

function Get-Url($Id) {
  $c = $index[$Id]
  if (-not $c) { throw "Missing candidate $Id." }
  if ($c.direct_file_url) { return [string]$c.direct_file_url }
  return [string]$c.source_url
}
function Get-Meta($Id, [string]$Field) {
  if ($meta.ContainsKey($Id)) { return $meta[$Id].$Field }
  return $null
}

$approvedRows = @($approved | ForEach-Object {
  [ordered]@{
    id = $_.id
    recommended_status = 'approved for addition'
    title = $_.title
    date = $_.date
    pages = $_.pages
    authoritative_url = Get-Url $_.id
    size_bytes = Get-Meta $_.id 'bytes'
    checksum_sha256 = Get-Meta $_.id 'sha'
    proposed_canonical_page = $_.page
    proposed_cross_listings = @($_.cross)
    description = $_.description
    description_word_count = @($_.description -split '\s+' | Where-Object { $_ }).Count
    evidence = $_.evidence
    link_check = 'HTTP 200 verified 2026-09-11'
  }
})

$artifact = [ordered]@{
  batch_id = 'early-go-bond-cluster-research-2026-09-11'
  lane = 'Claude research lane: next substantive pending-review cluster outside the DPM library'
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  cluster = 'City of Albuquerque 2003 and 2004 general obligation bond document sets under cip-documents/2003-bond-doc and cip-documents/2004-bond-documents.'
  scope = '25 pending-review PDF candidates. The two directory landing pages (src-a2aca9ec415a08bb, src-777e7ac772d0f391) were left out of scope as navigation records.'
  method = 'Fetched every file directly to a scratch directory without touching shared inventory state, recorded exact byte size and SHA-256, extracted text, and rendered image-only PDFs for visual review. Classified against the precedent already set in this directory: detailed project-scope and allocation tables are retained (src-e28f489ec0fba72f, src-0782d8521e42a068) while high-level percentage summaries are excluded (src-7405cfc41e5500c4).'
  classification_only = $true
  shared_state_written = @()
  duplicate_and_supersession_checks = [ordered]@{
    internal_hash_collisions = 0
    cross_inventory_hash_collisions = 0
    distinct_documents = 25
    note = 'All 25 SHA-256 values are distinct from each other and from every checksum recorded anywhere in master-inventory.json, so no duplicate or superseded relationship was found. R-03-265 amends R-03-215 and the two should be presented together, but both remain enacted authoritative records rather than a supersession pair.'
    already_covered_in_this_directory = @('src-e28f489ec0fba72f','src-0782d8521e42a068','src-74326241e19c1551','src-dc6e3fd3425cb32a','src-93e8d3f4cf0238e6','src-b196c741237acbf2','src-ba1ff357823017a2','src-c5569fc34458c4d2')
  }
  counts = [ordered]@{
    reviewed = 25
    approved_for_addition = $approvedRows.Count
    excluded = $excluded.Count
    requires_human_review = $humanReview.Count
    duplicate = 0
    superseded = 0
  }
  link_check = [ordered]@{checked=25;http_200=25;failed=0}
  approved_for_addition = $approvedRows
  excluded = @($excluded | ForEach-Object { [ordered]@{id=$_.id;item=$_.item;recommended_status='excluded';authoritative_url=(Get-Url $_.id);reason=$_.reason} })
  requires_human_review = @($humanReview | ForEach-Object { [ordered]@{id=$_.id;item=$_.item;recommended_status='requires human review';authoritative_url=(Get-Url $_.id);reason=$_.reason} })
  integration_note = 'Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. R2 archival is not authorized by this artifact; the approved records can be published as official-source links in the same way as the existing 2003 storm sewer and operations entries.'
  safeguards = @('no master-inventory.json write','no checkpoint.json write','no site content change','no R2 upload','no commit, merge, or deploy')
}

$artifact | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{reviewed=25;approved=$approvedRows.Count;excluded=$excluded.Count;requires_human_review=$humanReview.Count;output=$OutputPath} | ConvertTo-Json -Compress
