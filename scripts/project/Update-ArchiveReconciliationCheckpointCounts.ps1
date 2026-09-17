[CmdletBinding()]
param(
    [string]$MasterPath = 'project-state/master-inventory.json',
    [string]$CheckpointPath = 'project-state/checkpoint.json',
    [string]$DpmManifestPath = 'project-state/discovery/dpm-executive-committee-consolidation-manifest-2026-09-17.json'
)
$ErrorActionPreference = 'Stop'
$master = Get-Content -LiteralPath $MasterPath -Raw | ConvertFrom-Json -DateKind String
$checkpoint = Get-Content -LiteralPath $CheckpointPath -Raw | ConvertFrom-Json -DateKind String
$counts = [ordered]@{}
foreach ($status in $master.allowed_statuses) { $counts[$status] = @($master.candidates | Where-Object { [string]$_.status -eq $status }).Count }
$nonterminalStatuses = @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned')
$remaining = @($master.candidates | Where-Object { $_.status -in $nonterminalStatuses -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') })
$checkpoint.total_candidates = @($master.candidates).Count
$checkpoint.counts_by_status = [pscustomobject]$counts
$checkpoint.remaining_nonterminal = $remaining.Count
$checkpoint.next_pending_id = if ($remaining.Count) { [string](@($remaining | Sort-Object id)[0].id) } else { $null }
$dpm = Get-Content -LiteralPath $DpmManifestPath -Raw | ConvertFrom-Json -DateKind String
$dpmState = [pscustomobject][ordered]@{
    state = 'corrected_local_packets_generated_upload_externally_gated'
    manifest = $DpmManifestPath
    component_count = [int](@($dpm.annual_packets | ForEach-Object { $_.component_count }) | Measure-Object -Sum).Sum
    packets = @($dpm.annual_packets | ForEach-Object {
        [pscustomobject][ordered]@{
            year = $_.year
            component_count = $_.component_count
            page_count = $_.resulting_page_count
            size_bytes = $_.resulting_size_bytes
            sha256 = $_.resulting_sha256
            local_output_path = $_.local_output_path
            proposed_r2_key = $_.proposed_r2_key
        }
    })
}
if ($checkpoint.PSObject.Properties.Name -contains 'dpm_annual_consolidation') { $checkpoint.dpm_annual_consolidation = $dpmState } else { $checkpoint | Add-Member -NotePropertyName dpm_annual_consolidation -NotePropertyValue $dpmState }
$checkpoint.recorded_at = (Get-Date).ToUniversalTime().ToString('o')
$json = $checkpoint | ConvertTo-Json -Depth 20
[System.IO.File]::WriteAllText([System.IO.Path]::GetFullPath($CheckpointPath), "$json`r`n", [System.Text.UTF8Encoding]::new($false))
Write-Output "Checkpoint counts recomputed from ${MasterPath}: total=$($checkpoint.total_candidates), remaining=$($checkpoint.remaining_nonterminal), next=$($checkpoint.next_pending_id)."
