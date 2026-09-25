[CmdletBinding()]
param([string]$CheckpointPath = 'project-state/checkpoint.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$closeout = Get-Content -Raw -Encoding UTF8 -LiteralPath 'project-state/discovery/later-ms4-production-closeout-2026-09-25.json' | ConvertFrom-Json
if ($closeout.production_verification_result -ne 'passed' -or $closeout.pr_number -ne 174 -or @($closeout.inventory_ids_to_validate).Count -ne 6) { throw 'Later-MS4 production verification is incomplete.' }
$prior = Get-Content -Raw -Encoding UTF8 -LiteralPath $CheckpointPath | ConvertFrom-Json -DateKind String
$old = @($prior.blockers | Where-Object { [string]$_ -like 'Later-MS4 Hugo implementation is complete*' })
if ($old.Count -ne 1) { throw 'Expected exactly one pending later-MS4 review blocker.' }
$blockers = @($prior.blockers | Where-Object { [string]$_ -notlike 'Later-MS4 Hugo implementation is complete*' })
& "$PSScriptRoot/Write-ProjectCheckpoint.ps1" -OutputPath $CheckpointPath -CompletedRange 'PR #174 manually approved and merged at 04c5080cebf2ff094d569c941cc32b23a3e2ab6d. Direct fresh and ordinary production HTTP 200 checks passed for all six later-MS4 links and ten descending annual reports; six inventory records validated/live. R2 unchanged at 1,237 objects / 9,218,281,842 bytes. No new visible content edit.' -Blockers $blockers -ResumeCommand 'The later-MS4 family is complete and live; do not resurface it as ordinary work. Preserve the separately gated 2014 MS4 annual-report body and 27 attachments. Continue only with a separately authorized next family or task.' | Out-Null
