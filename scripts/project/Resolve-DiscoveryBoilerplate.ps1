[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json
$excludedTitles = @(
  'About',
  'About the Department',
  'Back to Events',
  'Boards & Committees',
  'Business Support',
  'Careers',
  'Contact Us',
  'Districts',
  'Employees',
  'Employment Verification',
  'Executive Staff',
  'Export .ics file',
  'Home',
  'How Do I...',
  'Internship Listing',
  'Latest News',
  'Legal Notices',
  'Manage options',
  'Manzano Mesa Multigenerational Center',
  'News and Announcements',
  'Office of General Counsel',
  'Office of Inspector General',
  'Procurement and Contract Services',
  'Programs',
  'Results',
  'Scenic Byways – Redirect to NM Tourism Department',
  'Social Media',
  'Travel Times',
  'Trucking Industry'
)

$changed = @()
foreach ($candidate in $inventory.candidates) {
  if ($candidate.status -ne 'pending review' -or $candidate.title -notin $excludedTitles) { continue }
  $candidate.status = 'excluded'
  $candidate.validation_status = 'excluded by deterministic boilerplate review'
  $candidate.exclusion_reason = 'Navigation, administrative, employment, promotional, temporary-event, or generic agency material without lasting Albuquerque public-information value.'
  $candidate.processing_notes = @($candidate.processing_notes) + 'Excluded by the repeatable discovery-boilerplate rules; no production content or R2 object created.'
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
  $changed += $candidate
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$next = @($inventory.candidates | Where-Object status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned','implemented') | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { $next[0].id } else { $null }
$inventory | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $InventoryPath -Encoding utf8
[pscustomobject]@{Excluded=$changed.Count;Counts=$counts} | ConvertTo-Json -Depth 5
