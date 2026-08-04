[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OverridesPath = 'project-state/inventory-overrides.json',
  [switch]$Rebuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$allowedStatuses = @(
  'pending review', 'approved for addition', 'downloading', 'downloaded',
  'parsed', 'description drafted', 'placement assigned', 'implemented',
  'validated', 'excluded', 'duplicate', 'superseded', 'blocked',
  'requires human review'
)

function Get-StableId([string]$Value) {
  $normalized = $Value.Trim().ToLowerInvariant()
  $bytes = [Text.Encoding]::UTF8.GetBytes($normalized)
  $sha256 = [Security.Cryptography.SHA256]::Create()
  try { $hash = $sha256.ComputeHash($bytes) } finally { $sha256.Dispose() }
  $hex = -join ($hash | ForEach-Object { $_.ToString('x2') })
  return 'src-' + $hex.Substring(0, 16)
}

function Get-Agency([string]$Url) {
  if ($Url -match 'cabq\.gov|abq-zone\.com') { return 'City of Albuquerque' }
  if ($Url -match 'bernco\.gov') { return 'Bernalillo County' }
  if ($Url -match 'mrcog-nm\.gov|mrcogshare\.org|riometro\.org') { return 'MRCOG' }
  if ($Url -match 'dot\.nm\.gov|nmroads\.com|stipviewer') { return 'NMDOT' }
  if ($Url -match 'files\.abqinfo\.com') { return 'Unreconciled archived source' }
  return 'Other authoritative source'
}

function Get-FileType([string]$Url) {
  $path = ([uri]$Url).AbsolutePath.ToLowerInvariant()
  if ($path.EndsWith('.pdf')) { return 'PDF' }
  if ($path.EndsWith('.docx')) { return 'DOCX' }
  if ($path.EndsWith('.xlsx')) { return 'XLSX' }
  if ($path.EndsWith('.csv')) { return 'CSV' }
  if ($Url -match '/MapServer|arcgis') { return 'ArcGIS service' }
  return 'Web page or live service'
}

function Get-PlainText([string]$Value) {
  $text = $Value -replace '\[(.*?)\]\(.*?\)', '$1'
  $text = $text -replace '[*_`#>]', ''
  return ($text -replace '\s+', ' ').Trim()
}

function Get-WordCount([AllowNull()][string]$Value) {
  if ([string]::IsNullOrWhiteSpace($Value)) { return 0 }
  return @($Value -split '\s+' | Where-Object { $_ }).Count
}

function Get-NormalizedDiscoveryUrl([string]$Url) {
  try {
    $builder = [UriBuilder]$Url
    $builder.Fragment = ''
    if ([string]::IsNullOrWhiteSpace($builder.Query) -or $builder.Query -eq '?') { $builder.Query = '' }
    if ($builder.Host -ieq 'nmroads.com' -and $builder.Path -match '(?i)^/mapIndex\.html$') { $builder.Path = '/' }
    return $builder.Uri.AbsoluteUri.TrimEnd('/')
  } catch { return $Url.Trim().TrimEnd('/') }
}

function Get-RecordUrls($Record) {
  return @($Record.source_url, $Record.direct_file_url, $Record.r2_url) |
    Where-Object { $_ -and $_ -match '^https?://' } |
    ForEach-Object { Get-NormalizedDiscoveryUrl ([string]$_) } |
    Sort-Object -Unique
}

function Test-DiscoveryCandidate([string]$Agency, [string]$Url) {
  try { $uri = [uri]$Url } catch { return $false }
  if ($uri.Scheme -notin @('http','https')) { return $false }
  $uriHost = $uri.Host.ToLowerInvariant()
  $path = $uri.AbsolutePath
  if ($path -match '^/(accessibility|copyright|privacy|sitemap|search|quicklinks\.aspx|directory\.aspx|calendar\.aspx|bids\.aspx)/?$') { return $false }
  if ($path -match '(?i)(\+\+resource\+\+|/image-repository/|/images?/|\.svg$|\.png$|\.jpe?g$|\.gif$|\.webp$)') { return $false }
  switch ($Agency.ToLowerInvariant()) {
    'cabq' { return $uriHost -match '(^|\.)(cabq\.gov|abq-zone\.com)$' }
    'bernco' { return $uriHost -match '(^|\.)(bernco\.gov)$' }
    'mrcog' { return $uriHost -match '(^|\.)(mrcog-nm\.gov|mrcogshare\.org|mrcogmaps\.org|riometro\.org|arcgis\.com)$' }
    'nmdot' { return $uriHost -match '(^|\.)(dot\.nm\.gov|nmroads\.com|pmgpro\.com|rtsclients\.com)$' }
    default { return $false }
  }
}

function Get-DiscoveryTitle([string]$Url, [AllowNull()][string]$AnchorText) {
  if (-not [string]::IsNullOrWhiteSpace($AnchorText)) { return Get-PlainText $AnchorText }
  try {
    $segment = [uri]::UnescapeDataString(([uri]$Url).Segments[-1].Trim('/'))
    if ($segment) { return (($segment -replace '[-_]',' ') -replace '\s+',' ').Trim() }
  } catch {}
  return 'Title pending source review'
}

function Get-PropertyValue($Object, [string]$Name) {
  $property = $Object.PSObject.Properties[$Name]
  if ($null -eq $property) { return $null }
  return $property.Value
}

function New-Record([string]$Url, [string]$Title, [string]$Status) {
  $now = (Get-Date).ToUniversalTime().ToString('o')
  return [ordered]@{
    id = Get-StableId $Url
    status = $Status
    source_url = if ($Url -match 'files\.abqinfo\.com') { $null } else { $Url }
    direct_file_url = if ((Get-FileType $Url) -in @('PDF','DOCX','XLSX','CSV')) { $Url } else { $null }
    r2_url = if ($Url -match 'files\.abqinfo\.com') { $Url } else { $null }
    r2_key = $null
    r2_etag = $null
    r2_last_modified = $null
    agency = Get-Agency $Url
    title = $Title
    date = $null
    file_type = Get-FileType $Url
    size_bytes = $null
    checksum_sha256 = $null
    proposed_canonical_page = $null
    description = $null
    description_word_count = 0
    processing_notes = @()
    implementation_location = $null
    implementation_locations = @()
    cross_listing_approved = $false
    validation_status = 'not run'
    exclusion_reason = $null
    local_path = $null
    discovered_at = $now
    updated_at = $now
  }
}

$records = @{}
if (-not $Rebuild -and (Test-Path -LiteralPath $InventoryPath)) {
  $prior = Get-Content -Raw $InventoryPath | ConvertFrom-Json
  foreach ($record in $prior.candidates) {
    $copy = [ordered]@{}
    foreach ($property in $record.PSObject.Properties) { $copy[$property.Name] = $property.Value }
    $records[$copy.id] = $copy
  }
}

# Placement is derived from the current Hugo tree on every import. Clearing the
# cached values prevents moved or removed links from surviving as phantom
# cross-listings in the durable inventory.
foreach ($record in $records.Values) {
  $record.implementation_location = $null
  $record.implementation_locations = @()
}

function Merge-Record([System.Collections.IDictionary]$Incoming) {
  $id = $Incoming.id
  if (-not $records.ContainsKey($id)) { $records[$id] = $Incoming; return }
  $existing = $records[$id]
  if ($existing.status -eq 'pending review' -and $existing.title -match '(?i)^(visit the project page|click here|here)(\b|\.)' -and $Incoming.title) {
    $existing.title = $Incoming.title
  }
  if ($Incoming.implementation_location) {
    $locations = @($existing.implementation_locations) + @($existing.implementation_location) + @($Incoming.implementation_location)
    $existing.implementation_locations = @($locations | Where-Object { $_ } | Sort-Object -Unique)
  }
  if ($Incoming.description) {
    $existing.description = $Incoming.description
    $existing.description_word_count = $Incoming.description_word_count
  }
  if ($Incoming.status -eq 'implemented' -and $existing.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned')) {
    $existing.status = 'implemented'
  }
  foreach ($key in $Incoming.Keys) {
    if (-not $existing.Contains($key) -or $null -eq $existing[$key] -or $existing[$key] -eq '' -or ($existing[$key] -is [array] -and $existing[$key].Count -eq 0)) {
      $existing[$key] = $Incoming[$key]
    }
  }
}

foreach ($file in Get-ChildItem content -Recurse -Filter *.md) {
  $lines = Get-Content $file.FullName
  for ($index = 0; $index -lt $lines.Count; $index++) {
    $matches = [regex]::Matches($lines[$index], '\[(?<title>[^\]]+)\]\((?<url>https?://[^\)\s]+)\)')
    foreach ($match in $matches) {
      $url = $match.Groups['url'].Value
      $record = New-Record $url (Get-PlainText $match.Groups['title'].Value) 'implemented'
      $record.implementation_location = $file.FullName.Substring((Get-Location).Path.Length + 1).Replace('\','/')
      $record.implementation_locations = @($record.implementation_location)
      $record.proposed_canonical_page = $record.implementation_location
      $baseIndent = ([regex]::Match($lines[$index], '^\s*')).Value.Length
      for ($next = $index + 1; $next -lt [Math]::Min($lines.Count, $index + 6); $next++) {
        if ([string]::IsNullOrWhiteSpace($lines[$next])) { continue }
        $nextIndent = ([regex]::Match($lines[$next], '^\s*')).Value.Length
        if ($lines[$next] -match '\]\(https?://') { break }
        if ($nextIndent -le $baseIndent -and $lines[$next] -match '^\s*[-*+#]') { break }
        $candidateDescription = Get-PlainText ($lines[$next] -replace '^\s*[-*+]\s+', '')
        if ($candidateDescription -and $candidateDescription -notmatch '^#') {
          $record.description = $candidateDescription
          $record.description_word_count = Get-WordCount $candidateDescription
          break
        }
      }
      Merge-Record $record
    }
  }
}

if (Test-Path -LiteralPath 'project-state/r2-inventory.json') {
  $r2Inventory = Get-Content -Raw 'project-state/r2-inventory.json' | ConvertFrom-Json
  foreach ($object in $r2Inventory.objects) {
    $record = New-Record ([string]$object.public_url) ([IO.Path]::GetFileNameWithoutExtension([string]$object.key) -replace '[-_]',' ') 'requires human review'
    $record.r2_key = [string]$object.key
    $record.r2_etag = [string]$object.etag
    $record.r2_last_modified = [string]$object.last_modified
    $record.size_bytes = [int64]$object.size_bytes
    $record.processing_notes = @('Existing R2 object is not linked from current content or has not yet been reconciled to its authoritative source URL.')
    Merge-Record $record
  }
}

$legacyPaths = @('research/audit/discovery-candidates.json','research/audit/nmdot-discovery.json')
foreach ($legacyPath in $legacyPaths) {
  if (-not (Test-Path -LiteralPath $legacyPath)) { continue }
  $legacy = Get-Content -Raw $legacyPath | ConvertFrom-Json
  $items = @()
  foreach ($collectionName in @('candidates','deferred_candidates','candidate_documents','authoritative_live_sources')) {
    $collection = Get-PropertyValue $legacy $collectionName
    if ($collection) { $items += $collection }
  }
  foreach ($item in $items) {
    $sourceUrl = Get-PropertyValue $item 'source_url'
    $pageUrl = Get-PropertyValue $item 'url'
    $url = if ($sourceUrl) { [string]$sourceUrl } elseif ($pageUrl) { [string]$pageUrl } else { continue }
    $record = New-Record $url ([string](Get-PropertyValue $item 'title')) 'pending review'
    $bytes = Get-PropertyValue $item 'bytes'
    $fileType = Get-PropertyValue $item 'file_type'
    $placement = Get-PropertyValue $item 'proposed_placement'
    $reason = Get-PropertyValue $item 'reason'
    $projectPage = Get-PropertyValue $item 'project_page'
    if ($bytes) { $record.size_bytes = [int64]$bytes }
    if ($fileType) { $record.file_type = [string]$fileType }
    if ($placement) { $record.proposed_canonical_page = [string]$placement }
    if ($reason) { $record.processing_notes = @([string]$reason) }
    if ($projectPage) { $record.source_url = [string]$projectPage; $record.direct_file_url = $url }
    Merge-Record $record
  }
}

foreach ($discoveryFile in Get-ChildItem 'research/discovery' -Filter '*-links.json' -File -ErrorAction SilentlyContinue) {
  $discovery = Get-Content -Raw -LiteralPath $discoveryFile.FullName | ConvertFrom-Json
  $agencyName = [string](Get-PropertyValue $discovery 'agency')
  $crawlSource = [string](Get-PropertyValue $discovery 'source_url')
  if ($crawlSource -and (Test-DiscoveryCandidate $agencyName $crawlSource)) {
    $normalizedSource = Get-NormalizedDiscoveryUrl $crawlSource
    $sourceRecord = New-Record $normalizedSource (Get-DiscoveryTitle $normalizedSource $null) 'pending review'
    $sourceRecord.processing_notes = @('User-selected scoped crawl starting page.', 'Page and authored main-content links were captured by the deterministic crawler.')
    Merge-Record $sourceRecord
  }
  $candidateItems = @(Get-PropertyValue $discovery 'candidates')
  if (-not $candidateItems.Count) {
    $candidateItems = @((Get-PropertyValue $discovery 'links') | ForEach-Object { [pscustomobject]@{url=$_;anchor_text=$null} })
  }
  foreach ($candidateItem in $candidateItems) {
    $rawUrl = [string](Get-PropertyValue $candidateItem 'url')
    if (-not $rawUrl -or -not (Test-DiscoveryCandidate $agencyName $rawUrl)) { continue }
    $url = Get-NormalizedDiscoveryUrl $rawUrl
    $anchorText = [string](Get-PropertyValue $candidateItem 'anchor_text')
    $record = New-Record $url (Get-DiscoveryTitle $url $anchorText) 'pending review'
    $record.processing_notes = @("Discovered by deterministic crawl of $crawlSource.", 'Exact metadata and relevance remain pending source review.')
    Merge-Record $record
  }
}

foreach ($file in Get-ChildItem research/staging -Recurse -Filter *.pdf -ErrorAction SilentlyContinue) {
  $match = $records.Values | Where-Object {
    ($_.r2_url -and ([uri]$_.r2_url).Segments[-1] -eq $file.Name) -or
    ($_.direct_file_url -and ([uri]$_.direct_file_url).Segments[-1] -eq $file.Name)
  } | Select-Object -First 1
  if ($match) {
    $match.local_path = $file.FullName.Substring((Get-Location).Path.Length + 1).Replace('\','/')
    $match.size_bytes = $file.Length
    $match.checksum_sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  } else {
    $record = New-Record ('local:' + $file.Name) $file.BaseName 'downloaded'
    $record.source_url = $null
    $record.direct_file_url = $null
    $record.file_type = 'PDF'
    $record.local_path = $file.FullName.Substring((Get-Location).Path.Length + 1).Replace('\','/')
    $record.size_bytes = $file.Length
    $record.checksum_sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $record.processing_notes = @('Staged file was not yet reconciled to a source URL.')
    Merge-Record $record
  }
}

if (Test-Path -LiteralPath $OverridesPath) {
  $overrides = Get-Content -Raw $OverridesPath | ConvertFrom-Json
  foreach ($override in $overrides) {
    $overrideId = Get-PropertyValue $override 'id'
    $matchUrl = Get-PropertyValue $override 'match_url'
    $match = $records.Values | Where-Object {
      ($overrideId -and $_.id -eq $overrideId) -or
      ($matchUrl -and ($_.r2_url -eq $matchUrl -or $_.direct_file_url -eq $matchUrl -or $_.source_url -eq $matchUrl))
    } | Select-Object -First 1
    if (-not $match) { continue }
    foreach ($property in $override.PSObject.Properties) {
      if ($property.Name -in @('match_url','id')) { continue }
      if ($property.Name -eq 'status' -and $match.status -eq 'validated' -and $property.Value -eq 'implemented') { continue }
      $match[$property.Name] = $property.Value
    }
    $match.description_word_count = Get-WordCount $match.description
  }
}

foreach ($pending in @($records.Values | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') })) {
    $pendingUrls = @(Get-RecordUrls $pending)
    $canonical = $records.Values | Where-Object {
        $canonicalUrls = @(Get-RecordUrls $_)
        $_.id -ne $pending.id -and
        $_.status -in @('implemented','validated') -and
        ((@($canonicalUrls | Where-Object { $_ -in $pendingUrls }).Count -gt 0) -or
         ($_.direct_file_url -and ($_.direct_file_url -eq $pending.direct_file_url -or $_.direct_file_url -eq $pending.source_url)) -or
         ($_.checksum_sha256 -and $pending.checksum_sha256 -and $_.checksum_sha256 -eq $pending.checksum_sha256))
    } | Select-Object -First 1

    if ($canonical) {
        $pending.status = 'duplicate'
        $pending.exclusion_reason = "Duplicate discovery record for implemented candidate $($canonical.id)."
        $pending.validation_status = 'duplicate discovery confirmed'
        $pending.updated_at = (Get-Date).ToUniversalTime().ToString('o')
    }
}

foreach ($record in $records.Values) {
  if ($record.status -eq 'pending review' -and $record.title -match '(?i)^(visit the project page|click here|here)(\b|\.)' -and $record.source_url) {
    try {
      $segments = @(([uri]$record.source_url).Segments)
      $slug = $segments[$segments.Count - 1].TrimEnd('/')
      if (-not $slug -and $segments.Count -gt 1) { $slug = $segments[$segments.Count - 2].TrimEnd('/') }
      if ($slug) {
        $record.title = (Get-Culture).TextInfo.ToTitleCase((([uri]::UnescapeDataString($slug) -replace '[-_]',' ') -replace '\s+',' ').Trim())
      }
    } catch {}
  }
  if ($record.status -notin $allowedStatuses) { throw "Invalid status '$($record.status)' for $($record.id)." }
  if ($record.status -eq 'validated' -and (-not $record.description -or $record.description_word_count -lt 20 -or $record.description_word_count -gt 50)) {
    $record.status = 'implemented'
  }
  if ($record.status -eq 'implemented') {
    if (-not $record.implementation_locations -and $record.implementation_location) { $record.implementation_locations = @($record.implementation_location) }
    if ($record.description -and $record.description_word_count -ge 20 -and $record.description_word_count -le 50) {
      $record.validation_status = 'pending full validation'
    } else {
      $record.validation_status = 'description missing or outside 20-50 words'
    }
  }
}

$directory = Split-Path -Parent $InventoryPath
if ($directory) { New-Item -ItemType Directory -Force $directory | Out-Null }
$sorted = @($records.Values | Sort-Object { [string]$_['id'] })
$counts = [ordered]@{}
foreach ($status in $allowedStatuses) { $counts[$status] = @($sorted | Where-Object status -eq $status).Count }
$nextCandidates = @($sorted | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | Select-Object -First 1)
$output = [ordered]@{
  schema_version = 1
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  allowed_statuses = $allowedStatuses
  counts = $counts
  next_pending_id = if ($nextCandidates.Count) { $nextCandidates[0].id } else { $null }
  candidates = $sorted
}
$output | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $InventoryPath -Encoding utf8
$output.counts | ConvertTo-Json -Compress
