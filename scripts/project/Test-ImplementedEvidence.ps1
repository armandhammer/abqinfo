[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$ReportPath = 'project-state/discovery/implemented-evidence-validation.json',
  [int]$RequestTimeoutSeconds = 30,
  [switch]$UpdateInventory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-AtomicJson($Value, [string]$Path) {
  $fullPath = [IO.Path]::GetFullPath($Path)
  $parent = Split-Path -Parent $fullPath
  if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent | Out-Null }
  $temporaryPath = "$fullPath.tmp-$PID"
  [IO.File]::WriteAllText($temporaryPath, ($Value | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
}

function Test-RemoteUrl([string]$Url) {
  $userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36 ABQInfo-Evidence-Validator/1.0'
  try {
    $response = Invoke-WebRequest -Uri $Url -Method Head -MaximumRedirection 10 -UseBasicParsing -TimeoutSec $RequestTimeoutSeconds -UserAgent $userAgent
    return [pscustomobject]@{ status = [int]$response.StatusCode; method = 'HEAD'; error = $null }
  } catch {
    try {
      $response = Invoke-WebRequest -Uri $Url -Method Get -MaximumRedirection 10 -UseBasicParsing -TimeoutSec $RequestTimeoutSeconds -UserAgent $userAgent
      return [pscustomobject]@{ status = [int]$response.StatusCode; method = 'GET fallback'; error = $null }
    } catch {
      return [pscustomobject]@{ status = $null; method = 'GET fallback'; error = $_.Exception.Message }
    }
  }
}

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$implemented = @($inventory.candidates | Where-Object status -eq 'implemented' | Sort-Object id)
$results = [Collections.Generic.List[object]]::new()
$now = (Get-Date).ToUniversalTime().ToString('o')

foreach ($candidate in $implemented) {
  $locations = @($candidate.implementation_locations | Where-Object { $_ })
  $candidateUrls = @($candidate.r2_url, $candidate.direct_file_url, $candidate.source_url) | Where-Object { $_ } | Select-Object -Unique
  $missingLocations = [Collections.Generic.List[string]]::new()
  foreach ($location in $locations) {
    if (-not (Test-Path -LiteralPath $location)) {
      $missingLocations.Add($location)
      continue
    }
    $content = Get-Content -Raw -Encoding UTF8 -LiteralPath $location
    if (-not @($candidateUrls | Where-Object { $content.Contains($_) }).Count) { $missingLocations.Add($location) }
  }

  $authoritativeUrl = @($candidate.direct_file_url, $candidate.source_url) |
    Where-Object { $_ -match '^https?://' -and $_ -notmatch '^https?://files\.abqinfo\.com(?:/|$)' } |
    Select-Object -First 1
  $descriptionValid = $candidate.description_word_count -ge 20 -and $candidate.description_word_count -le 50
  $crossListingValid = $locations.Count -le 1 -or [bool]$candidate.cross_listing_approved
  $placementValid = $locations.Count -gt 0 -and $missingLocations.Count -eq 0
  $remote = if ($authoritativeUrl -and $descriptionValid -and $crossListingValid -and $placementValid) {
    Test-RemoteUrl $authoritativeUrl
  } else {
    [pscustomobject]@{ status = $null; method = 'not attempted'; error = $null }
  }
  $remoteValid = $null -ne $remote.status -and $remote.status -ge 200 -and $remote.status -lt 400

  $decision = if (-not $authoritativeUrl) {
    'requires human review'
  } elseif ($descriptionValid -and $crossListingValid -and $placementValid -and $remoteValid) {
    'validated'
  } else {
    'implemented'
  }

  $result = [pscustomobject][ordered]@{
    id = $candidate.id
    title = $candidate.title
    authoritative_url = $authoritativeUrl
    description_valid = $descriptionValid
    cross_listing_valid = $crossListingValid
    implementation_locations = $locations
    missing_or_unlinked_locations = @($missingLocations)
    placement_valid = $placementValid
    http_status = $remote.status
    http_method = $remote.method
    http_error = $remote.error
    decision = $decision
  }
  $results.Add($result)

  if (-not $UpdateInventory) { continue }
  if ($decision -eq 'validated') {
    $candidate.status = 'validated'
    $candidate.validation_status = "passed: local placement, description, cross-listing, provenance, and authoritative source HTTP $($remote.status)"
    $candidate.updated_at = $now
  } elseif ($decision -eq 'requires human review') {
    $candidate.status = 'requires human review'
    $candidate.validation_status = 'published archive placement passed locally; authoritative government provenance remains unresolved'
    $candidate.processing_notes = @(@($candidate.processing_notes) + 'Automated evidence validation found no non-R2 authoritative source URL; the archived item requires provenance reconciliation.') | Sort-Object -Unique
    $candidate.updated_at = $now
  }
}

$summary = [ordered]@{
  generated_at = $now
  update_inventory = [bool]$UpdateInventory
  implemented_examined = $implemented.Count
  decisions = [ordered]@{
    validated = @($results | Where-Object decision -eq 'validated').Count
    remains_implemented = @($results | Where-Object decision -eq 'implemented').Count
    requires_human_review = @($results | Where-Object decision -eq 'requires human review').Count
  }
  results = @($results)
}
Write-AtomicJson $summary $ReportPath

if ($UpdateInventory) {
  $counts = [ordered]@{}
  foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
  $inventory.counts = [pscustomobject]$counts
  $inventory.generated_at = $now
  $next = @($inventory.candidates | Where-Object {
    $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or
    ($_.status -eq 'implemented' -and $_.validation_status -notlike 'passed:*')
  } | Sort-Object id | Select-Object -First 1)
  $inventory.next_pending_id = if ($next.Count) { $next[0].id } else { $null }
  Write-AtomicJson $inventory $InventoryPath
}

[pscustomobject]$summary | ConvertTo-Json -Depth 12
