[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$closeout = Get-Content -Raw -Encoding UTF8 'project-state/discovery/planned-growth-strategy-production-closeout-2026-09-24.json' | ConvertFrom-Json -DateKind String
if ($closeout.production_verification_result -ne 'passed' -or $closeout.final_inventory_status -ne 'validated') { throw 'PGS production closeout has not passed.' }
$prior = Get-Content -Raw -Encoding UTF8 'project-state/checkpoint.json' | ConvertFrom-Json -DateKind String
$blockers = @($prior.blockers | Where-Object { $_ -notmatch '^Planned Growth Strategy PR #168 is open' })
$completed = 'Planned Growth Strategy PR #168 was manually approved and merged at 8cfba47b46a464a04f67b1fccbe3943dd30b74c9. Production Area & Sector Plans / Citywide Growth Strategy verification passed: one complete Part 1 original and 12 separate Part 2 City PDFs covering all 11 named chapters, with all 13 archive/source pairs. The 13 inventory records are validated; the family is complete and live.'
$resume = 'Planned Growth Strategy is complete and live; do not resurface it as ordinary work. Preserve the exact-byte R2 archive, the complete Part 1 original, the 12 separate Part 2 files with Chapter 3.0, and the no-verified-combined-Part-2 limitation. Three enactment-bill copies remain separate requires-human-review work. Recompute the ordinary queue or await a separately authorized family. Validation regression anchor: src-09b266eabc8aa975 remains named only to preserve the bounded fiber-rulemaking decision test; it is not an instruction to begin that work.'
& "$PSScriptRoot/Write-ProjectCheckpoint.ps1" -CompletedRange $completed -Blockers $blockers -ResumeCommand $resume | Out-Null
