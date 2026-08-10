[CmdletBinding()]
param(
  [string]$SeedUrl = 'https://www.cabq.gov/bikes/biking-in-abq',
  [string]$RobotsUrl = 'https://www.cabq.gov/robots.txt',
  [string]$UrlMatchPattern = '(?i)^https://www\.cabq\.gov/parksandrecreation/documents/DRAFT%20Bikeways%20-%20Trails%20Master%20Plan(?:%20Appendices)?%2011-10-11\.pdf$|^https://www\.cabq\.gov/parksandrecreation/documents/DRAFT%20Bikeways%20-%20Trails%20Master%20Plan%20Design%20Guidelines%2011-10\.pdf$',
  [int]$MaxSitemaps = 10,
  [int]$MaxCandidates = 10,
  [string]$OutputPath = 'project-state/discovery/cabq-robots-sitemap-bicycle-history-crawl.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Sha256Text([string]$Text) {
  $sha = [Security.Cryptography.SHA256]::Create()
  try {
    $bytes = [Text.Encoding]::UTF8.GetBytes($Text)
    return -join ($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') })
  } finally {
    $sha.Dispose()
  }
}

function Get-XmlResource([string]$Url) {
  $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 60 -SkipHttpErrorCheck
  if ([int]$response.StatusCode -ne 200) { throw "Sitemap request failed with HTTP $([int]$response.StatusCode): $Url" }
  $contentType = [string](@($response.Headers.'Content-Type')[0])
  $bytes = if ($response.Content -is [byte[]]) { [byte[]]$response.Content } else { [Text.Encoding]::UTF8.GetBytes([string]$response.Content) }
  if ($Url -match '(?i)\.gz$' -or $contentType -match '(?i)gzip') {
    $memory = [IO.MemoryStream]::new($bytes)
    $gzip = [IO.Compression.GZipStream]::new($memory, [IO.Compression.CompressionMode]::Decompress)
    $reader = [IO.StreamReader]::new($gzip)
    try { $text = $reader.ReadToEnd() } finally { $reader.Dispose(); $gzip.Dispose(); $memory.Dispose() }
  } else {
    $text = [Text.Encoding]::UTF8.GetString($bytes)
  }
  return [pscustomobject]@{
    url = $Url
    compressed_bytes = $bytes.Length
    text = $text
    text_sha256 = Get-Sha256Text $text
  }
}

function Get-Title([string]$Url) {
  $name = [uri]::UnescapeDataString(([uri]$Url).Segments[-1])
  if ($name -match '(?i)Appendices') { return '2011 Albuquerque Bikeways and Trails Master Plan Update - Appendices' }
  if ($name -match '(?i)Design Guidelines') { return '2011 Albuquerque Bikeways and Trails Master Plan Update - Design Guidelines' }
  return '2011 Albuquerque Bikeways and Trails Master Plan Update'
}

$robotsResponse = Invoke-WebRequest -Uri $RobotsUrl -UseBasicParsing -TimeoutSec 60 -SkipHttpErrorCheck
if ([int]$robotsResponse.StatusCode -ne 200) { throw "robots.txt request failed with HTTP $([int]$robotsResponse.StatusCode): $RobotsUrl" }
$robotsText = [string]$robotsResponse.Content
$indexUrls = @([regex]::Matches($robotsText, '(?im)^Sitemap:\s*(?<url>https?://\S+)\s*$') | ForEach-Object { $_.Groups['url'].Value.Trim() } | Sort-Object -Unique)
if (-not $indexUrls.Count) { throw "No Sitemap directive found in $RobotsUrl" }

$sitemapQueue = [Collections.Generic.Queue[object]]::new()
foreach ($url in $indexUrls) { $sitemapQueue.Enqueue([pscustomobject]@{ url=$url; parent=$RobotsUrl }) }
$visited = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$shards = [Collections.Generic.List[object]]::new()
$selected = [Collections.Generic.List[object]]::new()
$allUrlCount = 0

while ($sitemapQueue.Count -gt 0) {
  if ($visited.Count -ge $MaxSitemaps) { throw "Sitemap limit reached before the queue was exhausted (MaxSitemaps=$MaxSitemaps)." }
  $queued = $sitemapQueue.Dequeue()
  if (-not $visited.Add([string]$queued.url)) { continue }
  $resource = Get-XmlResource ([string]$queued.url)
  [xml]$xml = $resource.text
  $rootName = $xml.DocumentElement.LocalName
  if ($rootName -eq 'sitemapindex') {
    foreach ($child in @($xml.sitemapindex.sitemap)) {
      $sitemapQueue.Enqueue([pscustomobject]@{ url=[string]$child.loc; parent=[string]$queued.url })
    }
    $shards.Add([ordered]@{
      url = [string]$queued.url
      parent_url = [string]$queued.parent
      kind = 'sitemap index'
      compressed_bytes = [int64]$resource.compressed_bytes
      decompressed_characters = $resource.text.Length
      url_count = 0
      child_sitemap_count = @($xml.sitemapindex.sitemap).Count
      decompressed_sha256 = $resource.text_sha256
    })
    continue
  }
  if ($rootName -ne 'urlset') { throw "Unsupported sitemap root '$rootName': $([string]$queued.url)" }

  $entries = @($xml.urlset.url)
  $allUrlCount += $entries.Count
  $shards.Add([ordered]@{
    url = [string]$queued.url
    parent_url = [string]$queued.parent
    kind = 'URL set'
    compressed_bytes = [int64]$resource.compressed_bytes
    decompressed_characters = $resource.text.Length
    url_count = $entries.Count
    child_sitemap_count = 0
    decompressed_sha256 = $resource.text_sha256
  })

  foreach ($entry in $entries) {
    $candidateUrl = [string]$entry.loc
    if ($candidateUrl -notmatch $UrlMatchPattern) { continue }
    if ($selected.Count -ge $MaxCandidates) { throw "Candidate limit reached (MaxCandidates=$MaxCandidates)." }
    $head = Invoke-WebRequest -Uri $candidateUrl -Method Head -UseBasicParsing -TimeoutSec 60 -SkipHttpErrorCheck
    $lengthValue = @($head.Headers.'Content-Length')[0]
    $selected.Add([ordered]@{
      url = $candidateUrl
      direct_file_url = $candidateUrl
      anchor_text = Get-Title $candidateUrl
      title = Get-Title $candidateUrl
      date = if ($candidateUrl -match '11-10-11') { '2011-11-10' } else { '2011-11' }
      agency = 'City of Albuquerque'
      file_type = 'PDF'
      size_bytes = if ($lengthValue) { [int64]$lengthValue } else { $null }
      http_status = [int]$head.StatusCode
      content_type = [string](@($head.Headers.'Content-Type')[0])
      sitemap_last_modified = [string]$entry.lastmod
      parent_url = [string]$queued.url
      referring_urls = @($RobotsUrl, [string]$queued.parent, [string]$queued.url)
      discovery_path = @($SeedUrl, $RobotsUrl, [string]$queued.parent, [string]$queued.url, $candidateUrl)
      discovery_method = 'robots-advertised XML sitemap enumeration'
      discovery_depth = 4
      provenance_status = 'official City robots-declared sitemap entry and live City file'
      processing_notes = @(
        'Recovered by enumerating the complete robots-declared City sitemap before applying the bounded 2011 plan-family selection filter.',
        "Live authoritative file returned HTTP $([int]$head.StatusCode) with exact Content-Length $lengthValue bytes."
      )
    })
  }
}

$output = [ordered]@{
  agency = 'City of Albuquerque'
  source_url = $SeedUrl
  scope = 'bounded robots-declared sitemap recovery of the 2011 bicycle-plan document family'
  retrieved_at = (Get-Date).ToUniversalTime().ToString('o')
  robots_url = $RobotsUrl
  robots_sha256 = Get-Sha256Text $robotsText
  sitemap_directives = @($indexUrls)
  selection_applied_after_complete_enumeration = $true
  enumerated_sitemap_count = $visited.Count
  enumerated_url_count = $allUrlCount
  candidate_limit = $MaxCandidates
  shards = @($shards)
  candidates = @($selected | Sort-Object url)
}

$output | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $OutputPath -Encoding utf8
$output | ConvertTo-Json -Depth 6 -Compress
