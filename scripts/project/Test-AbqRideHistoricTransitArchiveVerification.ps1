[CmdletBinding()]
param(
  [string]$PreparationPath = 'project-state/discovery/transit-openspace-nmdot-sustainability-archive-preparation-2026-09-20.json',
  [string]$VerificationPath = 'project-state/discovery/abq-ride-historic-transit-archive-public-byte-verification-2026-09-21.json',
  [string]$R2InventoryPath = 'project-state/r2-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ids = @('src-6220c942e21cbc67','src-cd76ed2642c5bc5b','src-e42bbc888a2b6931','src-ee0aec5b78f6ec86','src-54391dbd27e5d212','src-4092005fa5d61b38','src-e28e38dabfbdb2e2','src-2dbbf587fead4146','src-12207bd87008378c')
$preparation = Get-Content -Raw -Encoding UTF8 -LiteralPath $PreparationPath | ConvertFrom-Json
$verification = Get-Content -Raw -Encoding UTF8 -LiteralPath $VerificationPath | ConvertFrom-Json
$r2 = Get-Content -Raw -Encoding UTF8 -LiteralPath $R2InventoryPath | ConvertFrom-Json
if ($verification.state -ne 'complete_all_9_uploaded_public_byte_verified_and_r2_inventory_reconciled') { throw 'ABQ RIDE verification artifact is not complete.' }
foreach ($id in $ids) {
  $record = @($preparation.records | Where-Object id -eq $id)
  $result = @($verification.results | Where-Object id -eq $id)
  $preflight = @($verification.preflight | Where-Object id -eq $id)
  if ($record.Count -ne 1 -or $result.Count -ne 1 -or $preflight.Count -ne 1) { throw "Incomplete evidence for $id." }
  if ($result[0].source_byte_verification -ne 'passed' -or $result[0].upload -ne 'passed' -or $result[0].public_byte_verification -ne 'passed' -or $result[0].failure) { throw "Incomplete archive verification for $id." }
  if ([int64]$result[0].public_size_bytes -ne [int64]$record[0].source_evidence.size_bytes -or [string]$result[0].public_checksum_sha256 -ne [string]$record[0].source_evidence.sha256) { throw "Public bytes differ from saved evidence for $id." }
  if (@($r2.objects | Where-Object key -eq $record[0].archive_preparation.proposed_r2_key).Count -ne 1) { throw "R2 inventory is missing $id." }
}
foreach ($id in @('src-6220c942e21cbc67','src-cd76ed2642c5bc5b','src-e42bbc888a2b6931')) {
  $result = @($verification.results | Where-Object id -eq $id)[0]
  if ($result.visual_render_inspection -notlike 'passed:*') { throw "Legacy Word visual inspection is not recorded as passed for $id." }
}
$renderer = Get-Content -Raw -Encoding UTF8 -LiteralPath "$PSScriptRoot/Render-AbqRideLegacyWordInspection.ps1"
if ($renderer -notmatch 'preflightById' -or $renderer -notmatch 'preflight\.local_path') { throw 'Legacy Word renderer does not map result IDs to preflight local paths.' }
[pscustomobject]@{records=9;word_visual_inspections=3;public_byte_verified=9;object_count=$r2.object_count;total_bytes=$r2.total_bytes}|ConvertTo-Json -Compress
