[CmdletBinding()]
param([string]$InventoryPath='project-state/master-inventory.json',[string]$OutputPath='project-state/acfr-history-decisions-2026-08-24.json')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$parent='https://www.cabq.gov/dfa/treasury/investor-information/annual-comprehensive-financial-reports'
$inventory=Get-Content -Raw -Encoding UTF8 $InventoryPath|ConvertFrom-Json
$candidates=@($inventory.candidates|Where-Object {$_.parent_url -eq $parent -and $_.status -eq 'parsed'}|Sort-Object date)
if($candidates.Count -ne 21){throw "Expected 21 eligible parsed ACFRs; found $($candidates.Count)."}
$decisions=foreach($c in $candidates){
  $year=[regex]::Match([string]$c.date,'\d{4}').Value
  $d=[ordered]@{id=$c.id;title=$c.title;date=$c.date;canonical_page='content/city-data/budget-spending.md';source_page=$parent;direct_file_url=$c.direct_file_url;agency='City of Albuquerque';r2_key="city-data/budget-spending/cabq-annual-comprehensive-financial-report-fy$year.pdf";description="Presents Albuquerque’s independently audited financial statements for Fiscal Year $year, including government-wide and fund finances, revenues, expenditures, debt, pensions, capital assets, budget comparisons, notes, and long-term statistical trends.";processing_notes=@('Original authoritative PDF preserved without modification after complete text extraction and representative-page visual review.')}
  if([int64]$c.size_bytes -gt 25MB){$d.large_file_assessment='The official PDF is large because it contains roughly 300–370 pages of audited statements, notes, schedules, tables, and statistical material. No smaller authoritative edition is linked; preserve the original unchanged.'}
  $d
}
[ordered]@{batch_id='2026-08-24-acfr-history';decisions=@($decisions)}|ConvertTo-Json -Depth 7|Set-Content $OutputPath -Encoding utf8
[pscustomobject]@{Decisions=$decisions.Count;OutputPath=$OutputPath}|ConvertTo-Json -Compress
