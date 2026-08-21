[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OutputPath = 'project-state/five-year-forecast-history-decisions-2026-08-21.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$source = 'https://www.cabq.gov/dfa/budget/five-year-forecast'
$urls = [ordered]@{
  '2026'='https://www.cabq.gov/dfa/documents/five-year-forecast-final-3.pdf'
  '2025'='https://www.cabq.gov/dfa/documents/five-year-forecast-final-2.pdf'
  '2024'='https://www.cabq.gov/dfa/documents/five-year-forecast-final-1.pdf'
  '2023'='https://www.cabq.gov/dfa/documents/five-year-forecast-final-may-2023.pdf'
  '2022'='https://www.cabq.gov/dfa/documents/five-year-forecast-final.pdf'
  '2021'='https://www.cabq.gov/dfa/documents/five-year-forecast-2021.pdf'
  '2020'='https://www.cabq.gov/dfa/documents/five-year-forecast-fiscal-2020.pdf'
  '2019'='https://www.cabq.gov/dfa/documents/five-year-forecast-fiscal-2019.pdf'
  '2018'='https://www.cabq.gov/dfa/documents/five-year-forecast-fiscal-2018.pdf'
  '2017'='https://www.cabq.gov/dfa/documents/five-year-forecast-fiscal-2017.pdf'
  '2016'='https://www.cabq.gov/dfa/documents/five-year-forecast-fiscal-2016.pdf'
  '2015'='https://www.cabq.gov/dfa/documents/five-year-forecast-fiscal-2015.pdf'
  '2014'='https://www.cabq.gov/dfa/documents/five-year-forecast.pdf'
  '2013'='https://www.cabq.gov/dfa/documents/five-year-forecast-FY2013.pdf'
}

$decisions = foreach ($entry in $urls.GetEnumerator()) {
  $year = $entry.Key
  $title = "City of Albuquerque Five-Year Forecast, Fiscal Year $year"
  $description = "Preserves the City's fiscal year $year five-year outlook for General Fund revenues, expenditures, economic conditions, budget pressures, alternative scenarios, and the assumptions informing annual budget development."
  $record = & "$PSScriptRoot/Add-InventoryCandidate.ps1" -SourceUrl $entry.Value -DirectFileUrl $entry.Value -Agency 'City of Albuquerque' -Title $title -Date $year -FileType PDF -ParentUrl $source -DiscoveryMethod 'official fiscal forecast archive lineage link' -CrawlDepth 1 -InventoryPath $InventoryPath | ConvertFrom-Json
  [pscustomobject][ordered]@{
    id=$record.id; title=$title; date=$year
    r2_key="city-data/budget-spending/cabq-five-year-forecast-fy$year.pdf"
    canonical_page='content/city-data/budget-spending.md'; source_page=$source
    direct_file_url=$entry.Value; agency='City of Albuquerque'; description=$description
    decision='approved for addition'; provenance_status='official City forecast archive and direct government PDF recorded'
    processing_notes=@('Original authoritative City PDF will be preserved without modification; exact size and SHA-256 are recorded after download.')
  }
}

[ordered]@{batch_id='2026-08-21-five-year-forecast-history';decisions=@($decisions)} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{Items=@($decisions).Count;OutputPath=$OutputPath;Ids=@($decisions.id)} | ConvertTo-Json -Depth 4
