[CmdletBinding()]
param(
    [string]$MasterPath = 'project-state/master-inventory.json',
    [string]$CheckpointPath = 'project-state/checkpoint.json'
)
$ErrorActionPreference = 'Stop'
$master = Get-Content -LiteralPath $MasterPath -Raw | ConvertFrom-Json
$checkpoint = Get-Content -LiteralPath $CheckpointPath -Raw | ConvertFrom-Json
$counts = [ordered]@{}
foreach ($status in $master.allowed_statuses) { $counts[$status] = @($master.candidates | Where-Object { [string]$_.status -eq $status }).Count }
$sum = ($counts.Values | Measure-Object -Sum).Sum
if ($sum -ne @($master.candidates).Count) { throw "Master status counts sum $sum but candidate count is $(@($master.candidates).Count)." }
if ([int]$checkpoint.total_candidates -ne @($master.candidates).Count) { throw 'Checkpoint total_candidates differs from master inventory.' }
foreach ($status in $master.allowed_statuses) { if ([int]$checkpoint.counts_by_status.$status -ne $counts[$status]) { throw "Checkpoint count differs for $status." } }
$remainingStatuses = @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned')
$remaining = @($master.candidates | Where-Object { $_.status -in $remainingStatuses -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | Sort-Object id)
if ([int]$checkpoint.remaining_nonterminal -ne $remaining.Count) { throw 'Checkpoint remaining_nonterminal differs from master inventory.' }
$expectedNext = if ($remaining.Count) { [string]$remaining[0].id } else { $null }
if ([string]$checkpoint.next_pending_id -ne $expectedNext) { throw 'Checkpoint next_pending_id differs from established pending-record logic.' }
Write-Output "PASS: checkpoint counts equal authoritative master inventory; total=$($checkpoint.total_candidates), remaining=$($checkpoint.remaining_nonterminal), next=$expectedNext."
