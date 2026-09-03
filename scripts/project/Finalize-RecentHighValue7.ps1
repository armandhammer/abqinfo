[CmdletBinding()]
param([string]$InventoryPath = 'project-state/master-inventory.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$updates = @(
  @{
    id = 'src-55255b2a1e98df71'
    title = 'Cutler Avenue Street Improvements'
    date = '2021'
    page = 'content/transportation/roadway-projects/_index.md'
    description = 'Connects the completed pedestrian project with the earlier commercial-district plan, documenting improvements between the Cutler cul-de-sac and Washington Street alongside longer-term land-use, transportation, infrastructure, safety, and economic-development recommendations.'
    note = 'Completed project page reviewed; the linked 2018 report and 2021 pedestrian-improvements presentation were independently archived and validated.'
  },
  @{
    id = 'src-4fa70bed8f8460f7'
    title = 'Sunset Road Reconstruction Phase 2'
    date = '2024-07-15'
    page = 'content/transportation/roadway-projects/_index.md'
    description = 'Tracks design from Bridge Boulevard to Trujillo Road for a two-lane roadway, storm drainage, curb and gutter, sidewalks, and related improvements. The County page still reports 30% design and a fall 2025 completion target.'
    note = 'Official current-project page returned HTTP 200 on 2026-09-03; item-specific contact Jennifer Flor, 505-350-7833, jflor@bernco.gov was verified from the project section.'
  },
  @{
    id = 'src-99204ec44bdcdca0'
    title = 'Foothill Drive'
    date = '2025-03-25'
    page = 'content/transportation/roadway-projects/_index.md'
    description = 'Tracks right-of-way acquisition and design for roadway and storm-drainage improvements along Foothill Drive in the Atrisco community. The County page still reports design at 30% and a February 2026 completion target.'
    note = 'Official current-project page returned HTTP 200 on 2026-09-03; item-specific contact Vincent Bartholdi, 505-221-4030, vbartholdi@bernco.gov was verified from the project section.'
  },
  @{
    id = 'src-62d3b321644b2b1a'
    title = 'Central Atrisco Fiberoptic Expansion Project'
    date = '2024-07-15'
    page = 'content/public-works/capital-projects.md'
    description = "Preserves the County's recent fiber installation along Atrisco Vista Boulevard, Comfort Way, and Central Avenue, funded through federal Economic Development Administration and American Rescue Plan sources and completed in July 2025."
    note = 'Official completed-project page returned HTTP 200 on 2026-09-03; its completed status and funding sources were reviewed.'
  },
  @{
    id = 'src-ebce549c834584d9'
    title = 'Tijeras Creek Watershed Restoration Project'
    date = '2024-12-18'
    page = 'content/public-works/stormwater-drainage.md'
    description = "Documents the County's restoration of Tijeras Creek and its floodplain near Los Vecinos Community Center and A. Montoya Elementary School, using nature-based solutions to reduce flood risk, restore native habitat, and improve downstream water quality."
    note = 'Official project page returned HTTP 200 on 2026-09-03; the June 2025 completion target is historical, so the older project contact was intentionally omitted.'
  }
)

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$now = (Get-Date).ToUniversalTime().ToString('o')
foreach ($update in $updates) {
  $matches = @($inventory.candidates | Where-Object id -eq $update.id)
  if ($matches.Count -ne 1) { throw "Expected one candidate for '$($update.id)'; found $($matches.Count)." }
  $candidate = $matches[0]
  $wordCount = @([string]$update.description -split '\s+' | Where-Object { $_ }).Count
  if ($wordCount -lt 20 -or $wordCount -gt 50) { throw "Description for '$($update.id)' has $wordCount words." }
  $candidate.status = 'validated'
  $candidate.title = $update.title
  $candidate.date = $update.date
  $candidate.proposed_canonical_page = $update.page
  $candidate.description = $update.description
  $candidate.description_word_count = $wordCount
  $candidate.implementation_location = $update.page
  $candidate.implementation_locations = @($update.page)
  $candidate.provenance_status = 'authoritative government source recorded'
  $candidate.validation_status = 'passed: authoritative government page returned HTTP 200, substantive project details reviewed, 20–50-word description and page placement validated'
  $candidate.processing_notes = @($candidate.processing_notes) + @($update.note) | Sort-Object -Unique
  $candidate.exclusion_reason = $null
  $candidate.updated_at = $now
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

[pscustomobject]@{ finalized = $updates.Count; validated = $updates.Count } | ConvertTo-Json -Compress
