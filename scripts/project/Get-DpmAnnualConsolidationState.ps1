[CmdletBinding()]
param([string]$ManifestPath='project-state/discovery/dpm-executive-committee-consolidation-manifest-2026-09-17.json')
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
$state
