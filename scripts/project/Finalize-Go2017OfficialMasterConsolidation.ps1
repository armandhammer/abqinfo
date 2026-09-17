[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$ConsolidationPath = 'project-state/discovery/go2017-official-master-consolidation-2026-09-16.json',
  [string]$PublicValidationPath = 'project-state/discovery/go2017-official-master-r2-public-validation-2026-09-16.json',
  [string]$RetainedSourceQueuePath = 'project-state/discovery/retained-source-audit-queue.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$consolidation = Get-Content -Raw -Encoding UTF8 -LiteralPath $ConsolidationPath | ConvertFrom-Json
$public = Get-Content -Raw -Encoding UTF8 -LiteralPath $PublicValidationPath | ConvertFrom-Json
$queue = Get-Content -Raw -Encoding UTF8 -LiteralPath $RetainedSourceQueuePath | ConvertFrom-Json
$masterId = [string]$consolidation.master.id
$master = @($inventory.candidates | Where-Object id -eq $masterId)
if ($master.Count -ne 1 -or [string]$master[0].status -ne 'validated') { throw 'Validated official master record is missing.' }
$master = $master[0]
if (-not [bool]$public.byte_identical -or [int64]$public.size_bytes -ne [int64]$master.size_bytes -or [string]$public.checksum_sha256 -ne [string]$master.checksum_sha256) {
  throw 'Fresh public R2 validation does not match the master inventory record.'
}

$componentIds = @($consolidation.components | ForEach-Object { [string]$_.id })
if ($componentIds.Count -ne 30 -or @($componentIds | Sort-Object -Unique).Count -ne 30) { throw 'Expected 30 unique component IDs.' }
$components = @($inventory.candidates | Where-Object { $_.id -in $componentIds })
if ($components.Count -ne 30 -or @($components | Where-Object status -ne 'excluded').Count) { throw 'All 30 components must be retained as excluded standalone records.' }
foreach ($component in $components) {
  if (-not $component.r2_url -or -not $component.size_bytes -or -not $component.checksum_sha256 -or [string]$component.validation_status -notmatch '^passed:') {
    throw "Preserved verification metadata is incomplete for $($component.id)."
  }
}

$retired = @($queue.records | Where-Object { [string]$_.candidate_id -in $componentIds })
if ($retired.Count -notin @(0,30)) { throw "Expected zero or 30 active audit rows for the component family; found $($retired.Count)." }
if ($retired.Count -eq 30) {
  $retiredAt = (Get-Date).ToUniversalTime().ToString('o')
  $retiredHistory = foreach ($record in $retired) {
    $copy = $record.PSObject.Copy()
    $copy.audit_status = 'retired through canonical master consolidation'
    $copy.processing_notes = @(@($copy.processing_notes) + @(
      "Retired from the active retained-source audit queue at $retiredAt after the source component became archive-only.",
      "The authoritative official master record is $masterId and remains in the active retained-source audit policy scope."
    ) | Sort-Object -Unique)
    $copy.updated_at = $retiredAt
    $copy
  }
  $consolidation | Add-Member -NotePropertyName retired_retained_source_audit_records -NotePropertyValue @($retiredHistory) -Force
  $queue.records = @($queue.records | Where-Object { [string]$_.candidate_id -notin $componentIds })
} elseif (-not $consolidation.PSObject.Properties['retired_retained_source_audit_records'] -or @($consolidation.retired_retained_source_audit_records).Count -ne 30) {
  throw 'Active audit rows are already absent but their retired history is not preserved in the consolidation artifact.'
}

$queueCounts = [ordered]@{}
foreach ($status in $queue.allowed_statuses) { $queueCounts[$status] = @($queue.records | Where-Object audit_status -eq $status).Count }
$queue.counts = [pscustomobject]$queueCounts
$queue.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$next = @($queue.records | Where-Object audit_status -eq 'pending descendant crawl' | Sort-Object source_url | Select-Object -First 1)
$queue.next_pending_source_url = if ($next.Count) { [string]$next[0].source_url } else { $null }

$masterUrl = [string]$master.r2_url
$officialUrl = [string]$consolidation.master.official_record_url
foreach ($location in @($master.implementation_locations)) {
  $page = Get-Content -Raw -Encoding UTF8 -LiteralPath $location
  if ($page -notlike "*$masterUrl*" -or $page -notlike "*$officialUrl*") { throw "Master archive or official link missing from $location." }
}
foreach ($component in $components) {
  foreach ($page in Get-ChildItem content -Recurse -Filter *.md) {
    if ((Get-Content -Raw -Encoding UTF8 -LiteralPath $page.FullName) -like "*$($component.r2_url)*") {
      throw "Standalone component archive remains linked from $($page.FullName): $($component.id)."
    }
  }
}

$consolidation | Add-Member -NotePropertyName finalized_at -NotePropertyValue ((Get-Date).ToUniversalTime().ToString('o')) -Force
$consolidation | Add-Member -NotePropertyName validation_status -NotePropertyValue 'passed: official master integrity and public archive, complete component retention, retired active-audit history, and seven page placements verified' -Force

foreach ($write in @(
  [pscustomobject]@{Path=$RetainedSourceQueuePath;Value=$queue},
  [pscustomobject]@{Path=$ConsolidationPath;Value=$consolidation}
)) {
  $json = $write.Value | ConvertTo-Json -Depth 16
  $fullPath = [IO.Path]::GetFullPath([string]$write.Path)
  $temporaryPath = "$fullPath.tmp-$PID"
  [IO.File]::WriteAllText($temporaryPath,$json,[Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
}

[pscustomobject]@{
  master = $masterId
  components_preserved = $components.Count
  retired_audit_rows = @($consolidation.retired_retained_source_audit_records).Count
  active_queue_records = @($queue.records).Count
  implementation_locations = @($master.implementation_locations)
} | ConvertTo-Json -Depth 5 -Compress
