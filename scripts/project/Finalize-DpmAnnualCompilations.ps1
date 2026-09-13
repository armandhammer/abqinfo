[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$PlanPath,
  [Parameter(Mandatory)][string]$PublicValidationPath,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$plan = Get-Content -Raw -Encoding UTF8 -LiteralPath $PlanPath | ConvertFrom-Json
$public = Get-Content -Raw -Encoding UTF8 -LiteralPath $PublicValidationPath | ConvertFrom-Json
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json

foreach ($item in @($plan.items)) {
  $candidate = @($inventory.candidates | Where-Object id -eq $item.id)
  $result = @($public.results | Where-Object id -eq $item.id)
  if ($candidate.Count -ne 1 -or $result.Count -ne 1 -or -not [bool]$result[0].byte_identical) { throw "Missing candidate or successful public validation for $($item.id)." }
  $candidate = $candidate[0]
  if ([string]$result[0].checksum_sha256 -ne [string]$candidate.checksum_sha256 -or [int64]$result[0].size_bytes -ne [int64]$candidate.size_bytes) { throw "Public integrity result does not match inventory for $($item.id)." }
  if ([string]$candidate.provenance_status -notmatch '^ABQInfo compilation derived from separately archived and verified authoritative City originals') { throw "Compilation provenance is incomplete for $($item.id)." }
  $locations = @($item.implementation_locations)
  if (-not $locations.Count) { $locations = @([string]$item.proposed_canonical_page) }
  foreach ($location in $locations) {
    $page = Get-Content -Raw -Encoding UTF8 -LiteralPath $location
    if ($page -notlike "*$($candidate.r2_url)*" -or $page -notlike '*https://documents.cabq.gov/planning/development-process-manual/*') {
      throw "Compilation archive or official-source-family link is missing from $location for $($item.id)."
    }
  }
  $candidate.status = 'validated'
  $candidate.description = [string]$item.description
  $candidate.description_word_count = @([string]$item.description -split '\s+' | Where-Object { $_ }).Count
  $candidate.implementation_location = [string]$item.proposed_canonical_page
  $candidate.implementation_locations = $locations
  $candidate.cross_listing_approved = [bool]($locations.Count -gt 1)
  $candidate.validation_status = 'passed: separately archived official components, final compilation size and SHA-256, source-page equivalence, embedded provenance, visual QA, public byte-identical R2 download, description, and all page placements verified'
  $candidate.processing_notes = @($candidate.processing_notes) + @('Public compilation download matched exact local size and SHA-256 after upload.') | Sort-Object -Unique
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$json = $inventory | ConvertTo-Json -Depth 12
$fullPath = [IO.Path]::GetFullPath($InventoryPath)
$temporaryPath = "$fullPath.tmp-$PID"
[IO.File]::WriteAllText($temporaryPath, $json, [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
[pscustomobject]@{ finalized=@($plan.items).Count; status='validated published annual compilations' } | ConvertTo-Json -Compress
