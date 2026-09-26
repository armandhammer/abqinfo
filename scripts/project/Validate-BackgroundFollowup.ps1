[CmdletBinding()]
param([int]$Attempt = 1)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$folder = 'project-state/discovery/background-followup-2026-09-26'
$suffix = '{0:d3}' -f $Attempt
$log = "$folder/full-validation-$suffix.log"
$passed = $false
$logTail = @()
try {
  & "$PSScriptRoot/Invoke-ProjectValidation.ps1" *> $log
  if (-not $?) { throw 'Project validation failed.' }
  $passed = $true
} catch {
  $_ | Out-String | Add-Content -LiteralPath $log -Encoding utf8
} finally {
  $logTail = Get-Content -LiteralPath $log -Tail 30
  $rawHash = (Get-FileHash -LiteralPath $log -Algorithm SHA256).Hash.ToLowerInvariant()
  $compressedLog = "$log.gz"
  $outputStream = [IO.File]::Create((Join-Path (Get-Location) $compressedLog))
  try {
    $gzip = [IO.Compression.GZipStream]::new($outputStream, [IO.Compression.CompressionLevel]::Optimal, $true)
    try {
      $bytes = [IO.File]::ReadAllBytes((Join-Path (Get-Location) $log))
      $gzip.Write($bytes, 0, $bytes.Length)
    } finally { $gzip.Dispose() }
  } finally { $outputStream.Dispose() }
  Remove-Item -LiteralPath $log
  [ordered]@{
    result = $(if ($passed) { 'passed' } else { 'failed' })
    recorded_at = [DateTime]::UtcNow.ToString('o')
    validated_head = (& git rev-parse HEAD)
    log_artifact = $compressedLog
    log_sha256 = (Get-FileHash -LiteralPath $compressedLog -Algorithm SHA256).Hash.ToLowerInvariant()
    uncompressed_log_sha256 = $rawHash
    visitor_visible_content_changed = $false
  } | ConvertTo-Json | Set-Content -LiteralPath "$folder/validation-$suffix.json" -Encoding utf8
}
Write-Output "Full project validation: $passed ($log)"
if (-not $passed) { $logTail; exit 1 }
