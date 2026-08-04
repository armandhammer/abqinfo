[CmdletBinding()]
param(
  [string]$Id,
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [switch]$UpdateInventory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
for ($attempt = 1; $attempt -le 8; $attempt++) {
  try { $inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json; break }
  catch [System.IO.IOException] {
    if ($attempt -eq 8) { throw }
    Start-Sleep -Milliseconds (50 * $attempt)
  }
}
if (-not $Id) { $Id = $inventory.next_pending_id }
$candidate = $inventory.candidates | Where-Object { $_.id -eq $Id } | Select-Object -First 1
if (-not $candidate) { throw "Candidate not found: $Id" }
$locations = @($candidate.implementation_locations | Where-Object { $_ })
if ($UpdateInventory -and $candidate.status -eq 'implemented') {
  if ($candidate.description_word_count -lt 20 -or $candidate.description_word_count -gt 50) {
    throw "Candidate $Id cannot be validated until its description is 20-50 words."
  }
  if ($locations.Count -gt 1 -and -not $candidate.cross_listing_approved) {
    throw "Candidate $Id has multiple placements without an approved cross-listing."
  }
}
$url = if ($candidate.direct_file_url) { $candidate.direct_file_url } elseif ($candidate.source_url) { $candidate.source_url } else { $candidate.r2_url }
if (-not $url) { throw "Candidate has no testable URL: $Id" }

$method = 'HEAD'
try {
  $response = Invoke-WebRequest -Uri $url -Method Head -MaximumRedirection 10 -UseBasicParsing
} catch {
  $method = 'GET fallback'
  $response = Invoke-WebRequest -Uri $url -Method Get -MaximumRedirection 10 -UseBasicParsing
}
$result = [ordered]@{ id = $Id; title = $candidate.title; url = $url; http_status = [int]$response.StatusCode }
$result.method = $method

if ($UpdateInventory -and $response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $Id -InventoryPath $InventoryPath -Set @{
    status = 'validated'
    validation_status = "passed: HTTP $([int]$response.StatusCode)"
  } | Out-Null
  $result.updated_status = 'validated'
}

$result | ConvertTo-Json -Compress
