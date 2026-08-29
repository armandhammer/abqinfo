[CmdletBinding()]
param([string]$InventoryPath = 'project-state/master-inventory.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-NormalizedSourceUrl([string]$Url) {
  if ([string]::IsNullOrWhiteSpace($Url)) { return $null }
  try {
    $uri = [uri]$Url
    $hostName = $uri.Host.ToLowerInvariant() -replace '^www\.', ''
    $path = $uri.AbsolutePath.TrimEnd('/')
    $query = $uri.Query
    if ($query -match '^\?bidid=$') { $query = '' }
    return "$hostName$path$query"
  }
  catch {
    return $Url.Trim().TrimEnd('/')
  }
}

function Write-AtomicJson($Value, [string]$Path) {
  $fullPath = [IO.Path]::GetFullPath($Path)
  $temporaryPath = "$fullPath.tmp-$PID"
  $json = $Value | ConvertTo-Json -Depth 12
  [IO.File]::WriteAllText($temporaryPath, $json, [Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
}

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$rank = @{
  'validated' = 0
  'implemented' = 1
  'placement assigned' = 2
  'description drafted' = 3
  'parsed' = 4
  'downloaded' = 5
  'approved for addition' = 6
  'pending review' = 7
  'requires human review' = 8
  'blocked' = 9
  'superseded' = 10
  'excluded' = 11
  'duplicate' = 12
}

$resolved = 0
$groups = @($inventory.candidates |
  Where-Object source_url |
  Group-Object { Get-NormalizedSourceUrl ([string]$_.source_url) } |
  Where-Object Count -gt 1)
$now = (Get-Date).ToUniversalTime().ToString('o')

foreach ($group in $groups) {
  $pending = @($group.Group | Where-Object status -eq 'pending review')
  if (-not $pending.Count) { continue }

  $canonical = @($group.Group | Sort-Object @(
    @{ Expression = { if ($rank.ContainsKey([string]$_.status)) { $rank[[string]$_.status] } else { 99 } } },
    @{ Expression = { if ($_.checksum_sha256) { 0 } else { 1 } } },
    @{ Expression = { if ($_.direct_file_url) { 0 } else { 1 } } },
    @{ Expression = { if ($_.title) { 0 } else { 1 } } },
    @{ Expression = 'id' }
  ) | Select-Object -First 1)[0]

  foreach ($candidate in $pending) {
    if ($candidate.id -eq $canonical.id) { continue }
    $canonical.referring_urls = @(
      @($canonical.referring_urls) +
      @($candidate.referring_urls) +
      @($candidate.parent_url) +
      @($candidate.source_url)
    ) | Where-Object { $_ } | Sort-Object -Unique
    $canonical.discovery_path = @(
      @($canonical.discovery_path) + @($candidate.discovery_path)
    ) | Where-Object { $_ } | Sort-Object -Unique
    $canonical.processing_notes = @(
      @($canonical.processing_notes) +
      "Merged discovery provenance from normalized-URL duplicate $($candidate.id)."
    ) | Sort-Object -Unique
    $canonical.updated_at = $now

    $candidate.status = 'duplicate'
    $candidate.exclusion_reason = "Normalized source URL is identical to canonical inventory record $($canonical.id); www, trailing-slash, or empty bidId variations do not identify different content."
    $candidate.validation_status = 'terminal normalized-source-url duplicate recorded'
    $candidate.processing_notes = @(
      @($candidate.processing_notes) +
      "Discovery provenance merged into canonical record $($canonical.id)."
    ) | Sort-Object -Unique
    $candidate.updated_at = $now
    $resolved++
  }
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) {
  $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count
}
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = $now
$next = @($inventory.candidates | Where-Object {
  $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or
  ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed')
} | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { $next[0].id } else { $null }
Write-AtomicJson $inventory $InventoryPath

[pscustomobject]@{
  duplicate_groups_reviewed = $groups.Count
  pending_duplicates_resolved = $resolved
  pending_review = $counts['pending review']
  duplicate = $counts['duplicate']
  next_pending_id = $inventory.next_pending_id
} | ConvertTo-Json -Compress
