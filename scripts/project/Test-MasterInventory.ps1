[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$ContentRoot = 'content'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw -Encoding UTF8 $InventoryPath | ConvertFrom-Json
$errors = [Collections.Generic.List[string]]::new()
$ids = @{}
$primaryUrls = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
$provenanceUrls = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)

function Add-HttpUrl([Collections.Generic.HashSet[string]]$Target, $Value) {
  foreach ($item in @($Value)) {
    if ([string]$item -match '^https?://') { [void]$Target.Add([string]$item) }
  }
}

function Test-SupportingIndexUrl([string]$ContentPath, [string]$Url) {
  # The bicycling page contains a compact index of official meeting records.
  # Those links are published source records, not separately described document
  # candidates; keep this exception restricted to that page and URL shape.
  return (
    $ContentPath -eq 'content/transportation/bicycling/_index.md' -and
    $Url -match '^https://onbase\.cabq\.gov/publicaccess/api/Document/\d+/$'
  )
}

foreach ($candidate in $inventory.candidates) {
  Add-HttpUrl $primaryUrls $candidate.source_url
  Add-HttpUrl $primaryUrls $candidate.direct_file_url
  Add-HttpUrl $primaryUrls $candidate.r2_url
  foreach ($field in @('parent_url','referring_urls','discovery_path','discovery_method','crawl_depth','cited_predecessors','cited_successors','provenance_status')) {
    if (-not $candidate.PSObject.Properties[$field]) {
      $errors.Add("Missing discovery/provenance field: $($candidate.id) = $field")
    } elseif ($field -in @('parent_url','referring_urls','discovery_path')) {
      Add-HttpUrl $provenanceUrls $candidate.$field
    }
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
foreach ($file in Get-ChildItem $ContentRoot -Recurse -Filter *.md) {
  $raw = Get-Content -Raw -Encoding UTF8 $file.FullName
  $contentPath = [IO.Path]::GetRelativePath((Get-Location).Path,$file.FullName).Replace('\','/')
  $linkedUrls += [regex]::Matches($raw,'https?://[^\s\)\]]+') | ForEach-Object {
    [pscustomobject]@{Url=$_.Value;ContentPath=$contentPath}
  }
}
$supportingIndexUrls = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach ($group in $linkedUrls | Group-Object Url) {
  $url = [string]$group.Name
  if ($primaryUrls.Contains($url) -or $provenanceUrls.Contains($url)) { continue }
  $onlySupportingIndexOccurrences = @($group.Group | Where-Object {
    Test-SupportingIndexUrl $_.ContentPath $_.Url
  }).Count -eq @($group.Group).Count
  if ($onlySupportingIndexOccurrences) {
    [void]$supportingIndexUrls.Add($url)
    continue
  }
  $errors.Add("Content URL missing from inventory: $url")
}

$result = [pscustomobject]@{
  Candidates = $inventory.candidates.Count
  ContentUrls = @($linkedUrls.Url | Sort-Object -Unique).Count
  InventoryPrimaryUrls = $primaryUrls.Count
  InventoryProvenanceUrls = $provenanceUrls.Count
  SupportingIndexUrls = $supportingIndexUrls.Count
  Errors = $errors.Count
  Messages = @($errors)
}
$result | ConvertTo-Json -Depth 5
if ($errors.Count) { exit 1 }
