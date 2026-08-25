[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$QueuePath = 'project-state/discovery/retained-source-audit-queue.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$queue = Get-Content -Raw -Encoding UTF8 -LiteralPath $QueuePath | ConvertFrom-Json
$eligible = @($inventory.candidates | Where-Object {
  $_.status -in @('implemented','validated') -and
  $_.source_url -match '^https?://' -and
  $_.source_url -notmatch '^https://files\.abqinfo\.com/' -and
  $_.source_url -notmatch '(?i)\.(pdf|docx?|xlsx?|csv|zip)(?:[?#]|$)' -and
  ($_.file_type -match '(?i)HTML|web page|live service' -or
    ($_.direct_file_url -match '^https?://' -and $_.source_url -ne $_.direct_file_url))
})
$expectedUrls = @($eligible.source_url | Sort-Object -Unique)
$actualUrls = @($queue.records.source_url | Sort-Object -Unique)
$missing = @($expectedUrls | Where-Object { $_ -notin $actualUrls })
$duplicates = @($queue.records | Group-Object source_url | Where-Object Count -gt 1 | Select-Object -ExpandProperty Name)
$invalidCandidateLinks = @($queue.records | Where-Object {
  $record = $_
  -not @($eligible | Where-Object { $_.id -eq $record.candidate_id -and $_.source_url -eq $record.source_url }).Count
} | Select-Object -ExpandProperty source_url)
$errors = @()
if ($missing.Count) { $errors += "Eligible retained sources missing from audit queue: $($missing -join ', ')" }
if ($duplicates.Count) { $errors += "Duplicate retained-source queue URLs: $($duplicates -join ', ')" }
if ($invalidCandidateLinks.Count) { $errors += "Queue records not linked to an eligible inventory candidate: $($invalidCandidateLinks -join ', ')" }
[pscustomobject]@{EligibleSources=$expectedUrls.Count;QueueRecords=@($queue.records).Count;Missing=$missing.Count;Errors=$errors}|ConvertTo-Json -Depth 5
if ($errors.Count) { exit 1 }
