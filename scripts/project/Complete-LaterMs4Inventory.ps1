[CmdletBinding()]
param(
  [string]$CloseoutPath = 'project-state/discovery/later-ms4-production-closeout-2026-09-25.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$closeout = Get-Content -Raw -Encoding UTF8 -LiteralPath $CloseoutPath | ConvertFrom-Json -DateKind String
$archive = Get-Content -Raw -Encoding UTF8 -LiteralPath 'project-state/discovery/later-ms4-archive-public-byte-verification-2026-09-25.json' | ConvertFrom-Json
$implementation = Get-Content -Raw -Encoding UTF8 -LiteralPath 'project-state/discovery/later-ms4-hugo-implementation-2026-09-25.json' | ConvertFrom-Json
$ids = @('src-5cdb4d5491c3a02d','src-975528e01439f6df','src-fdc66c5b8de48584','src-7c1a063b817989bd','src-eda3280085776f61','src-e531466aed7f5387')
if ($closeout.production_verification_result -ne 'passed' -or $closeout.pr_number -ne 174 -or $closeout.pr_head_sha -ne '85f66b737eb4829d703bbe042697dac5cd0fab78' -or $closeout.merge_commit_sha -ne '04c5080cebf2ff094d569c941cc32b23a3e2ab6d') { throw 'Later-MS4 production closeout is not verified for the approved PR merge.' }
if (($closeout.inventory_ids_to_validate -join ',') -cne ($ids -join ',') -or ($implementation.implemented_inventory_ids -join ',') -cne ($ids -join ',') -or @($closeout.six_new_archive_and_official_source_link_checks).Count -ne 6 -or $archive.summary.public_byte_verified -ne 6) { throw 'Later-MS4 closeout must have exactly six implemented and public-byte-verified IDs.' }
if ($closeout.http_result -ne 200 -or $closeout.r2_accounting_unchanged.object_count -ne 1237 -or $closeout.r2_accounting_unchanged.total_bytes -ne 9218281842 -or -not $closeout.r2_accounting_unchanged.every_key_size_etag_matches_fresh_live_listing) { throw 'Production HTTP or R2 accounting check is incomplete.' }
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json -DateKind String
foreach ($id in $ids) {
  $row = @($inventory.candidates | Where-Object id -eq $id)
  $verified = @($archive.results | Where-Object id -eq $id)
  if ($row.Count -ne 1 -or $verified.Count -ne 1 -or -not $verified[0].byte_identical) { throw "Missing validated archive/inventory identity: $id" }
  if ($row[0].status -notin @('implemented','validated') -or $row[0].implementation_location -cne 'content/public-works/stormwater-drainage.md' -or $row[0].r2_url -cne $verified[0].public_url -or $row[0].checksum_sha256 -cne $verified[0].expected_checksum_sha256 -or $row[0].size_bytes -ne $verified[0].expected_size_bytes) { throw "Unexpected implementation, source, or archive state for $id" }
}
$note = "Later-MS4 production closeout 2026-09-25: PR #174 manually approved and merged at $($closeout.merge_commit_sha). Fresh and ordinary production HTTP 200 responses verified the Municipal Stormwater section at $($closeout.verification_timestamp): 2014 NMR04A000 permit and City NMR04A014 coverage, ten annual reports in descending FY order, six exact archive/source pairs, and preserved 2005 permit; draft, letter, and separate 2014 annual-report package absent. See later-ms4-production-closeout-2026-09-25.json."
$status = "Passed: PR #174 merged; production Stormwater and Drainage / Municipal Stormwater section verified $($closeout.verification_timestamp); exact archive/source links live."
foreach ($id in $ids) {
  $row = @($inventory.candidates | Where-Object id -eq $id)[0]
  $notes = @($row.processing_notes)
  if ($note -notin $notes) { $notes += $note }
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $id -InventoryPath $InventoryPath -Set @{ status='validated';validation_status=$status;processing_notes=$notes } | Out-Null
  Write-Host "Validated $id"
}
