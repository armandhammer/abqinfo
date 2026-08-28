[CmdletBinding()]
param(
  [Parameter(Mandatory)][ValidateSet('cabq','bernco','mrcog','nmdot')][string]$Agency,
  [Parameter(Mandatory)][string]$StartUrl,
  [Parameter(Mandatory)][string]$PathPrefix,
  [string]$OutputPath = "research/discovery/$Agency-section-links.json",
  [ValidateRange(0,8)][int]$MaxDepth = 3,
  [ValidateRange(1,1000)][int]$MaxPages = 200,
  [string]$ExcludePathPattern = '(?i)/(events?|news|calendar|contact|jobs?|liquor-hearings|administration-questions-answers)(/|$)',
  [string[]]$RecognizedPublishingHosts = @(),
  [string]$RelevantOutboundPattern = '',
  [bool]$CaptureRelevantOutboundLinks = $true,
  [switch]$Resume
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/Discovery.Common.ps1"

if (-not $RecognizedPublishingHosts.Count) {
  $RecognizedPublishingHosts = @(Get-DefaultRecognizedPublishingHosts)
}
if ([string]::IsNullOrWhiteSpace($RelevantOutboundPattern)) {
  $RelevantOutboundPattern = Get-DefaultDiscoveryRelevantPattern
}

$documentPattern = '(?i)\.(pdf|docx?|xlsx?|csv|zip|kml|kmz|shp)(?:/view)?(?:$|[?#])'
$start = [uri]$StartUrl
$queue = [Collections.Generic.Queue[object]]::new()
$queue.Enqueue([pscustomobject]@{url=$start.AbsoluteUri;depth=0;parent_url=$null;path=@($start.AbsoluteUri);method='user seed'})
$queued = @{$start.AbsoluteUri.TrimEnd('/')=$true}
$visited = @{}
$candidates = [ordered]@{}
$pages = [Collections.Generic.List[object]]::new()
$tempRoot = Join-Path 'tmp' 'scoped-section-crawl'
New-Item -ItemType Directory -Force $tempRoot | Out-Null

function Add-ScopedSeedAncestors {
  $ancestorDepth = 1
  foreach ($ancestorUrl in @(Get-DiscoverySeedAncestorUrls -Url $start.AbsoluteUri -MinimumPathPrefix $PathPrefix)) {
    if ($ancestorDepth -gt $MaxDepth) { break }
    $ancestorKey = $ancestorUrl.TrimEnd('/')
    if (-not $visited.ContainsKey($ancestorKey) -and -not $queued.ContainsKey($ancestorKey)) {
      $queue.Enqueue([pscustomobject]@{url=$ancestorUrl;depth=$ancestorDepth;parent_url=$start.AbsoluteUri;path=@($start.AbsoluteUri,$ancestorUrl);method='user-seed ancestor traversal'})
      $queued[$ancestorKey] = $true
    }
    $ancestorDepth++
  }
}

Add-ScopedSeedAncestors

if ($Resume -and (Test-Path -LiteralPath $OutputPath)) {
  $prior = Get-Content -Raw -Encoding UTF8 -LiteralPath $OutputPath | ConvertFrom-Json
  $queue.Clear()
  foreach ($page in @($prior.pages)) {
    if ($page.status -eq 'error') {
      $pagePath = if ($page.PSObject.Properties['discovery_path']) { @($page.discovery_path) } else { @($page.url) }
      $pageMethod = if ($page.PSObject.Properties['discovery_method']) { [string]$page.discovery_method } else { 'resumed failed page' }
      $pageKey = ([uri]$page.url).AbsoluteUri.TrimEnd('/')
      if (-not $queued.ContainsKey($pageKey)) {
        $queue.Enqueue([pscustomobject]@{url=$page.url;depth=$page.depth;parent_url=$page.parent_url;path=$pagePath;method=$pageMethod})
        $queued[$pageKey] = $true
      }
      continue
    }
    $pages.Add($page)
    $visited[([uri]$page.url).GetLeftPart([UriPartial]::Path).TrimEnd('/')] = $true
  }
  foreach ($candidate in @($prior.candidates)) {
    try {
      $builder = [UriBuilder]$candidate.url
      $builder.Fragment = ''
      $candidate.url = $builder.Uri.AbsoluteUri
    } catch { continue }
    if (-not $candidates.Contains([string]$candidate.url)) { $candidates[[string]$candidate.url] = $candidate }
  }
  $queueProperty = $prior.PSObject.Properties['next_queue']
  $savedQueue = @(if ($queueProperty) { @($queueProperty.Value) })
  if (-not $savedQueue.Count) {
    foreach ($url in @($prior.next_urls)) {
      $known = @($prior.candidates | Where-Object url -eq $url | Select-Object -First 1)
      $savedUri = [uri]$url
      if ($ExcludePathPattern -and $savedUri.AbsolutePath -match $ExcludePathPattern) { continue }
      if ($savedUri.AbsolutePath -match '(?i)/resolveuid/') { continue }
      $builder = [UriBuilder]$savedUri
      $builder.Fragment = ''
      $savedUrl = $builder.Uri.AbsoluteUri
      $savedKey = $savedUrl.TrimEnd('/')
      if ($visited.ContainsKey($savedKey) -or $queued.ContainsKey($savedKey)) { continue }
      $queue.Enqueue([pscustomobject]@{url=$savedUrl;depth=if($known.Count){[int]$known[0].discovery_depth}else{0};parent_url=if($known.Count){$known[0].parent_url}else{$null};path=if($known.Count -and $known[0].PSObject.Properties['discovery_path']){@($known[0].discovery_path)}else{@($savedUrl)};method=if($known.Count -and $known[0].PSObject.Properties['discovery_method']){[string]$known[0].discovery_method}else{'resumed candidate'}})
      $queued[$savedKey] = $true
    }
  } else {
    foreach ($saved in $savedQueue) {
      $savedUri = [uri]$saved.url
      if ($ExcludePathPattern -and $savedUri.AbsolutePath -match $ExcludePathPattern) { continue }
      if ($savedUri.AbsolutePath -match '(?i)/resolveuid/') { continue }
      $builder = [UriBuilder]$savedUri
      $builder.Fragment = ''
      $saved.url = $builder.Uri.AbsoluteUri
      $savedKey = $saved.url.TrimEnd('/')
      if ($visited.ContainsKey($savedKey) -or $queued.ContainsKey($savedKey)) { continue }
      $queue.Enqueue($saved)
      $queued[$savedKey] = $true
    }
  }
  Add-ScopedSeedAncestors
}

while ($queue.Count -and $pages.Count -lt $MaxPages) {
  $item = $queue.Dequeue()
  $normalized = ([uri]$item.url).AbsoluteUri.TrimEnd('/')
  if ($visited.ContainsKey($normalized)) { continue }
  $visited[$normalized] = $true
  $tempPath = Join-Path $tempRoot ("page-{0:d4}.json" -f $pages.Count)
  try {
    & "$PSScriptRoot/Invoke-SourceCrawl.ps1" -Agency $Agency -StartUrl $item.url -OutputPath $tempPath -MainOnly | Out-Null
    $page = Get-Content -Raw -Encoding UTF8 -LiteralPath $tempPath | ConvertFrom-Json
    $itemPath = if ($item.PSObject.Properties['path']) { @($item.path) } else { @($item.url) }
    $itemMethod = if ($item.PSObject.Properties['method']) { [string]$item.method } else { 'legacy queued page' }
    $pages.Add([pscustomobject]@{url=$item.url;depth=$item.depth;parent_url=$item.parent_url;discovery_path=$itemPath;discovery_method=$itemMethod;status='retrieved';link_count=@($page.candidates).Count;error=$null})
    foreach ($link in @($page.candidates)) {
      try {
        $builder = [UriBuilder]$link.url
        $builder.Fragment = ''
        $uri = $builder.Uri
      } catch { continue }
      if ($uri.Scheme -notin @('http','https') -or [string]::IsNullOrWhiteSpace($uri.Host)) { continue }
      if ($ExcludePathPattern -and $uri.AbsolutePath -match $ExcludePathPattern) { continue }
      $sameSection = $uri.Host -ieq $start.Host -and $uri.AbsolutePath.StartsWith($PathPrefix,[StringComparison]::OrdinalIgnoreCase)
      $policy = Get-DiscoveryLinkPolicy `
        -Url $uri.AbsoluteUri `
        -AnchorText ([string]$link.anchor_text) `
        -AllowedHosts @($start.Host) `
        -RecognizedPublishingHosts $RecognizedPublishingHosts `
        -RelevantPattern $RelevantOutboundPattern `
        -DocumentPattern $documentPattern `
        -CaptureRelevantOutboundLinks $CaptureRelevantOutboundLinks
      if (-not $sameSection -and -not $policy.capture) { continue }
      if (-not $candidates.Contains($uri.AbsoluteUri)) {
        $candidates[$uri.AbsoluteUri] = [ordered]@{
          url=$uri.AbsoluteUri
          anchor_text=[string]$link.anchor_text
          discovery_depth=($item.depth + 1)
          parent_url=$item.url
          discovery_path=@($itemPath) + $uri.AbsoluteUri
          discovery_method=if($sameSection){'scoped authored link'}else{'authoritative outbound link'}
          recursive_crawl_allowed=[bool]$sameSection
          host_classification=Get-DiscoveryHostClassification -HostName $uri.Host -AllowedHosts @($start.Host) -RecognizedPublishingHosts $RecognizedPublishingHosts
        }
      }
      if (-not $sameSection) { continue }
      if ($item.depth -ge $MaxDepth) { continue }
      if ($uri.AbsolutePath -match $documentPattern) { continue }
      if ($uri.AbsolutePath -match '(?i)/resolveuid/') { continue }
      $next = $uri.AbsoluteUri.TrimEnd('/')
      if (-not $visited.ContainsKey($next) -and -not $queued.ContainsKey($next)) {
        $queue.Enqueue([pscustomobject]@{url=$uri.AbsoluteUri;depth=($item.depth + 1);parent_url=$item.url;path=@($itemPath) + $uri.AbsoluteUri;method='scoped authored link'})
        $queued[$next] = $true
      }
    }
  } catch {
    $errorPath = if ($item.PSObject.Properties['path']) { @($item.path) } else { @($item.url) }
    $errorMethod = if ($item.PSObject.Properties['method']) { [string]$item.method } else { 'legacy queued page' }
    $pages.Add([pscustomobject]@{url=$item.url;depth=$item.depth;parent_url=$item.parent_url;discovery_path=$errorPath;discovery_method=$errorMethod;status='error';link_count=0;error=$_.Exception.Message})
  }

  $snapshot = [ordered]@{
    agency=$Agency;source_url=$StartUrl;scope="main-content recursive section crawl: $PathPrefix";retrieved_at=(Get-Date).ToUniversalTime().ToString('o')
    max_depth=$MaxDepth;max_pages=$MaxPages;recognized_publishing_hosts=@($RecognizedPublishingHosts);capture_relevant_outbound_links=$CaptureRelevantOutboundLinks;pages=@($pages);links=@($candidates.Keys | Sort-Object);candidates=@($candidates.Values | Sort-Object url)
    next_urls=@($queue.ToArray() | Select-Object -ExpandProperty url)
    next_queue=@($queue.ToArray())
  }
  $directory = Split-Path -Parent $OutputPath
  if ($directory) { New-Item -ItemType Directory -Force $directory | Out-Null }
  $snapshot | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
}

$finalSnapshot = [ordered]@{
  agency=$Agency;source_url=$StartUrl;scope="main-content recursive section crawl: $PathPrefix";retrieved_at=(Get-Date).ToUniversalTime().ToString('o')
  max_depth=$MaxDepth;max_pages=$MaxPages;recognized_publishing_hosts=@($RecognizedPublishingHosts);capture_relevant_outbound_links=$CaptureRelevantOutboundLinks;pages=@($pages);links=@($candidates.Keys | Sort-Object);candidates=@($candidates.Values | Sort-Object url)
  next_urls=@($queue.ToArray() | Select-Object -ExpandProperty url);next_queue=@($queue.ToArray())
}
$finalDirectory = Split-Path -Parent $OutputPath
if ($finalDirectory) { New-Item -ItemType Directory -Force $finalDirectory | Out-Null }
$finalSnapshot | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8

[pscustomobject]@{Agency=$Agency;Pages=$pages.Count;Candidates=$candidates.Count;Remaining=$queue.Count;OutputPath=$OutputPath} | ConvertTo-Json -Compress
