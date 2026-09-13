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
  if (-not $candidate.source_url -or -not $candidate.direct_file_url -or [string]$candidate.provenance_status -notmatch '^official') { throw "Official provenance is incomplete for $($item.id)." }
  $candidate.status = 'excluded'
  $candidate.implementation_location = $null
  $candidate.implementation_locations = @()
  $candidate.cross_listing_approved = $false
  $candidate.exclusion_reason = 'Excluded from standalone site publication after exhaustive annual source-family review; preserved byte-identically in R2 and presented only within the verified annual compilation.'
  $candidate.validation_status = 'passed: official City provenance, local exact size and SHA-256, and public byte-identical R2 download verified; retained as an annual-compilation component with no standalone site entry'
  $candidate.processing_notes = @($candidate.processing_notes) + @('Original authoritative file uploaded without modification; public R2 download matched exact size and SHA-256. Preserved as a source component only.') | Sort-Object -Unique
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
[pscustomobject]@{ finalized=@($plan.items).Count; status='archived and excluded from standalone publication' } | ConvertTo-Json -Compress
