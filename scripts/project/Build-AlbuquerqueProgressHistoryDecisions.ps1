[CmdletBinding()]
param([string]$OutputPath = 'project-state/discovery/albuquerque-progress-history-decisions.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$page = 'content/city-data/city-progress-surveys.md'
$sourcePage = 'https://www.cabq.gov/progress/albuquerque-progress-report'
$decisions = @(
  [pscustomobject][ordered]@{id='src-d62d1abce680dce0';title='2008 Albuquerque Progress Report';date='2008';r2_key='city-data/city-progress/cabq-albuquerque-progress-report-2008.pdf';canonical_page=$page;source_page=$sourcePage;description="Measures Albuquerque’s community conditions across eight resident-defined goals, preserving detailed indicators, peer comparisons, trends, data sources, and the Indicators Progress Commission’s assessment of where the city was advancing or falling behind."}
  [pscustomobject][ordered]@{id='src-3af3d3d2b34a5606';title='2012 Albuquerque Progress Report Snapshot';date='2012';r2_key='city-data/city-progress/cabq-albuquerque-progress-report-snapshot-2012.pdf';canonical_page=$page;source_page=$sourcePage;description="Condenses the 2012 citywide indicator report into a scorecard of key measures, four-year trends, and peer-community comparisons covering family development, safety, infrastructure, sustainability, environment, economy, culture, and government performance."}
  [pscustomobject][ordered]@{id='src-572f6d8a7a30f8a1';title='2014 Albuquerque Progress Report';date='2014';r2_key='city-data/city-progress/cabq-albuquerque-progress-report-2014.pdf';canonical_page=$page;source_page=$sourcePage;description="Tracks citywide progress through indicator scorecards, trend analysis, regional and national comparisons, and source documentation across Albuquerque’s eight long-term community goals."}
  [pscustomobject][ordered]@{id='src-f9c6246de583e9da';title='2016 Albuquerque Progress Report';date='2016';r2_key='city-data/city-progress/cabq-albuquerque-progress-report-2016.pdf';canonical_page=$page;source_page=$sourcePage;description="Documents Albuquerque’s changing community conditions using desired-condition indicators, historical trends, peer comparisons, and scorecards for human development, safety, infrastructure, sustainable development, environment, economy, civic life, and government effectiveness."}
  [pscustomobject][ordered]@{id='src-5da6965abacdaee9';title='2018 Albuquerque Progress Report';date='2018';r2_key='city-data/city-progress/cabq-albuquerque-progress-report-2018.pdf';canonical_page=$page;source_page=$sourcePage;description="Preserves the Indicators Progress Commission’s 2018 citywide assessment, including measures and scorecards for public safety, infrastructure, sustainability, environmental protection, economic vitality, community engagement, family development, and government effectiveness."}
  [pscustomobject][ordered]@{id='src-f920e1a97488d336';title='2020 Albuquerque Progress Report';date='2020';r2_key='city-data/city-progress/cabq-albuquerque-progress-report-2020.pdf';canonical_page=$page;source_page=$sourcePage;description="Combines the biennial community indicator scorecard with 2020 resident-satisfaction results, documenting trends across eight City goals and conditions during the opening phase of the COVID-19 pandemic."}
  [pscustomobject][ordered]@{id='src-cd8f57c4c1140437';title='2022 Albuquerque Progress Report';date='2022';r2_key='city-data/city-progress/cabq-albuquerque-progress-report-2022.pdf';canonical_page=$page;source_page=$sourcePage;description="Provides the latest archived Indicators Progress Commission scorecard, with measures, trend direction, benchmark comparisons, data sources, and analysis across Albuquerque’s eight adopted community-goal areas."}
  [pscustomobject][ordered]@{id='src-0cec8aac1c0949a7';title='Informe de Progreso de Albuquerque 2022';date='2022';r2_key='city-data/city-progress/cabq-informe-de-progreso-de-albuquerque-2022-es.pdf';canonical_page=$page;source_page=$sourcePage;description="Preserva la edición oficial en español del informe de 2022, con indicadores y tendencias sobre desarrollo humano, seguridad pública, infraestructura, sostenibilidad, medio ambiente, economía, participación comunitaria y eficacia gubernamental."}
  [pscustomobject][ordered]@{id='src-a9edf95587555344';title='2020 Albuquerque Citizen Perception Survey';date='2020';r2_key='city-data/city-progress/cabq-citizen-perception-survey-2020.pdf';canonical_page=$page;source_page=$sourcePage;description="Reports an August 2020 telephone survey of 303 adult residents about City services, COVID-19 response, crime, safety, the economy, community priorities, and Albuquerque’s overall direction."}
  [pscustomobject][ordered]@{id='src-d136988f67d3e648';title='2021 Albuquerque Citizen Perception Survey';date='2021';r2_key='city-data/city-progress/cabq-citizen-perception-survey-2021.pdf';canonical_page=$page;source_page=$sourcePage;description="Documents a 300-resident telephone survey conducted in November 2020, measuring satisfaction with City services and views on COVID-19 response, crime, homelessness, public safety, and municipal priorities."}
  [pscustomobject][ordered]@{id='src-e4691b2ec7a08601';title='2022 Albuquerque Citizen Perception Survey';date='2022';r2_key='city-data/city-progress/cabq-citizen-perception-survey-2022.pdf';canonical_page=$page;source_page=$sourcePage;description="Presents methodology, executive findings, full tables, demographics, and questionnaire results from a June 2022 telephone survey of 400 Albuquerque adults about services, safety, homelessness, COVID-19, and community conditions."}
  [pscustomobject][ordered]@{id='src-bf7598bed4055750';title='Albuquerque Yearly Survey Results (2024)';date='2024';r2_key='city-data/city-progress/cabq-albuquerque-yearly-survey-results-2024.pdf';canonical_page=$page;source_page=$sourcePage;description="Summarizes a February 2024 poll of 400 adults covering neighborhood safety, city direction, cost of living, reckless driving, panhandling, public-safety initiatives, housing, behavioral health, and other resident priorities."}
)

foreach ($decision in $decisions) {
  $words = @($decision.description -split '\s+' | Where-Object { $_ }).Count
  if ($words -lt 20 -or $words -gt 50) { throw "$($decision.id) description has $words words." }
  $decision | Add-Member -NotePropertyName processing_notes -NotePropertyValue @(
    'Original authoritative City PDF preserved without modification.',
    'Description reviewed against complete extracted text and representative visual inspection.'
  )
}

[ordered]@{schema_version=1;batch_id='albuquerque-progress-history-29';decisions=$decisions} |
  ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{Decisions=$decisions.Count;OutputPath=$OutputPath}|ConvertTo-Json -Compress
