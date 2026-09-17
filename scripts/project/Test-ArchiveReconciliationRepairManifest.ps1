[CmdletBinding()]
param([string]$ManifestPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-repair-manifest-2026-09-17.json')
$m = Get-Content $ManifestPath -Raw | ConvertFrom-Json
if (-not $m.dry_run -or $m.execution_performed) { throw 'Manifest is not dry-run only.' }
if ($m.summary.decision_groups -ne 44 -or $m.coverage.missing.Count -ne 0 -or $m.coverage.duplicated_coverage.Count -ne 0) { throw 'Decision-group coverage is incomplete or duplicated.' }
if ($m.summary.unexpected_editorial_judgment_cases -ne 0) { throw 'Unexpected editorial-judgment action present.' }
Write-Output 'Repair manifest validation passed: all 44 decision groups are covered exactly once through consolidated dry-run actions.'
