[CmdletBinding()]
param(
  [string]$ImplementationPath = 'project-state/discovery/later-ms4-hugo-implementation-2026-09-25.json',
  [string]$PreparationPath = 'project-state/discovery/later-ms4-archive-preparation-2026-09-24.json',
  [string]$ArchivePath = 'project-state/discovery/later-ms4-archive-public-byte-verification-2026-09-25.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$implementation = Get-Content -Raw -Encoding UTF8 -LiteralPath $ImplementationPath | ConvertFrom-Json
$prepared = Get-Content -Raw -Encoding UTF8 -LiteralPath $PreparationPath | ConvertFrom-Json
$archive = Get-Content -Raw -Encoding UTF8 -LiteralPath $ArchivePath | ConvertFrom-Json
$page = [string]$implementation.page
$ids = @('src-5cdb4d5491c3a02d','src-975528e01439f6df','src-fdc66c5b8de48584','src-7c1a063b817989bd','src-eda3280085776f61','src-e531466aed7f5387')
if ($implementation.state -ne 'implemented_on_planning_branch_not_live' -or $page -cne 'content/public-works/stormwater-drainage.md' -or (@($implementation.implemented_inventory_ids) -join ',') -cne ($ids -join ',')) { throw 'Implementation scope differs from the authorized six records and page.' }
if ($archive.state -ne 'complete_all_six_public_byte_verified_and_inventory_reconciled' -or $archive.summary.public_byte_verified -ne 6) { throw 'Six exact public-byte verifications are required before implementation.' }
$preparedById = @{}; foreach ($record in @($prepared.records)) { $preparedById[$record.id] = $record }
$verifiedById = @{}; foreach ($result in @($archive.results)) { $verifiedById[$result.id] = $result }
foreach ($id in $ids) {
  if (-not $preparedById.ContainsKey($id) -or -not $verifiedById.ContainsKey($id)) { throw "Missing prepared or verified record: $id" }
  $record = $preparedById[$id]
  $result = $verifiedById[$id]
  if (-not $result.byte_identical -or $result.public_url -cne $record.proposed_future_archive_url -or $result.public_checksum_sha256 -cne $record.checksum_sha256 -or [int64]$result.public_size_bytes -ne [int64]$record.size_bytes) { throw "Public-byte evidence mismatch: $id" }
  $inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json -DateKind String
  $candidate = @($inventory.candidates | Where-Object id -eq $id)
  if ($candidate.Count -ne 1) { throw "Inventory record missing or duplicated: $id" }
  $candidate = $candidate[0]
  if ($candidate.status -notin @('placement assigned','implemented') -or $candidate.r2_url -cne $result.public_url -or $candidate.direct_file_url -cne $record.authoritative_source_url -or $candidate.checksum_sha256 -cne $record.checksum_sha256 -or $candidate.size_bytes -ne $record.size_bytes -or $candidate.proposed_canonical_page -cne $page) { throw "Inventory identity or lifecycle mismatch: $id" }
  $note = 'Later-MS4 Hugo implementation 2026-09-25: listed once in the Municipal Stormwater Program and Annual Reports section with exact verified archive and authoritative source links; planning branch only, PR preview and manual review pending.'
  $notes = @($candidate.processing_notes)
  if ($note -notin $notes) { $notes += $note }
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $id -InventoryPath $InventoryPath -Set @{
    status='implemented';implementation_location=$page;implementation_locations=@($page)
    validation_status='implemented on planning branch with exact archived/source links; local Hugo validation passed; non-production PR preview and manual editorial review pending; not live'
    processing_notes=$notes
  } | Out-Null
}
Write-Output 'Later-MS4 six inventory records implemented on planning branch; production not claimed.'
