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
if (Test-Path -LiteralPath 'project-state/discovery/approved-inventory-mission-scope-audit-2026-09-22.json') {
  & python "$PSScriptRoot/Test-MissionScopeAudit.py"
  if ($LASTEXITCODE) { throw 'Mission-scope audit regression failed.' }
}
& "$PSScriptRoot/Test-UpdateCouncilCloseoutCheckpoint.ps1"
if (-not $?) { throw 'Council checkpoint idempotency validation failed.' }
& "$PSScriptRoot/Test-ProjectStateRegeneration.ps1" -MasterPath $InventoryPath
if (-not $?) { throw 'Project-state regeneration validation failed.' }
& "$PSScriptRoot/Test-PullRequestDescriptionRegression.ps1"
if (-not $?) { throw 'Pull-request description regression failed.' }
& python "$PSScriptRoot/Test-ApplySavedTerminalResearch.py"
if ($LASTEXITCODE) { throw 'Saved terminal research regression failed.' }
if (Test-Path -LiteralPath 'project-state/discovery/nmdot-grant-administration-and-application-decision-2026-09-19.json') {
  & python "$PSScriptRoot/Test-NmdotGrantAdministrationDecision.py"
  if ($LASTEXITCODE) { throw 'NMDOT grant-administration decision validation failed.' }
}
if (Test-Path -LiteralPath 'project-state/discovery/nmdot-statewide-truck-parking-study-archive-preparation-2026-09-21.json') {
  & python "$PSScriptRoot/Test-NmdotTruckParkingStudyArchivePreparation.py"
  if ($LASTEXITCODE) { throw 'NMDOT truck-parking study archive-preparation validation failed.' }
}
if (Test-Path -LiteralPath 'project-state/discovery/municipaldevelopment-standard-forms-archive-preparation-2026-09-19.json') {
  & python "$PSScriptRoot/Test-MunicipalDevelopmentStandardFormsArchivePreparation.py"
  & python "$PSScriptRoot/Test-MunicipalDevelopmentAgendaMinutesArchivePreparation.py"
  if ($LASTEXITCODE) { throw 'Municipal Development standard-forms archive-preparation validation failed.' }
}
if (Test-Path -LiteralPath 'project-state/discovery/mra-appeal-form-family-decision-2026-09-19.json') {
  & python "$PSScriptRoot/Test-MraAppealFormFamilyDecision.py"
  if ($LASTEXITCODE) { throw 'MRA Appeal Form family-decision validation failed.' }
}
if (Test-Path -LiteralPath 'project-state/discovery/fiber-rulemaking-meeting-records-decision-2026-09-19.json') {
  & python "$PSScriptRoot/Test-FiberRulemakingMeetingRecordsDecision.py"
  if ($LASTEXITCODE) { throw 'Fiber rulemaking meeting-records decision validation failed.' }
}
if (Test-Path -LiteralPath 'project-state/discovery/2014-ms4-package-decision-2026-09-18.json') {
  & "$PSScriptRoot/Test-2014Ms4PackageDecision.ps1"
  if (-not $?) { throw '2014 MS4 package-decision validation failed.' }
}
if (Test-Path -LiteralPath 'project-state/discovery/2011-capital-spending-consolidation-manifest-2026-09-18.json') {
  & python "$PSScriptRoot/Test-2011CapitalSpendingConsolidation.py"
  if ($LASTEXITCODE) { throw '2011 Capital Spending consolidation validation failed.' }
}
if (Test-Path -LiteralPath 'project-state/discovery/2009-capital-spending-consolidation-decision-2026-09-18.json') {
  & python "$PSScriptRoot/Test-2009CapitalSpendingConsolidationDecision.py"
  if ($LASTEXITCODE) { throw '2009 Capital Spending consolidation decision validation failed.' }
}
if (Test-Path -LiteralPath 'project-state/discovery/2007-2016-capital-details-consolidation-decision-2026-09-18.json') {
  & python "$PSScriptRoot/Test-2007DecadePlanCapitalDetailsDecision.py"
  if ($LASTEXITCODE) { throw '2007--2016 Capital Spending consolidation decision validation failed.' }
}
if (Test-Path -LiteralPath 'project-state/discovery/2005-2013-impact-fee-ccip-consolidation-decision-2026-09-18.json') {
  & python "$PSScriptRoot/Test-ImpactFeeCcipConsolidationDecision.py"
  if ($LASTEXITCODE) { throw '2005--2013 impact-fee CCIP consolidation decision validation failed.' }
}
if (Test-Path -LiteralPath 'project-state/discovery/energy-water-public-facilities-capital-spending-family-map-2026-09-18.json') {
  & python "$PSScriptRoot/Test-EnergyWaterBondFamilyMap.py"
  if ($LASTEXITCODE) { throw 'Energy/Water Capital Spending family-map validation failed.' }
}
if (Test-Path -LiteralPath 'project-state/discovery/2011-2023-energy-water-public-facilities-system-modernization-cycle-scopes-decision-2026-09-18.json') {
  & python "$PSScriptRoot/Test-EnergyWaterCycleScopeDecision.py"
  if ($LASTEXITCODE) { throw 'Energy/Water six-cycle scope decision validation failed.' }
}
if (Test-Path -LiteralPath 'project-state/discovery/capital-spending-consolidation-closeout-status-2026-09-18.json') {
  & python "$PSScriptRoot/Test-CapitalSpendingConsolidationCloseout.py"
  if ($LASTEXITCODE) { throw 'Capital Spending consolidation closeout validation failed.' }
}
Get-ChildItem -LiteralPath 'project-state/discovery' -Filter 'ordinary-queue-terminal-integration-batch*.json' | ForEach-Object {
  & python "$PSScriptRoot/Test-OrdinaryQueueTerminalIntegrationBatch.py" --artifact ([IO.Path]::GetRelativePath((Get-Location).Path, $_.FullName).Replace('\','/'))
  if ($LASTEXITCODE) { throw "Ordinary-queue terminal integration validation failed for $($_.Name)." }
}
& "$PSScriptRoot/Test-ContentStyle.ps1"

& "$PSScriptRoot/Test-ContentPublicationQualityRegression.ps1"
if (-not $?) { throw 'Content publication quality regression failed.' }
& "$PSScriptRoot/Test-DiscoveryCrawlerRegression.ps1" -OutputPath 'tmp/crawler-regression-report.json'
if (-not $?) { throw 'Crawler discovery regression failed.' }
& "$PSScriptRoot/Test-ParallelVerificationWorkflow.ps1"
if (-not $?) { throw 'Parallel verification workflow regression failed.' }
& "$PSScriptRoot/Test-ParallelVerificationCampaignWorkflow.ps1"
if (-not $?) { throw 'Autonomous parallel verification campaign regression failed.' }
& "$PSScriptRoot/Test-RetainedSourceAuditCoverage.ps1" -InventoryPath $InventoryPath
if (-not $?) { throw 'Retained-source descendant-audit coverage failed.' }
& $HugoPath --gc --minify --cleanDestinationDir --destination tmp/site-build
if ($LASTEXITCODE) { throw 'Hugo build failed.' }

$broken = @()
if ($CheckExternalLinks) {
  $inventory = Get-Content -Raw -Encoding UTF8 $InventoryPath | ConvertFrom-Json
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
