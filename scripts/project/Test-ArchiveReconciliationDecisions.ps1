[CmdletBinding()]
param(
    [string]$PacketPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-review-packet-2026-09-16.json',
    [string]$DecisionPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-decisions-2026-09-17.json'
)

$ErrorActionPreference = 'Stop'
$packet = Get-Content $PacketPath -Raw | ConvertFrom-Json
$decisions = (Get-Content $DecisionPath -Raw | ConvertFrom-Json).decisions
$packetIds = @($packet.cases.issue_group_id | Sort-Object -Unique)
$decisionIds = @($decisions.issue_group_id | Sort-Object -Unique)
$allowed = @(
    'retain and publish',
    'retain intentionally unpublished',
    'accounting/inventory repair only',
    'duplicate/superseded - retain canonical',
    'probable R2 deletion candidate',
    'unresolved / user decision required'
)
$errors = @()
if ($packetIds.Count -ne 44) { $errors += "Expected 44 review-packet groups; found $($packetIds.Count)." }
if ($decisions.Count -ne 44) { $errors += "Expected 44 decision records; found $($decisions.Count)." }
if ((Compare-Object $packetIds $decisionIds).Count -ne 0) { $errors += 'Decision group IDs do not exactly match review-packet group IDs.' }
if (@($decisions | Where-Object { $allowed -notcontains $_.disposition }).Count -ne 0) { $errors += 'One or more dispositions are not allowed.' }
if (@($decisions | Where-Object { [string]::IsNullOrWhiteSpace($_.rationale) -or @($_.case_specific_evidence).Count -eq 0 }).Count -ne 0) { $errors += 'Every decision requires rationale and case-specific evidence.' }
if ($errors.Count) { throw ($errors -join ' ') }
Write-Output 'Archive-reconciliation decision coverage and evidence validation passed.'
