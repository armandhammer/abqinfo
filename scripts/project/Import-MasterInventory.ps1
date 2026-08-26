[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OverridesPath = 'project-state/inventory-overrides.json',
  [string]$QualityExclusionsPath = 'project-state/quality-exclusions.json',
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
  if ($Url -match 'mrcog-nm\.gov|mrcogshare\.org|riometro\.org|mrmpo\.nm\.tipviewer\.pmgpro\.com') { return 'MRCOG' }
  if ($Url -match 'dot\.nm\.gov|nmroads\.com|stipviewer') { return 'NMDOT' }
  if ($Url -match 'upgradeunserpaseo\.com') { return 'City of Albuquerque / New Mexico Department of Transportation' }
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
  $isDmdLibraryItem = $path -match '(?i)^/municipaldevelopment/documents/'
  if ($path -match '(?i)(\+\+resource\+\+|/image-repository/|/images?/|\.svg$|\.png$|\.jpe?g$|\.gif$|\.webp$)' -and -not $isDmdLibraryItem) { return $false }
  switch ($Agency.ToLowerInvariant()) {
    'cabq' { return $uriHost -match '(^|\.)(cabq\.gov|abq-zone\.com|arcgis\.com)$' }
    'bernco' { return $uriHost -match '(^|\.)(bernco\.gov)$' }
    'mrcog' { return $uriHost -match '(^|\.)(mrcog-nm\.gov|mrcogshare\.org|mrcogmaps\.org|riometro\.org|arcgis\.com|nm\.tipviewer\.pmgpro\.com)$' }
    'nmdot' { return $uriHost -match '(^|\.)(dot\.nm\.gov|nmroads\.com|pmgpro\.com|rtsclients\.com|upgradeunserpaseo\.com)$' }
    'rio metro / nmrx / regional rail' { return $uriHost -match '(^|\.)(riometro\.org|mrcog-nm\.gov|dot\.nm\.gov|rtsclients\.com|arcgis\.com)$' }
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
    parent_url = $null
    referring_urls = @()
    discovery_path = @()
    discovery_method = $null
    crawl_depth = $null
    cited_predecessors = @()
    cited_successors = @()
    provenance_status = if ($Url -match 'files\.abqinfo\.com') { 'unreconciled archived copy' } else { 'source URL recorded' }
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
  $prior = Get-Content -Raw -Encoding UTF8 $InventoryPath | ConvertFrom-Json
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
    $incomingDescriptionValid = $Incoming.description_word_count -ge 20 -and $Incoming.description_word_count -le 50
    $existingDescriptionValid = $existing.description_word_count -ge 20 -and $existing.description_word_count -le 50
    if ($incomingDescriptionValid -or -not $existingDescriptionValid) {
      $existing.description = $Incoming.description
      $existing.description_word_count = $Incoming.description_word_count
    }
  }
  if ($Incoming.referring_urls) {
    $existing.referring_urls = @(@(Get-PropertyValue $existing 'referring_urls') + @($Incoming.referring_urls) | Where-Object { $_ } | Sort-Object -Unique)
  }
  $existingPath = @(Get-PropertyValue $existing 'discovery_path')
  if ($Incoming.discovery_path -and (-not $existingPath.Count -or @($Incoming.discovery_path).Count -lt $existingPath.Count)) {
    $existing.discovery_path = @($Incoming.discovery_path)
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
  $lines = Get-Content -Encoding UTF8 $file.FullName
  for ($index = 0; $index -lt $lines.Count; $index++) {
    $matches = [regex]::Matches($lines[$index], '\[(?<title>[^\]]+)\]\((?<url>https?://[^\)\s]+)\)')
    foreach ($match in $matches) {
      $url = $match.Groups['url'].Value
      $record = New-Record $url (Get-PlainText $match.Groups['title'].Value) 'implemented'
      $record.implementation_location = $file.FullName.Substring((Get-Location).Path.Length + 1).Replace('\','/')
      $record.implementation_locations = @($record.implementation_location)
      $record.proposed_canonical_page = $record.implementation_location
      $baseIndent = ([regex]::Match($lines[$index], '^\s*')).Value.Length

      # A source-of-truth link embedded at the end of an item's prose inherits
      # that item's description. Keep only the prose before the first link so
      # labels such as "Official City PDF" are not counted as description text.
      $inlineProse = Get-PlainText (($lines[$index] -split '\[[^\]]+\]\(https?://', 2)[0] -replace '^\s*[-*+]\s+', '')
      if ((Get-WordCount $inlineProse) -ge 20 -and (Get-WordCount $inlineProse) -le 50) {
        $record.description = $inlineProse
        $record.description_word_count = Get-WordCount $inlineProse
      }
      for ($next = $index + 1; $next -lt [Math]::Min($lines.Count, $index + 6); $next++) {
        if ([string]::IsNullOrWhiteSpace($lines[$next])) { continue }
        $nextIndent = ([regex]::Match($lines[$next], '^\s*')).Value.Length
        if ($nextIndent -le $baseIndent -and $lines[$next] -match '^\s*[-*+#]') { break }
        $candidateDescription = Get-PlainText ((($lines[$next] -split '\[[^\]]+\]\(https?://', 2)[0]) -replace '^\s*[-*+]\s+', '')
        $candidateWords = Get-WordCount $candidateDescription
        if ($candidateDescription -and $candidateDescription -notmatch '^#' -and $candidateWords -ge 20 -and $candidateWords -le 50) {
          $record.description = $candidateDescription
          $record.description_word_count = $candidateWords
          break
        }
      }
      if (-not $record.description) {
        for ($previous = $index - 1; $previous -ge [Math]::Max(0, $index - 6); $previous--) {
          if ([string]::IsNullOrWhiteSpace($lines[$previous])) { continue }
          if ($lines[$previous] -match '^\s*#') { break }
          $candidateDescription = Get-PlainText ((($lines[$previous] -split '\[[^\]]+\]\(https?://', 2)[0]) -replace '^\s*[-*+]\s+', '')
          $candidateWords = Get-WordCount $candidateDescription
          if ($candidateWords -ge 20 -and $candidateWords -le 50) {
            $record.description = $candidateDescription
            $record.description_word_count = $candidateWords
            break
          }
          if ($lines[$previous] -match '^\s*[-*+]\s+\[') { break }
        }
      }
      Merge-Record $record
    }
  }
}

if (Test-Path -LiteralPath 'project-state/r2-inventory.json') {
  $r2Inventory = Get-Content -Raw -Encoding UTF8 'project-state/r2-inventory.json' | ConvertFrom-Json
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
  $legacy = Get-Content -Raw -Encoding UTF8 $legacyPath | ConvertFrom-Json
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

$excludedDiscoveryFiles = @{}
$discoveryImportExclusionsPath = 'project-state/discovery/import-exclusions.json'
if (Test-Path -LiteralPath $discoveryImportExclusionsPath) {
  foreach ($item in (Get-Content -Raw -Encoding UTF8 -LiteralPath $discoveryImportExclusionsPath | ConvertFrom-Json)) {
    $excludedDiscoveryFiles[[string]$item.file] = [string]$item.reason
  }
}
$discoveryFiles = @(
  Get-ChildItem 'research/discovery' -Filter '*-links.json' -File -ErrorAction SilentlyContinue
  Get-ChildItem 'project-state/discovery' -Filter '*-crawl.json' -File -ErrorAction SilentlyContinue
) | Where-Object { -not $excludedDiscoveryFiles.ContainsKey($_.Name) }
foreach ($discoveryFile in $discoveryFiles) {
  $discovery = Get-Content -Raw -Encoding UTF8 -LiteralPath $discoveryFile.FullName | ConvertFrom-Json
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
    $candidateId = [string](Get-PropertyValue $candidateItem 'id')
    if ($candidateId) { $record.id = $candidateId }
    $record.processing_notes = @("Discovered by deterministic crawl of $crawlSource.", 'Exact metadata and relevance remain pending source review.')
    $candidateAgency = [string](Get-PropertyValue $candidateItem 'agency')
    $candidateFileType = [string](Get-PropertyValue $candidateItem 'file_type')
    $candidateDirectFileUrl = [string](Get-PropertyValue $candidateItem 'direct_file_url')
    $candidateSourceUrl = [string](Get-PropertyValue $candidateItem 'source_url')
    $candidateSizeBytes = Get-PropertyValue $candidateItem 'size_bytes'
    $candidateProvenance = [string](Get-PropertyValue $candidateItem 'provenance_status')
    $candidateNotes = @(Get-PropertyValue $candidateItem 'processing_notes')
    $candidateDate = [string](Get-PropertyValue $candidateItem 'date')
    $candidateDescription = [string](Get-PropertyValue $candidateItem 'description')
    $candidateCanonicalPage = [string](Get-PropertyValue $candidateItem 'proposed_canonical_page')
    if ($candidateAgency) { $record.agency = $candidateAgency }
    if ($candidateFileType) { $record.file_type = $candidateFileType }
    if ($candidateSourceUrl) { $record.source_url = $candidateSourceUrl }
    if ($candidateDirectFileUrl) { $record.direct_file_url = $candidateDirectFileUrl }
    if ($null -ne $candidateSizeBytes) { $record.size_bytes = [long]$candidateSizeBytes }
    if ($candidateProvenance) { $record.provenance_status = $candidateProvenance }
    if ($candidateNotes.Count) { $record.processing_notes = @($record.processing_notes) + $candidateNotes }
    if ($candidateDate) { $record.date = $candidateDate }
    if ($candidateDescription) {
      $record.description = $candidateDescription
      $record.description_word_count = Get-WordCount $candidateDescription
    }
    if ($candidateCanonicalPage) { $record.proposed_canonical_page = $candidateCanonicalPage }
    $parentUrl = Get-PropertyValue $candidateItem 'parent_url'
    $referringUrls = Get-PropertyValue $candidateItem 'referring_urls'
    $discoveryPath = Get-PropertyValue $candidateItem 'discovery_path'
    $discoveryMethod = Get-PropertyValue $candidateItem 'discovery_method'
    $crawlDepth = Get-PropertyValue $candidateItem 'discovery_depth'
    if ($parentUrl) { $record.parent_url = [string]$parentUrl }
    if ($referringUrls) { $record.referring_urls = @($referringUrls) } elseif ($parentUrl) { $record.referring_urls = @([string]$parentUrl) }
    if ($discoveryPath) { $record.discovery_path = @($discoveryPath) }
    if ($discoveryMethod) { $record.discovery_method = [string]$discoveryMethod }
    if ($null -ne $crawlDepth) { $record.crawl_depth = [int]$crawlDepth }
    Merge-Record $record
  }
}

$lineagePath = 'project-state/discovery/pdf-lineage-references.json'
if (Test-Path -LiteralPath $lineagePath) {
  $lineage = Get-Content -Raw -Encoding UTF8 -LiteralPath $lineagePath | ConvertFrom-Json
  foreach ($reference in @($lineage.references)) {
    $record = New-Record ("https://lineage.invalid/{0}" -f $reference.id) ([string]$reference.referenced_title) 'pending review'
    $record.id = [string]$reference.id
    $record.source_url = $null
    $record.direct_file_url = $null
    $record.agency = [string]$reference.agency
    $record.date = $reference.referenced_date
    $record.file_type = [string]$reference.file_type
    $record.parent_url = [string]$reference.parent_url
    $record.referring_urls = @($reference.referring_urls)
    $record.discovery_path = @($reference.discovery_path)
    $record.discovery_method = [string]$reference.discovery_method
    $record.crawl_depth = $reference.crawl_depth
    $record.processing_notes = @($reference.processing_notes) + @("Lineage relation: $($reference.relation).", "Evidence: $($reference.evidence)")
    $record.provenance_status = 'named in an in-scope source; authoritative file not yet located'
    Merge-Record $record

    if ([string]$reference.relation -match '(?i)^(combined and updated|replaces|previous plan|maintained from)$' -and
        [string]$reference.referenced_title -notmatch '(?i)^(the |previous |2024 plan$)') {
      $sourceRecord = $records[[string]$reference.source_candidate_id]
      if ($sourceRecord) {
        $label = [string]$reference.referenced_title
        if ($reference.referenced_date) { $label += " ($($reference.referenced_date))" }
        $sourceRecord.cited_predecessors = @(@($sourceRecord.cited_predecessors) + $label | Where-Object { $_ } | Sort-Object -Unique)
      }
    }
  }
}

$stagingCandidateByPath = @{}
if (Test-Path -LiteralPath 'project-state/staging-manifest.json') {
  foreach ($item in (Get-Content -Raw -Encoding UTF8 -LiteralPath 'project-state/staging-manifest.json' | ConvertFrom-Json)) {
    $stagingCandidateByPath[([string]$item.local_path).Replace('\','/')] = [string]$item.candidate_id
  }
}
foreach ($file in Get-ChildItem research/staging -Recurse -Filter *.pdf -ErrorAction SilentlyContinue) {
  $relativeStagingPath = $file.FullName.Substring((Get-Location).Path.Length + 1).Replace('\','/')
  $manifestCandidateId = if ($stagingCandidateByPath.ContainsKey($relativeStagingPath)) { $stagingCandidateByPath[$relativeStagingPath] } else { $null }
  $match = $records.Values | Where-Object {
    ($manifestCandidateId -and $_.id -eq $manifestCandidateId) -or
    $_.id -eq $file.BaseName -or
    ($_.r2_url -and ([uri]$_.r2_url).Segments[-1] -eq $file.Name) -or
    ($_.direct_file_url -and ([uri]$_.direct_file_url).Segments[-1] -eq $file.Name)
  } | Select-Object -First 1
  if ($match) {
    $match.local_path = $relativeStagingPath
    $match.size_bytes = $file.Length
    $match.checksum_sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($match.status -in @('pending review','approved for addition','downloading')) { $match.status = 'downloaded' }
  } else {
    $record = New-Record ('local:' + $file.Name) $file.BaseName 'downloaded'
    $record.source_url = $null
    $record.direct_file_url = $null
    $record.file_type = 'PDF'
    $record.local_path = $relativeStagingPath
    $record.size_bytes = $file.Length
    $record.checksum_sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $record.processing_notes = @('Staged file was not yet reconciled to a source URL.')
    Merge-Record $record
  }
}

$overridePaths = @($OverridesPath)
$overridePaths += @(Get-ChildItem 'project-state/discovery' -Filter '*-overrides.json' -File -ErrorAction SilentlyContinue | ForEach-Object FullName)
foreach ($overridePath in @($overridePaths | Where-Object { Test-Path -LiteralPath $_ } | Sort-Object -Unique)) {
  $overrides = Get-Content -Raw -Encoding UTF8 -LiteralPath $overridePath | ConvertFrom-Json
  foreach ($override in @($overrides)) {
    $overrideId = Get-PropertyValue $override 'id'
    $matchUrl = Get-PropertyValue $override 'match_url'
    # A stable ID is authoritative when supplied. Falling through to a URL
    # match only when that ID is absent prevents a content-derived R2 alias
    # from receiving metadata intended for its source-discovery record.
    $match = if ($overrideId) {
      $records.Values | Where-Object { $_.id -eq $overrideId } | Select-Object -First 1
    } else { $null }
    if (-not $match -and $matchUrl) {
      $match = $records.Values | Where-Object {
        $_.r2_url -eq $matchUrl -or $_.direct_file_url -eq $matchUrl -or $_.source_url -eq $matchUrl
      } | Select-Object -First 1
    }
    if (-not $match) { continue }
    foreach ($property in $override.PSObject.Properties) {
      if ($property.Name -in @('match_url','id')) { continue }
      if ($property.Name -eq 'status' -and $match.status -eq 'validated' -and $property.Value -eq 'implemented') { continue }
      $match[$property.Name] = $property.Value
    }
    $match.description_word_count = Get-WordCount $match.description
  }
}

# User-approved quality exclusions are applied after ordinary metadata overrides so
# broad recrawls cannot silently re-promote material deliberately removed from the site.
if (Test-Path -LiteralPath $QualityExclusionsPath) {
  $qualityExclusions = Get-Content -Raw -Encoding UTF8 $QualityExclusionsPath | ConvertFrom-Json
  foreach ($exclusion in $qualityExclusions) {
    $matchUrl = ([string](Get-PropertyValue $exclusion 'url')).TrimEnd('/')
    if (-not $matchUrl) { continue }
    foreach ($match in @($records.Values | Where-Object {
      @($_.r2_url,$_.direct_file_url,$_.source_url) |
        Where-Object { $_ -and ([string]$_).TrimEnd('/') -eq $matchUrl }
    })) {
      $match.status = 'excluded'
      $match.validation_status = 'user-approved quality exclusion'
      $match.exclusion_reason = [string](Get-PropertyValue $exclusion 'reason')
      $match.implementation_location = $null
      $match.implementation_locations = @()
      $match.updated_at = (Get-Date).ToUniversalTime().ToString('o')
    }
  }
}

# A content link to an R2 URL and its provenance-rich discovery record may have
# different stable IDs. Consolidate their placement onto the best documented
# record so the archive is represented once without losing authoritative-source
# metadata, checksums, or validated state.
$r2Groups = @($records.Values | Where-Object r2_url | Group-Object r2_url | Where-Object Count -gt 1)
foreach ($group in $r2Groups) {
  $members = @($group.Group)
  $aliases = @($members | Where-Object {
    -not $_.source_url -and -not $_.checksum_sha256 -and -not $_.local_path -and
    $_.provenance_status -eq 'unreconciled archived copy'
  })
  $documented = @($members | Where-Object { $_.id -notin @($aliases.id) })
  if (-not $aliases.Count -or -not $documented.Count) { continue }
  $locations = @($members | ForEach-Object { @($_.implementation_locations) + @($_.implementation_location) } | Where-Object { $_ } | Sort-Object -Unique)
  foreach ($canonical in $documented) {
    if ($locations.Count) {
      $canonical.implementation_locations = $locations
      $canonical.implementation_location = $locations[0]
      $canonical.proposed_canonical_page = $locations[0]
      if ($canonical.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned')) {
        $canonical.status = 'implemented'
      }
    }
    if ($members | Where-Object cross_listing_approved) { $canonical.cross_listing_approved = $true }
  }
  $preferredCanonical = @($documented | Sort-Object @{Expression={ if ($_.status -eq 'validated') { 0 } else { 1 } }}, id | Select-Object -First 1)[0]
  foreach ($alias in $aliases) {
    if ($alias.status -notin @('excluded','superseded','blocked')) {
      $alias.status = 'duplicate'
      $alias.exclusion_reason = "Duplicate R2 representation of canonical candidate $($preferredCanonical.id)."
      $alias.validation_status = 'duplicate archive representation consolidated'
      $alias.implementation_location = $null
      $alias.implementation_locations = @()
      $alias.updated_at = (Get-Date).ToUniversalTime().ToString('o')
    }
  }
}

$canonicalByUrl = @{}
$canonicalByChecksum = @{}
foreach ($canonicalRecord in @($records.Values | Where-Object { $_.status -in @('implemented','validated') })) {
  foreach ($canonicalUrl in @(Get-RecordUrls $canonicalRecord)) {
    if (-not $canonicalByUrl.ContainsKey($canonicalUrl)) { $canonicalByUrl[$canonicalUrl] = $canonicalRecord }
  }
  if ($canonicalRecord.checksum_sha256 -and -not $canonicalByChecksum.ContainsKey([string]$canonicalRecord.checksum_sha256)) {
    $canonicalByChecksum[[string]$canonicalRecord.checksum_sha256] = $canonicalRecord
  }
}

foreach ($pending in @($records.Values | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') })) {
    $canonical = $null
    foreach ($pendingUrl in @(Get-RecordUrls $pending)) {
      if ($canonicalByUrl.ContainsKey($pendingUrl)) { $canonical = $canonicalByUrl[$pendingUrl]; break }
    }
    if (-not $canonical -and $pending.checksum_sha256 -and $canonicalByChecksum.ContainsKey([string]$pending.checksum_sha256)) {
      $canonical = $canonicalByChecksum[[string]$pending.checksum_sha256]
    }

    if ($canonical -and $canonical.id -ne $pending.id) {
        $pending.status = 'duplicate'
        $pending.exclusion_reason = "Duplicate discovery record for implemented candidate $($canonical.id)."
        $pending.validation_status = 'duplicate discovery confirmed'
        $pending.updated_at = (Get-Date).ToUniversalTime().ToString('o')
    }
}

foreach ($record in $records.Values) {
  foreach ($field in @('parent_url','discovery_method','crawl_depth')) {
    if (-not $record.Contains($field)) { $record[$field] = $null }
  }
  foreach ($field in @('referring_urls','discovery_path','cited_predecessors','cited_successors')) {
    if (-not $record.Contains($field)) { $record[$field] = @() }
  }
  if (-not $record.Contains('provenance_status')) { $record.provenance_status = 'not assessed' }
  if ($record.r2_url -and -not $record.source_url) {
    $record.provenance_status = 'unreconciled archived copy'
    if ($record.status -eq 'validated') {
      $record.status = 'requires human review'
      $record.validation_status = 'R2 link passed; authoritative government provenance unreconciled'
      $record.updated_at = (Get-Date).ToUniversalTime().ToString('o')
    }
  } elseif ($record.source_url -and $record.source_url -match '(?i)(cabq\.gov|bernco\.gov|mrcog-nm\.gov|dot\.nm\.gov|legistar\.com|amlegal\.com)' -and
    $record.provenance_status -in @('not assessed','source URL recorded','unreconciled archived copy','authoritative government source recorded')) {
    $record.provenance_status = 'authoritative government source recorded'
  }
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
