[CmdletBinding()]
param([string]$CheckpointPath = 'project-state/checkpoint.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$evidence = Get-Content -Raw -Encoding UTF8 -LiteralPath 'project-state/discovery/later-ms4-archive-public-byte-verification-2026-09-25.json' | ConvertFrom-Json
if ($evidence.state -ne 'complete_all_six_public_byte_verified_and_inventory_reconciled' -or $evidence.summary.public_byte_verified -ne 6) { throw 'Later-MS4 archival stage is not complete.' }
$prior = Get-Content -Raw -Encoding UTF8 -LiteralPath $CheckpointPath | ConvertFrom-Json -DateKind String
$blockers = @($prior.blockers | ForEach-Object {
  if ([string]$_ -like 'Later-MS4 preflight is complete*') {
    'Later-MS4 archival is complete: six unchanged originals / 426,926,738 bytes are exact public-byte verified, R2 accounting is reconciled, and six records are placement assigned. Bounded Stormwater and Drainage Hugo/editorial implementation requires a separate manual-review content PR.'
  } else { [string]$_ }
})
if (@($blockers | Where-Object { $_ -like 'Later-MS4 archival is complete*' }).Count -ne 1) { throw 'Expected exactly one later-MS4 checkpoint blocker to update.' }
& "$PSScriptRoot/Write-ProjectCheckpoint.ps1" -OutputPath $CheckpointPath -CompletedRange 'R2 archived and publicly exact-byte verified all six later-MS4 originals (426,926,738 added bytes); saved/live R2 inventory reconciled at 1,237 objects / 9,218,281,842 bytes; six inventory records placement assigned. No visitor-visible content changed.' -Blockers $blockers -ResumeCommand 'The bounded later-MS4 archival stage is complete. Next: separately authorized Stormwater and Drainage Hugo/editorial implementation as one curated chronological compliance series, followed by a content PR for the user''s manual review before merge. Do not reopen the separate 2014 MS4 28-record package.' | Out-Null
