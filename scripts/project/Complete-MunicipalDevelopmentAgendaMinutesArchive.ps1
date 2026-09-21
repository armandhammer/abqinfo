[CmdletBinding()]
param(
  [string]$PreparationPath = 'project-state/discovery/municipaldevelopment-agenda-minutes-archive-preparation-2026-09-20.json',
  [string]$VerificationPath = 'project-state/discovery/municipaldevelopment-agenda-minutes-archive-public-byte-verification-2026-09-21.json',
  [string]$PlanPath = 'project-state/discovery/municipaldevelopment-agenda-minutes-r2-archive-plan-2026-09-21.json',
  [string]$PublicValidationPath = 'project-state/discovery/municipaldevelopment-agenda-minutes-public-byte-validation-2026-09-21.json',
  [string]$R2InventoryPath = 'project-state/r2-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Json([object]$Value, [string]$Path) {
  $fullPath = [IO.Path]::GetFullPath($Path)
  $temporaryPath = "$fullPath.tmp-$PID"
  [IO.File]::WriteAllText($temporaryPath, ($Value | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
}

$preparation = Get-Content -Raw -Encoding UTF8 -LiteralPath $PreparationPath | ConvertFrom-Json
$verification = Get-Content -Raw -Encoding UTF8 -LiteralPath $VerificationPath | ConvertFrom-Json
$r2 = Get-Content -Raw -Encoding UTF8 -LiteralPath $R2InventoryPath | ConvertFrom-Json
if ($verification.state -notin @('complete_all_18_uploaded_and_public_byte_verified', 'complete_all_18_uploaded_public_byte_verified_and_r2_inventory_reconciled')) { throw 'The 18-record archive verification is not complete.' }
if (@($preparation.records).Count -ne 18 -or @($verification.results).Count -ne 18) { throw 'Expected exactly 18 prepared and verified records.' }

$items = @()
$validationResults = @()
foreach ($record in @($preparation.records)) {
  $result = @($verification.results | Where-Object id -eq $record.id)
  if ($result.Count -ne 1 -or $result[0].source_byte_verification -ne 'passed' -or $result[0].upload -ne 'passed' -or $result[0].public_byte_verification -ne 'passed') { throw "Missing complete verification for $($record.id)." }
  if ([int64]$result[0].public_size_bytes -ne [int64]$record.size_bytes -or [string]$result[0].public_checksum_sha256 -ne [string]$record.checksum_sha256) { throw "Public-byte evidence differs from prepared source for $($record.id)." }
  $items += [pscustomobject][ordered]@{ id = $record.id; r2_key = $record.proposed_r2_key; size_bytes = [int64]$record.size_bytes; checksum_sha256 = $record.checksum_sha256 }
  $validationResults += [pscustomobject][ordered]@{ id = $record.id; public_url = $result[0].public_url; size_bytes = [int64]$result[0].public_size_bytes; checksum_sha256 = $result[0].public_checksum_sha256; byte_identical = $true; verified_at = $result[0].public_verified_at }
}
if (@($items.r2_key | Group-Object | Where-Object Count -gt 1).Count) { throw 'Duplicate R2 key in the prepared 18-record batch.' }
$existingCount = @($items | Where-Object { @($r2.objects | Where-Object key -eq $_.r2_key).Count -eq 1 }).Count
if ($existingCount -ne 0 -and $existingCount -ne $items.Count) { throw 'Local R2 inventory contains only a partial prepared-key set; refuse ambiguous reconciliation.' }
if ($existingCount -eq $items.Count) {
  foreach ($item in $items) {
    $object = @($r2.objects | Where-Object key -eq $item.r2_key)[0]
    if ([int64]$object.size_bytes -ne [int64]$item.size_bytes) { throw "Existing R2 inventory size mismatch for $($item.id)." }
  }
  $accounting = [pscustomobject]@{ object_count = $r2.object_count; total_bytes = $r2.total_bytes; added_or_reconciled = $items.Count; inventory_path = $R2InventoryPath }
} else {
  [int64]$addedBytes = ($items | Measure-Object size_bytes -Sum).Sum
  $plan = [ordered]@{ schema_version = 1; batch_id = 'municipaldevelopment-agenda-minutes-archive-2026-09-21'; current_r2_bytes = [int64]$r2.total_bytes; maximum_object_bytes = 100000000; maximum_projected_r2_bytes = 10000000000; batch_bytes = $addedBytes; added_bytes = $addedBytes; projected_r2_bytes = [int64]$r2.total_bytes + $addedBytes; items = $items }
  $validation = [ordered]@{ schema_version = 1; artifact_type = 'public_byte_validation'; verified_at = (Get-Date).ToUniversalTime().ToString('o'); results = $validationResults }
  Write-Json $plan $PlanPath
  Write-Json $validation $PublicValidationPath
  $accounting = & "$PSScriptRoot/Update-R2InventoryFromArchivePlan.ps1" -PlanPath $PlanPath -PublicValidationPath $PublicValidationPath -R2InventoryPath $R2InventoryPath
}
$verification | Add-Member -NotePropertyName r2_inventory_accounting -NotePropertyValue $accounting -Force
$verification.state = 'complete_all_18_uploaded_public_byte_verified_and_r2_inventory_reconciled'
$verification.completed_at = (Get-Date).ToUniversalTime().ToString('o')
Write-Json $verification $VerificationPath
$accounting | ConvertTo-Json -Compress
