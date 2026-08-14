[CmdletBinding()]
param(
  [string]$SeedUrl = 'https://www.cabq.gov/municipaldevelopment/documents',
  [string]$OutputPath = 'project-state/discovery/cabq-dmd-document-library-crawl.json',
  [ValidateRange(5,120)][int]$RequestTimeoutSeconds = 30,
  [ValidateRange(0,5)][int]$MaxRetries = 2,
  [ValidateRange(1,5000)][int]$MaxCollectionPages = 2000,
  [switch]$Resume
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$seedUri = [uri]$SeedUrl
$libraryPrefix = $seedUri.AbsolutePath.TrimEnd('/') + '/'
$filePattern = '(?i)\.(pdf|docx?|xlsx?|xls|csv|txt|rtf|zip|kml|kmz|shp|json|xml|png|jpe?g|gif|tiff?|svg)(?:/view)?$'

function Get-StableId([string]$Value) {
  $normalized = $Value.Trim().TrimEnd('/').ToLowerInvariant()
  $bytes = [Text.Encoding]::UTF8.GetBytes($normalized)
  $sha256 = [Security.Cryptography.SHA256]::Create()
  try { $hash = $sha256.ComputeHash($bytes) } finally { $sha256.Dispose() }
  $hex = -join ($hash | ForEach-Object { $_.ToString('x2') })
  return 'src-' + $hex.Substring(0,16)
}

function Get-NormalizedUrl([string]$Url, [uri]$BaseUri = $null) {
  try {
    $uri = if ($BaseUri) { [uri]::new($BaseUri,$Url) } else { [uri]$Url }
    if ($uri.Scheme -notin @('http','https')) { return $null }
    $builder = [UriBuilder]$uri
    $builder.Fragment = ''
    $pairs = @($builder.Query.TrimStart('?') -split '&' | Where-Object { $_ -match '^b_start:int=\d+$' })
    $builder.Query = $pairs -join '&'
    return $builder.Uri.AbsoluteUri.TrimEnd('/')
  } catch { return $null }
}

function Get-PlainText([AllowNull()][string]$Html) {
  if ([string]::IsNullOrWhiteSpace($Html)) { return '' }
  $text = $Html -replace '(?is)<(script|style|noscript)\b.*?</\1>',' '
  $text = $text -replace '(?is)<[^>]+>',' '
  return (([Net.WebUtility]::HtmlDecode($text)) -replace '\s+',' ').Trim()
}

function Get-DirectFileUrl([string]$Url) {
  return ($Url -replace '(?i)/view$','').TrimEnd('/')
}

function Get-FileType([string]$Url, [AllowNull()][string]$ContentType) {
  $path = ([uri]$Url).AbsolutePath -replace '(?i)/view$',''
  $extension = [IO.Path]::GetExtension($path).TrimStart('.').ToUpperInvariant()
  if ($extension) {
    if ($extension -eq 'JPG') { return 'JPEG' }
    if ($extension -eq 'TIF') { return 'TIFF' }
    return $extension
  }
  if ($ContentType -match '(?i)application/pdf') { return 'PDF' }
  return 'Web page or live service'
}

function Invoke-WithRetry([string]$Url, [ValidateSet('Get','Head')][string]$Method) {
  $lastError = $null
  for ($attempt = 1; $attempt -le ($MaxRetries + 1); $attempt++) {
    try {
      return Invoke-WebRequest -Uri $Url -Method $Method -UseBasicParsing -MaximumRedirection 10 -TimeoutSec $RequestTimeoutSeconds
    } catch {
      $lastError = $_
      $retryable = $_.Exception.Message -match '(?i)(timed? out|unable to connect|connection.*(closed|reset)|HTTP.*429|HTTP.*5\d\d|\(429\)|\(5\d\d\))'
      if (-not $retryable -or $attempt -gt $MaxRetries) { break }
      Start-Sleep -Milliseconds (250 * $attempt)
    }
  }
  throw $lastError
}

function Get-CollectionEntries([string]$Html, [uri]$BaseUri) {
  $mainMatch = [regex]::Match($Html,'(?is)<main\b[^>]*>(?<content>.*?)</main>')
  $region = if ($mainMatch.Success) { $mainMatch.Groups['content'].Value } else { $Html }
  $entries = [Collections.Generic.List[object]]::new()

  foreach ($article in [regex]::Matches($region,'(?is)<article\b[^>]*>(?<article>.*?)</article>')) {
    $articleHtml = $article.Groups['article'].Value
    $link = [regex]::Match($articleHtml,'(?is)<a\b(?<attrs>[^>]*?)href\s*=\s*(?<q>["''])(?<href>.*?)\k<q>(?<tail>[^>]*)>(?<text>.*?)</a>')
    if (-not $link.Success) { continue }
    $url = Get-NormalizedUrl ([Net.WebUtility]::HtmlDecode($link.Groups['href'].Value)) $BaseUri
    if (-not $url) { continue }
    $uri = [uri]$url
    if ($uri.Host -ine $seedUri.Host -or -not $uri.AbsolutePath.StartsWith($libraryPrefix,[StringComparison]::OrdinalIgnoreCase)) { continue }
    $classText = "$($link.Groups['attrs'].Value) $($link.Groups['tail'].Value)"
    $typeMatch = [regex]::Match($classText,'(?i)contenttype-(?<type>[a-z0-9_-]+)')
    $descriptionMatch = [regex]::Match($articleHtml,'(?is)<p\b[^>]*>(?<description>.*?)</p>')
    $entries.Add([pscustomobject]@{
      url = $url
      title = Get-PlainText $link.Groups['text'].Value
      listing_description = if ($descriptionMatch.Success) { Get-PlainText $descriptionMatch.Groups['description'].Value } else { '' }
      collection_item_type = if ($typeMatch.Success) { $typeMatch.Groups['type'].Value.ToLowerInvariant() } else { 'unknown' }
    })
  }

  $pagination = foreach ($link in [regex]::Matches($region,'(?is)<a\b[^>]*?href\s*=\s*(?<q>["''])(?<href>.*?)\k<q>[^>]*>')) {
    $url = Get-NormalizedUrl ([Net.WebUtility]::HtmlDecode($link.Groups['href'].Value)) $BaseUri
    if (-not $url) { continue }
    $uri = [uri]$url
    if ($uri.Host -ieq $seedUri.Host -and $uri.AbsolutePath.TrimEnd('/') -ieq $BaseUri.AbsolutePath.TrimEnd('/') -and $uri.Query -match 'b_start:int=\d+') {
      $url
    }
  }

  return [pscustomobject]@{
    entries = @($entries | Sort-Object url -Unique)
    pagination = @($pagination | Sort-Object -Unique)
  }
}

function Save-State {
  $directory = Split-Path -Parent $OutputPath
  if ($directory) { New-Item -ItemType Directory -Force $directory | Out-Null }
  $files = @($candidateMap.Values | Where-Object { $_.direct_file_url })
  $state = [ordered]@{
    schema_version = 1
    agency = 'cabq'
    source_url = $SeedUrl
    seed_urls = @($SeedUrl)
    collection_scope = 'Every item recursively listed beneath the City of Albuquerque Municipal Development document library; relevance is evaluated after enumeration.'
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    frontier = @($frontier.ToArray())
    visited_urls = @($visited.Keys | Sort-Object)
    pages = @($pages)
    candidates = @($candidateMap.Values | Sort-Object url)
    links = @($candidateMap.Values | ForEach-Object url | Sort-Object -Unique)
    counts = [ordered]@{
      collection_pages = $pages.Count
      candidates = $candidateMap.Count
      files = $files.Count
      exact_size_recorded = @($files | Where-Object { $null -ne $_.size_bytes }).Count
      metadata_failures = @($files | Where-Object { $_.metadata_error }).Count
      over_25_mib = @($files | Where-Object { $null -ne $_.size_bytes -and [int64]$_.size_bytes -gt 25MB }).Count
      over_100_mb = @($files | Where-Object { $null -ne $_.size_bytes -and [int64]$_.size_bytes -gt 100000000 }).Count
    }
  }
  $json = $state | ConvertTo-Json -Depth 14
  $temporaryPath = "$OutputPath.tmp.$PID"
  $json | Set-Content -LiteralPath $temporaryPath -Encoding utf8
  if (Test-Path -LiteralPath $OutputPath) {
    $outputFullPath = [IO.Path]::GetFullPath($OutputPath)
    $backupFullPath = "$outputFullPath.bak.$PID"
    [IO.File]::Replace([IO.Path]::GetFullPath($temporaryPath),$outputFullPath,$backupFullPath)
    if ([IO.File]::Exists($backupFullPath)) { [IO.File]::Delete($backupFullPath) }
  } else {
    Move-Item -LiteralPath $temporaryPath -Destination $OutputPath
  }
}

$frontier = [Collections.Generic.Queue[object]]::new()
$queued = @{}
$visited = @{}
$candidateMap = @{}
$pages = [Collections.Generic.List[object]]::new()

if ($Resume -and (Test-Path -LiteralPath $OutputPath)) {
  $prior = Get-Content -Raw -LiteralPath $OutputPath | ConvertFrom-Json
  foreach ($url in @($prior.visited_urls)) { $visited[[string]$url] = $true }
  foreach ($candidate in @($prior.candidates)) { $candidateMap[[string]$candidate.id] = $candidate }
  foreach ($page in @($prior.pages)) { $pages.Add($page) }
  foreach ($item in @($prior.frontier)) {
    $frontier.Enqueue($item)
    $queued[([string]$item.url).TrimEnd('/')] = $true
  }
  $normalizedSeed = Get-NormalizedUrl $SeedUrl
  $seedKey = $normalizedSeed.TrimEnd('/')
  if (-not $visited.ContainsKey($seedKey) -and -not $queued.ContainsKey($seedKey)) {
    $frontier.Enqueue([pscustomobject]@{url=$normalizedSeed;parent_url=$null;depth=0;discovery_path=@($normalizedSeed)})
    $queued[$seedKey] = $true
  }
} else {
  $normalizedSeed = Get-NormalizedUrl $SeedUrl
  $frontier.Enqueue([pscustomobject]@{url=$normalizedSeed;parent_url=$null;depth=0;discovery_path=@($normalizedSeed)})
  $queued[$normalizedSeed] = $true
}

while ($frontier.Count -and $pages.Count -lt $MaxCollectionPages) {
  $item = $frontier.Dequeue()
  $key = ([string]$item.url).TrimEnd('/')
  if ($visited.ContainsKey($key)) { continue }
  $pageRecord = [ordered]@{
    url = [string]$item.url
    parent_url = $item.parent_url
    depth = [int]$item.depth
    discovery_path = @($item.discovery_path)
    status = 'pending'
    http_status = $null
    title = $null
    item_count = 0
    pagination_count = 0
    error = $null
  }
  try {
    $response = Invoke-WithRetry -Url ([string]$item.url) -Method Get
    $pageRecord.http_status = [int]$response.StatusCode
    $heading = [regex]::Match([string]$response.Content,'(?is)<h1\b[^>]*>(?<title>.*?)</h1>')
    if ($heading.Success) { $pageRecord.title = Get-PlainText $heading.Groups['title'].Value }
    $parsed = Get-CollectionEntries -Html ([string]$response.Content) -BaseUri ([uri]$item.url)
    $pageRecord.item_count = @($parsed.entries).Count
    $pageRecord.pagination_count = @($parsed.pagination).Count
    $pageRecord.status = 'retrieved'

    foreach ($pageUrl in @($parsed.pagination)) {
      $pageKey = $pageUrl.TrimEnd('/')
      if (-not $visited.ContainsKey($pageKey) -and -not $queued.ContainsKey($pageKey)) {
        $frontier.Enqueue([pscustomobject]@{url=$pageUrl;parent_url=$item.url;depth=[int]$item.depth;discovery_path=@($item.discovery_path)+$pageUrl})
        $queued[$pageKey] = $true
      }
    }

    foreach ($entry in @($parsed.entries)) {
      $entryUri = [uri]$entry.url
      $isFile = $entry.url -match $filePattern -or $entry.collection_item_type -in @('file','image')
      $canonicalUrl = if ($isFile) { Get-DirectFileUrl $entry.url } else { $entry.url }
      $id = Get-StableId $canonicalUrl
      $directFileUrl = if ($isFile) { $canonicalUrl } else { $null }
      $fileType = if ($isFile) { Get-FileType -Url $canonicalUrl -ContentType $null } else { 'Web page or live service' }
      $sizeBytes = $null
      $contentType = $null
      $httpStatus = $null
      $metadataError = $null
      if ($isFile) {
        try {
          $head = Invoke-WithRetry -Url $canonicalUrl -Method Head
          $httpStatus = [int]$head.StatusCode
          $contentType = [string]@($head.Headers['Content-Type'])[0]
          $length = [string]@($head.Headers['Content-Length'])[0]
          if ($length -match '^\d+$') { $sizeBytes = [int64]$length }
          if ($fileType -eq 'Web page or live service') { $fileType = Get-FileType -Url $canonicalUrl -ContentType $contentType }
        } catch {
          $metadataError = $_.Exception.Message
        }
      }

      if (-not $candidateMap.ContainsKey($id)) {
        $candidateMap[$id] = [pscustomobject][ordered]@{
          id = $id
          url = $canonicalUrl
          source_url = if ($isFile) { $entry.url } else { $canonicalUrl }
          direct_file_url = $directFileUrl
          parent_url = [string]$item.url
          referring_urls = @([string]$item.url)
          discovery_path = @($item.discovery_path) + $entry.url
          discovery_method = 'exhaustive Plone collection enumeration'
          discovery_depth = [int]$item.depth + 1
          agency = 'City of Albuquerque'
          title = if ($entry.title) { [string]$entry.title } else { [IO.Path]::GetFileNameWithoutExtension($entryUri.AbsolutePath) }
          date = $null
          file_type = $fileType
          size_bytes = $sizeBytes
          checksum_sha256 = $null
          listing_description = [string]$entry.listing_description
          description = $null
          proposed_canonical_page = $null
          collection_item_type = [string]$entry.collection_item_type
          http_status = $httpStatus
          content_type = $contentType
          metadata_error = $metadataError
          provenance_status = 'official City Plone document-library listing and direct item URL recorded'
          processing_notes = @(
            'Enumerated without a relevance-name filter from the Municipal Development document library.'
            if ($null -ne $sizeBytes) { "Exact authoritative-source size: $sizeBytes bytes." } else { "Exact size unavailable during cataloging: $metadataError" }
          )
        }
      } else {
        $candidate = $candidateMap[$id]
        $candidate.referring_urls = @(@($candidate.referring_urls) + [string]$item.url | Sort-Object -Unique)
        if (@($item.discovery_path).Count + 1 -lt @($candidate.discovery_path).Count) {
          $candidate.parent_url = [string]$item.url
          $candidate.discovery_path = @($item.discovery_path) + $entry.url
          $candidate.discovery_depth = [int]$item.depth + 1
        }
      }

      if (-not $isFile) {
        $childKey = $canonicalUrl.TrimEnd('/')
        if (-not $visited.ContainsKey($childKey) -and -not $queued.ContainsKey($childKey)) {
          $frontier.Enqueue([pscustomobject]@{url=$canonicalUrl;parent_url=$item.url;depth=([int]$item.depth+1);discovery_path=@($item.discovery_path)+$canonicalUrl})
          $queued[$childKey] = $true
        }
      }
      # Persist after each enumerated item so exact-size and provenance work is
      # resumable even if the run ends before the containing page is finished.
      Save-State
    }
  } catch {
    $pageRecord.status = 'error'
    $pageRecord.error = $_.Exception.Message
  }
  $visited[$key] = $true
  $pages.Add([pscustomobject]$pageRecord)
  Save-State
}

Save-State
$files = @($candidateMap.Values | Where-Object { $_.direct_file_url })
[pscustomobject]@{
  CollectionPages = $pages.Count
  Candidates = $candidateMap.Count
  Files = $files.Count
  ExactSizes = @($files | Where-Object { $null -ne $_.size_bytes }).Count
  MetadataFailures = @($files | Where-Object { $_.metadata_error }).Count
  Remaining = $frontier.Count
  OutputPath = $OutputPath
} | ConvertTo-Json -Compress
