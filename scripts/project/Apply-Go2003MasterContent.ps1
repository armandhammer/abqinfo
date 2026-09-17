[CmdletBinding()]
param(
  [string]$PlanPath = 'project-state/discovery/go2003-master-compilation-r2-archive-plan-2026-09-13.json',
  [string]$PublicValidationPath = 'project-state/discovery/go2003-master-compilation-r2-public-validation-2026-09-13.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$plan = Get-Content -Raw -Encoding UTF8 -LiteralPath $PlanPath | ConvertFrom-Json
$public = Get-Content -Raw -Encoding UTF8 -LiteralPath $PublicValidationPath | ConvertFrom-Json
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$item = @($plan.items)
if ($item.Count -ne 1) { throw 'Expected exactly one 2003 master compilation.' }
$item = $item[0]
$result = @($public.results | Where-Object id -eq $item.id)
if ($result.Count -ne 1 -or -not [bool]$result[0].byte_identical -or [string]$result[0].checksum_sha256 -ne [string]$item.checksum_sha256 -or [int64]$result[0].size_bytes -ne [int64]$item.size_bytes) {
  throw 'The 2003 master compilation has not passed exact public R2 validation.'
}
$candidate = @($inventory.candidates | Where-Object id -eq $item.id)
if ($candidate.Count -ne 1 -or -not $candidate[0].r2_url) { throw 'The master compilation inventory record is incomplete.' }
$masterUrl = [string]$candidate[0].r2_url
$official = 'https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2003-bond-doc'
$fullProgram = '/city-data/capital-spending/#20032004-general-obligation-bond-program'

function Remove-EntryByArchiveUrl([string]$Text,[string]$Url,[string]$Context) {
  $escaped = [regex]::Escape($Url)
  $pattern = "(?ms)^- \[[^`r`n]+\]\($escaped\)`r?`n`r?`n.*?(?=^- \[|^#{1,6} |\z)"
  $matches = [regex]::Matches($Text,$pattern)
  if ($matches.Count -ne 1) { throw "Expected one entry for $Context; found $($matches.Count)." }
  return [regex]::Replace($Text,$pattern,'')
}

function Replace-EntryByArchiveUrl([string]$Text,[string]$Url,[string]$Replacement,[string]$Context) {
  $escaped = [regex]::Escape($Url)
  $pattern = "(?ms)^- \[[^`r`n]+\]\($escaped\)`r?`n`r?`n.*?(?=^- \[|^#{1,6} |\z)"
  $matches = [regex]::Matches($Text,$pattern)
  if ($matches.Count -ne 1) { throw "Expected one entry for $Context; found $($matches.Count)." }
  return [regex]::Replace($Text,$pattern,[System.Text.RegularExpressions.MatchEvaluator]{ param($m) $Replacement.TrimEnd() + "`n`n" })
}

function Master-Entry([string]$Description,[bool]$Canonical = $false) {
  $links = if ($Canonical) { "[Official City source library]($official)" } else { "[Full 2003 program record]($fullProgram) · [Official City source library]($official)" }
  return @"
- [2003 General Obligation Bond Program: Master Record (ABQInfo Historical Compilation, Archived PDF)]($masterUrl)

  $Description

  $links
"@
}

$capitalPath = 'content/city-data/capital-spending.md'
$capital = Get-Content -Raw -Encoding UTF8 -LiteralPath $capitalPath
$capitalUrls = @(
  'https://files.abqinfo.com/city-data/capital-spending/cabq-go-bond-operating-maintenance-cost-impacts-2003.pdf',
  'https://files.abqinfo.com/city-data/capital-spending/cabq-decade-plan-project-evaluation-criteria-2003.pdf',
  'https://files.abqinfo.com/city-data/capital-spending/cabq-go-bond-project-rankings-2003.pdf',
  'https://files.abqinfo.com/city-data/capital-spending/cabq-2003-capital-improvements-priorities-resolution-r-02-30.pdf',
  'https://files.abqinfo.com/city-data/capital-spending/cabq-2003-2012-decade-plan-capital-budget-resolution-r-03-215.pdf',
  'https://files.abqinfo.com/city-data/capital-spending/cabq-2003-go-bond-funding-allocation-chart.pdf',
  'https://files.abqinfo.com/city-data/capital-spending/cabq-2003-go-bond-rehabilitation-maintenance-deficiency-summary.pdf',
  'https://files.abqinfo.com/city-data/capital-spending/cabq-2003-street-go-bond-project-scopes.pdf',
  'https://files.abqinfo.com/city-data/capital-spending/cabq-2003-parks-recreation-go-bond-project-scopes.pdf',
  'https://files.abqinfo.com/city-data/capital-spending/cabq-2003-senior-family-community-center-go-bond-project-scopes.pdf',
  'https://files.abqinfo.com/city-data/capital-spending/cabq-2003-zoo-biological-park-museum-go-bond-project-scopes.pdf',
  'https://files.abqinfo.com/city-data/capital-spending/cabq-2003-public-facilities-equipment-system-modernization-go-bond-project-scopes.pdf',
  'https://files.abqinfo.com/city-data/capital-spending/cabq-2003-public-transportation-go-bond-project-scopes.pdf',
  'https://files.abqinfo.com/city-data/capital-spending/cabq-2003-police-go-bond-project-scopes.pdf',
  'https://files.abqinfo.com/city-data/capital-spending/cabq-2003-fire-protection-go-bond-project-scopes.pdf',
  'https://files.abqinfo.com/city-data/capital-spending/cabq-2003-library-go-bond-project-scopes.pdf',
  'https://files.abqinfo.com/city-data/capital-spending/cabq-2003-storm-sewer-system-go-bond-project-scopes.pdf'
)
foreach ($url in $capitalUrls) { $capital = Remove-EntryByArchiveUrl $capital $url $url }
$oldIntroduction = 'These official City records document the adopted 2003 capital program and the 2004 streets program. Department-specific scope tables are cross-listed on the subject pages below.'
if ([regex]::Matches($capital,[regex]::Escape($oldIntroduction)).Count -ne 1) { throw 'Could not uniquely locate the 2003–2004 program introduction.' }
$canonicalDescription = 'Combines 21 City records covering the governing resolutions, allocation and maintenance tables, Environmental Planning Commission recommendation, purpose-by-purpose project scopes, operating impacts, public FAQ, and Water Master Plan zone map for the 2003 bond program.'
$replacementIntroduction = "The complete 2003 program is consolidated below as one navigable annual record; every original remains separately archived and identified by source URL and checksum. The related 2004 streets records remain separate.`n`n" + (Master-Entry $canonicalDescription $true).TrimEnd()
$capital = $capital.Replace($oldIntroduction,$replacementIntroduction)

$pages = @(
  [pscustomobject]@{ Path='content/city-data/public-safety-data.md'; Old='https://files.abqinfo.com/city-data/capital-spending/cabq-2003-police-go-bond-project-scopes.pdf'; Description='Preserves the police and fire purpose sheets together with the governing resolutions, allocations, project-selection records, operating impacts, and other purpose scopes needed to interpret Albuquerque''s 2003 public-safety investments.' },
  [pscustomobject]@{ Path='content/public-works/parks-recreation.md'; Old='https://files.abqinfo.com/city-data/capital-spending/cabq-2003-parks-recreation-go-bond-project-scopes.pdf'; Description='Preserves the parks and recreation purpose sheet within the complete annual record, including the governing resolutions, funding tables, project rankings, operating impacts, and related citywide capital scopes.' },
  [pscustomobject]@{ Path='content/transportation/transit/abq-ride.md'; Old='https://files.abqinfo.com/city-data/capital-spending/cabq-2003-public-transportation-go-bond-project-scopes.pdf'; Description='Preserves the public-transportation purpose sheet within the complete annual record, including the Alvarado Transportation Center, vehicle and maintenance investments, governing resolutions, allocations, project rankings, and operating impacts.' },
  [pscustomobject]@{ Path='content/public-works/stormwater-drainage.md'; Old='https://files.abqinfo.com/city-data/capital-spending/cabq-2003-storm-sewer-system-go-bond-project-scopes.pdf'; Description='Preserves the storm-sewer purpose sheet within the complete annual record, including drainage rehabilitation, monitoring, pumps, channels, collectors and crossings alongside the governing resolutions, allocations, and project-selection evidence.' },
  [pscustomobject]@{ Path='content/transportation/transportation-plans.md'; Old='https://files.abqinfo.com/city-data/capital-spending/cabq-2003-street-go-bond-project-scopes.pdf'; Description='Preserves the 2003 street proposal within the complete annual program record. The compilation documents that voters rejected this purpose in 2003 before the City resubmitted a separate streets program in 2004.' }
)
foreach ($page in $pages) {
  $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $page.Path
  $text = Replace-EntryByArchiveUrl $text $page.Old (Master-Entry $page.Description $false) $page.Path
  if ($page.Path -eq 'content/city-data/public-safety-data.md') {
    $text = Remove-EntryByArchiveUrl $text 'https://files.abqinfo.com/city-data/capital-spending/cabq-2003-fire-protection-go-bond-project-scopes.pdf' 'public-safety fire cross-listing'
  }
  $page | Add-Member -NotePropertyName Text -NotePropertyValue $text
}

$writes = @([pscustomobject]@{Path=$capitalPath;Text=$capital}) + @($pages | Select-Object Path,Text)
foreach ($write in $writes) {
  $fullPath = [IO.Path]::GetFullPath([string]$write.Path)
  $temporaryPath = "$fullPath.tmp-$PID"
  $writeBom = [string]$write.Path -eq 'content/transportation/transportation-plans.md'
  [IO.File]::WriteAllText($temporaryPath,[string]$write.Text,[Text.UTF8Encoding]::new($writeBom))
  Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
}
[pscustomobject]@{ modified_pages=@($writes.Path); removed_individual_entries=23; compilation_links=6 } | ConvertTo-Json -Compress
