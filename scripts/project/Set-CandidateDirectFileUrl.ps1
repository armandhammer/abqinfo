[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$Id,
  [Parameter(Mandatory)][uri]$DirectFileUrl,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$matches = @($inventory.candidates | Where-Object id -eq $Id)
if ($matches.Count -ne 1) { throw "Expected one candidate for '$Id'; found $($matches.Count)." }
$candidate = $matches[0]
$candidate.direct_file_url = $DirectFileUrl.AbsoluteUri
$candidate.status = 'pending review'
$candidate.local_path = $null
$candidate.size_bytes = $null
$candidate.checksum_sha256 = $null
$candidate.processing_notes = @(
  @($candidate.processing_notes) +
  "Resolved the authoritative page's direct file link: $($DirectFileUrl.AbsoluteUri)"
  | Sort-Object -Unique
)
$candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) {
  $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count
}
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')

$json = $inventory | ConvertTo-Json -Depth 12
$fullPath = [IO.Path]::GetFullPath($InventoryPath)
$temporaryPath = "$fullPath.tmp-$PID-$([guid]::NewGuid().ToString('n'))"
try {
  [IO.File]::WriteAllText($temporaryPath, $json, [Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
} finally {
  if (Test-Path -LiteralPath $temporaryPath) { Remove-Item -LiteralPath $temporaryPath -Force }
}

$candidate | Select-Object id,status,source_url,direct_file_url | ConvertTo-Json
