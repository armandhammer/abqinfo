[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$PlanPath,
  [Parameter(Mandatory)][string]$PublicValidationPath,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$plan = Get-Content -Raw -Encoding UTF8 -LiteralPath $PlanPath | ConvertFrom-Json
$validation = Get-Content -Raw -Encoding UTF8 -LiteralPath $PublicValidationPath | ConvertFrom-Json
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json

foreach ($item in @($plan.items)) {
  $candidate = @($inventory.candidates | Where-Object id -eq $item.id)
  $result = @($validation.results | Where-Object id -eq $item.id)
  if ($candidate.Count -ne 1 -or $result.Count -ne 1 -or -not $result[0].byte_identical) { throw "Missing or failed validation for '$($item.id)'." }
  $candidate = $candidate[0]
  if ([string]$result[0].checksum_sha256 -ne [string]$candidate.checksum_sha256) { throw "Checksum mismatch for '$($item.id)'." }
  $page = Get-Content -Raw -Encoding UTF8 -LiteralPath $item.proposed_canonical_page
  if ($page -notlike "*$($candidate.r2_url)*" -or $page -notlike "*$($candidate.source_url)*") { throw "Archive or project-context link missing for '$($item.id)'." }
  $candidate.status = 'requires human review'
  $candidate.description = [string]$item.description
  $candidate.description_word_count = @([string]$item.description -split '\s+' | Where-Object { $_ }).Count
  $candidate.implementation_location = [string]$item.proposed_canonical_page
  $candidate.implementation_locations = @([string]$item.proposed_canonical_page)
  $candidate.validation_status = 'passed: exact local size and SHA-256, reviewed full-sheet rendering, public byte-identical R2 download, description, and page placement; exact-file authoritative provenance remains unresolved'
  $candidate.processing_notes = @($candidate.processing_notes) + @('Original contributed file uploaded without modification; public R2 download matched exact size and SHA-256.') | Sort-Object -Unique
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
[IO.File]::WriteAllText($temporaryPath,$json,[Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
[pscustomobject]@{Finalized=@($plan.items).Count;Status='requires human review';NextPending=$inventory.next_pending_id}|ConvertTo-Json -Compress
