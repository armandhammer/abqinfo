[CmdletBinding()]
param(
  [string]$MasterPath = 'project-state/master-inventory.json',
  [string]$CheckpointPath = 'project-state/checkpoint.json',
  [string]$DpmManifestPath = 'project-state/discovery/dpm-executive-committee-consolidation-manifest-2026-09-17.json',
  [string]$Ms4GatePath = 'project-state/discovery/2014-ms4-family-package-gate-2026-09-18.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-BytesHash { param([string]$Path) (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash }
function Assert-Equal { param($Actual, $Expected, [string]$Message) if ($Actual -ne $Expected) { throw "$Message Expected '$Expected'; found '$Actual'." } }

& (Join-Path $PSScriptRoot 'Test-ArchiveReconciliationCheckpointCounts.ps1') -MasterPath $MasterPath -CheckpointPath $CheckpointPath | Out-Host
$master = Get-Content -Raw -Encoding UTF8 -LiteralPath $MasterPath | ConvertFrom-Json
$checkpoint = Get-Content -Raw -Encoding UTF8 -LiteralPath $CheckpointPath | ConvertFrom-Json
$manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $DpmManifestPath | ConvertFrom-Json
$gate = Get-Content -Raw -Encoding UTF8 -LiteralPath $Ms4GatePath | ConvertFrom-Json

if ($checkpoint.PSObject.Properties.Name -notcontains 'dpm_annual_consolidation') { throw 'Checkpoint lost durable dpm_annual_consolidation metadata.' }
$dpm = $checkpoint.dpm_annual_consolidation
Assert-Equal $dpm.state (& "$PSScriptRoot/Get-DpmAnnualConsolidationState.ps1" -ManifestPath $DpmManifestPath).state 'Unexpected DPM state.'
Assert-Equal $dpm.manifest $DpmManifestPath 'Unexpected DPM manifest path.'
Assert-Equal @($dpm.packets).Count @($manifest.annual_packets).Count 'DPM packet count differs from manifest.'
Assert-Equal ([int]$dpm.component_count) ([int](@($manifest.annual_packets | ForEach-Object { $_.component_count }) | Measure-Object -Sum).Sum) 'DPM component count differs from manifest.'
foreach ($packet in $manifest.annual_packets) {
  $actual = @($dpm.packets | Where-Object { [int]$_.year -eq [int]$packet.year })
  Assert-Equal $actual.Count 1 "DPM packet missing or duplicated for $($packet.year)."
  Assert-Equal ([int]$actual[0].component_count) ([int]$packet.component_count) "DPM component count differs for $($packet.year)."
  Assert-Equal ([int]$actual[0].page_count) ([int]$packet.resulting_page_count) "DPM page count differs for $($packet.year)."
  Assert-Equal ([int64]$actual[0].size_bytes) ([int64]$packet.resulting_size_bytes) "DPM byte count differs for $($packet.year)."
  Assert-Equal $actual[0].sha256 $packet.resulting_sha256 "DPM hash differs for $($packet.year)."
  Assert-Equal $actual[0].local_output_path $packet.local_output_path "DPM output path differs for $($packet.year)."
  Assert-Equal $actual[0].proposed_r2_key $packet.proposed_r2_key "DPM key differs for $($packet.year)."
}
foreach ($entry in @($checkpoint.history)) {
  if (([string]$entry.completed_item_range).StartsWith('.') -or ([string]$entry.next_pending_id).StartsWith('.') -or ([string]$entry.resume_command).StartsWith('.')) {
    throw 'Checkpoint history contains a malformed shell-placeholder state.'
  }
}

Assert-Equal ([int]$gate.scope.candidate_count) 28 'MS4 gate candidate count is not 28.'
Assert-Equal @($gate.scope.candidate_ids).Count 28 'MS4 gate ID count is not 28.'
Assert-Equal (@($gate.scope.candidate_ids | Select-Object -Unique).Count) 28 'MS4 gate contains duplicate candidate IDs.'
Assert-Equal ([int]$gate.scope.composition.main_body_count) 1 'MS4 gate main-body count is not one.'
Assert-Equal ([int]$gate.scope.composition.attachment_count) 27 'MS4 gate attachment count is not 27.'
Assert-Equal ([int]$gate.scope.composition.total_record_count) 28 'MS4 gate total record count is not 28.'
if ($gate.saved_evidence.source_discovery -match 'and the cover') { throw 'MS4 gate wording implies the cover letter is an additional record.' }
if ($gate.scope.composition.attachment_set_note -notmatch 'not an additional twenty-ninth record') { throw 'MS4 gate lacks the explicit 28-record boundary.' }
$main = @($master.candidates | Where-Object { $_.id -eq $gate.scope.composition.main_body_candidate_id })
Assert-Equal $main.Count 1 'MS4 gate main-body candidate is absent from master inventory.'
if ($main[0].title -ne '2014 MS4 Annual Report: main body') { throw 'MS4 gate main-body candidate does not identify the report main body.' }
foreach ($id in $gate.scope.candidate_ids) { if (@($master.candidates | Where-Object { $_.id -eq $id }).Count -ne 1) { throw "MS4 gate candidate $id is absent or duplicated in master inventory." } }

# Exercise each state writer on temporary copies. The probe represents a future
# durable top-level field; regeneration must retain it. The second pass must be
# byte-identical, proving that a no-op regeneration does not rewrite state.
$tempRoot = Join-Path ([IO.Path]::GetTempPath()) ("abqinfo-state-regeneration-$PID")
New-Item -ItemType Directory -Path $tempRoot | Out-Null
try {
  $tempCheckpoint = Join-Path $tempRoot 'checkpoint.json'
  $checkpoint | Add-Member -NotePropertyName stabilization_probe -NotePropertyValue ([pscustomobject]@{ retained = $true; scope = 'temporary-regression-test' })
  $checkpoint.PSObject.Properties.Remove('dpm_annual_consolidation')
  [IO.File]::WriteAllText($tempCheckpoint, ($checkpoint | ConvertTo-Json -Depth 30), [Text.UTF8Encoding]::new($false))
  $writer = Join-Path $PSScriptRoot 'Write-ProjectCheckpoint.ps1'
  & $writer -InventoryPath $MasterPath -OutputPath $tempCheckpoint -DpmManifestPath $DpmManifestPath -CompletedRange $checkpoint.completed_item_range -NextPendingId $checkpoint.next_pending_id -Blockers @($checkpoint.blockers) -ResumeCommand $checkpoint.resume_command | Out-Null
  $repaired = Get-Content -Raw -Encoding UTF8 -LiteralPath $tempCheckpoint | ConvertFrom-Json
  if (-not $repaired.stabilization_probe.retained) { throw 'Checkpoint writer dropped an unknown durable top-level field.' }
  if ($repaired.PSObject.Properties.Name -notcontains 'dpm_annual_consolidation') { throw 'Checkpoint writer did not restore DPM metadata from the manifest.' }
  $firstCheckpointHash = Get-BytesHash $tempCheckpoint
  & $writer -InventoryPath $MasterPath -OutputPath $tempCheckpoint -DpmManifestPath $DpmManifestPath -CompletedRange $checkpoint.completed_item_range -NextPendingId $checkpoint.next_pending_id -Blockers @($checkpoint.blockers) -ResumeCommand $checkpoint.resume_command | Out-Null
  Assert-Equal (Get-BytesHash $tempCheckpoint) $firstCheckpointHash 'Second checkpoint regeneration changed a stable checkpoint.'

  $tempMaster = Join-Path $tempRoot 'master-inventory.json'
  $master | Add-Member -NotePropertyName stabilization_probe -NotePropertyValue ([pscustomobject]@{ retained = $true })
  $master.counts.'pending review' = -1
  [IO.File]::WriteAllText($tempMaster, ($master | ConvertTo-Json -Depth 30), [Text.UTF8Encoding]::new($false))
  $aggregateWriter = Join-Path $PSScriptRoot 'Update-MasterInventoryAggregates.ps1'
  & $aggregateWriter -InventoryPath $tempMaster | Out-Null
  $repairedMaster = Get-Content -Raw -Encoding UTF8 -LiteralPath $tempMaster | ConvertFrom-Json
  if (-not $repairedMaster.stabilization_probe.retained) { throw 'Master aggregate writer dropped durable top-level metadata.' }
  $firstMasterHash = Get-BytesHash $tempMaster
  & $aggregateWriter -InventoryPath $tempMaster | Out-Null
  Assert-Equal (Get-BytesHash $tempMaster) $firstMasterHash 'Second master aggregate regeneration changed stable inventory state.'
  $candidateWriter = Join-Path $PSScriptRoot 'Update-Candidate.ps1'
  $probeCandidate = @($repairedMaster.candidates | Select-Object -First 1)[0]
  & $candidateWriter -Id $probeCandidate.id -Set @{ status = [string]$probeCandidate.status } -InventoryPath $tempMaster | Out-Null
  Assert-Equal (Get-BytesHash $tempMaster) $firstMasterHash 'No-op candidate update rewrote stable inventory state.'

  $archiveCheckpoint = Join-Path $tempRoot 'archive-checkpoint.json'
  $repaired | Add-Member -NotePropertyName archive_probe -NotePropertyValue ([pscustomobject]@{ retained = $true })
  $repaired.PSObject.Properties.Remove('dpm_annual_consolidation')
  [IO.File]::WriteAllText($archiveCheckpoint, ($repaired | ConvertTo-Json -Depth 30), [Text.UTF8Encoding]::new($false))
  $archiveWriter = Join-Path $PSScriptRoot 'Update-ArchiveReconciliationCheckpointCounts.ps1'
  & $archiveWriter -MasterPath $MasterPath -CheckpointPath $archiveCheckpoint -DpmManifestPath $DpmManifestPath | Out-Null
  $archiveRepaired = Get-Content -Raw -Encoding UTF8 -LiteralPath $archiveCheckpoint | ConvertFrom-Json
  if (-not $archiveRepaired.archive_probe.retained) { throw 'Archive checkpoint writer dropped durable top-level metadata.' }
  $firstArchiveHash = Get-BytesHash $archiveCheckpoint
  & $archiveWriter -MasterPath $MasterPath -CheckpointPath $archiveCheckpoint -DpmManifestPath $DpmManifestPath | Out-Null
  Assert-Equal (Get-BytesHash $archiveCheckpoint) $firstArchiveHash 'Second archive checkpoint regeneration changed stable state.'
}
finally {
  if (Test-Path -LiteralPath $tempRoot) { Remove-Item -LiteralPath $tempRoot -Recurse -Force }
}

Write-Output 'PASS: project-state regeneration preserves durable metadata, restores DPM state, enforces the 28-record MS4 package, and is idempotent on a second pass.'
