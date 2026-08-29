[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$Id,
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$DownloadDirectory = 'research/staging/queue'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Read-InventoryWithRetry([string]$Path) {
  for ($attempt = 1; $attempt -le 8; $attempt++) {
    try { return Get-Content -Raw -Encoding UTF8 -LiteralPath $Path | ConvertFrom-Json }
    catch [System.IO.IOException] {
      if ($attempt -eq 8) { throw }
      Start-Sleep -Milliseconds (50 * $attempt)
    }
  }
}

function Write-InventoryWithRetry($Value, [string]$Path) {
  $json = $Value | ConvertTo-Json -Depth 12
  for ($attempt = 1; $attempt -le 8; $attempt++) {
    $fullPath = [IO.Path]::GetFullPath($Path)
    $temporaryPath = "$fullPath.tmp-$PID-$attempt"
    try {
      [IO.File]::WriteAllText($temporaryPath, $json, [Text.UTF8Encoding]::new($false))
      Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
      return
    }
    catch [System.IO.IOException] {
      if (Test-Path -LiteralPath $temporaryPath) { Remove-Item -LiteralPath $temporaryPath -Force }
      if ($attempt -eq 8) { throw }
      Start-Sleep -Milliseconds (50 * $attempt)
    }
  }
}

function Add-ProcessingNote($Candidate, [string]$Note) {
  $existing = @($Candidate.processing_notes) | ForEach-Object { ([string]$_).Trim() } | Where-Object { $_ }
  $Candidate.processing_notes = @(@($existing) + $Note | Sort-Object -Unique)
}

$inventory = Read-InventoryWithRetry $InventoryPath
$candidate = @($inventory.candidates | Where-Object id -eq $Id)
if ($candidate.Count -ne 1) { throw "Expected one candidate for '$Id'; found $($candidate.Count)." }
$candidate = $candidate[0]
$url = if ($candidate.direct_file_url) { $candidate.direct_file_url } else { $candidate.source_url }
if (-not $url) { throw "Candidate '$Id' has no downloadable URL." }
$candidate.status = 'downloading'
$candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
Write-InventoryWithRetry $inventory $InventoryPath
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
  $headers = @{
    'User-Agent' = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36'
  }
  if ($candidate.parent_url -and [uri]::IsWellFormedUriString([string]$candidate.parent_url, [UriKind]::Absolute)) {
    $headers['Referer'] = [string]$candidate.parent_url
  }
  Invoke-WebRequest -Uri $url -OutFile $path -UseBasicParsing -Headers $headers
  $file = Get-Item -LiteralPath $path
  $candidate.status = 'downloaded'
  $candidate.local_path = $file.FullName.Substring((Get-Location).Path.Length + 1).Replace('\','/')
  $candidate.size_bytes = $file.Length
  $candidate.checksum_sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($extension -eq '.pdf') { $candidate.file_type = 'PDF' }
  $humanSize = if ($file.Length -ge 1MB) { '{0:N2} MiB' -f ($file.Length / 1MB) } elseif ($file.Length -ge 1KB) { '{0:N2} KiB' -f ($file.Length / 1KB) } else { "$($file.Length) bytes" }
  Add-ProcessingNote $candidate "Downloaded exact size: $($file.Length) bytes ($humanSize); SHA-256 recorded."
  if ($file.Length -gt 100MB) { Add-ProcessingNote $candidate 'File exceeds the 100 MB production-upload approval threshold; no R2 upload is authorized.' }
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
  $counts = [ordered]@{}
  foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
  $inventory.counts = [pscustomobject]$counts
  $inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
  Write-InventoryWithRetry $inventory $InventoryPath
  $candidate | ConvertTo-Json -Depth 8
} catch {
  $candidate.status = 'pending review'
  Add-ProcessingNote $candidate "Download failed: $($_.Exception.Message)"
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
  Write-InventoryWithRetry $inventory $InventoryPath
  throw
}
