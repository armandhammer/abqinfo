[CmdletBinding()]
param(
  [Parameter(Mandatory)][string[]]$Ids,
  [Parameter(Mandatory)][string]$DownloadDirectory,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json

foreach ($id in $Ids) {
  $candidate = @($inventory.candidates | Where-Object id -eq $id)
  if ($candidate.Count -ne 1) { throw "Expected one candidate for '$id'; found $($candidate.Count)." }
  $candidate = $candidate[0]
  $file = @(Get-ChildItem -LiteralPath $DownloadDirectory -File | Where-Object BaseName -eq $id)
  if ($file.Count -ne 1) { throw "Expected one downloaded file for '$id'; found $($file.Count)." }
  $file = $file[0]
  $candidate.status = 'downloaded'
  $candidate.local_path = $file.FullName.Substring((Get-Location).Path.Length + 1).Replace('\','/')
  $candidate.size_bytes = [int64]$file.Length
  $candidate.checksum_sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  $candidate.file_type = if ($file.Extension -eq '.pdf') { 'PDF' } else { $candidate.file_type }
  $humanSize = if ($file.Length -ge 1MB) { '{0:N2} MiB' -f ($file.Length / 1MB) } elseif ($file.Length -ge 1KB) { '{0:N2} KiB' -f ($file.Length / 1KB) } else { "$($file.Length) bytes" }
  $note = "Downloaded exact size: $($file.Length) bytes ($humanSize); SHA-256 recorded."
  $candidate.processing_notes = @(@($candidate.processing_notes) + $note | Sort-Object -Unique)
  if ($file.Length -gt 100MB) {
    $candidate.processing_notes = @(@($candidate.processing_notes) + 'File exceeds the 100 MB production-upload approval threshold; no R2 upload is authorized.' | Sort-Object -Unique)
  }
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$json = $inventory | ConvertTo-Json -Depth 12
$fullPath = [IO.Path]::GetFullPath($InventoryPath)
for ($attempt = 1; $attempt -le 60; $attempt++) {
  $temporaryPath = "$fullPath.tmp-$PID-$attempt-$([guid]::NewGuid().ToString('n'))"
  try {
    [IO.File]::WriteAllText($temporaryPath, $json, [Text.UTF8Encoding]::new($false))
    [IO.File]::Move($temporaryPath, $fullPath, $true)
    [pscustomobject]@{ Updated=$Ids.Count; InventoryPath=$InventoryPath } | ConvertTo-Json -Compress
    return
  }
  catch {
    $retryable = $_.Exception -is [System.IO.IOException] -or $_.Exception -is [System.UnauthorizedAccessException] -or $_.Exception.InnerException -is [System.IO.IOException] -or $_.Exception.InnerException -is [System.UnauthorizedAccessException]
    if (Test-Path -LiteralPath $temporaryPath) { Remove-Item -LiteralPath $temporaryPath -Force }
    if (-not $retryable -or $attempt -eq 60) { throw }
    Start-Sleep -Milliseconds 500
  }
}
