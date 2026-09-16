[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$DecisionPath = 'project-state/discovery/code-enforcement-snapshot-supersession-2026-09-11.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -LiteralPath $InventoryPath -Raw -Encoding UTF8 | ConvertFrom-Json
$decision = Get-Content -LiteralPath $DecisionPath -Raw -Encoding UTF8 | ConvertFrom-Json
$predecessor = @($inventory.candidates | Where-Object id -eq $decision.predecessor_id)
$successor = @($inventory.candidates | Where-Object id -eq $decision.successor_id)
if ($predecessor.Count -ne 1 -or $successor.Count -ne 1) { throw 'Expected exactly one predecessor and successor.' }
if ([string]$predecessor[0].status -ne 'validated') { throw "Unexpected predecessor status: $($predecessor[0].status)" }
if ([string]$successor[0].status -ne 'approved for addition') { throw "Unexpected successor status: $($successor[0].status)" }
$url = [string]$decision.successor_url
$predecessor[0].status = 'superseded'
$predecessor[0].cited_successors = @($predecessor[0].cited_successors) + @($url) | Select-Object -Unique
$predecessor[0].validation_status = 'superseded by verified authoritative cumulative City snapshot; historical R2 archive and completed verification retained'
$predecessor[0].exclusion_reason = [string]$decision.decision
$note = "Code-enforcement snapshot succession 2026-09-11: $($decision.decision)"
if (@($predecessor[0].processing_notes) -notcontains $note) { $predecessor[0].processing_notes = @($predecessor[0].processing_notes) + @($note) }
$predecessor[0].updated_at = (Get-Date).ToUniversalTime().ToString('o')
$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object { [string]$_.status -eq $status }).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$full = [IO.Path]::GetFullPath($InventoryPath); $tmp = "$full.tmp-$PID"
try { [IO.File]::WriteAllText($tmp, ($inventory | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false)); Move-Item -LiteralPath $tmp -Destination $full -Force }
finally { if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force } }
[pscustomobject]@{ predecessor = $decision.predecessor_id; successor = $decision.successor_id; counts = $inventory.counts } | ConvertTo-Json -Depth 5
