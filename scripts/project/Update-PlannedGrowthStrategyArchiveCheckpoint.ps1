[CmdletBinding()]
param([string]$CheckpointPath = 'project-state/checkpoint.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$evidence = Get-Content -Raw -Encoding UTF8 -LiteralPath 'project-state/discovery/planned-growth-strategy-archive-public-byte-verification-2026-09-23.json' | ConvertFrom-Json
if ($evidence.state -ne 'complete_all_13_public_byte_verified_and_inventory_reconciled' -or $evidence.summary.public_byte_verified -ne 13) { throw 'PGS archival stage is not durably complete.' }
$prior = Get-Content -Raw -Encoding UTF8 -LiteralPath $CheckpointPath | ConvertFrom-Json -DateKind String
$blockers = @($prior.blockers | ForEach-Object {
  if ([string]$_ -like 'Planned Growth Strategy archive preparation is complete*' -or [string]$_ -like 'Planned Growth Strategy R2 archival is complete*') {
    'Planned Growth Strategy R2 archival is complete: all 13 unchanged originals / 109,212,492 bytes are exact public-byte verified; no verified complete combined Part 2 original exists. Hugo/editorial implementation remains separately gated.'
  } else { [string]$_ }
})
if (@($blockers | Where-Object { $_ -like 'Planned Growth Strategy R2 archival is complete*' }).Count -ne 1) { throw 'Expected exactly one current PGS checkpoint blocker to update.' }
& "$PSScriptRoot/Write-ProjectCheckpoint.ps1" -OutputPath $CheckpointPath -CompletedRange 'Archived and publicly exact-byte verified all 13 Planned Growth Strategy City originals (109,212,492 added bytes); R2 inventory reconciled at 1,231 objects / 8,791,355,104 bytes. No Hugo/content, PR, merge, or deployment action.' -Blockers $blockers -ResumeCommand 'The bounded Planned Growth Strategy R2 archival and public-byte-verification stage is complete. The 13 separate City originals are placement assigned; any curated Citywide Growth Strategy Hugo/editorial implementation is a separately gated next stage. Preserve Part 1 as one complete original and Part 2 as 12 separate deliveries covering 11 named chapters, with no verified complete combined Part 2 original. Do not synthesize a combined PDF or resolve the three enactment bills under this handoff. Validation regression anchor: src-09b266eabc8aa975 remains named only to preserve the bounded fiber-rulemaking decision test; it is not an instruction to begin that work.' | Out-Null
