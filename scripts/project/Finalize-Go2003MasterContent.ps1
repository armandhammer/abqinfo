[CmdletBinding()]
param(
  [string]$PlanPath = 'project-state/discovery/go2003-master-compilation-r2-archive-plan-2026-09-13.json',
  [string]$PublicValidationPath = 'project-state/discovery/go2003-master-compilation-r2-public-validation-2026-09-13.json',
  [string]$ResearchPath = 'project-state/discovery/claude-consolidation-2003-general-obligation-bond-program-master-record-2026-09-13.json',
  [string]$DecisionsPath = 'project-state/discovery/go2003-master-compilation-decisions-2026-09-13.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$plan = Get-Content -Raw -Encoding UTF8 -LiteralPath $PlanPath | ConvertFrom-Json
$public = Get-Content -Raw -Encoding UTF8 -LiteralPath $PublicValidationPath | ConvertFrom-Json
$research = Get-Content -Raw -Encoding UTF8 -LiteralPath $ResearchPath | ConvertFrom-Json
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$item = @($plan.items)
if ($item.Count -ne 1) { throw 'Expected exactly one 2003 master compilation.' }
$item = $item[0]
$result = @($public.results | Where-Object id -eq $item.id)
$master = @($inventory.candidates | Where-Object id -eq $item.id)
if ($result.Count -ne 1 -or $master.Count -ne 1 -or -not [bool]$result[0].byte_identical) { throw 'Master candidate or successful public verification is missing.' }
$master = $master[0]
if ([string]$result[0].checksum_sha256 -ne [string]$master.checksum_sha256 -or [int64]$result[0].size_bytes -ne [int64]$master.size_bytes) { throw 'Public master integrity does not match inventory.' }
$locations = @(
  'content/city-data/capital-spending.md',
  'content/city-data/public-safety-data.md',
  'content/public-works/parks-recreation.md',
  'content/transportation/transit/abq-ride.md',
  'content/public-works/stormwater-drainage.md',
  'content/transportation/transportation-plans.md'
)
$official = 'https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2003-bond-doc'
foreach ($location in $locations) {
  $page = Get-Content -Raw -Encoding UTF8 -LiteralPath $location
  if ($page -notlike "*$($master.r2_url)*" -or $page -notlike "*$official*") { throw "Master archive or official source-family link missing from $location." }
}
$master.status = 'validated'
$master.implementation_location = $locations[0]
$master.implementation_locations = $locations
$master.cross_listing_approved = $true
$master.validation_status = 'passed: all 21 authoritative City components separately archived; final compilation size and SHA-256, source-page equivalence, embedded provenance, visual QA, public byte-identical R2 download, description, and six page placements verified'
$master.processing_notes = @($master.processing_notes) + @('Public compilation download matched exact local size and SHA-256 after guarded upload.') | Sort-Object -Unique
$master.updated_at = (Get-Date).ToUniversalTime().ToString('o')

$componentIds = @($research.ordered_members | Sort-Object order | ForEach-Object candidate_id) + @('src-74326241e19c1551')
foreach ($id in $componentIds) {
  $candidate = @($inventory.candidates | Where-Object id -eq $id)
  if ($candidate.Count -ne 1) { throw "Expected one component inventory record for $id." }
  $candidate = $candidate[0]
  if (-not $candidate.r2_url -or -not $candidate.checksum_sha256 -or -not $candidate.size_bytes) { throw "Archived component metadata is incomplete for $id." }
  if ([string]$candidate.validation_status -notmatch '^passed:') { throw "Completed verification is not recorded for $id." }
  $prior = [string]$candidate.validation_status
  $candidate.status = 'excluded'
  $candidate.implementation_location = $null
  $candidate.implementation_locations = @()
  $candidate.cross_listing_approved = $false
  $candidate.exclusion_reason = if ($id -eq 'src-74326241e19c1551') { 'Excluded from standalone site publication because its complete content is already contained in R-02-30 and therefore in the verified 2003 annual master compilation; original archive and history retained.' } else { 'Excluded from standalone site publication after complete official-source-family review; retained byte-identically in R2 and presented through the verified 2003 annual master compilation.' }
  $candidate.validation_status = 'passed: authoritative provenance, exact original size and SHA-256, and public byte-identical archive were previously verified; retained as a source component with no standalone site entry'
  $candidate.processing_notes = @($candidate.processing_notes) + @("Prior completed verification preserved during consolidation: $prior",'Standalone listing removed under the approved sparse-series consolidation policy; original archive object remains unchanged.') | Sort-Object -Unique
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$decisions = Get-Content -Raw -Encoding UTF8 -LiteralPath $DecisionsPath | ConvertFrom-Json
$masterDecision = @($decisions.decisions | Where-Object id -eq $master.id)
if ($masterDecision.Count -ne 1) { throw 'The master compilation decision record is missing.' }
$masterDecision[0].implementation_locations = $locations
$masterDecision[0].cross_listing_approved = $true
$decisions | Add-Member -NotePropertyName updated_at -NotePropertyValue ((Get-Date).ToUniversalTime().ToString('o')) -Force
$decisionJson = $decisions | ConvertTo-Json -Depth 12
$decisionFullPath = [IO.Path]::GetFullPath($DecisionsPath)
$decisionTemporaryPath = "$decisionFullPath.tmp-$PID"
[IO.File]::WriteAllText($decisionTemporaryPath,$decisionJson,[Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $decisionTemporaryPath -Destination $decisionFullPath -Force

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$next = @($inventory.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { $next[0].id } else { $null }
$json = $inventory | ConvertTo-Json -Depth 12
$fullPath = [IO.Path]::GetFullPath($InventoryPath)
$temporaryPath = "$fullPath.tmp-$PID"
[IO.File]::WriteAllText($temporaryPath,$json,[Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
[pscustomobject]@{ master=$master.id; master_status=$master.status; component_records_retained=$componentIds.Count; implementation_locations=$locations } | ConvertTo-Json -Depth 4
