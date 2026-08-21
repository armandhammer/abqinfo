[CmdletBinding()]
param(
  [string]$SourcePath = 'research/staging/document-review/Buena Vista Roll Plot_NEW.pdf',
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$DecisionsPath = 'project-state/buena-vista-roll-plot-decisions-2026-08-21.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-StableId([string]$Value) {
  $bytes = [Text.Encoding]::UTF8.GetBytes($Value.Trim().ToLowerInvariant())
  $hash = [Security.Cryptography.SHA256]::HashData($bytes)
  return 'src-' + (-join ($hash | ForEach-Object { $_.ToString('x2') })).Substring(0,16)
}

$file = Get-Item -LiteralPath $SourcePath
$checksum = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
$id = Get-StableId "user-contributed:$($file.Name):$checksum"
$title = 'Buena Vista Bike Boulevard Project Roll Plot (2026)'
$description = 'Provides an August 2026 aerial roll plot of the Buena Vista Bike Boulevard from Gibson Boulevard to Central Avenue, identifying proposed signs, pavement markings, speed cushions, crossings, signals, parking restrictions, and pavement work.'
$officialContext = 'https://onbase.cabq.gov/publicaccess/api/Document/12239706/'
$page = 'content/transportation/bicycling/projects/_index.md'
$key = 'transportation/bicycling/projects/cabq-buena-vista-bike-boulevard-roll-plot-2026.pdf'

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$matches = @($inventory.candidates | Where-Object id -eq $id)
if ($matches.Count -gt 1) { throw "Duplicate inventory ID '$id'." }
if ($matches.Count -eq 0) {
  $now = (Get-Date).ToUniversalTime().ToString('o')
  $record = [pscustomobject][ordered]@{
    id=$id; status='parsed'; source_url=$officialContext; direct_file_url=$null
    r2_url='https://files.abqinfo.com/'+$key; r2_key=$key; r2_etag=$null; r2_last_modified=$null
    agency='City of Albuquerque Department of Municipal Development'; title=$title; date='2026-08-18'; file_type='PDF'
    size_bytes=[int64]$file.Length; checksum_sha256=$checksum; parent_url=$officialContext
    referring_urls=@($officialContext); discovery_path=@($officialContext,"user-contributed:$($file.Name)")
    discovery_method='User-contributed document review with official project-context reconciliation'; crawl_depth=$null
    cited_predecessors=@('Buena Vista Bike Boulevard 60% Plans'); cited_successors=@()
    provenance_status='Official City GAATC records corroborate the active Buena Vista Bike Boulevard project, but the exact August 2026 roll plot is user-contributed and no authoritative direct file URL has been recovered'
    proposed_canonical_page=$page; description=$description
    description_word_count=@($description -split '\s+' | Where-Object { $_ }).Count
    processing_notes=@('One-page aerial roll plot created August 18, 2026.','PDF metadata identifies NMDOT Survey & Lands Engineering and Autodesk Civil 3D 2024.','Representative full-sheet rendering and extracted labels reviewed; exact size and SHA-256 recorded.','Exact-file provenance remains unresolved, so the terminal inventory status must remain requires human review after archival and site validation.')
    implementation_location=$null; implementation_locations=@(); cross_listing_approved=$false
    validation_status='local PDF text and full-sheet rendering reviewed; exact size and SHA-256 recorded; R2 upload pending'
    exclusion_reason=$null; local_path=$file.FullName.Substring((Get-Location).Path.Length+1).Replace('\','/')
    discovered_at=$now; updated_at=$now
  }
  $inventory.candidates = @($inventory.candidates) + $record | Sort-Object id
} else {
  $record = $matches[0]
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$json = $inventory | ConvertTo-Json -Depth 12
$fullPath = [IO.Path]::GetFullPath($InventoryPath)
$temporaryPath = "$fullPath.tmp-$PID"
[IO.File]::WriteAllText($temporaryPath,$json,[Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force

[ordered]@{
  batch_id='2026-08-21-buena-vista-roll-plot'
  decisions=@([ordered]@{
    id=$id; title=$title; date='2026-08-18'; r2_key=$key; canonical_page=$page
    source_page=$officialContext; direct_file_url=''; agency='City of Albuquerque Department of Municipal Development'
    description=$description; decision='include with provenance warning; requires human review'
    provenance_status=$record.provenance_status; processing_notes=@($record.processing_notes)
  })
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $DecisionsPath -Encoding utf8

[pscustomobject]@{Id=$id;Bytes=$file.Length;Checksum=$checksum;DecisionsPath=$DecisionsPath}|ConvertTo-Json -Compress
