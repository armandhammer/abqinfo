[CmdletBinding()]
param(
  [Parameter(Mandatory)][string[]]$SeedUrls,
  [Parameter(Mandatory)][string]$Agency,
  [string[]]$AllowedHosts = @('www.cabq.gov','beta.cabq.gov','documents.cabq.gov','cabq.legistar.com','codelibrary.amlegal.com'),
  [string[]]$RecognizedPublishingHosts = @(),
  [string]$RelevantPattern = '',
  [bool]$CaptureRelevantOutboundLinks = $true,
  [ValidateSet('custom','bicycle-history')][string]$DiscoveryProfile = 'custom',
  [string]$OutputPath = 'project-state/discovery/unknown-document-crawl.json',
  [ValidateRange(1,10)][int]$MaxDepth = 6,
  [ValidateRange(1,5000)][int]$MaxPages = 500,
  [ValidateRange(5,120)][int]$RequestTimeoutSeconds = 20,
  [ValidateRange(0,5)][int]$MaxRetries = 2,
  [switch]$Resume,
  [switch]$IncludeSiteInfrastructure
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/Discovery.Common.ps1"

if (-not $RecognizedPublishingHosts.Count) {
  $RecognizedPublishingHosts = @(Get-DefaultRecognizedPublishingHosts)
}
if ([string]::IsNullOrWhiteSpace($RelevantPattern)) {
  $RelevantPattern = Get-DefaultDiscoveryRelevantPattern
}

if ($DiscoveryProfile -eq 'bicycle-history') {
  $RelevantPattern = Get-BicycleHistoryRelevantPattern
}

$documentPattern = '(?i)\.(pdf|docx?|xlsx?|csv|zip|kml|kmz|shp)(?:/view)?(?:$|[?#])'
$excludedPattern = '(?i)(/events?(?:/|$)|/news(?:/|$)|/jobs?(?:/|$)|mailto:|tel:|javascript:|facebook\.com|instagram\.com|youtube\.com|twitter\.com|linkedin\.com)'
$collectionPattern = '(?i)(?:^|[\s/_-])(documents?|resources?|plans?|publications?|archives?|reports?|maps?|attachments?)(?:$|[\s/_-])'

function Get-NormalizedUrl([string]$Url, [uri]$BaseUri = $null) {
  try {
    $uri = if ($BaseUri) { [uri]::new($BaseUri,$Url) } else { [uri]$Url }
    if ($uri.Scheme -notin @('http','https')) { return $null }
    $builder = [UriBuilder]$uri
    $builder.Fragment = ''
    foreach ($name in @('utm_source','utm_medium','utm_campaign','utm_term','utm_content')) {
      $builder.Query = (($builder.Query.TrimStart('?') -split '&' | Where-Object { $_ -and $_ -notmatch "^$name=" }) -join '&')
    }
    return $builder.Uri.AbsoluteUri
  } catch { return $null }
}

function Test-AllowedHost([string]$DomainName) {
  return Test-DiscoveryHostMatch -HostName $DomainName -HostPatterns $AllowedHosts
}

function Get-PlainText([string]$Html) {
  if ([string]::IsNullOrWhiteSpace($Html)) { return '' }
  $value = $Html -replace '(?is)<(script|style|noscript)\b.*?</\1>', ' '
  $value = $value -replace '(?is)<[^>]+>', ' '
  $value = [Net.WebUtility]::HtmlDecode($value)
  return ($value -replace '\s+', ' ').Trim()
}

function Get-ContentRegion([string]$Html, [uri]$Uri) {
  if ($Uri.AbsolutePath -match '(?i)(sitemap|@@search|/search)') { return $Html }
  $match = [regex]::Match($Html,'(?is)<main\b[^>]*>(?<content>.*?)</main>')
  if (-not $match.Success) { $match = [regex]::Match($Html,'(?is)<article\b[^>]*>(?<content>.*?)</article>') }
  if ($match.Success) { return $match.Groups['content'].Value }
  return $Html
}

function Get-Links([string]$Html, [uri]$BaseUri) {
  $links = foreach ($match in [regex]::Matches($Html,'(?is)<a\b[^>]*?\bhref\s*=\s*(?<quote>["''])(?<href>.*?)\k<quote>[^>]*>(?<text>.*?)</a>')) {
    $href = [Net.WebUtility]::HtmlDecode($match.Groups['href'].Value)
    $url = Get-NormalizedUrl $href $BaseUri
    if (-not $url) { continue }
    [pscustomobject]@{url=$url;anchor_text=(Get-PlainText $match.Groups['text'].Value)}
  }
  return @($links | Sort-Object url -Unique)
}

function Get-ParentFolderUrl([string]$Url) {
  try {
    $uri = [uri]$Url
    $path = $uri.AbsolutePath
    if (-not ($path -match $documentPattern)) { return $null }
    $folder = $path.Substring(0,$path.LastIndexOf('/') + 1)
    return "{0}://{1}{2}" -f $uri.Scheme,$uri.Authority,$folder
  } catch { return $null }
}

function Add-Candidate([hashtable]$Map, [string]$Url, [string]$Anchor, [object]$Item, [string]$Method) {
  $key = $Url.TrimEnd('/')
  $candidateUri = [uri]$Url
  $recursiveAllowed = Test-AllowedHost $candidateUri.Host
  $hostClassification = Get-DiscoveryHostClassification -HostName $candidateUri.Host -AllowedHosts $AllowedHosts -RecognizedPublishingHosts $RecognizedPublishingHosts
  if (-not $Map.ContainsKey($key)) {
    $path = @($Item.path) + $Url
    $Map[$key] = [ordered]@{
      url=$Url
      anchor_text=$Anchor
      parent_url=$Item.url
      referring_urls=@($Item.url)
      discovery_path=$path
      discovery_method=$Method
      discovery_depth=([int]$Item.depth + 1)
      file_type=if($Url -match $documentPattern){([IO.Path]::GetExtension(([uri]$Url).AbsolutePath).TrimStart('.').ToUpperInvariant())}else{'Web page or live service'}
      size_bytes=$null
      http_status=$null
      content_type=$null
      recursive_crawl_allowed=[bool]$recursiveAllowed
      host_classification=$hostClassification
      processing_notes=@()
    }
    if (-not $recursiveAllowed) {
      $Map[$key].processing_notes = @("Captured from authoritative page $($Item.url); external host was not recursively crawled.")
    }
  } else {
    $record = $Map[$key]
    if (-not $record.PSObject.Properties['recursive_crawl_allowed']) {
      $record | Add-Member -NotePropertyName recursive_crawl_allowed -NotePropertyValue ([bool]$recursiveAllowed)
    }
    if (-not $record.PSObject.Properties['host_classification']) {
      $record | Add-Member -NotePropertyName host_classification -NotePropertyValue $hostClassification
    }
    $record.referring_urls = @(@($record.referring_urls) + $Item.url | Sort-Object -Unique)
    $newPath = @($Item.path) + $Url
    if ($newPath.Count -lt @($record.discovery_path).Count) {
      $record.discovery_path = $newPath
      $record.parent_url = $Item.url
      $record.discovery_depth = [int]$Item.depth + 1
    }
  }
}

function Add-SeedAncestorsToFrontier([string]$SeedUrl) {
  $ancestorDepth = 1
  foreach ($ancestorUrl in @(Get-DiscoverySeedAncestorUrls -Url $SeedUrl)) {
    if ($ancestorDepth -gt $MaxDepth) { break }
    $ancestorKey = $ancestorUrl.TrimEnd('/')
    if (-not $visited.ContainsKey($ancestorKey) -and -not $queued.ContainsKey($ancestorKey)) {
      $frontier.Enqueue([pscustomobject]@{
        url=$ancestorUrl
        depth=$ancestorDepth
        parent_url=$SeedUrl
        path=@($SeedUrl,$ancestorUrl)
        method='user-seed ancestor traversal'
        attempt=1
      })
      $queued[$ancestorKey] = $true
    }
    $ancestorDepth++
  }
}

function Save-State([Collections.Generic.Queue[object]]$Frontier, [hashtable]$Visited, [hashtable]$CandidateMap, [Collections.Generic.List[object]]$Pages) {
  $directory = Split-Path -Parent $OutputPath
  if ($directory) { New-Item -ItemType Directory -Force $directory | Out-Null }
  $json = [ordered]@{
    schema_version=2
    agency=$Agency
    source_url=$SeedUrls[0]
    seed_urls=@($SeedUrls)
    allowed_hosts=@($AllowedHosts)
    recognized_publishing_hosts=@($RecognizedPublishingHosts)
    capture_relevant_outbound_links=$CaptureRelevantOutboundLinks
    relevant_pattern=$RelevantPattern
    generated_at=(Get-Date).ToUniversalTime().ToString('o')
    max_depth=$MaxDepth
    max_pages=$MaxPages
    frontier=@($Frontier.ToArray())
    visited_urls=@($Visited.Keys | Sort-Object)
    pages=@($Pages)
    candidates=@($CandidateMap.Values | Sort-Object url)
    links=@($CandidateMap.Values | ForEach-Object url | Sort-Object -Unique)
  } | ConvertTo-Json -Depth 12
  $temporaryPath = "$OutputPath.tmp.$PID"
  $json | Set-Content -LiteralPath $temporaryPath -Encoding utf8
  if (Test-Path -LiteralPath $OutputPath) {
    $saved = $false
    for ($saveAttempt = 1; $saveAttempt -le 5; $saveAttempt++) {
      try {
        $temporaryFullPath = [IO.Path]::GetFullPath($temporaryPath)
        $outputFullPath = [IO.Path]::GetFullPath($OutputPath)
        $backupFullPath = "$outputFullPath.bak.$PID"
        [IO.File]::Replace($temporaryFullPath, $outputFullPath, $backupFullPath)
        if ([IO.File]::Exists($backupFullPath)) { [IO.File]::Delete($backupFullPath) }
        $saved = $true
        break
      } catch {
        if ($saveAttempt -eq 5) { throw }
        Start-Sleep -Milliseconds (100 * $saveAttempt)
      }
    }
    if (-not $saved) { throw "Unable to atomically replace $OutputPath." }
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
  foreach ($candidate in @($prior.candidates)) { $candidateMap[([string]$candidate.url).TrimEnd('/')] = $candidate }
  foreach ($page in @($prior.pages)) { $pages.Add($page) }
  foreach ($item in @($prior.frontier)) {
    $frontier.Enqueue($item)
    $queued[([string]$item.url).TrimEnd('/')] = $true
  }
  foreach ($page in @($prior.pages | Where-Object {
    $_.status -eq 'retrieved' -and "$($_.url) $($_.title)" -match $RelevantPattern
  })) {
    $ancestorOffset = 1
    foreach ($parentPage in @(Get-DiscoverySeedAncestorUrls -Url ([string]$page.url))) {
      $parentDepth = [int]$page.depth + $ancestorOffset
      if ($parentDepth -gt $MaxDepth) { break }
      $parentKey = $parentPage.TrimEnd('/')
      if (-not $visited.ContainsKey($parentKey) -and -not $queued.ContainsKey($parentKey)) {
        $frontier.Enqueue([pscustomobject]@{url=$parentPage;depth=$parentDepth;parent_url=$page.url;path=@($page.discovery_path) + $parentPage;method='relevant-page ancestor traversal';attempt=1})
        $queued[$parentKey] = $true
      }
      $ancestorOffset++
    }
  }
  foreach ($seedUrl in $SeedUrls) { Add-SeedAncestorsToFrontier $seedUrl }
} else {
  foreach ($seedUrl in $SeedUrls) {
    $url = Get-NormalizedUrl $seedUrl
    if (-not $url) { continue }
    $frontier.Enqueue([pscustomobject]@{url=$url;depth=0;parent_url=$null;path=@($url);method='user seed'})
    $queued[$url.TrimEnd('/')] = $true
    Add-SeedAncestorsToFrontier $url
  }
  if ($IncludeSiteInfrastructure) {
    foreach ($seedUrl in $SeedUrls) {
      $seed = [uri]$seedUrl
      if ($seed.Host -ieq 'www.cabq.gov') {
        foreach ($infrastructure in @('https://www.cabq.gov/sitemap','https://www.cabq.gov/@@sitemap','https://beta.cabq.gov/@@sitemap','https://www.cabq.gov/@@search?SearchableText=bike')) {
          $key = $infrastructure.TrimEnd('/')
          if (-not $queued.ContainsKey($key)) {
            $frontier.Enqueue([pscustomobject]@{url=$infrastructure;depth=0;parent_url=$seedUrl;path=@($seedUrl,$infrastructure);method='derived site discovery infrastructure'})
            $queued[$key] = $true
          }
        }
      }
    }
  }
}

while ($frontier.Count -and $pages.Count -lt $MaxPages) {
  $item = $frontier.Dequeue()
  $key = ([string]$item.url).TrimEnd('/')
  if ($visited.ContainsKey($key)) { continue }
  $uri = [uri]$item.url
  if (-not (Test-AllowedHost $uri.Host)) { continue }

  $attempt = if ($item.PSObject.Properties['attempt']) { [int]$item.attempt } else { 1 }
  $pageRecord = [ordered]@{url=$item.url;depth=$item.depth;parent_url=$item.parent_url;discovery_path=@($item.path);discovery_method=$item.method;attempt=$attempt;status='pending';http_status=$null;content_type=$null;content_length=$null;title=$null;link_count=0;error=$null;retryable=$false;retry_rule="retry network, HTTP 429, and HTTP 5xx failures up to $MaxRetries times"}
  try {
    if ($uri.AbsoluteUri -match $documentPattern) {
      $response = Invoke-WebRequest -Uri $uri.AbsoluteUri -Method Head -UseBasicParsing -MaximumRedirection 10 -TimeoutSec $RequestTimeoutSeconds
      $pageRecord.http_status = [int]$response.StatusCode
      $pageRecord.content_type = [string]$response.Headers['Content-Type']
      $length = [string]$response.Headers['Content-Length']
      if ($length -match '^\d+$') { $pageRecord.content_length = [int64]$length }
      $pageRecord.status = 'document metadata recorded'
      $candidate = $candidateMap[$key]
      if ($candidate) {
        $candidate.http_status = $pageRecord.http_status
        $candidate.content_type = $pageRecord.content_type
        $candidate.size_bytes = $pageRecord.content_length
      }
    } else {
      $response = Invoke-WebRequest -Uri $uri.AbsoluteUri -UseBasicParsing -MaximumRedirection 10 -TimeoutSec $RequestTimeoutSeconds
      $pageRecord.http_status = [int]$response.StatusCode
      $pageRecord.content_type = [string]$response.Headers['Content-Type']
      $length = [string]$response.Headers['Content-Length']
      if ($length -match '^\d+$') { $pageRecord.content_length = [int64]$length }
      # Windows PowerShell exposes the final URI as ResponseUri, while
      # PowerShell 7 wraps a HttpResponseMessage whose redirect target is on
      # RequestMessage.RequestUri. Support both so the resumable crawl behaves
      # deterministically in either runtime.
      $finalUri = $null
      if ($response.BaseResponse.PSObject.Properties['ResponseUri']) {
        $finalUri = $response.BaseResponse.ResponseUri
      } elseif ($response.BaseResponse.PSObject.Properties['RequestMessage'] -and $response.BaseResponse.RequestMessage) {
        $finalUri = $response.BaseResponse.RequestMessage.RequestUri
      }
      if (-not $finalUri) { $finalUri = $uri }
      $deliveredDocument = $pageRecord.content_type -match '(?i)(application/pdf|application/msword|officedocument|application/zip)' -or $finalUri.AbsoluteUri -match $documentPattern
      if ($deliveredDocument) {
        $pageRecord.status = 'document metadata recorded'
        $candidate = $candidateMap[$key]
        if ($candidate) {
          $candidate.http_status = $pageRecord.http_status
          $candidate.content_type = $pageRecord.content_type
          $candidate.size_bytes = $pageRecord.content_length
          if ($candidate.file_type -eq 'Web page or live service') { $candidate.file_type = 'PDF or document (extensionless URL)' }
          $candidate.processing_notes = @($candidate.processing_notes) + "Delivered as $($pageRecord.content_type); not parsed as HTML."
        }
      } else {
      $region = Get-ContentRegion ([string]$response.Content) $finalUri
      $heading = [regex]::Match($region,'(?is)<h1\b[^>]*>(?<title>.*?)</h1>')
      if ($heading.Success) { $pageRecord.title = Get-PlainText $heading.Groups['title'].Value }
      $links = @(Get-Links $region $finalUri)
      # Government CMS navigation often exposes a relevant document collection
      # outside <main> (for example a sibling named simply "documents"). When the
      # current page is already in scope, include those collection edges from the
      # full page so generic labels do not sever the document graph.
      $currentPageRelevant = ("$($finalUri.AbsolutePath) $($pageRecord.title)" -match $RelevantPattern)
      $isDiscoveryAncestor = ([string]$item.method) -match '(?i)ancestor traversal'
      # An explicitly supplied or inventory-derived source page is already in
      # scope by editorial decision. Treat it as a discovery root even when a
      # generic label such as "Links and Resources" contains no topical term.
      # Otherwise a retained landing page can become an accidental crawl stop.
      $isExplicitDiscoveryRoot = ([string]$item.method) -match '(?i)^(user seed|retained source audit)$'
      $pageInDiscoveryContext = $currentPageRelevant -or $isDiscoveryAncestor -or $isExplicitDiscoveryRoot
      if ($pageInDiscoveryContext) {
        $collectionLinks = @(Get-Links ([string]$response.Content) $finalUri | Where-Object {
          $linkContext = "$($_.anchor_text) $(([uri]$_.url).AbsolutePath)"
          $linkContext -match $collectionPattern -and (-not $isDiscoveryAncestor -or $linkContext -match $RelevantPattern)
        })
        $links = @($links + $collectionLinks | Sort-Object url -Unique)
      }
      $pageRecord.link_count = $links.Count
      $pageRecord.status = 'retrieved'
      $isInfrastructure = $uri.AbsolutePath -match '(?i)(sitemap|@@search|/search)' -or $uri.Query -match '(?i)b_start'

      foreach ($link in $links) {
        $linkUri = [uri]$link.url
        if ($link.url -match $excludedPattern) { continue }
        $isDocument = $link.url -match $documentPattern
        $isSpecial = $linkUri.AbsolutePath -match '(?i)(sitemap|@@search|/search)' -or $linkUri.Query -match '(?i)b_start'
        $isCollectionEdge = $pageInDiscoveryContext -and ("$($link.anchor_text) $($linkUri.AbsolutePath)" -match $collectionPattern)
        $policy = Get-DiscoveryLinkPolicy `
          -Url $link.url `
          -AnchorText ([string]$link.anchor_text) `
          -AllowedHosts $AllowedHosts `
          -RecognizedPublishingHosts $RecognizedPublishingHosts `
          -RelevantPattern $RelevantPattern `
          -DocumentPattern $documentPattern `
          -IsCollectionEdge $isCollectionEdge `
          -IsSpecial $isSpecial `
          -IsInfrastructure $isInfrastructure `
          -CaptureRelevantOutboundLinks $CaptureRelevantOutboundLinks
        if (-not $policy.capture) { continue }

        $method = if (-not $policy.allowed_host) { 'authoritative outbound link' } elseif ($isDocument) { 'authored document link' } elseif ($isCollectionEdge) { 'relevant-page collection navigation' } elseif ($isInfrastructure) { 'site index or catalog' } else { 'authored relevant link' }
        Add-Candidate $candidateMap $link.url ([string]$link.anchor_text) $item $method

        if (-not $policy.allowed_host) { continue }

        if ($isDocument) {
          $parentFolder = Get-ParentFolderUrl $link.url
          if ($parentFolder -and [int]$item.depth -lt $MaxDepth) {
            $parentKey = $parentFolder.TrimEnd('/')
            if (-not $visited.ContainsKey($parentKey) -and -not $queued.ContainsKey($parentKey)) {
              $frontier.Enqueue([pscustomobject]@{url=$parentFolder;depth=([int]$item.depth + 1);parent_url=$item.url;path=@($item.path) + $parentFolder;method='document parent folder'})
              $queued[$parentKey] = $true
            }
          }
        } elseif ([int]$item.depth -lt $MaxDepth) {
          $nextKey = $link.url.TrimEnd('/')
          if (-not $visited.ContainsKey($nextKey) -and -not $queued.ContainsKey($nextKey)) {
            $frontier.Enqueue([pscustomobject]@{url=$link.url;depth=([int]$item.depth + 1);parent_url=$item.url;path=@($item.path) + $link.url;method=$method})
            $queued[$nextKey] = $true
          }
        }
      }
      # Probe the conventional Plone child collection from broad topical hubs.
      # This recovers unlinked sibling archives such as /bike/documents without
      # relying on any known document title. Failed probes remain page failures
      # and are not promoted into the candidate inventory.
      if ($pageInDiscoveryContext -and [int]$item.depth -lt $MaxDepth) {
        $leaf = $finalUri.AbsolutePath.TrimEnd('/').Split('/')[-1]
        if ($leaf -match '(?i)^(bike|bikes|bicycling|biking-in-abq|transportation|active-transportation)$') {
          $probeUrl = $finalUri.AbsoluteUri.TrimEnd('/') + '/documents'
          $probeKey = $probeUrl.TrimEnd('/')
          if (-not $visited.ContainsKey($probeKey) -and -not $queued.ContainsKey($probeKey)) {
            $frontier.Enqueue([pscustomobject]@{url=$probeUrl;depth=([int]$item.depth + 1);parent_url=$item.url;path=@($item.path) + $probeUrl;method='derived topical Plone document collection'})
            $queued[$probeKey] = $true
          }
        }
        if ($currentPageRelevant) {
          $ancestorOffset = 1
          foreach ($parentPage in @(Get-DiscoverySeedAncestorUrls -Url $finalUri.AbsoluteUri)) {
            $parentDepth = [int]$item.depth + $ancestorOffset
            if ($parentDepth -gt $MaxDepth) { break }
            $parentKey = $parentPage.TrimEnd('/')
            if (-not $visited.ContainsKey($parentKey) -and -not $queued.ContainsKey($parentKey)) {
              $frontier.Enqueue([pscustomobject]@{url=$parentPage;depth=$parentDepth;parent_url=$item.url;path=@($item.path) + $parentPage;method='relevant-page ancestor traversal';attempt=1})
              $queued[$parentKey] = $true
            }
            $ancestorOffset++
          }
        }
      }
      }
    }
  } catch {
    $pageRecord.error = $_.Exception.Message
    $requiresRenderedBrowser = $pageRecord.error -match '(?i)(403|forbidden|attention required|cloudflare|access denied|you have been blocked)'
    $pageRecord.status = if ($requiresRenderedBrowser) { 'requires rendered-browser review' } else { 'error' }
    $pageRecord.retryable = -not $requiresRenderedBrowser -and $pageRecord.error -match '(?i)(timed? out|unable to connect|connection.*(closed|reset)|HTTP.*429|HTTP.*5\d\d|\(429\)|\(5\d\d\))'
    if ($requiresRenderedBrowser) {
      $pageRecord.retry_rule = 'Open in a rendered browser, enumerate authored links, and preserve the complete discovery path; do not treat this page as exhausted.'
    }
  }
  if ($pageRecord.status -eq 'error' -and $pageRecord.retryable -and $attempt -le $MaxRetries) {
    $pageRecord.status = 'retry scheduled'
    $frontier.Enqueue([pscustomobject]@{url=$item.url;depth=$item.depth;parent_url=$item.parent_url;path=@($item.path);method=$item.method;attempt=($attempt + 1)})
  } else {
    $visited[$key] = $true
  }
  $pages.Add([pscustomobject]$pageRecord)
  Save-State $frontier $visited $candidateMap $pages
}

Save-State $frontier $visited $candidateMap $pages
[pscustomobject]@{Agency=$Agency;Pages=$pages.Count;Candidates=$candidateMap.Count;Remaining=$frontier.Count;OutputPath=$OutputPath} | ConvertTo-Json -Compress
