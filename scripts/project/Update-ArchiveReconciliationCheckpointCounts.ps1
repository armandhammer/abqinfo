[CmdletBinding()]
param(
    [string]$MasterPath = 'project-state/master-inventory.json',
    [string]$CheckpointPath = 'project-state/checkpoint.json',
    [string]$DpmManifestPath = 'project-state/discovery/dpm-executive-committee-consolidation-manifest-2026-09-17.json'
)
$ErrorActionPreference = 'Stop'
$master = Get-Content -LiteralPath $MasterPath -Raw | ConvertFrom-Json -DateKind String
$checkpoint = Get-Content -LiteralPath $CheckpointPath -Raw | ConvertFrom-Json -DateKind String
$priorTotal = $checkpoint.total_candidates
$priorCounts = if ($checkpoint.PSObject.Properties.Name -contains 'counts_by_status') { $checkpoint.counts_by_status | ConvertTo-Json -Depth 20 -Compress } else { $null }
$priorRemaining = $checkpoint.remaining_nonterminal
$priorNext = $checkpoint.next_pending_id
$priorDpm = if ($checkpoint.PSObject.Properties.Name -contains 'dpm_annual_consolidation') { $checkpoint.dpm_annual_consolidation | ConvertTo-Json -Depth 20 -Compress } else { $null }
$counts = [ordered]@{}
foreach ($status in $master.allowed_statuses) { $counts[$status] = @($master.candidates | Where-Object { [string]$_.status -eq $status }).Count }
$nonterminalStatuses = @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned')
$remaining = @($master.candidates | Where-Object { $_.status -in $nonterminalStatuses -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') })
$checkpoint.total_candidates = @($master.candidates).Count
$checkpoint.counts_by_status = [pscustomobject]$counts
$checkpoint.remaining_nonterminal = $remaining.Count
$checkpoint.next_pending_id = if ($remaining.Count) { [string](@($remaining | Sort-Object id)[0].id) } else { $null }
$dpmState = & "$PSScriptRoot/Get-DpmAnnualConsolidationState.ps1" -ManifestPath $DpmManifestPath
if ($checkpoint.PSObject.Properties.Name -contains 'dpm_annual_consolidation') { $checkpoint.dpm_annual_consolidation = $dpmState } else { $checkpoint | Add-Member -NotePropertyName dpm_annual_consolidation -NotePropertyValue $dpmState }
$changed =
    $priorTotal -ne $checkpoint.total_candidates -or
    $priorCounts -ne ($checkpoint.counts_by_status | ConvertTo-Json -Depth 20 -Compress) -or
    $priorRemaining -ne $checkpoint.remaining_nonterminal -or
    $priorNext -ne $checkpoint.next_pending_id -or
    $priorDpm -ne ($checkpoint.dpm_annual_consolidation | ConvertTo-Json -Depth 20 -Compress)
if ($changed) {
    $checkpoint.recorded_at = (Get-Date).ToUniversalTime().ToString('o')
    $json = $checkpoint | ConvertTo-Json -Depth 20
    [System.IO.File]::WriteAllText([System.IO.Path]::GetFullPath($CheckpointPath), "$json`r`n", [System.Text.UTF8Encoding]::new($false))
}
Write-Output "Checkpoint counts recomputed from ${MasterPath}: total=$($checkpoint.total_candidates), remaining=$($checkpoint.remaining_nonterminal), next=$($checkpoint.next_pending_id), changed=$changed."
