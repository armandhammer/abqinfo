[CmdletBinding()]
param(
  [string]$InputDirectory = 'research/staging/document-review',
  [string]$OutputPath = 'project-state/contributed-document-review-2026-08-14.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-HumanSize([int64]$Bytes) {
  if ($Bytes -ge 1GB) { return ('{0:N2} GiB' -f ($Bytes / 1GB)) }
  if ($Bytes -ge 1MB) { return ('{0:N2} MiB' -f ($Bytes / 1MB)) }
  if ($Bytes -ge 1KB) { return ('{0:N2} KiB' -f ($Bytes / 1KB)) }
  return "$Bytes bytes"
}

$python = 'C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$extractor = Join-Path $PSScriptRoot 'extract_pdf.py'
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$knownByHash = @{}
foreach ($candidate in $inventory.candidates) {
  if ($candidate.checksum_sha256) { $knownByHash[[string]$candidate.checksum_sha256.ToLowerInvariant()] = $candidate }
}

$extractedDirectory = Join-Path $InputDirectory '.extracted'
New-Item -ItemType Directory -Force -Path $extractedDirectory | Out-Null
$items = @()
foreach ($file in Get-ChildItem -LiteralPath $InputDirectory -File | Sort-Object Name) {
  $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  $parsed = (& $python $extractor $file.FullName) | ConvertFrom-Json
  $textPath = Join-Path $extractedDirectory ($file.BaseName + '.txt')
  $parsed.text | Set-Content -LiteralPath $textPath -Encoding utf8
  $known = $knownByHash[$hash]
  $items += [pscustomobject][ordered]@{
    id = 'local-' + $hash.Substring(0, 16)
    filename = $file.Name
    local_path = $file.FullName
    file_type = $file.Extension.TrimStart('.').ToUpperInvariant()
    size_bytes = [int64]$file.Length
    size_human = Get-HumanSize $file.Length
    exceeds_25_mib = $file.Length -gt 25MB
    exceeds_100_mib = $file.Length -gt 100MB
    checksum_sha256 = $hash
    pages = [int]$parsed.pages
    pdf_metadata = $parsed.metadata
    embedded_links = @($parsed.links)
    extracted_text_path = $textPath
    matching_inventory_id = if ($known) { [string]$known.id } else { $null }
    matching_inventory_status = if ($known) { [string]$known.status } else { $null }
    review_status = if ($known) { 'duplicate' } else { 'pending review' }
    decision = if ($known) { "Exact SHA-256 match to $($known.id)." } else { $null }
    proposed_canonical_page = $null
    official_source_url = $null
    r2_url = if ($known) { [string]$known.r2_url } else { $null }
    implementation_location = if ($known) { [string]$known.implementation_location } else { $null }
  }
}

$totalBytes = [int64](($items | ForEach-Object { [int64]$_.size_bytes } | Measure-Object -Sum).Sum)
$result = [ordered]@{
  schema_version = 1
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  input_directory = (Resolve-Path -LiteralPath $InputDirectory).Path
  file_count = $items.Count
  total_bytes = $totalBytes
  total_human = Get-HumanSize $totalBytes
  exact_inventory_duplicates = @($items | Where-Object matching_inventory_id).Count
  pending_review = @($items | Where-Object { -not $_.matching_inventory_id }).Count
  items = $items
}

$result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $OutputPath -Encoding utf8
$result
