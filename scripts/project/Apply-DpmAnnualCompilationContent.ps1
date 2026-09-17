[CmdletBinding()]
param(
  [string]$PlanPath = 'project-state/discovery/dpm-annual-compilations-r2-archive-plan-2026-09-13.json',
  [string]$PublicValidationPath = 'project-state/discovery/dpm-annual-compilations-r2-public-validation-2026-09-13.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$plan = Get-Content -Raw -Encoding UTF8 -LiteralPath $PlanPath | ConvertFrom-Json
$public = Get-Content -Raw -Encoding UTF8 -LiteralPath $PublicValidationPath | ConvertFrom-Json
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$byYear = @{}
foreach ($item in @($plan.items)) {
  $result = @($public.results | Where-Object id -eq $item.id)
  if ($result.Count -ne 1 -or -not [bool]$result[0].byte_identical -or [string]$result[0].checksum_sha256 -ne [string]$item.checksum_sha256) {
    throw "Compilation $($item.id) has not passed exact public R2 validation."
  }
  $candidate = @($inventory.candidates | Where-Object id -eq $item.id)
  if ($candidate.Count -ne 1 -or -not $candidate[0].r2_url) { throw "Compilation inventory record is incomplete for $($item.id)." }
  $year = [int]$item.date
  $byYear[$year] = [pscustomobject]@{ url=[string]$candidate[0].r2_url; title=[string]$item.title; description=[string]$item.description }
}
foreach ($year in 2014..2018) { if (-not $byYear.ContainsKey($year)) { throw "Missing verified compilation for $year." } }

$official = 'https://documents.cabq.gov/planning/development-process-manual/'
function Entry([int]$Year) {
  $record = $byYear[$Year]
  $label = if ($Year -eq 2018) { "Development Process Manual Executive Committee Meeting Records, $Year" } else { "Development Process Manual Executive Committee Minutes, $Year" }
  return @"
- [$label (ABQInfo Historical Compilation, Archived PDF)]($($record.url))

  $($record.description)

  [Official City source library]($official)
"@
}

$canonicalPath = 'content/development-land-use/development-process.md'
$canonical = Get-Content -Raw -Encoding UTF8 -LiteralPath $canonicalPath
$canonicalBlock = ((2014..2018 | ForEach-Object { (Entry $_).Trim() }) -join "`n`n").TrimEnd() + "`n`n"
$canonicalPattern = '(?ms)^- \[Development Process Executive Committee Minutes, September 24, 2014.*?(?=^## Historic Preservation and Overlay-Zone Guidance)'
if ([regex]::Matches($canonical,$canonicalPattern).Count -ne 1) { throw 'Could not uniquely locate the individual DPM records on the canonical page.' }
$canonical = [regex]::Replace($canonical,$canonicalPattern,[System.Text.RegularExpressions.MatchEvaluator]{ param($m) $canonicalBlock })

$stormPath = 'content/public-works/stormwater-drainage.md'
$storm = Get-Content -Raw -Encoding UTF8 -LiteralPath $stormPath
$stormBlock = @"
- [DPM Executive Committee Minutes, 2016 (ABQInfo Historical Compilation, Archived PDF)]($($byYear[2016].url))

  The annual record traces Chapter 22's section-by-section review and approval, including drainage and erosion control, plus stormwater-modeling discussions; individual two-page minutes remain preserved inside the compilation.

  [Full annual committee record](/development-land-use/development-process/#archived-approved-amendments) · [Official City source library]($official)

- [DPM Executive Committee Minutes, 2017 (ABQInfo Historical Compilation, Archived PDF)]($($byYear[2017].url))

  The annual record completes Chapter 22 and Chapter 18 approvals while preserving all fifteen meeting records as one navigable sequence; the original PDFs remain separately archived with exact provenance.

  [Full annual committee record](/development-land-use/development-process/#archived-approved-amendments) · [Official City source library]($official)

"@
$stormBlock = $stormBlock.TrimEnd() + "`n`n"
$stormPattern = '(?ms)^- \[DPM Executive Committee Minutes, September 7, 2016.*?(?=^- \[City of Albuquerque Construction Site Manual)'
if ([regex]::Matches($storm,$stormPattern).Count -ne 1) { throw 'Could not uniquely locate the individual DPM stormwater cross-listings.' }
$storm = [regex]::Replace($storm,$stormPattern,[System.Text.RegularExpressions.MatchEvaluator]{ param($m) $stormBlock })

$designPath = 'content/transportation/design-references.md'
$design = Get-Content -Raw -Encoding UTF8 -LiteralPath $designPath
$designBlock = @"
- [DPM Executive Committee Minutes, 2017 (ABQInfo Historical Compilation, Archived PDF)]($($byYear[2017].url))

  The annual record documents adopted survey, public-transit, parking, pedestrian, pavement, building-permit, and related design provisions across fifteen committee meetings, consolidated into one provenance-preserving volume.

  [Full annual committee record](/development-land-use/development-process/#archived-approved-amendments) · [Official City source library]($official)

- [DPM Executive Committee Meeting Records, 2018 (ABQInfo Historical Compilation, Archived PDF)]($($byYear[2018].url))

  The annual record documents network-connectivity, intersection-design, construction-plan, and subdivision-compliance actions, plus the April 4 agenda clearly labeled because approved minutes were not located.

  [Full annual committee record](/development-land-use/development-process/#archived-approved-amendments) · [Official City source library]($official)

"@
$designBlock = $designBlock.TrimEnd() + "`n`n"
$designPattern = '(?ms)^- \[DPM Executive Committee Minutes, May 3, 2017.*?(?=^- \[Special Order 19 Notice)'
if ([regex]::Matches($design,$designPattern).Count -ne 1) { throw 'Could not uniquely locate the individual DPM design-reference cross-listings.' }
$design = [regex]::Replace($design,$designPattern,[System.Text.RegularExpressions.MatchEvaluator]{ param($m) $designBlock })

foreach ($pair in @(@($canonicalPath,$canonical),@($stormPath,$storm),@($designPath,$design))) {
  $fullPath = [IO.Path]::GetFullPath([string]$pair[0])
  $temporaryPath = "$fullPath.tmp-$PID"
  [IO.File]::WriteAllText($temporaryPath,[string]$pair[1],[Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
}
[pscustomobject]@{ modified_pages=@($canonicalPath,$stormPath,$designPath); canonical_compilations=5; stormwater_cross_listings=2; design_cross_listings=2 } | ConvertTo-Json -Compress
