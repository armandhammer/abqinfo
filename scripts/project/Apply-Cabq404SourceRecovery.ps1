[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$DecisionPath = 'project-state/discovery/cabq-404-source-recovery-2026-09-11.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$inventoryFull = [IO.Path]::GetFullPath($InventoryPath)
$decisions = Get-Content -LiteralPath $DecisionPath -Raw -Encoding UTF8 | ConvertFrom-Json
$inventory = Get-Content -LiteralPath $inventoryFull -Raw -Encoding UTF8 | ConvertFrom-Json
$byId = @{}
foreach ($candidate in $inventory.candidates) { $byId[[string]$candidate.id] = $candidate }
$seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
$updatedSuccessors = [Collections.Generic.List[string]]::new()
$terminalized = [Collections.Generic.List[string]]::new()

foreach ($decision in @($decisions.decisions)) {
  foreach ($id in @($decision.ids | ForEach-Object { [string]$_ })) {
    if (-not $seen.Add($id)) { throw "Duplicate decision candidate ID: $id" }
    if (-not $byId.ContainsKey($id)) { throw "Decision candidate is not in the inventory: $id" }
    $candidate = $byId[$id]
    if ([string]$candidate.status -ne 'requires human review') { throw "Decision candidate is no longer in requires human review: $id = $($candidate.status)" }
    $note = "City HTTP-404 source-recovery review 2026-09-11: $($decision.note)"
    if ([string]$decision.outcome -eq 'current official hub or successor located') {
      $replacement = [string]$decision.replacement_url
      if ($replacement -notmatch '^https://(www\.)?cabq\.gov/' -and $replacement -notmatch '^https://documents\.cabq\.gov/') { throw "Replacement URL is not a City source: $replacement" }
      $prior = if ($candidate.direct_file_url) { [string]$candidate.direct_file_url } else { [string]$candidate.source_url }
      if ($prior -and $prior -ne $replacement -and @($candidate.referring_urls) -notcontains $prior) { $candidate.referring_urls = @($candidate.referring_urls) + @($prior) }
      if ($candidate.direct_file_url) { $candidate.direct_file_url = $replacement } else { $candidate.source_url = $replacement }
      $candidate.validation_status = 'requires human review: official City successor or current hub recorded; completed failed verification result preserved; re-verification requires separate authorization'
      if (@($candidate.processing_notes) -notcontains $note) { $candidate.processing_notes = @($candidate.processing_notes) + @($note) }
      $updatedSuccessors.Add($id)
    } elseif ([string]$decision.outcome -eq 'no current standalone replacement located') {
      $candidate.status = 'excluded'
      $candidate.validation_status = 'excluded: City HTTP-404 review found no current standalone authoritative replacement'
      $candidate.exclusion_reason = "No current standalone authoritative replacement was located. $($decision.note)"
      if (@($candidate.processing_notes) -notcontains $note) { $candidate.processing_notes = @($candidate.processing_notes) + @($note) }
      $terminalized.Add($id)
    } else { throw "Unsupported recovery outcome for $($id): $($decision.outcome)" }
    $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
  }
}

if ($seen.Count -ne 42 -or $updatedSuccessors.Count -ne 28 -or $terminalized.Count -ne 14) { throw "Unexpected recovery decision totals: reviewed=$($seen.Count), successors=$($updatedSuccessors.Count), terminalized=$($terminalized.Count)" }
$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object { [string]$_.status -eq $status }).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$next = @($inventory.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { [string]$next[0].id } else { $null }
$temporary = "$inventoryFull.tmp-$PID"
try { [IO.File]::WriteAllText($temporary, ($inventory | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false)); Move-Item -LiteralPath $temporary -Destination $inventoryFull -Force } finally { if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force } }
[pscustomobject][ordered]@{ reviewed=$seen.Count; successors_recorded=$updatedSuccessors.Count; excluded=$terminalized.Count; counts=$inventory.counts; next_pending_id=$inventory.next_pending_id } | ConvertTo-Json -Depth 5
