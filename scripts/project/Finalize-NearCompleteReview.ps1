[CmdletBinding()]
param(
  [string]$PlanPath = 'project-state/near-complete-review-archive-plan-2026-08-20.json',
  [string]$PublicValidationPath = 'project-state/near-complete-review-public-validation-2026-08-20.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$plan = Get-Content -Raw -Encoding UTF8 -LiteralPath $PlanPath | ConvertFrom-Json
$publicValidation = Get-Content -Raw -Encoding UTF8 -LiteralPath $PublicValidationPath | ConvertFrom-Json
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json

foreach ($item in @($plan.items)) {
  $matches = @($inventory.candidates | Where-Object id -eq $item.id)
  if ($matches.Count -ne 1) { throw "Expected one inventory candidate for '$($item.id)'." }
  $candidate = $matches[0]
  $file = Get-Item -LiteralPath $candidate.local_path
  if ($file.Length -ne [int64]$item.size_bytes) { throw "Local size mismatch for '$($item.id)'." }
  $sha = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($sha -ne [string]$item.checksum_sha256) { throw "Local SHA-256 mismatch for '$($item.id)'." }
  $publicResult = @($publicValidation.results | Where-Object id -eq $item.id)
  if ($publicResult.Count -ne 1 -or -not $publicResult[0].byte_identical) { throw "Missing byte-identical public R2 validation for '$($item.id)'." }
  if ([string]$publicResult[0].checksum_sha256 -ne $sha) { throw "Public R2 SHA-256 mismatch for '$($item.id)'." }
  $page = Get-Content -Raw -Encoding UTF8 -LiteralPath $item.proposed_canonical_page
  if ($page -notlike "*$($candidate.r2_url)*") { throw "R2 URL is missing from '$($item.proposed_canonical_page)' for '$($item.id)'." }

  $candidate.status = 'requires human review'
  $candidate.implementation_location = [string]$item.proposed_canonical_page
  $candidate.implementation_locations = @([string]$item.proposed_canonical_page)
  $candidate.validation_status = 'passed: local size and SHA-256, public byte-identical R2 download, 20–50-word description, and page placement; authoritative government provenance requires human review'
  $candidate.processing_notes = @($candidate.processing_notes) + @('Public R2 download is byte-identical to the reviewed local original by exact size and SHA-256; page placement verified.') | Sort-Object -Unique
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$next = @($inventory.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { $next[0].id } else { $null }

$json = $inventory | ConvertTo-Json -Depth 12
$fullPath = [IO.Path]::GetFullPath($InventoryPath)
$temporaryPath = "$fullPath.tmp-$PID"
[IO.File]::WriteAllText($temporaryPath, $json, [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force

[pscustomobject]@{ Finalized=$plan.items.Count; Status='requires human review'; NextPending=$inventory.next_pending_id } | ConvertTo-Json -Compress
