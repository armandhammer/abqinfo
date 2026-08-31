[CmdletBinding()]
param([string]$OutputPath = 'project-state/discovery/bicycle-pedestrian-data-history-decisions.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$page = 'content/transportation/bicycling/safety-crash-data.md'
$analysisPage = 'https://www.mrcog-nm.gov/568/Bicycle-and-Pedestrian-Analysis-and-Repo'
$crashPage = 'https://www.mrcog-nm.gov/572/Archived-Crash-Reports'
$decisions = @(
  [pscustomobject][ordered]@{id='src-6c0a311dd3a08a51';title='Albuquerque Metropolitan Crash and Safety Report, 2001–2010';date='2011';r2_key='transportation/bicycling/safety-crash-data/mrmpo-albuquerque-metropolitan-crash-safety-report-2001-2010.pdf';canonical_page=$page;source_page=$crashPage;description="Analyzes a decade of metropolitan crash trends, severity, roadway characteristics, contributing factors, intersections, pedestrians, bicyclists, and geographic patterns to support Albuquerque-area transportation planning and safety investment."}
  [pscustomobject][ordered]@{id='src-1c71a4326a470435';title='Albuquerque Metropolitan Crash and Safety Report, 2002–2011';date='2012';r2_key='transportation/bicycling/safety-crash-data/mrmpo-albuquerque-metropolitan-crash-safety-report-2002-2011.pdf';canonical_page=$page;source_page=$crashPage;description="Updates the metropolitan crash baseline through 2011, documenting trends, severity, locations, roadway and driver factors, pedestrian and bicyclist crashes, and comparisons used in regional safety planning."}
  [pscustomobject][ordered]@{id='src-3b45c3557a8dfd40';title='Bernalillo County Pedestrian and Bicycle Crash Data Analysis, 2010–2014';date='2016';r2_key='transportation/bicycling/safety-crash-data/mrmpo-bernalillo-county-pedestrian-bicycle-crash-analysis-2010-2014.pdf';canonical_page=$page;source_page=$crashPage;description="Examines pedestrian and bicycle crash severity, locations, timing, people involved, and reported contributing factors across Bernalillo County, identifying East Central Avenue as the region’s highest-crash corridor."}
  [pscustomobject][ordered]@{id='src-470289bc6b339acd';title='Pedestrian and Bicycle Travel Monitoring Report';date='2016';r2_key='transportation/bicycling/safety-crash-data/mrmpo-pedestrian-bicycle-travel-monitoring-report-2016.pdf';canonical_page=$page;source_page=$analysisPage;description="Analyzes pedestrian and bicycle counts, observed behavior, land use, transit access, and built-environment conditions at International District and South Valley locations to inform active-transportation planning and public-health investment."}
  [pscustomobject][ordered]@{id='src-b5ca82f0a87d9451';title='Paseo del Bosque and North Diversion Channel Bicycle Trends';date='2018';r2_key='transportation/bicycling/safety-crash-data/mrmpo-paseo-del-bosque-north-diversion-channel-bicycle-trends-2018.pdf';canonical_page=$page;source_page=$analysisPage;description="Uses permanent trail-counter data to compare recreational and commute-oriented bicycling patterns on the Paseo del Bosque and North Diversion Channel trails, including hourly, weekday, and weekend trends."}
  [pscustomobject][ordered]@{id='src-282e583e7246853d';title='2019 Bike to Work Day Survey Report';date='2020';r2_key='transportation/bicycling/safety-crash-data/mrmpo-bike-to-work-day-survey-report-2019.pdf';canonical_page=$page;source_page=$analysisPage;description="Analyzes 1,002 Albuquerque Bike to Work Day responses about rider demographics, trip purposes, bicycling frequency, perceived conditions, barriers, route and facility needs, event participation, and priorities for improvement."}
  [pscustomobject][ordered]@{id='src-29f5622a2a55a74f';title='2020 Bike to Work Day Survey Report';date='2020';r2_key='transportation/bicycling/safety-crash-data/mrmpo-bike-to-work-day-survey-report-2020.pdf';canonical_page=$page;source_page=$analysisPage;description="Summarizes 895 online responses about Albuquerque bicycling during the COVID-19 pandemic, including trip purposes, perceived conditions, barriers, protected-lane and network priorities, driver behavior, destinations, and desired improvements."}
  [pscustomobject][ordered]@{id='src-c4bc0920de6e9e4b';title='2022 Bike to Wherever Day Survey Report';date='2022';r2_key='transportation/bicycling/safety-crash-data/mrmpo-bike-to-wherever-day-survey-report-2022.pdf';canonical_page=$page;source_page=$analysisPage;description="Documents Albuquerque-area rider characteristics, trip purposes, safety perceptions, barriers, facility preferences, event participation, and changing sentiment, with respondents emphasizing protected lanes, connected routes, and safer driver behavior."}
  [pscustomobject][ordered]@{id='src-d47ebc84d3471e5b';title='2025 Bike to Work Day Survey Results';date='2025';r2_key='transportation/bicycling/safety-crash-data/mrcog-bike-to-work-day-survey-results-2025.pdf';canonical_page=$page;source_page=$analysisPage;description="Reports 191 English and Spanish survey responses on bicycling frequency, rider experience, electric-bike use, commute patterns, perceived conditions, barriers, infrastructure priorities, driver behavior, and outreach for Albuquerque’s annual event."}
)

foreach ($decision in $decisions) {
  $words = @($decision.description -split '\s+' | Where-Object { $_ }).Count
  if ($words -lt 20 -or $words -gt 50) { throw "$($decision.id) description has $words words." }
  $decision | Add-Member -NotePropertyName processing_notes -NotePropertyValue @(
    'Original authoritative MRCOG/MRMPO PDF preserved without modification.',
    'Description reviewed against complete extracted text and representative visual inspection.'
  )
}

[ordered]@{schema_version=1;batch_id='bicycle-pedestrian-data-history-30';decisions=$decisions} |
  ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{Decisions=$decisions.Count;OutputPath=$OutputPath}|ConvertTo-Json -Compress
