[CmdletBinding()]
param([string]$InventoryPath = 'project-state/master-inventory.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-AtomicJson($Value, [string]$Path) {
  $fullPath = [IO.Path]::GetFullPath($Path)
  $temporaryPath = "$fullPath.tmp-$PID"
  $json = $Value | ConvertTo-Json -Depth 12
  [IO.File]::WriteAllText($temporaryPath, $json, [Text.UTF8Encoding]::new($false))
  [IO.File]::Move($temporaryPath, $fullPath, $true)
}

$inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json
$exactNoiseTitles = @(
  'A-Z',
  'Contact Information',
  'Contact Us',
  'Full contact information',
  'Learn More',
  'Print this information out and take it with you!',
  'Read More',
  'Send us an online request',
  'Skip to Main Content',
  'View upcoming events for the command.'
)
$noisePatterns = @(
  '^\d+$',
  '^\d+ records?$',
  '^<?\s*Previous \d+ items?$',
  '^Next \d+ items?\s*>?$',
  '^View\.ashx$',
  '^Find another City Council district\.?$'
)

$resolved = 0
$now = (Get-Date).ToUniversalTime().ToString('o')
foreach ($candidate in @($inventory.candidates | Where-Object status -eq 'pending review')) {
  $title = ([string]$candidate.title).Trim()
  $isNoise = $title -in $exactNoiseTitles
  if (-not $isNoise) {
    $isNoise = @($noisePatterns | Where-Object { $title -match $_ }).Count -gt 0
  }
  if (-not $isNoise) { continue }

  $candidate.status = 'excluded'
  $candidate.exclusion_reason = 'Navigation, pagination, contact, or generic interface text captured as a candidate; it is not a substantive plan, study, map, dataset, project record, or source page.'
  $candidate.validation_status = 'terminal deterministic discovery-noise exclusion recorded'
  $candidate.processing_notes = @(@($candidate.processing_notes) + 'Excluded by reviewed deterministic discovery-noise rules; no substantive government content was discarded.') | Sort-Object -Unique
  $candidate.updated_at = $now
  $resolved++
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
Write-AtomicJson $inventory $InventoryPath

[pscustomobject]@{
  resolved = $resolved
  pending_review = $counts['pending review']
  excluded = $counts['excluded']
  next_pending_id = $inventory.next_pending_id
} | ConvertTo-Json -Compress
