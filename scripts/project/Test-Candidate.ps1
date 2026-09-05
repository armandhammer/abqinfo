[CmdletBinding()]
param(
  [string]$Id,
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [switch]$UpdateInventory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
for ($attempt = 1; $attempt -le 8; $attempt++) {
  try { $inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json; break }
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

# A successful response from ABQInfo's R2 archive proves only that the archive
# link works. It does not establish authoritative government provenance. When
# updating inventory state, prefer a non-R2 source URL and keep R2-only records
# out of the terminal "validated" state.
$authoritativeUrl = @($candidate.source_url, $candidate.direct_file_url) |
  Where-Object { $_ -and $_ -match '^https?://' -and $_ -notmatch '^https?://files\.abqinfo\.com(?:/|$)' } |
  Select-Object -First 1

$url = if ($UpdateInventory -and $authoritativeUrl) {
  $authoritativeUrl
} elseif ($candidate.direct_file_url) {
  $candidate.direct_file_url
} elseif ($candidate.source_url) {
  $candidate.source_url
} else {
  $candidate.r2_url
}
if (-not $url) { throw "Candidate has no testable URL: $Id" }

$method = 'HEAD'
$userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36 ABQInfo-Link-Validator/1.0'
try {
  $response = Invoke-WebRequest -Uri $url -Method Head -MaximumRedirection 10 -UseBasicParsing -UserAgent $userAgent
} catch {
  $method = 'GET fallback'
  $response = Invoke-WebRequest -Uri $url -Method Get -MaximumRedirection 10 -UseBasicParsing -UserAgent $userAgent
}

# Legistar can return HTTP 200 for a page that visibly reports an invalid
# matter-detail parameter set.  Inspect that rendered response for this known
# semantic error rather than treating the status code alone as validation.
if ($url -match '(?i)^https?://[^/]*legistar\.com/LegislationDetail\.aspx(?:[?#]|$)') {
  $detailResponse = Invoke-WebRequest -Uri $url -Method Get -MaximumRedirection 10 -UseBasicParsing -UserAgent $userAgent
  if ([string]$detailResponse.Content -match '(?i)invalid parameters!') {
    throw "Legistar matter-detail page reports 'Invalid parameters!' despite HTTP $([int]$detailResponse.StatusCode): $url"
  }
}
$result = [ordered]@{ id = $Id; title = $candidate.title; url = $url; http_status = [int]$response.StatusCode }
$result.method = $method

if ($UpdateInventory -and $response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
  if ($authoritativeUrl) {
    & "$PSScriptRoot/Update-Candidate.ps1" -Id $Id -InventoryPath $InventoryPath -Set @{
      status = 'validated'
      validation_status = "passed: authoritative source HTTP $([int]$response.StatusCode)"
    } | Out-Null
    $result.updated_status = 'validated'
  } else {
    $note = 'HTTP-only archive validation did not establish authoritative-source provenance.'
    $notes = @($candidate.processing_notes | Where-Object { $_ })
    if ($notes -notcontains $note) { $notes += $note }
    & "$PSScriptRoot/Update-Candidate.ps1" -Id $Id -InventoryPath $InventoryPath -Set @{
      status = 'requires human review'
      validation_status = "R2 archive link passed HTTP $([int]$response.StatusCode); authoritative government provenance remains unresolved"
      processing_notes = $notes
    } | Out-Null
    $result.updated_status = 'requires human review'
  }
}

$result | ConvertTo-Json -Compress
