[CmdletBinding()]
param([string]$InventoryPath = 'project-state/master-inventory.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$open = @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned')
$now = (Get-Date).ToUniversalTime().ToString('o')
$changed = [System.Collections.Generic.List[object]]::new()

function Set-Terminal {
  param([string]$Id,[string]$Status,[string]$Reason,[string]$SupersededBy='')
  $candidate = @($inventory.candidates | Where-Object id -eq $Id)
  if ($candidate.Count -ne 1) { throw "Expected one candidate for '$Id'." }
  if ($candidate[0].status -notin $open) { return }
  $candidate[0].status = $Status
  $candidate[0].exclusion_reason = $Reason
  $candidate[0].validation_status = "terminal review decision: $Status"
  $candidate[0].processing_notes = @($candidate[0].processing_notes) + @($Reason) | Sort-Object -Unique
  if ($SupersededBy) {
    if ($candidate[0].PSObject.Properties['superseded_by']) { $candidate[0].superseded_by = $SupersededBy }
    else { $candidate[0] | Add-Member -NotePropertyName superseded_by -NotePropertyValue $SupersededBy }
  }
  $candidate[0].updated_at = $now
  $changed.Add([pscustomobject]@{id=$Id;status=$Status;title=$candidate[0].title})
}

Set-Terminal 'src-388dc8d67b786df4' 'duplicate' 'The collection page is retained as the official source for the complete curated 2007–2016 Decade Plan section.' 'src-ef823eb290efe729'
Set-Terminal 'src-e27f50d004db87c9' 'excluded' 'The City file named introduction.pdf serves an unrelated Urban Enhancement Trust Fund page, not the capital-plan introduction; it would be misleading to publish.'
Set-Terminal 'src-07d0261e51101ae5' 'excluded' 'Urban Enhancement Trust Fund grantee detail is a cultural-grant administration record outside the selected ABQInfo capital-infrastructure scope.'
Set-Terminal 'src-c73c66f581fb5143' 'excluded' 'Urban Enhancement Trust Fund summary is a cultural-grant administration record outside the selected ABQInfo capital-infrastructure scope.'

$scopeToSummary = @{
  'src-f9aa1f9578dd03a4'='src-be39966975e9924a'
  'src-7b5fae53edd6fbea'='src-baa2a3551783da18'
  'src-d673c4706e89ca74'='src-e665566329c4a04d'
  'src-31567db89d1226ff'='src-857af4faf4a82a56'
  'src-868df2baccfd1981'='src-857af4faf4a82a56'
  'src-108108642115e35e'='src-3176f1245fb14160'
  'src-3ceefdafa188e2e1'='src-fbf2928dc2388b68'
  'src-32a77d3856e9a056'='src-d554e2dfdf46e98b'
  'src-1d0fde9269d1e1bb'='src-d91051fe76863796'
  'src-4eacfa2b453b394b'='src-514c1cb1098dac8d'
  'src-3b069521e2d7d70d'='src-0c38e48c453a12db'
  'src-2313679384176f05'='src-1446091908574fda'
  'src-6d5ab056ef1d28d4'='src-ab1f9d7ff3dfd004'
  'src-85801aeb8cb46ef9'='src-a4c924b7039b13da'
  'src-8209c4dd917e64da'='src-c862e9705c4818eb'
  'src-9fea6f100259e1f2'='src-a9e35369bc0ff59e'
}
foreach ($pair in $scopeToSummary.GetEnumerator()) {
  Set-Terminal $pair.Key 'superseded' 'Department scope sheet is superseded for ABQInfo by the retained decade-wide project and funding summary.' $pair.Value
}

$crossListings = @{
  'src-c862e9705c4818eb'='content/transportation/transportation-plans.md'
  'src-a9e35369bc0ff59e'='content/transportation/transit/abq-ride.md'
  'src-a4c924b7039b13da'='content/public-works/stormwater-drainage.md'
  'src-c83a5233716f5e1f'='content/public-works/stormwater-drainage.md'
  'src-514c1cb1098dac8d'='content/public-works/parks-recreation.md'
  'src-389b414dbe0fb8b9'='content/public-works/parks-recreation.md'
  'src-89cf13c2d742e6d2'='content/public-works/parks-recreation.md'
  'src-43f135ae1e00492e'='content/development-land-use/redevelopment-plans.md'
  'src-e665566329c4a04d'='content/public-works/city-facilities.md'
  'src-d91051fe76863796'='content/public-works/parks-recreation.md'
  'src-0c38e48c453a12db'='content/development-land-use/redevelopment-plans.md'
}
foreach ($pair in $crossListings.GetEnumerator()) {
  $candidate = @($inventory.candidates | Where-Object id -eq $pair.Key)
  if ($candidate.Count -ne 1 -or $candidate[0].status -ne 'validated') { throw "Validated cross-listing candidate missing: $($pair.Key)." }
  $candidate[0].implementation_locations = @('content/city-data/capital-spending.md',[string]$pair.Value)
  if ($candidate[0].PSObject.Properties['cross_listing_approved']) { $candidate[0].cross_listing_approved = $true }
  else { $candidate[0] | Add-Member -NotePropertyName cross_listing_approved -NotePropertyValue $true }
  $candidate[0].processing_notes = @($candidate[0].processing_notes) + @('Cross-listed on the relevant subject page while Capital Spending remains canonical.') | Sort-Object -Unique
  $candidate[0].updated_at = $now
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = $now
$next = @($inventory.candidates | Where-Object { $_.status -in $open -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { $next[0].id } else { $null }
$json = $inventory | ConvertTo-Json -Depth 12
$full = [IO.Path]::GetFullPath($InventoryPath)
$temporary = "$full.tmp-$PID"
[IO.File]::WriteAllText($temporary,$json,[Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporary -Destination $full -Force

[pscustomobject]@{
  terminal_decisions=$changed.Count
  excluded=@($changed|Where-Object status -eq 'excluded').Count
  duplicate=@($changed|Where-Object status -eq 'duplicate').Count
  superseded=@($changed|Where-Object status -eq 'superseded').Count
  next_pending=$inventory.next_pending_id
}|ConvertTo-Json -Compress
