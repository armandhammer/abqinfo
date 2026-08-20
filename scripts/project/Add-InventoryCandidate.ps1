[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$SourceUrl,
  [string]$DirectFileUrl,
  [Parameter(Mandatory)][string]$Agency,
  [Parameter(Mandatory)][string]$Title,
  [string]$Date,
  [Parameter(Mandatory)][string]$FileType,
  [string]$ParentUrl,
  [string]$DiscoveryMethod = 'authoritative outbound link',
  [Nullable[int]]$CrawlDepth,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-StableId([string]$Value) {
  $normalized = $Value.Trim().ToLowerInvariant()
  $bytes = [Text.Encoding]::UTF8.GetBytes($normalized)
  $sha256 = [Security.Cryptography.SHA256]::Create()
  try { $hash = $sha256.ComputeHash($bytes) } finally { $sha256.Dispose() }
  $hex = -join ($hash | ForEach-Object { $_.ToString('x2') })
  return 'src-' + $hex.Substring(0, 16)
}

function Write-AtomicJson($Value, [string]$Path) {
  $fullPath = [IO.Path]::GetFullPath($Path)
  $json = $Value | ConvertTo-Json -Depth 12
  for ($attempt = 1; $attempt -le 8; $attempt++) {
    $temporaryPath = "$fullPath.tmp-$PID-$attempt"
    try {
      [IO.File]::WriteAllText($temporaryPath, $json, [Text.UTF8Encoding]::new($false))
      [IO.File]::Move($temporaryPath, $fullPath, $true)
      return
    }
    catch {
      $retryable = $_.Exception -is [System.IO.IOException] -or $_.Exception -is [System.UnauthorizedAccessException] -or $_.Exception.InnerException -is [System.IO.IOException] -or $_.Exception.InnerException -is [System.UnauthorizedAccessException]
      if (Test-Path -LiteralPath $temporaryPath) { Remove-Item -LiteralPath $temporaryPath -Force }
      if (-not $retryable -or $attempt -eq 8) { throw }
      Start-Sleep -Milliseconds (100 * $attempt)
    }
  }
}

$inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json
$id = Get-StableId $SourceUrl
$existing = @($inventory.candidates | Where-Object id -eq $id)
if ($existing.Count) {
  if ($existing.Count -ne 1) { throw "Inventory contains $($existing.Count) records with stable ID '$id'." }
  $existing[0] | ConvertTo-Json -Depth 8
  return
}

$now = (Get-Date).ToUniversalTime().ToString('o')
$candidate = [pscustomobject][ordered]@{
  id = $id
  status = 'pending review'
  source_url = $SourceUrl
  direct_file_url = if ($DirectFileUrl) { $DirectFileUrl } elseif ($FileType -match '^(PDF|DOCX|XLSX|CSV|ZIP)$') { $SourceUrl } else { $null }
  r2_url = $null
  r2_key = $null
  r2_etag = $null
  r2_last_modified = $null
  agency = $Agency
  title = $Title
  date = if ($Date) { $Date } else { $null }
  file_type = $FileType
  size_bytes = $null
  checksum_sha256 = $null
  parent_url = if ($ParentUrl) { $ParentUrl } else { $null }
  referring_urls = @($ParentUrl | Where-Object { $_ })
  discovery_path = @($ParentUrl, $SourceUrl | Where-Object { $_ } | Select-Object -Unique)
  discovery_method = $DiscoveryMethod
  crawl_depth = if ($null -ne $CrawlDepth) { $CrawlDepth } else { $null }
  cited_predecessors = @()
  cited_successors = @()
  provenance_status = 'source URL recorded'
  proposed_canonical_page = $null
  description = $null
  description_word_count = 0
  processing_notes = @("Added through $DiscoveryMethod from the recorded authoritative source graph.")
  implementation_location = $null
  implementation_locations = @()
  cross_listing_approved = $false
  validation_status = 'not run'
  exclusion_reason = $null
  local_path = $null
  discovered_at = $now
  updated_at = $now
}

$inventory.candidates = @($inventory.candidates) + $candidate | Sort-Object id
$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = $now
Write-AtomicJson $inventory $InventoryPath
$candidate | ConvertTo-Json -Depth 8
