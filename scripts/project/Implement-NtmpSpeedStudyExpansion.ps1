[CmdletBinding()]
param(
  [string]$PlanPath = 'project-state/discovery/ntmp-speed-study-expansion-23-plan.json',
  [string]$ContentPath = 'content/transportation/roadway-projects/speed-management.md'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$plan = Get-Content -Raw -Encoding UTF8 -LiteralPath $PlanPath | ConvertFrom-Json
$content = Get-Content -Raw -Encoding UTF8 -LiteralPath $ContentPath
$startMarker = '### Historical Neighborhood Speed Studies'
$endMarker = '## Citywide Safety Program'
$start = $content.IndexOf($startMarker)
$end = $content.IndexOf($endMarker)
if ($start -lt 0 -or $end -le $start) { throw 'Could not locate the historical-study section boundaries.' }

$existingSection = $content.Substring($start, $end - $start)
$existingBlocks = @([regex]::Matches($existingSection, '(?ms)^- \[.*?(?=^- \[|\z)') | ForEach-Object { $_.Value.Trim() })
$newBlocks = foreach ($item in @($plan.items)) {
  $year = if ([string]$item.date -match '^(\d{4})') { $Matches[1] } else { [string]$item.date }
  $archiveUrl = "https://files.abqinfo.com/$($item.r2_key)"
  @"
- [$($item.title) ($year archived PDF)]($archiveUrl)

  $($item.description)

  [Official City PDF]($($item.direct_file_url))
"@.Trim()
}

$allBlocks = @($existingBlocks + $newBlocks)
$duplicateArchiveUrls = @($allBlocks | ForEach-Object {
  if ($_ -match 'https://files\.abqinfo\.com/[^)]+') { $Matches[0] }
} | Group-Object | Where-Object Count -gt 1)
if ($duplicateArchiveUrls.Count) { throw "Duplicate archive links in generated study section: $($duplicateArchiveUrls.Name -join ', ')" }

$sortedBlocks = @($allBlocks | Sort-Object {
  if ($_ -match '^- \[([^]]+)\]') { $Matches[1].ToLowerInvariant() } else { $_.ToLowerInvariant() }
})
$intro = @"
### Historical Neighborhood Speed Studies

These City reports preserve the street-level speed, volume, crash, and roadway evidence behind Albuquerque traffic-calming decisions. The archive spans 2015–2021 and includes both streets that qualified for NTMP treatment and streets that did not, preserving the basis for each decision.

$($sortedBlocks -join "`r`n`r`n")

"@

$updated = $content.Substring(0, $start) + $intro.TrimEnd() + "`r`n`r`n" + $content.Substring($end)
$fullPath = [IO.Path]::GetFullPath($ContentPath)
$temporaryPath = "$fullPath.tmp-$PID"
[IO.File]::WriteAllText($temporaryPath, $updated, [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force

[pscustomobject]@{
  ExistingStudies = $existingBlocks.Count
  AddedStudies = $newBlocks.Count
  TotalStudies = $sortedBlocks.Count
  ContentPath = $ContentPath
} | ConvertTo-Json -Compress
