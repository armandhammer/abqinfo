[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$closeout = Get-Content -Raw -Encoding UTF8 'project-state/discovery/planned-growth-strategy-production-closeout-2026-09-24.json' | ConvertFrom-Json -DateKind String
if ($closeout.production_verification_result -ne 'passed' -or $closeout.pr_number -ne 168 -or $closeout.merge_commit_sha -ne '8cfba47b46a464a04f67b1fccbe3943dd30b74c9') {
  throw 'PGS production closeout evidence is not verified.'
}
if (@($closeout.ordered_inventory_ids).Count -ne 13 -or @($closeout.ordered_inventory_ids | Sort-Object -Unique).Count -ne 13) {
  throw 'PGS closeout must contain exactly 13 distinct inventory IDs.'
}
$inventory = Get-Content -Raw -Encoding UTF8 'project-state/master-inventory.json' | ConvertFrom-Json -DateKind String
$note = "PGS production closeout 2026-09-24: PR #168 was manually reviewed and merged at $($closeout.merge_commit_sha). Production $($closeout.production_page_url) was verified at $($closeout.production_verified_at): the single Citywide Growth Strategy section is live with the complete Part 1 original and 12 separate Part 2 City originals covering all 11 named chapters, including Chapter 3.0; all 13 archive and official-source link pairs match the prepared records in order. No verified complete combined Part 2 original exists. See planned-growth-strategy-production-closeout-2026-09-24.json."
$status = "Passed: PR #168 merged; production Area & Sector Plans / Citywide Growth Strategy verified $($closeout.production_verified_at); live as one curated PGS family."
foreach ($id in $closeout.ordered_inventory_ids) {
  $row = @($inventory.candidates | Where-Object id -eq $id)
  if ($row.Count -ne 1) { throw "Expected one inventory row for $id." }
  if ($row[0].status -notin @('implemented', 'validated')) { throw "Unexpected inventory status for ${id}: $($row[0].status)" }
  if ($row[0].implementation_location -ne 'content/development-land-use/area-sector-plans.md') { throw "Unexpected PGS implementation location for $id." }
  $notes = @($row[0].processing_notes)
  if ($note -notin $notes) { $notes += $note }
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $id -Set @{ status = 'validated'; validation_status = $status; processing_notes = $notes } | Out-Null
  Write-Host "Validated $id"
}
