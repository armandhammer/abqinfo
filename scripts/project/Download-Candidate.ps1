[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$Id,
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$DownloadDirectory = 'research/staging/queue'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw $InventoryPath | ConvertFrom-Json
$candidate = @($inventory.candidates | Where-Object id -eq $Id)
if ($candidate.Count -ne 1) { throw "Expected one candidate for '$Id'; found $($candidate.Count)." }
$candidate = $candidate[0]
$url = if ($candidate.direct_file_url) { $candidate.direct_file_url } else { $candidate.source_url }
if (-not $url) { throw "Candidate '$Id' has no downloadable URL." }
$candidate.status = 'downloading'
$candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
$inventory | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $InventoryPath -Encoding utf8
New-Item -ItemType Directory -Force $DownloadDirectory | Out-Null
$extension = [IO.Path]::GetExtension(([uri]$url).AbsolutePath)
if (-not $extension) {
  $knownExtensions = @{
    'CSV' = '.csv'
    'DOCX' = '.docx'
    'JSON' = '.json'
    'PDF' = '.pdf'
    'TXT' = '.txt'
    'XLSX' = '.xlsx'
    'ZIP' = '.zip'
  }
  $declaredType = ([string]$candidate.file_type).ToUpperInvariant()
  if ($url -match '(?i)/DocumentCenter/View/' -or $candidate.title -match '(?i)\bPDF\b|\(PDF\)') {
    $extension = '.pdf'
  } else {
    $extension = if ($knownExtensions.ContainsKey($declaredType)) { $knownExtensions[$declaredType] } else { '.bin' }
  }
}
$path = Join-Path $DownloadDirectory ($Id + $extension.ToLowerInvariant())
try {
  Invoke-WebRequest -Uri $url -OutFile $path -UseBasicParsing
  $file = Get-Item -LiteralPath $path
  $candidate.status = 'downloaded'
  $candidate.local_path = $file.FullName.Substring((Get-Location).Path.Length + 1).Replace('\','/')
  $candidate.size_bytes = $file.Length
  $candidate.checksum_sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($extension -eq '.pdf') { $candidate.file_type = 'PDF' }
  $humanSize = if ($file.Length -ge 1MB) { '{0:N2} MiB' -f ($file.Length / 1MB) } elseif ($file.Length -ge 1KB) { '{0:N2} KiB' -f ($file.Length / 1KB) } else { "$($file.Length) bytes" }
  $candidate.processing_notes += "Downloaded exact size: $($file.Length) bytes ($humanSize); SHA-256 recorded."
  if ($file.Length -gt 100MB) { $candidate.processing_notes += 'File exceeds the 100 MB production-upload approval threshold; no R2 upload is authorized.' }
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
  $inventory | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $InventoryPath -Encoding utf8
  $candidate | ConvertTo-Json -Depth 8
} catch {
  $candidate.status = 'pending review'
  $candidate.processing_notes += "Download failed: $($_.Exception.Message)"
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
  $inventory | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $InventoryPath -Encoding utf8
  throw
}
