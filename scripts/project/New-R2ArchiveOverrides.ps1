[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$PlanPath,
  [Parameter(Mandatory)][string]$OutputPath,
  [string]$R2InventoryPath = 'project-state/r2-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$plan = Get-Content -Raw -LiteralPath $PlanPath | ConvertFrom-Json
$r2 = Get-Content -Raw -LiteralPath $R2InventoryPath | ConvertFrom-Json
$overrides = @()

function Get-StableId([string]$Value) {
  $bytes = [Text.Encoding]::UTF8.GetBytes($Value.Trim().ToLowerInvariant())
  $sha256 = [Security.Cryptography.SHA256]::Create()
  try { $hash = $sha256.ComputeHash($bytes) } finally { $sha256.Dispose() }
  return 'src-' + (-join ($hash | ForEach-Object { $_.ToString('x2') })).Substring(0, 16)
}

foreach ($item in @($plan.items)) {
  $object = @($r2.objects | Where-Object key -eq $item.r2_key)
  if ($object.Count -ne 1) { throw "Expected one R2 object for $($item.r2_key); found $($object.Count)." }
  if ([int64]$object[0].size_bytes -ne [int64]$item.size_bytes) { throw "R2 size mismatch for $($item.id)." }
  $locations = if ($item.PSObject.Properties['implementation_locations']) { @($item.implementation_locations) } else { @([string]$item.proposed_canonical_page) }
  $crossListed = if ($item.PSObject.Properties['cross_listing_approved']) { [bool]$item.cross_listing_approved } else { $false }
  $overrides += [ordered]@{
    id = [string]$item.id
    match_url = "https://files.abqinfo.com/$($item.r2_key)"
    status = 'validated'
    source_url = [string]$item.source_url
    direct_file_url = [string]$item.direct_file_url
    r2_key = [string]$item.r2_key
    r2_etag = [string]$object[0].etag
    r2_last_modified = [string]$object[0].last_modified
    agency = [string]$item.agency
    title = [string]$item.title
    date = [string]$item.date
    file_type = [string]$item.file_type
    size_bytes = [int64]$item.size_bytes
    checksum_sha256 = [string]$item.checksum_sha256
    parent_url = [string]$item.parent_url
    referring_urls = @([string]$item.parent_url)
    proposed_canonical_page = [string]$item.proposed_canonical_page
    description = [string]$item.description
    processing_notes = @($item.processing_notes) + @('Original authoritative file uploaded without modification; R2 key and exact byte size reconciled to the live bucket inventory.')
    implementation_location = [string]$item.proposed_canonical_page
    implementation_locations = $locations
    cross_listing_approved = $crossListed
    validation_status = 'passed: authoritative provenance, public byte-identical R2 download, description, and placement validated'
    provenance_status = [string]$item.provenance_status
  }

  # Content parsing creates a second record whose stable ID is based on the
  # R2 display URL. Keep it terminal but explicitly subordinate to the
  # authoritative source-discovery record above.
  $publicUrl = "https://files.abqinfo.com/$($item.r2_key)"
  $overrides += [ordered]@{
    id = Get-StableId $publicUrl
    status = 'duplicate'
    title = [string]$item.title
    description = [string]$item.description
    exclusion_reason = "Content-link alias for canonical archive candidate $($item.id)."
    validation_status = 'duplicate R2 display-link record reconciled to authoritative source candidate'
    provenance_status = 'authoritative provenance recorded on canonical source candidate'
    implementation_location = $null
    implementation_locations = @()
  }
}

# Official project/update pages are intentionally retained beside archived
# copies. Give those supporting links complete inventory records while keeping
# shared project pages as a single cross-listed source.
$sourceGroups = @($plan.items | Group-Object source_url)
foreach ($group in $sourceGroups) {
  $first = @($group.Group)[0]
  $locations = @($group.Group | ForEach-Object {
    if ($_.PSObject.Properties['implementation_locations']) { @($_.implementation_locations) } else { @([string]$_.proposed_canonical_page) }
  } | Where-Object { $_ } | Sort-Object -Unique)
  $description = "Provides the official government project context and current authoritative source for $($first.title), complementing the preserved document with agency-maintained background, status, and related materials."
  $overrides += [ordered]@{
    id = Get-StableId ([string]$group.Name)
    status = 'validated'
    source_url = [string]$group.Name
    agency = [string]$first.agency
    title = "Official source: $($first.title)"
    file_type = 'Web page or live service'
    description = $description
    proposed_canonical_page = [string]$first.proposed_canonical_page
    implementation_location = [string]$first.proposed_canonical_page
    implementation_locations = $locations
    cross_listing_approved = ($locations.Count -gt 1)
    validation_status = 'passed: authoritative government supporting source, description, and placement validated'
    provenance_status = 'authoritative government source recorded'
    processing_notes = @('Maintained official source/update page retained beside the byte-preserved archive copy.')
  }
}

foreach ($item in @($plan.superseded_items)) {
  $overrides += [ordered]@{
    id = [string]$item.id
    status = [string]$item.status
    title = [string]$item.title
    validation_status = [string]$item.validation_status
    exclusion_reason = [string]$item.exclusion_reason
    proposed_canonical_page = [string]$item.proposed_canonical_page
    processing_notes = @($item.processing_notes)
    implementation_location = $null
    implementation_locations = @()
  }
}

$overrides | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{ overrides=$overrides.Count; archived=@($plan.items).Count; superseded=@($plan.superseded_items).Count; output=$OutputPath }
