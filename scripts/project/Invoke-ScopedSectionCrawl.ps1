[CmdletBinding()]
param(
  [Parameter(Mandatory)][ValidateSet('cabq','bernco','mrcog','nmdot')][string]$Agency,
  [Parameter(Mandatory)][string]$StartUrl,
  [Parameter(Mandatory)][string]$PathPrefix,
  [string]$OutputPath = "research/discovery/$Agency-section-links.json",
  [ValidateRange(0,8)][int]$MaxDepth = 3,
  [ValidateRange(1,1000)][int]$MaxPages = 200,
  [string]$ExcludePathPattern = '(?i)/(events?|news|calendar|contact|jobs?|liquor-hearings|administration-questions-answers)(/|$)',
  [switch]$Resume
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$start = [uri]$StartUrl
$queue = [Collections.Generic.Queue[object]]::new()
$queue.Enqueue([pscustomobject]@{url=$start.AbsoluteUri;depth=0;parent_url=$null})
$queued = @{$start.AbsoluteUri.TrimEnd('/')=$true}
$visited = @{}
$candidates = [ordered]@{}
$pages = [Collections.Generic.List[object]]::new()
$tempRoot = Join-Path 'tmp' 'scoped-section-crawl'
New-Item -ItemType Directory -Force $tempRoot | Out-Null

if ($Resume -and (Test-Path -LiteralPath $OutputPath)) {
  $prior = Get-Content -Raw -LiteralPath $OutputPath | ConvertFrom-Json
  $queue.Clear()
  foreach ($page in @($prior.pages)) {
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
      $queue.Enqueue([pscustomobject]@{url=$savedUrl;depth=if($known.Count){[int]$known[0].discovery_depth}else{0};parent_url=if($known.Count){$known[0].parent_url}else{$null}})
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
}

while ($queue.Count -and $pages.Count -lt $MaxPages) {
  $item = $queue.Dequeue()
  $normalized = ([uri]$item.url).AbsoluteUri.TrimEnd('/')
  if ($visited.ContainsKey($normalized)) { continue }
  $visited[$normalized] = $true
  $tempPath = Join-Path $tempRoot ("page-{0:d4}.json" -f $pages.Count)
  try {
    & "$PSScriptRoot/Invoke-SourceCrawl.ps1" -Agency $Agency -StartUrl $item.url -OutputPath $tempPath -MainOnly | Out-Null
    $page = Get-Content -Raw -LiteralPath $tempPath | ConvertFrom-Json
    $pages.Add([pscustomobject]@{url=$item.url;depth=$item.depth;parent_url=$item.parent_url;status='retrieved';link_count=@($page.candidates).Count;error=$null})
    foreach ($link in @($page.candidates)) {
      try {
        $builder = [UriBuilder]$link.url
        $builder.Fragment = ''
        $uri = $builder.Uri
      } catch { continue }
      if ($uri.Host -ne $start.Host) { continue }
      if (-not $uri.AbsolutePath.StartsWith($PathPrefix,[StringComparison]::OrdinalIgnoreCase)) { continue }
      if (-not $candidates.Contains($uri.AbsoluteUri)) {
        $candidates[$uri.AbsoluteUri] = [ordered]@{url=$uri.AbsoluteUri;anchor_text=[string]$link.anchor_text;discovery_depth=($item.depth + 1);parent_url=$item.url}
      }
      if ($item.depth -ge $MaxDepth) { continue }
      if ($uri.AbsolutePath -match '(?i)\.(pdf|docx?|xlsx?|csv|zip|kml|kmz)$') { continue }
      if ($uri.AbsolutePath -match '(?i)/resolveuid/') { continue }
      if ($ExcludePathPattern -and $uri.AbsolutePath -match $ExcludePathPattern) { continue }
      $next = $uri.AbsoluteUri.TrimEnd('/')
      if (-not $visited.ContainsKey($next) -and -not $queued.ContainsKey($next)) {
        $queue.Enqueue([pscustomobject]@{url=$uri.AbsoluteUri;depth=($item.depth + 1);parent_url=$item.url})
        $queued[$next] = $true
      }
    }
  } catch {
    $pages.Add([pscustomobject]@{url=$item.url;depth=$item.depth;parent_url=$item.parent_url;status='error';link_count=0;error=$_.Exception.Message})
  }

  $snapshot = [ordered]@{
    agency=$Agency;source_url=$StartUrl;scope="main-content recursive section crawl: $PathPrefix";retrieved_at=(Get-Date).ToUniversalTime().ToString('o')
    max_depth=$MaxDepth;max_pages=$MaxPages;pages=@($pages);links=@($candidates.Keys | Sort-Object);candidates=@($candidates.Values | Sort-Object url)
    next_urls=@($queue.ToArray() | Select-Object -ExpandProperty url)
    next_queue=@($queue.ToArray())
  }
  $directory = Split-Path -Parent $OutputPath
  if ($directory) { New-Item -ItemType Directory -Force $directory | Out-Null }
  $snapshot | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
}

$finalSnapshot = [ordered]@{
  agency=$Agency;source_url=$StartUrl;scope="main-content recursive section crawl: $PathPrefix";retrieved_at=(Get-Date).ToUniversalTime().ToString('o')
  max_depth=$MaxDepth;max_pages=$MaxPages;pages=@($pages);links=@($candidates.Keys | Sort-Object);candidates=@($candidates.Values | Sort-Object url)
  next_urls=@($queue.ToArray() | Select-Object -ExpandProperty url);next_queue=@($queue.ToArray())
}
$finalDirectory = Split-Path -Parent $OutputPath
if ($finalDirectory) { New-Item -ItemType Directory -Force $finalDirectory | Out-Null }
$finalSnapshot | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8

[pscustomobject]@{Agency=$Agency;Pages=$pages.Count;Candidates=$candidates.Count;Remaining=$queue.Count;OutputPath=$OutputPath} | ConvertTo-Json -Compress
