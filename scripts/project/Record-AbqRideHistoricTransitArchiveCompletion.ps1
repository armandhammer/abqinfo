[CmdletBinding()]
param(
  [string]$VerificationPath = 'project-state/discovery/abq-ride-historic-transit-archive-public-byte-verification-2026-09-21.json',
  [string]$CheckpointPath = 'project-state/checkpoint.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Utf8Json([object]$Value, [string]$Path) {
  $fullPath = [IO.Path]::GetFullPath($Path)
  $temporaryPath = "$fullPath.tmp-$PID"
  [IO.File]::WriteAllText($temporaryPath, ($Value | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
}

$verification = Get-Content -Raw -Encoding UTF8 -LiteralPath $VerificationPath | ConvertFrom-Json
if ($verification.state -ne 'complete_all_9_uploaded_public_byte_verified_and_r2_inventory_reconciled' -or $verification.summary.uploaded -ne 9 -or $verification.summary.public_byte_verified -ne 9) { throw 'ABQ RIDE archive verification is not complete.' }
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$checkpoint = Get-Content -Raw -Encoding UTF8 -LiteralPath $CheckpointPath | ConvertFrom-Json -DateKind String
$ids = @('src-6220c942e21cbc67','src-cd76ed2642c5bc5b','src-e42bbc888a2b6931','src-ee0aec5b78f6ec86','src-54391dbd27e5d212','src-4092005fa5d61b38','src-e28e38dabfbdb2e2','src-2dbbf587fead4146','src-12207bd87008378c')
if (@($inventory.candidates | Where-Object { $_.id -in $ids -and $_.status -eq 'placement assigned' -and $_.r2_url }).Count -ne 9) { throw 'All nine archive-verified records must be placement assigned before checkpoint completion.' }
$blocker = 'ABQ RIDE historic-transit archive stage is blocked before R2 mutation: all nine City originals passed fresh size/SHA-256 verification, but the three required legacy-Word visual renders failed because Word automation returned 0x80070520 (no active logon session); live R2 reconciliation also could not run because Windows credential abqinfo-r2-upload was unavailable.'
$checkpoint.recorded_at = (Get-Date).ToUniversalTime().ToString('o')
$checkpoint.completed_item_range = 'Completed the explicitly authorized nine-record ABQ RIDE historic-transit archive/public-byte stage: all three Para-Transit legacy Word originals were rendered and visually inspected in the normal interactive host session, and all nine unchanged originals are R2-archived and exact public-byte verified. R2 is reconciled at 1,218 objects / 8,682,142,612 bytes. Durable evidence: project-state/discovery/abq-ride-historic-transit-archive-public-byte-verification-2026-09-21.json. No Hugo, PR, merge, or deployment action occurred; public-content implementation remains separately authorized.'
$checkpoint.total_candidates = @($inventory.candidates).Count
$checkpoint.counts_by_status = $inventory.counts
$checkpoint.remaining_nonterminal = @($inventory.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') }).Count
$checkpoint.next_pending_id = $inventory.next_pending_id
$checkpoint.blockers = @($checkpoint.blockers | Where-Object { $_ -ne $blocker })
$checkpoint.resume_command = 'The nine-record ABQ RIDE historic-transit archive unit is complete and archive-verified. Do not alter its public placement without separate authorization for Hugo/public-content implementation; any future implementation must use the prepared ABQ RIDE Para-Transit Advisory Board minutes and Montano Rail Runner Station placement.'
Write-Utf8Json $checkpoint $CheckpointPath
[pscustomobject]@{records=9;object_count=$verification.r2_reconciliation.object_count;total_bytes=$verification.r2_reconciliation.total_bytes;checkpoint_path=$CheckpointPath}|ConvertTo-Json -Compress
