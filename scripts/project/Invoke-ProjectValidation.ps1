[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$HugoPath = 'C:\Users\ben\AppData\Local\Microsoft\WinGet\Packages\Hugo.Hugo.Extended_Microsoft.Winget.Source_8wekyb3d8bbwe\hugo.exe',
  [switch]$CheckExternalLinks
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
& "$PSScriptRoot/Test-MasterInventory.ps1" -InventoryPath $InventoryPath
if (-not $?) { throw 'Master inventory validation failed.' }
& "$PSScriptRoot/Test-DiscoveryCrawlerRegression.ps1" -OutputPath 'tmp/crawler-regression-report.json'
if (-not $?) { throw 'Crawler discovery regression failed.' }
& $HugoPath --gc --minify --destination tmp/site-build
if ($LASTEXITCODE) { throw 'Hugo build failed.' }

$broken = @()
if ($CheckExternalLinks) {
  $inventory = Get-Content -Raw $InventoryPath | ConvertFrom-Json
  foreach ($candidate in $inventory.candidates | Where-Object status -in @('implemented','validated')) {
    $url = if ($candidate.r2_url) { $candidate.r2_url } elseif ($candidate.direct_file_url) { $candidate.direct_file_url } else { $candidate.source_url }
    if (-not $url) { continue }
    try {
      $response = Invoke-WebRequest -Uri $url -Method Head -UseBasicParsing
      if ($response.StatusCode -ge 400) { $broken += [pscustomobject]@{Id=$candidate.id;Url=$url;Status=$response.StatusCode} }
    } catch {
      try {
        $response = Invoke-WebRequest -Uri $url -Method Get -UseBasicParsing
        if ($response.StatusCode -ge 400) { $broken += [pscustomobject]@{Id=$candidate.id;Url=$url;Status=$response.StatusCode} }
      } catch { $broken += [pscustomobject]@{Id=$candidate.id;Url=$url;Status='error';Message=$_.Exception.Message} }
    }
  }
}
[pscustomobject]@{Hugo='passed';ExternalLinksChecked=[bool]$CheckExternalLinks;BrokenLinks=$broken.Count;Broken=$broken} | ConvertTo-Json -Depth 5
if ($broken.Count) { exit 1 }
