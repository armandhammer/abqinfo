[CmdletBinding()]
param(
  [string]$ManifestPath='project-state/discovery/dpm-executive-committee-consolidation-manifest-2026-09-17.json',
  [string]$ReconciliationPath='project-state/governance/remaining-agenda-resolution-2026-10-07/generated-manifest.json'
)
Set-StrictMode -Version Latest
$manifest=Get-Content $ManifestPath -Raw -Encoding utf8 | ConvertFrom-Json -DateKind String
$state=[pscustomobject][ordered]@{
  state='corrected_local_packets_generated_upload_externally_gated'
  manifest=$ManifestPath
  component_count=[int](@($manifest.annual_packets | ForEach-Object component_count) | Measure-Object -Sum).Sum
  packets=@($manifest.annual_packets | ForEach-Object {
    [pscustomobject][ordered]@{year=$_.year;component_count=$_.component_count;page_count=$_.resulting_page_count;size_bytes=$_.resulting_size_bytes;sha256=$_.resulting_sha256;local_output_path=$_.local_output_path;proposed_r2_key=$_.proposed_r2_key}
  })
}
$path=Join-Path $PSScriptRoot '../../project-state/discovery/approved-backlog-background-archive-campaign-2026-09-26.json'
if (Test-Path -LiteralPath $path) {
  $campaign=Get-Content $path -Raw -Encoding utf8 | ConvertFrom-Json -DateKind String
  $archived=@($campaign.generated_packages | Where-Object { $_.family -eq 'DPM corrected annual packets' -and $_.outcome -eq 'archive_complete' })
  if ($archived.Count) {
    $state.state='corrected_packets_partially_archived_2018_human_review_deferred'
    $state | Add-Member -NotePropertyName archive_evidence -NotePropertyValue 'project-state/discovery/approved-backlog-background-archive-campaign-2026-09-26.json'
    foreach ($packet in $state.packets) {
      $row=@($campaign.generated_packages | Where-Object id -eq "generated-dpm-$($packet.year)")[0]
      $packet | Add-Member -NotePropertyName archive_outcome -NotePropertyValue $row.outcome
      if ($row.outcome -eq 'archive_complete') {
        if (-not $row.public_verification.byte_identical -or $row.public_verification.checksum_sha256 -cne $packet.sha256 -or $row.public_verification.size_bytes -ne $packet.size_bytes) {throw 'DPM archival evidence mismatch'}
        $packet | Add-Member -NotePropertyName public_url -NotePropertyValue $row.public_verification.public_url
      }
    }
  }
}
$correctionFile=Join-Path $PSScriptRoot "../../$ReconciliationPath"
if (Test-Path -LiteralPath $correctionFile) {
  $correction=Get-Content -LiteralPath $correctionFile -Raw -Encoding utf8 | ConvertFrom-Json -DateKind String
  if ($correction.source_manifest -eq $ManifestPath) {
    # Historical package bytes remain evidence; they cannot describe a rebuilt packet.
    $registry=Get-Content (Join-Path $PSScriptRoot '../../project-state/governance-registry.json') -Raw -Encoding utf8 | ConvertFrom-Json -DateKind String
    $rule=@($registry.entries | Where-Object { $_.state -eq 'active' -and $_.governance_id -eq 'decision-dpm-executive-committee-manifest-march21-reconciliation-2026-10-07' })
    if ($rule.Count -ne 1 -or @($rule[0].controlling_artifacts | Where-Object path -eq $ReconciliationPath).Count -ne 1) { throw 'DPM composition correction is not registered active authority.' }
    $pin=@($rule[0].controlling_artifacts | Where-Object path -eq $ReconciliationPath)[0]
    $normalized=[IO.File]::ReadAllText($correctionFile).Replace("`r`n","`n")
    $hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($normalized))).ToLowerInvariant()
    if ($hash -cne $pin.sha256) { throw 'Registered DPM correction bytes changed.' }
    $packet=$correction.packet
    if ($packet.generated_id -ne 'generated-dpm-2018' -or $packet.component_count -ne 5 -or $packet.total_original_pages -ne 8 -or -not $packet.factual_composition_blocker_cleared -or $packet.corrected_pdf_generated -or $packet.archival_authorized) { throw 'Unexpected DPM correction scope/state.' }
    $actual=@($state.packets | Where-Object year -eq 2018)[0]
    $old=$actual | ConvertTo-Json -Depth 20 | ConvertFrom-Json -DateKind String
    $state.component_count += [int]$packet.component_count - [int]$actual.component_count
    $actual.component_count=5
    $actual.page_count=$null
    $actual.size_bytes=$null
    $actual.sha256=$null
    $actual.local_output_path=$null
    $actual.archive_outcome='composition_reconciled_local_manifest_only_not_archived'
    $actual | Add-Member -NotePropertyName original_page_count -NotePropertyValue 8
    $actual | Add-Member -NotePropertyName historical_package_metadata -NotePropertyValue $old
    $actual | Add-Member -NotePropertyName corrected_manifest -NotePropertyValue $ReconciliationPath
    $state.state='corrected_packets_partially_archived_2018_composition_reconciled_unarchived'
    $state | Add-Member -NotePropertyName composition_reconciliation -NotePropertyValue $ReconciliationPath
  }
}
$state
