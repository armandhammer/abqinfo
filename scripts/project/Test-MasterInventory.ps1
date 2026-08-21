[CmdletBinding()]
param([string]$InventoryPath = 'project-state/master-inventory.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw -Encoding UTF8 $InventoryPath | ConvertFrom-Json
$errors = [Collections.Generic.List[string]]::new()
$ids = @{}

foreach ($candidate in $inventory.candidates) {
  foreach ($field in @('parent_url','referring_urls','discovery_path','discovery_method','crawl_depth','cited_predecessors','cited_successors','provenance_status')) {
    if (-not $candidate.PSObject.Properties[$field]) { $errors.Add("Missing discovery/provenance field: $($candidate.id) = $field") }
  }
  if ($ids.ContainsKey($candidate.id)) { $errors.Add("Duplicate id: $($candidate.id)") } else { $ids[$candidate.id] = $true }
  if ($candidate.status -notin $inventory.allowed_statuses) { $errors.Add("Invalid status: $($candidate.id) = $($candidate.status)") }
  if (-not $candidate.title) { $errors.Add("Missing title: $($candidate.id)") }
  if ($candidate.description) {
    $actual = @($candidate.description -split '\s+' | Where-Object { $_ }).Count
    if ($actual -ne $candidate.description_word_count) { $errors.Add("Description word count mismatch: $($candidate.id) stored=$($candidate.description_word_count) actual=$actual") }
    if ($candidate.status -in @('implemented','validated') -and ($actual -lt 20 -or $actual -gt 50)) { $errors.Add("Implemented description outside 20-50 words: $($candidate.id) = $actual") }
  }
  if ($candidate.status -in @('implemented','validated') -and -not $candidate.description) { $errors.Add("Implemented item missing description: $($candidate.id)") }
  if ($candidate.status -in @('excluded','duplicate','superseded') -and -not $candidate.exclusion_reason) { $errors.Add("Terminal exclusion missing reason: $($candidate.id)") }
  if ($candidate.status -in @('implemented','validated') -and -not $candidate.implementation_location) { $errors.Add("Implemented item missing location: $($candidate.id)") }
  if ($candidate.status -eq 'validated' -and $candidate.r2_url -and -not $candidate.source_url) { $errors.Add("R2-only item incorrectly marked validated without authoritative provenance: $($candidate.id)") }
  $locations = @($candidate.implementation_locations | Where-Object { $_ } | Sort-Object -Unique)
  if ($locations.Count -gt 1 -and -not $candidate.cross_listing_approved) { $errors.Add("Unapproved multiple-page placement: $($candidate.id) = $($locations -join ', ')") }
}

$linkedUrls = @()
foreach ($file in Get-ChildItem content -Recurse -Filter *.md) {
  $raw = Get-Content -Raw -Encoding UTF8 $file.FullName
  $linkedUrls += [regex]::Matches($raw,'https?://[^\s\)\]]+') | ForEach-Object { $_.Value }
}
foreach ($url in $linkedUrls | Sort-Object -Unique) {
  if (-not ($inventory.candidates | Where-Object { $_.source_url -eq $url -or $_.direct_file_url -eq $url -or $_.r2_url -eq $url })) { $errors.Add("Content URL missing from inventory: $url") }
}

$result = [pscustomobject]@{Candidates=$inventory.candidates.Count;Errors=$errors.Count;Messages=@($errors)}
$result | ConvertTo-Json -Depth 5
if ($errors.Count) { exit 1 }
