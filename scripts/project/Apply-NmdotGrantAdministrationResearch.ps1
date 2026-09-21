[CmdletBinding()]
param(
  [string]$ResearchPath = 'project-state/discovery/nmdot-file-host-cluster-research-2026-09-13.json',
  [string]$DecisionPath = 'project-state/discovery/nmdot-grant-administration-and-application-decision-2026-09-19.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$research = Get-Content -Raw -Encoding UTF8 -LiteralPath $ResearchPath | ConvertFrom-Json
$records = @(
  $research.PSObject.Properties | ForEach-Object {
    if ($_.Value -is [System.Collections.IEnumerable] -and $_.Value -isnot [string]) {
      $_.Value | Where-Object {
        $_ -is [psobject] -and $_.PSObject.Properties.Name -contains 'group' -and
        $_.group -eq 'grant administration and application'
      }
    }
  }
)
if ($records.Count -ne 18) { throw "Expected 18 grant-administration records; found $($records.Count)." }
if (@($records.id | Sort-Object -Unique).Count -ne 18) { throw 'Saved grant-administration IDs are not unique.' }
foreach ($record in $records) {
  if ($record.recommended_status -ne 'approved for addition') { throw "Unexpected saved status for $($record.id)." }
  if ($record.publisher -ne 'New Mexico Department of Transportation') { throw "Unexpected saved publisher for $($record.id)." }
  $note = "Saved NMDOT grant administration and application research 2026-09-13: $($record.evidence) Container verified by leading bytes $($record.leading_bytes); placement is unresolved under $DecisionPath."
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $record.id -InventoryPath $InventoryPath -Set @{
    status = 'approved for addition'
    source_url = [string]$record.authoritative_url
    direct_file_url = [string]$record.authoritative_url
    agency = 'New Mexico Department of Transportation'
    title = [string]$record.title
    description = [string]$record.description
    size_bytes = [int64]$record.size_bytes
    checksum_sha256 = [string]$record.checksum_sha256
    proposed_canonical_page = $null
    implementation_location = $null
    implementation_locations = @()
    validation_status = 'saved authoritative NMDOT source, exact size, SHA-256, and container identification retained; inventory-only, with R2 archival and public verification not run'
    provenance_status = 'authoritative NMDOT source and exact-file research saved'
    processing_notes = @($note, "Saved publisher: $($record.publisher). The realfile.rtsclients.com delivery host is not treated as publisher.")
    exclusion_reason = $null
  } | Out-Null
}

& "$PSScriptRoot/Update-MasterInventoryAggregates.ps1" -InventoryPath $InventoryPath
