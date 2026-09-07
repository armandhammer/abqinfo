[CmdletBinding()]
param([string]$InventoryPath = 'project-state/master-inventory.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$now = (Get-Date).ToUniversalTime().ToString('o')
$changed = [System.Collections.Generic.List[object]]::new()

function Set-Terminal {
  param([string]$Id, [string]$Status, [string]$Reason, [string]$Canonical = '')
  $candidate = @($inventory.candidates | Where-Object id -eq $Id)
  if ($candidate.Count -ne 1) { throw "Expected one candidate for '$Id'." }
  if ($candidate[0].status -in @('validated','excluded','duplicate','superseded')) { return }
  $candidate[0].status = $Status
  $candidate[0].exclusion_reason = $Reason
  $candidate[0].validation_status = "terminal review decision: $Status"
  $candidate[0].processing_notes = @(@($candidate[0].processing_notes) + $Reason | Sort-Object -Unique)
  if ($Canonical) {
    if ($candidate[0].PSObject.Properties['superseded_by']) { $candidate[0].superseded_by = $Canonical }
    else { $candidate[0] | Add-Member -NotePropertyName superseded_by -NotePropertyValue $Canonical }
  }
  $candidate[0].updated_at = $now
  $changed.Add([pscustomobject]@{ id = $Id; status = $Status; title = $candidate[0].title })
}

$excerptIds = @(
  'src-f3dc1a2363ce7d73','src-6e0f602072fa847e','src-89cf115be2831624',
  'src-d78eadf4da1202b6','src-ca7bbb63647635b8','src-cd6623f3a327e9f6',
  'src-bb79521ff9138182','src-8c36d7a8443cbb1f','src-b302368628df6bbb',
  'src-6e0dcb5754d102a5','src-6e5f3a2fb6c6ecb3','src-66a0c737d5253d90',
  'src-8031f6997dafce69'
)
foreach ($id in $excerptIds) {
  Set-Terminal $id 'duplicate' 'Published City category, summary, or election-question excerpt is reproduced in the complete 2021 General Obligation Bond Program by Purpose; retain the complete original only.' 'src-7b20faff7d0ee849'
}
Set-Terminal 'src-d0097e31d9906afb' 'excluded' 'City property fact sheet for Tower Road SW; it is neither a City plan, study, ordinance, nor durable capital-project record for this batch.'
Set-Terminal 'src-b31ba27136b9bc8c' 'excluded' 'City property fact sheet for Old Coors NW; it is neither a City plan, study, ordinance, nor durable capital-project record for this batch.'

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = $now
$open = @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned')
$next = @($inventory.candidates | Where-Object { $_.status -in $open -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { $next[0].id } else { $null }
$json = $inventory | ConvertTo-Json -Depth 12
$full = [IO.Path]::GetFullPath($InventoryPath)
$temporary = "$full.tmp-$PID"
[IO.File]::WriteAllText($temporary, $json, [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporary -Destination $full -Force

[pscustomobject]@{
  terminal_decisions = $changed.Count
  duplicate = @($changed | Where-Object status -eq 'duplicate').Count
  excluded = @($changed | Where-Object status -eq 'excluded').Count
  next_pending = $inventory.next_pending_id
} | ConvertTo-Json -Compress
