[CmdletBinding()]
param([string]$InventoryPath = 'project-state/master-inventory.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$updates = @(
  @{
    id = 'src-41dd0953c79a9816'
    status = 'duplicate'
    reason = 'Alternate official City Council copy of Zuni Road Study Part II; the same collected-data report is already preserved and validated as src-257a9d7a9cd2784a.'
    validation = 'terminal duplicate decision recorded; alternate authoritative provenance retained'
  },
  @{
    id = 'src-cc2a2198a662141c'
    status = 'validated'
    title = 'Isleta Boulevard Corridor Lighting'
    date = '2025-11-03'
    page = 'content/transportation/roadway-projects/_index.md'
    description = 'Designs LED lighting upgrades along Isleta Boulevard from Durand Road to Bridge Boulevard, ten intersections, and the I-25 Exit 213 ramps. Bernalillo County reports design at 30% with construction anticipated in 2026–2027.'
    validation = 'passed: authoritative County page returned HTTP 200, current project details and item-specific contact reviewed, 20–50-word description and page placement validated'
  },
  @{
    id = 'src-3531b330bc1f738f'
    status = 'validated'
    title = 'Foothill Pond Feasibility Study'
    date = '2021-04-15'
    page = 'content/public-works/stormwater-drainage.md'
    description = 'Evaluates Foothill Bridge Pond and a possible connection to the Isleta Drain, including site survey, hydraulic capacity, a 30% conceptual design, and construction-cost estimate for improving the stormwater outfall system.'
    validation = 'passed: authoritative County page returned HTTP 200, substantive project record reviewed, 20–50-word description and page placement validated'
  }
)

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$now = (Get-Date).ToUniversalTime().ToString('o')
foreach ($update in $updates) {
  $matches = @($inventory.candidates | Where-Object id -eq $update.id)
  if ($matches.Count -ne 1) { throw "Expected one candidate for '$($update.id)'; found $($matches.Count)." }
  $candidate = $matches[0]
  $candidate.status = $update.status
  $candidate.validation_status = $update.validation
  $candidate.updated_at = $now
  if ($update.status -eq 'duplicate') {
    $candidate.exclusion_reason = $update.reason
    $candidate.processing_notes = @($candidate.processing_notes) + @($update.reason) | Sort-Object -Unique
  } else {
    $wordCount = @([string]$update.description -split '\s+' | Where-Object { $_ }).Count
    if ($wordCount -lt 20 -or $wordCount -gt 50) { throw "Description for '$($update.id)' has $wordCount words." }
    $candidate.proposed_canonical_page = $update.page
    $candidate.title = $update.title
    $candidate.date = $update.date
    $candidate.description = $update.description
    $candidate.description_word_count = $wordCount
    $candidate.implementation_location = $update.page
    $candidate.implementation_locations = @($update.page)
    $candidate.exclusion_reason = $null
  }
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = $now
$next = @($inventory.candidates | Where-Object {
  $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or
  ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed')
} | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { $next[0].id } else { $null }

$json = $inventory | ConvertTo-Json -Depth 12
$fullPath = [IO.Path]::GetFullPath($InventoryPath)
$temporaryPath = "$fullPath.tmp-$PID"
[IO.File]::WriteAllText($temporaryPath, $json, [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force

[pscustomobject]@{ finalized = $updates.Count; validated = 2; duplicate = 1 } | ConvertTo-Json -Compress
