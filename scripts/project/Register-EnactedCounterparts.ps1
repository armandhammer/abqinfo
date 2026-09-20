[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$ManifestPath,
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$R2InventoryPath = 'project-state/r2-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-StableId([string]$Value) {
  $bytes = [Text.Encoding]::UTF8.GetBytes($Value.Trim().ToLowerInvariant())
  $sha256 = [Security.Cryptography.SHA256]::Create()
  try { $hex = -join ($sha256.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') }) }
  finally { $sha256.Dispose() }
  'src-' + $hex.Substring(0,16)
}

function Write-AtomicJson($Value, [string]$Path) {
  $fullPath = [IO.Path]::GetFullPath($Path)
  $temporaryPath = "$fullPath.tmp-$PID"
  try {
    [IO.File]::WriteAllText($temporaryPath, ($Value | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
  } finally {
    if (Test-Path -LiteralPath $temporaryPath) { Remove-Item -LiteralPath $temporaryPath -Force }
  }
}

$manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $ManifestPath | ConvertFrom-Json
if ($manifest.artifact_type -ne 'enacted_counterpart_capture') { throw 'Manifest is not an enacted-counterpart capture artifact.' }
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$r2Inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $R2InventoryPath | ConvertFrom-Json
$r2Keys = @{}; foreach ($object in $r2Inventory.objects) { $r2Keys[$object.key] = $true }
$byId = @{}; foreach ($candidate in $inventory.candidates) { $byId[$candidate.id] = $candidate }
$byHash = @{}; foreach ($candidate in $inventory.candidates) { if ($candidate.checksum_sha256) { $byHash[$candidate.checksum_sha256.ToLowerInvariant()] = $candidate.id } }
$now = (Get-Date).ToUniversalTime().ToString('o')

foreach ($item in @($manifest.records | Where-Object capture_status -eq 'captured')) {
  if ($item.file_type -ne 'PDF') { throw "Only PDF enactments are supported: $($item.enactment)" }
  if ($item.size_bytes -le 0 -or $item.checksum_sha256 -notmatch '^[0-9a-f]{64}$' -or $item.page_count -le 0) { throw "Incomplete capture metadata for $($item.enactment)." }
  if ($byHash.ContainsKey($item.checksum_sha256)) { throw "$($item.enactment) collides by SHA-256 with $($byHash[$item.checksum_sha256])." }
  if (@($inventory.candidates | Where-Object r2_key -eq $item.proposed_r2_key).Count) { throw "$($item.enactment) has an existing R2-key collision: $($item.proposed_r2_key)." }
  if ($r2Keys.ContainsKey($item.proposed_r2_key)) { throw "$($item.enactment) has a live-R2-key collision: $($item.proposed_r2_key)." }
  $id = Get-StableId $item.source_url
  if ($byId.ContainsKey($id)) { throw "$($item.enactment) has an existing source-ID collision: $id." }
  $quality = [ordered]@{
    visual_inspection = $item.quality_assessment.visual_inspection
    measured_content = $item.quality_assessment.measured_content
    standalone_public_value = $item.quality_assessment.standalone_public_value
    information_density = $item.quality_assessment.information_density
    series_component_relationship = $item.quality_assessment.series_component_relationship
    intended_publication_form = $item.quality_assessment.intended_publication_form
    rationale = $item.quality_assessment.rationale
  }
  $candidate = [pscustomobject][ordered]@{
    id = $id; status = 'approved for addition'; source_url = $item.source_url; direct_file_url = $item.direct_file_url
    r2_url = $null; r2_key = $null; r2_etag = $null; r2_last_modified = $null; agency = 'City of Albuquerque'
    title = $item.title; date = $item.date; file_type = 'PDF'; size_bytes = [int64]$item.size_bytes; checksum_sha256 = $item.checksum_sha256
    parent_url = $item.source_url; referring_urls = @($item.source_url); discovery_path = @($item.source_url,$item.direct_file_url)
    discovery_method = 'deterministic enacted-counterpart capture'; crawl_depth = $null; cited_predecessors = @($item.held_substitute_source_url)
    cited_successors = @(); provenance_status = "Authoritative final enacted attachment captured from City Legistar; $($item.enactment) and publication date verified against the legislative detail page."
    proposed_canonical_page = $item.proposed_canonical_page; description = $item.description; description_word_count = ($item.description -split '\s+' | Where-Object { $_ }).Count
    processing_notes = @("Final enacted counterpart to $($item.held_substitute_bill) ($($item.held_substitute_id)); captured container has $($item.page_count) pages, $($item.size_bytes) bytes, and SHA-256 $($item.checksum_sha256).", "Archive preparation only: proposed R2 key $($item.proposed_r2_key) was collision-checked against project-state/r2-inventory.json; no R2 upload or public content action is authorized.")
    implementation_location = $null; implementation_locations = @(); cross_listing_approved = $false; validation_status = 'inventory-only final-enactment capture; archive preparation pending authorization'
    exclusion_reason = $null; local_path = $null; discovered_at = $now; updated_at = $now; quality_assessment = [pscustomobject]$quality
  }
  $inventory.candidates = @($inventory.candidates) + $candidate; $byId[$id] = $candidate; $byHash[$item.checksum_sha256] = $id
}
$inventory.candidates = @($inventory.candidates | Sort-Object id)
$counts = [ordered]@{}; foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }; $inventory.counts = [pscustomobject]$counts
$pending = @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned')
$eligible = @($inventory.candidates | Where-Object { $_.status -in $pending -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | ForEach-Object id | Sort-Object)
$inventory.next_pending_id = if ($eligible.Count) { $eligible[0] } else { $null }; $inventory.generated_at = $now
Write-AtomicJson $inventory $InventoryPath
[pscustomobject]@{registered=@($manifest.records|Where-Object capture_status -eq 'captured').Count;counts=$counts;next_pending_id=$inventory.next_pending_id}|ConvertTo-Json -Depth 5
