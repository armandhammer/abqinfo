[CmdletBinding()]
param([string]$InventoryPath = 'project-state/master-inventory.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$now = (Get-Date).ToUniversalTime().ToString('o')

foreach ($id in @('src-7ef6d021d2326e49','src-5cdd997502c0d388')) {
  $candidate = @($inventory.candidates | Where-Object id -eq $id)
  if ($candidate.Count -ne 1 -or $candidate[0].status -ne 'validated') { throw "Expected validated map candidate $id." }
  $candidate = $candidate[0]
  $candidate.cross_listing_approved = $true
  $candidate.implementation_locations = @('content/development-land-use/area-sector-plans.md','content/maps/maps.md')
  $candidate.processing_notes = @(@($candidate.processing_notes) + 'Cross-listed on Maps because it is both a planning-history record and a standalone geographic reference.' | Sort-Object -Unique)
  $candidate.updated_at = $now
}

$alias = @($inventory.candidates | Where-Object id -eq 'src-0043470c0b07bceb')
if ($alias.Count -ne 1) { throw 'Expected one overlay-map view alias.' }
$alias = $alias[0]
$alias.status = 'duplicate'
$alias.exclusion_reason = 'Plone /view alias for canonical archived candidate src-5cdd997502c0d388; the canonical record preserves the direct City PDF, R2 object, and page placements.'
$alias.validation_status = 'duplicate: normalized source alias reconciled to src-5cdd997502c0d388'
$alias.processing_notes = @(@($alias.processing_notes) + 'Reconciled after direct PDF review in North Fourth historical batch 26.' | Sort-Object -Unique)
$alias.updated_at = $now

foreach ($status in $inventory.allowed_statuses) {
  $inventory.counts.$status = @($inventory.candidates | Where-Object status -eq $status).Count
}
$nonterminal = @('pending review','approved for addition','downloading','downloaded','parsed','description drafted','placement assigned','implemented')
$inventory.next_pending_id = @($inventory.candidates | Where-Object status -in $nonterminal | Sort-Object id | Select-Object -First 1).id
$inventory.generated_at = $now
[IO.File]::WriteAllText([IO.Path]::GetFullPath($InventoryPath), ($inventory | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))

[pscustomobject]@{ CrossListed = 2; DuplicatesReconciled = 1; NextPending = $inventory.next_pending_id } | ConvertTo-Json -Compress
