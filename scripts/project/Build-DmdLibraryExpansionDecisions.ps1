[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OutputPath = 'project-state/dmd-library-expansion-decisions-2026-08-14.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$decisions = [System.Collections.Generic.List[object]]::new()

function Add-Decision {
  param(
    [Parameter(Mandatory)][string]$Id,
    [Parameter(Mandatory)][string]$Title,
    [Parameter(Mandatory)][string]$Date,
    [Parameter(Mandatory)][string]$R2Key,
    [Parameter(Mandatory)][string]$CanonicalPage,
    [Parameter(Mandatory)][string]$Description,
    [string]$LargeFileAssessment
  )
  $candidate = @($inventory.candidates | Where-Object id -eq $Id)
  if ($candidate.Count -ne 1) { throw "Expected one inventory candidate for '$Id'; found $($candidate.Count)." }
  $wordCount = @($Description -split '\s+' | Where-Object { $_ }).Count
  if ($wordCount -lt 20 -or $wordCount -gt 50) { throw "Description for '$Id' has $wordCount words; expected 20-50." }
  $entry = [ordered]@{
    id = $Id
    title = $Title
    date = $Date
    r2_key = $R2Key
    canonical_page = $CanonicalPage
    source_page = [string]$candidate[0].source_url
    description = $Description
    decision = 'approved for addition'
  }
  if ($LargeFileAssessment) { $entry.large_file_assessment = $LargeFileAssessment }
  $decisions.Add([pscustomobject]$entry)
}

$speedStudies = @(
  @{id='src-9b50c853b151ada2';title='17th Street Speed Study';date='2021-03';limits='Old Town Road to Lomas Boulevard';slug='17th-street-speed-study-2021'},
  @{id='src-5492d231debc826a';title='61st Street Speed Study';date='2021-03';limits='Avalon Road to Bluewater Road';slug='61st-street-speed-study-2021'},
  @{id='src-26eec5c4fc575e19';title='7 Bar Loop Speed and Volume Study';date='2021-11-22';limits='Westside Boulevard to Ellison Drive';slug='7-bar-loop-speed-volume-study-2021'},
  @{id='src-82ed5901df5a3610';title='7th Street Speed Study';date='2021-03';limits='Coal Avenue to Stover Avenue';slug='7th-street-speed-study-2021'},
  @{id='src-c2112472deff2555';title='Baja Drive Speed Study';date='2021-03';limits='Juan Tabo Boulevard to Cairo Drive';slug='baja-drive-speed-study-2021'},
  @{id='src-50b22c2cff55127c';title='Constitution Avenue Speed Study';date='2021-03';limits='Morris Street to Juan Tabo Boulevard';slug='constitution-avenue-speed-study-2021'},
  @{id='src-6c6f2aed1a9d4d1f';title='Desert Springs Drive Speed Study';date='2021-03';limits='Spring Flower Road to Desert Canyon Place';slug='desert-springs-drive-speed-study-2021'},
  @{id='src-ce04fb6842a09dea';title='Field Drive Speed Study';date='2021-03';limits='Indian School Road to Snow Heights Boulevard';slug='field-drive-speed-study-2021'},
  @{id='src-70d6d253b034c1aa';title='Freedom Way Speed Study';date='2021-03';limits='Ventura Street to Don Diego Street';slug='freedom-way-speed-study-2021'},
  @{id='src-443d248392597a00';title='Iliff Road Speed Study';date='2021-03';limits='Coors Boulevard to Atrisco Drive';slug='iliff-road-speed-study-2021'},
  @{id='src-f18cd98a58a4fef5';title='Kimmick Drive Speed and Volume Study';date='2021-11-23';limits='Paseo del Norte Boulevard to Urraca Street';slug='kimmick-drive-speed-volume-study-2021'},
  @{id='src-d19827d1fca91d3f';title='Milky Way Street Speed Study';date='2021-03';limits='Black Arroyo Boulevard to McMahon Boulevard';slug='milky-way-street-speed-study-2021'},
  @{id='src-7c6240f55fadae7a';title='Morningside Drive Speed Study';date='2021-03';limits='Coal Avenue to Pershing Avenue';slug='morningside-drive-speed-study-2021'},
  @{id='src-cef309f0fc19d674';title='Ruidoso Road Speed Study';date='2021-03';limits='Curry Avenue to Mosquero Avenue';slug='ruidoso-road-speed-study-2021'},
  @{id='src-310e89e31b12747a';title='San Francisco Road Speed Study';date='2020-04';limits='San Pedro Drive to Louisiana Boulevard';slug='san-francisco-road-speed-study-2020'},
  @{id='src-b978a32849d783ce';title='Sierra Grande Avenue Speed Study';date='2021-03';limits='Loyola Avenue to Loyola Place';slug='sierra-grande-avenue-speed-study-2021'},
  @{id='src-c68882c45fa8d45c';title='Storrie Place Speed Study';date='2021-03';limits='Palomas Park Avenue to La Mariposa Place';slug='storrie-place-speed-study-2021'},
  @{id='src-ea9e689316a9e3ee';title='Sunridge Avenue Speed Study';date='2021-03';limits='Sunburst Road to 90th Street';slug='sunridge-avenue-speed-study-2021'},
  @{id='src-55919b89045da7bf';title='Truman Street Speed Study';date='2021-03';limits='Headingly Avenue to Candelaria Road';slug='truman-street-speed-study-2021'},
  @{id='src-23d0c6c8780944f9';title='Vivian Drive Speed Study';date='2021-03';limits='Glendora Drive to Truchas Drive';slug='vivian-drive-speed-study-2021'}
)

foreach ($study in $speedStudies) {
  $description = "Documents measured speeds and traffic volumes along $($study.title.Replace(' Speed and Volume Study','').Replace(' Speed Study','')) from $($study.limits), providing neighborhood-scale evidence for traffic-calming evaluation and future street-safety decisions."
  Add-Decision -Id $study.id -Title $study.title -Date $study.date -R2Key "transportation/roadway-projects/speed-management/cabq-$($study.slug).pdf" -CanonicalPage 'content/transportation/roadway-projects/speed-management.md' -Description $description
}

Add-Decision -Id 'src-0c338b7492be1b45' -Title 'Yellow-Light and All-Red Clearance Timing Effectiveness Study' -Date '2012-09' -R2Key 'transportation/operations-data/cabq-yellow-all-red-clearance-timing-effectiveness-study-2012.pdf' -CanonicalPage 'content/transportation/operations-data.md' -Description 'Evaluates crash frequency, type, and severity after yellow-light timing changes at 18 Albuquerque intersections and all-red clearance changes at two intersections formerly monitored by red-light cameras.'
Add-Decision -Id 'src-043b8237ba0764e6' -Title 'HAWK Signal Guide for Lomas Boulevard and Alvarado Drive' -Date 'undated' -R2Key 'transportation/operations-data/cabq-hawk-signal-lomas-alvarado-guide.pdf' -CanonicalPage 'content/transportation/operations-data.md' -Description 'Explains how pedestrians, bicyclists, and drivers use the HAWK crossing signal at Lomas Boulevard and Alvarado Drive, including beacon phases, countdown indications, and the median restart button.'
Add-Decision -Id 'src-869bb49fc86733b4' -Title 'Dr. Martin Luther King Jr. Avenue Separated Bike Lane Pilot FAQ' -Date '2026' -R2Key 'transportation/bicycling/projects/cabq-mlk-separated-bike-lane-pilot-faq-2026.pdf' -CanonicalPage 'content/transportation/bicycling/projects/_index.md' -Description 'Explains the pilot limits, safety purpose, separation materials, intersection treatments, maintenance evaluation, ridership data collection, community feedback, and relationship to the adopted Albuquerque bicycle priorities.'
Add-Decision -Id 'src-438b3ebcc3f671e2' -Title 'Mountain Road Bike Boulevard Crossing at San Pedro Drive' -Date '2015-06-08' -R2Key 'transportation/bicycling/projects/cabq-mountain-road-bike-boulevard-san-pedro-crossing-2015.pdf' -CanonicalPage 'content/transportation/bicycling/projects/_index.md' -Description 'Preserves the GABAC presentation evaluating crossing concepts for the offset Mountain Road bike boulevard at San Pedro Drive, including access concerns, design precedents, alternatives, and recommendations.'
Add-Decision -Id 'src-0f5f4a570a7fe2b6' -Title 'Two-Stage Bike Box at MLK Avenue and Broadway Boulevard' -Date 'undated' -R2Key 'transportation/bicycling/projects/cabq-mlk-broadway-two-stage-bike-box-guide.pdf' -CanonicalPage 'content/transportation/bicycling/projects/_index.md' -Description 'Illustrates the two-stage bicycle left-turn process at Dr. Martin Luther King Jr. Avenue and Broadway Boulevard, showing rider positioning, signal sequence, travel path, and driver stop location.'
Add-Decision -Id 'src-380ba25628c0ee5c' -Title 'Two-Stage Bike Box at MLK Avenue and Broadway Boulevard — Image' -Date 'undated' -R2Key 'transportation/bicycling/projects/cabq-mlk-broadway-two-stage-bike-box-guide.png' -CanonicalPage 'content/transportation/bicycling/projects/_index.md' -Description 'Preserves the original City image-format instruction sheet for the MLK Avenue and Broadway Boulevard two-stage bike box, suitable for quick viewing without opening the printable PDF.'
Add-Decision -Id 'src-ef552ed5fa8021e6' -Title 'Albuquerque Automated Speed Enforcement Regulation' -Date '2022' -R2Key 'transportation/roadway-projects/speed-management/cabq-automated-speed-enforcement-regulation-2022.pdf' -CanonicalPage 'content/transportation/roadway-projects/speed-management.md' -Description 'Sets administrative rules for automated speed-enforcement fines, notices, payment deadlines, community service, hearings, evidence, registered-owner responsibility, and enforcement under the governing Albuquerque ordinance.'

Add-Decision -Id 'src-7b6cb9849a434271' -Title 'City of Albuquerque MS4 Annual Report, FY 2025' -Date '2025-12' -R2Key 'public-works/stormwater-drainage/cabq-ms4-annual-report-fy2025.pdf' -CanonicalPage 'content/public-works/stormwater-drainage.md' -Description 'Reports FY 2025 municipal stormwater permit compliance in Albuquerque, including monitoring, pollutant controls, inspections, public education, construction oversight, water-quality results, and extensive supporting records and appendices.' -LargeFileAssessment 'The 461-page PDF is 45,666,232 bytes and is large because it compiles monitoring data, forms, maps, photographs, laboratory material, and permit appendices. No smaller authoritative final version was found; optimization would alter the source, so the original is preserved unchanged.'
Add-Decision -Id 'src-cac65cdc3b8dace0' -Title 'City of Albuquerque MS4 Annual Report, FY 2024' -Date '2024' -R2Key 'public-works/stormwater-drainage/cabq-ms4-annual-report-fy2024.pdf' -CanonicalPage 'content/public-works/stormwater-drainage.md' -Description 'Documents FY 2024 municipal stormwater permit work, including water-quality protection, illicit-discharge control, construction and post-construction programs, pollution prevention, monitoring, public outreach, and supporting appendices.'
Add-Decision -Id 'src-a9a656ef061f06b5' -Title 'City of Albuquerque MS4 Annual Report, FY 2022' -Date '2022-11-21' -R2Key 'public-works/stormwater-drainage/cabq-ms4-annual-report-fy2022.pdf' -CanonicalPage 'content/public-works/stormwater-drainage.md' -Description 'Preserves the FY 2022 municipal stormwater compliance record for Albuquerque, including monitoring, impaired-water responses, illicit-discharge work, construction oversight, municipal operations, public education, and program attachments.'
Add-Decision -Id 'src-de16a832dd3bdd8a' -Title 'City of Albuquerque Stormwater Management Program' -Date '2019-12-01' -R2Key 'public-works/stormwater-drainage/cabq-stormwater-management-program-2019.pdf' -CanonicalPage 'content/public-works/stormwater-drainage.md' -Description 'Defines the municipal stormwater program for Albuquerque under the watershed-based MS4 permit, covering legal authority, monitoring, public involvement, illicit discharges, construction, post-construction controls, municipal operations, schedules, and responsibilities.' -LargeFileAssessment 'The 559-page PDF is 60,117,040 bytes and is large because it contains the complete program narrative, tables, forms, maps, and extensive supporting appendices. No smaller authoritative City version was found; optimization would alter the source, so the original is preserved unchanged.'
Add-Decision -Id 'src-5244dc0ca1c18e95' -Title 'Albuquerque MS4 Bacterial TMDL Loading Report, Water Year 2015' -Date '2016-03-06' -R2Key 'public-works/stormwater-drainage/cabq-ms4-bacterial-tmdl-loading-report-wy2015.pdf' -CanonicalPage 'content/public-works/stormwater-drainage.md' -Description 'Calculates estimated E. coli loads from major Albuquerque stormwater outfalls during water year 2015 and compares daily results with Middle Rio Grande bacterial TMDL wasteload allocations.'
Add-Decision -Id 'src-64fe15e764b8c334' -Title 'City of Albuquerque NPDES Permit Transitional Update' -Date '2015' -R2Key 'public-works/stormwater-drainage/cabq-npdes-ms4-permit-transitional-update-2015.pdf' -CanonicalPage 'content/public-works/stormwater-drainage.md' -Description 'Documents the 2015 Albuquerque transition from its former Phase I municipal stormwater permit to the watershed-based MS4 permit, reconciling reporting periods, monitoring, program responsibilities, and compliance activities.'

Add-Decision -Id 'src-cb8cd727e3ca1fde' -Title '2013–2022 Decade Plan and 2013 General Obligation Bond Program' -Date '2012-11' -R2Key 'city-data/capital-spending/cabq-2013-2022-decade-plan-go-bond-program.pdf' -CanonicalPage 'content/city-data/capital-spending.md' -Description 'Presents the Environmental Planning Commission version of the 2013–2022 Albuquerque capital-improvement decade plan and 2013 bond program, with department projects, funding schedules, maps, justifications, and program criteria.'
Add-Decision -Id 'src-4ce8e84444dd90a8' -Title '2019 General Obligation Bond Program Book' -Date '2019' -R2Key 'city-data/capital-spending/cabq-2019-go-bond-program-book.pdf' -CanonicalPage 'content/city-data/capital-spending.md' -Description 'Documents the 2019 Albuquerque capital program by bond purpose and department, preserving proposed project scopes, costs, locations, schedules, funding sources, and the broader decade-plan context.'
Add-Decision -Id 'src-ee36b5c72dd925b8' -Title '2021 General Obligation Bond Approved Program' -Date '2021' -R2Key 'city-data/capital-spending/cabq-2021-go-bond-approved-program.pdf' -CanonicalPage 'content/city-data/capital-spending.md' -Description 'Preserves the approved 2021 Albuquerque bond program, including department allocations, detailed capital-project requests, project purposes, locations, schedules, costs, funding sources, and implementation information.'
Add-Decision -Id 'src-af35c3eb64539dab' -Title '2023 General Obligation Bond Program Book' -Date '2023' -R2Key 'city-data/capital-spending/cabq-2023-go-bond-program-book.pdf' -CanonicalPage 'content/city-data/capital-spending.md' -Description 'Compiles the 2023 Albuquerque General Obligation Bond program by purpose and department, with project descriptions, locations, justifications, requested funding, schedules, and capital-planning context.'
Add-Decision -Id 'src-e0944409dcca0904' -Title '2025–2034 Approved Decade Plan Summary' -Date '2025' -R2Key 'city-data/capital-spending/cabq-2025-2034-approved-decade-plan-summary.pdf' -CanonicalPage 'content/city-data/capital-spending.md' -Description 'Summarizes approved capital allocations across the 2025–2034 decade plan by department and biennial bond cycle, showing long-range funding for streets, drainage, parks, transit, housing, facilities, and public safety.'
Add-Decision -Id 'src-00e4a0dfe5460a1d' -Title '2025–2034 Decade Plan Funding Allocation Workbook' -Date '2025' -R2Key 'city-data/capital-spending/cabq-2025-2034-decade-plan-funding-allocations.xlsx' -CanonicalPage 'content/city-data/capital-spending.md' -Description 'Provides the downloadable City allocation workbook for the 2025–2034 decade plan, comparing percentages, available funding, and department plan submissions across five biennial General Obligation Bond cycles.'
Add-Decision -Id 'src-646e9ec716227351' -Title '2027–2036 Decade Plan Funding Allocation Chart' -Date '2026-04-24' -R2Key 'city-data/capital-spending/cabq-2027-2036-decade-plan-funding-allocation-chart.pdf' -CanonicalPage 'content/city-data/capital-spending.md' -Description 'Shows preliminary department allocations and plan submissions for the 2027–2036 decade plan across four bond cycles, including streets, drainage, parks, transit, housing, public safety, community facilities, and mandated set-asides.'

$payload = [ordered]@{
  batch_id = '2026-08-14-dmd-document-library-expansion'
  decisions = $decisions
}
$payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8

[pscustomobject]@{
  OutputPath = $OutputPath
  Decisions = $decisions.Count
  TotalBytes = [int64](($decisions | ForEach-Object { $id=$_.id; ($inventory.candidates | Where-Object id -eq $id).size_bytes } | Measure-Object -Sum).Sum)
} | ConvertTo-Json -Compress
