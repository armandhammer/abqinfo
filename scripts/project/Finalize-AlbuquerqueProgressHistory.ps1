[CmdletBinding()]
param([string]$InventoryPath = 'project-state/master-inventory.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$now = (Get-Date).ToUniversalTime().ToString('o')
$changed = [System.Collections.Generic.List[object]]::new()

function Set-Terminal {
  param([string]$Id,[string]$Status,[string]$Reason,[string]$Canonical='')
  $candidate = @($inventory.candidates | Where-Object id -eq $Id)
  if ($candidate.Count -ne 1) { throw "Expected one candidate for '$Id'." }
  if ($candidate[0].status -notin @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned')) { return }
  $candidate[0].status = $Status
  $candidate[0].exclusion_reason = $Reason
  $candidate[0].validation_status = "terminal review decision: $Status"
  $candidate[0].processing_notes = @($candidate[0].processing_notes) + @($Reason) | Sort-Object -Unique
  if ($Canonical) {
    if ($candidate[0].PSObject.Properties['duplicate_of']) { $candidate[0].duplicate_of = $Canonical }
    else { $candidate[0] | Add-Member -NotePropertyName duplicate_of -NotePropertyValue $Canonical }
  }
  $candidate[0].updated_at = $now
  $changed.Add([pscustomobject]@{id=$Id;status=$Status;title=$candidate[0].title})
}

$duplicates = @{
  'src-e6e3b6c0fdb46562'='src-572f6d8a7a30f8a1'
  'src-d1af29c369338d37'='src-f9c6246de583e9da'
  'src-30ea962b044d904b'='src-5da6965abacdaee9'
  'src-62d0c689f88da29e'='src-cd8f57c4c1140437'
  'src-ca5210d597e746b4'='src-0cec8aac1c0949a7'
  'src-0964495fb5d9c510'='src-3af3d3d2b34a5606'
}
foreach ($pair in $duplicates.GetEnumerator()) {
  Set-Terminal $pair.Key 'duplicate' 'The Plone view record duplicates the retained authoritative PDF from the same official City archive page.' $pair.Value
}

$missing = @($inventory.candidates | Where-Object id -eq 'src-352d880cb11386d3')
if ($missing.Count -ne 1) { throw 'Missing 2004 Progress Report record.' }
if ($missing[0].status -eq 'pending review') {
  $missing[0].status = 'requires human review'
  $missing[0].proposed_canonical_page = 'content/city-data/city-progress-surveys.md'
  $missing[0].validation_status = 'official archive link redirects to organization sign-in; original report file not recovered'
  $missing[0].processing_notes = @($missing[0].processing_notes) + @('The City archive lists a 2004 report, but its current link redirects to Microsoft organization sign-in. A preserved authoritative copy should be sought through the Internet Archive or City records.') | Sort-Object -Unique
  $missing[0].updated_at = $now
  $changed.Add([pscustomobject]@{id=$missing[0].id;status=$missing[0].status;title=$missing[0].title})
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = $now
$open = @('pending review','approved for addition','downloading','downloaded','parsed','description drafted','placement assigned')
$next = @($inventory.candidates | Where-Object { $_.status -in $open -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { $next[0].id } else { $null }
$json = $inventory | ConvertTo-Json -Depth 12
$full = [IO.Path]::GetFullPath($InventoryPath)
$temporary = "$full.tmp-$PID"
[IO.File]::WriteAllText($temporary,$json,[Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporary -Destination $full -Force

[pscustomobject]@{terminal_decisions=$changed.Count;duplicates=@($changed|Where-Object status -eq 'duplicate').Count;requires_human_review=@($changed|Where-Object status -eq 'requires human review').Count;next_pending=$inventory.next_pending_id}|ConvertTo-Json -Compress
