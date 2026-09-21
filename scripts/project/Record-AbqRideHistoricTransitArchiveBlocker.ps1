[CmdletBinding()]
param(
  [string]$VerificationPath = 'project-state/discovery/abq-ride-historic-transit-archive-public-byte-verification-2026-09-21.json',
  [string]$CheckpointPath = 'project-state/checkpoint.json',
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$R2InventoryPath = 'project-state/r2-inventory.json'
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
if ($verification.state -ne 'blocked_legacy_word_visual_rendering_unavailable_no_r2_mutation') { throw 'This checkpoint updater is only for the no-mutation legacy-Word rendering blocker.' }
if ([int]$verification.summary.source_byte_verified -ne 9 -or [int]$verification.summary.uploaded -ne 0 -or [int]$verification.summary.public_byte_verified -ne 0) { throw 'Unexpected archive result; refuse to record this as the known no-mutation blocker.' }

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$r2Inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $R2InventoryPath | ConvertFrom-Json
$verification | Add-Member -NotePropertyName r2_reconciliation -NotePropertyValue ([pscustomobject][ordered]@{
  state = 'not_run_live_credential_unavailable'; exact_problem = 'Get-R2Inventory.ps1 could not read Windows credential abqinfo-r2-upload.'
  local_r2_inventory_object_count = $r2Inventory.object_count; local_r2_inventory_total_bytes = $r2Inventory.total_bytes
  no_upload_occurred = $true
}) -Force
Write-Utf8Json $verification $VerificationPath
$checkpoint = Get-Content -Raw -Encoding UTF8 -LiteralPath $CheckpointPath | ConvertFrom-Json -DateKind String
$blocker = 'ABQ RIDE historic-transit archive stage is blocked before R2 mutation: all nine City originals passed fresh size/SHA-256 verification, but the three required legacy-Word visual renders failed because Word automation returned 0x80070520 (no active logon session); live R2 reconciliation also could not run because Windows credential abqinfo-r2-upload was unavailable.'
$priorBlockerOrder = @(
  'Capital Spending publication/build/archive gate remains externally gated.',
  '2014 MS4 is a 28-record externally gated package; skip it.',
  'Prescription Trails remains externally gated.',
  'Code-enforcement Notices and Orders remain externally gated.',
  'LGCC agenda family remains externally gated.',
  'Approved NMDOT inventory-only families await R2/public-byte/placement work.',
  'Two prepared Municipal Development standard-form agreements await R2/public-byte verification.',
  'Privacy-sensitive fiber correspondence remains requires human review.',
  'Unresolved PGS enactment-bill records remain requires human review.',
  'O-23-96 and F/S R-24-17 final-disposition questions remain unresolved.',
  'Corrected DPM packet/archive gates remain externally gated.',
  'O-2024-006 final enacted file is not downloadable from the authoritative Clerk notice; do not register the available draft.',
  'Construction-documents family has completed saved research; do not resurface the prior 18-record handoff.'
)
$otherBlockers = @($checkpoint.blockers | Where-Object { $_ -notin $priorBlockerOrder -and $_ -ne $blocker })
$blockers = @($priorBlockerOrder + $otherBlockers + $blocker)
$checkpoint.recorded_at = (Get-Date).ToUniversalTime().ToString('o')
$checkpoint.completed_item_range = 'Attempted the explicitly authorized nine-record ABQ RIDE historic-transit archive/public-byte stage. All nine freshly downloaded City originals exactly matched saved source size and SHA-256, but no upload or public-byte verification occurred: the required three legacy Word visual renders are blocked by Word automation error 0x80070520, and live R2 reconciliation is blocked by unavailable Windows credential abqinfo-r2-upload. Durable evidence: project-state/discovery/abq-ride-historic-transit-archive-public-byte-verification-2026-09-21.json. No Hugo, PR, merge, deployment, or inventory advancement occurred.'
$checkpoint.total_candidates = @($inventory.candidates).Count
$checkpoint.counts_by_status = $inventory.counts
$checkpoint.remaining_nonterminal = @($inventory.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') }).Count
$checkpoint.next_pending_id = $inventory.next_pending_id
$checkpoint.blockers = $blockers
$checkpoint.resume_command = 'Restore an interactive Word rendering session and the abqinfo-r2-upload Windows credential, then rerun only the already prepared nine-record ABQ RIDE historic-transit archive stage: visually inspect the three unchanged legacy Word originals, upload each exact verified original to its prepared R2 key, verify every public byte stream, reconcile R2 inventory, and only then consider separately authorized Hugo/public-content work. Do not reopen family research or touch any other family.'
Write-Utf8Json $checkpoint $CheckpointPath
[pscustomobject]@{ source_byte_verified = $verification.summary.source_byte_verified; uploaded = $verification.summary.uploaded; public_byte_verified = $verification.summary.public_byte_verified; checkpoint_path = $CheckpointPath } | ConvertTo-Json -Compress
