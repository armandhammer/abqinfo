[CmdletBinding()]
param([string]$CheckpointPath = 'project-state/checkpoint.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$implementation = Get-Content -Raw -Encoding UTF8 -LiteralPath 'project-state/discovery/later-ms4-hugo-implementation-2026-09-25.json' | ConvertFrom-Json
if ($implementation.state -ne 'implemented_on_planning_branch_not_live' -or @($implementation.implemented_inventory_ids).Count -ne 6) { throw 'Later-MS4 branch implementation is incomplete.' }
$prior = Get-Content -Raw -Encoding UTF8 -LiteralPath $CheckpointPath | ConvertFrom-Json -DateKind String
$blockers = @($prior.blockers | ForEach-Object {
  if ([string]$_ -like 'Later-MS4 archival is complete*') {
    'Later-MS4 Hugo implementation is complete on the planning branch: six exact-byte archived originals are implemented on Stormwater and Drainage, not production/live. A verified non-production content PR preview and the owner''s manual review are required before merge; no record is validated.'
  } else { [string]$_ }
})
if (@($blockers | Where-Object { $_ -like 'Later-MS4 Hugo implementation is complete*' }).Count -ne 1) { throw 'Expected exactly one later-MS4 checkpoint blocker to update.' }
& "$PSScriptRoot/Write-ProjectCheckpoint.ps1" -OutputPath $CheckpointPath -CompletedRange 'Implemented the 2014 watershed MS4 permit and FY2016, FY2017, FY2019, final FY2020, and final FY2021 reports in the existing Stormwater and Drainage section on the planning branch. Six inventory records implemented; R2 remains 1,237 objects / 9,218,281,842 bytes; not live or validated.' -Blockers $blockers -ResumeCommand 'Open and verify the non-production preview for the bounded later-MS4 Stormwater and Drainage content PR, then stop for the owner''s manual review. Do not merge, deploy production, mark records validated, mutate R2, or reopen the separate 2014 MS4 package.' | Out-Null
