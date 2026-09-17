[CmdletBinding()]
param(
  [string]$SitemapUrl = 'https://abqinfo.com/sitemap.xml',
  [string]$OutputPath = 'project-state/discovery/live-abqinfo-document-link-inventory-2026-09-16.json',
  [int]$TimeoutSeconds = 60
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-PageHtml([string]$Url) {
  $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSeconds -SkipHttpErrorCheck
  [pscustomobject]@{
    status = [int]$response.StatusCode
    content = [string]$response.Content
    content_type = [string](@($response.Headers.'Content-Type')[0])
  }
}

function Get-VisibleText([string]$Html) {
  $text = [Net.WebUtility]::HtmlDecode(($Html -replace '(?is)<script\b[^>]*>.*?</script>', ' ' -replace '(?is)<style\b[^>]*>.*?</style>', ' ' -replace '(?is)<[^>]+>', ' '))
  return (($text -replace '\s+', ' ').Trim())
}

function Get-DocumentKind([uri]$Url) {
  if ($Url.Host -eq 'files.abqinfo.com') { return 'r2_archive' }
  if ($Url.Host -eq 'documents.cabq.gov') { return 'official_document_or_source' }
  if ($Url.Host -eq 'onbase.cabq.gov' -and $Url.AbsolutePath -match '(?i)(/Document/|\.pdf(?:/|$))') { return 'official_document_or_source' }
  if ($Url.AbsolutePath -match '(?i)\.(pdf|docx?|xlsx?|csv|zip|pptx?|json)(?:$|[?#])') { return 'document_or_data' }
  return $null
}

$sitemapResponse = Get-PageHtml $SitemapUrl
if ($sitemapResponse.status -ne 200) { throw "Sitemap returned HTTP $($sitemapResponse.status): $SitemapUrl" }
[xml]$sitemapXml = $sitemapResponse.content
$namespace = [Xml.XmlNamespaceManager]::new($sitemapXml.NameTable)
$namespace.AddNamespace('sm', 'http://www.sitemaps.org/schemas/sitemap/0.9')
$pageUrls = @($sitemapXml.SelectNodes('//sm:loc', $namespace) | ForEach-Object { [string]$_.InnerText } | Sort-Object -Unique)
if (-not $pageUrls.Count) { throw "No page URLs found in sitemap: $SitemapUrl" }

$pages = [Collections.Generic.List[object]]::new()
$links = [Collections.Generic.List[object]]::new()
$pageNumber = 0
foreach ($pageUrl in $pageUrls) {
  $pageNumber++
  $page = Get-PageHtml $pageUrl
  $html = $page.content
  $titleMatch = [regex]::Match($html, '(?is)<title\b[^>]*>(?<text>.*?)</title>')
  $pageTitle = if ($titleMatch.Success) { Get-VisibleText $titleMatch.Groups['text'].Value } else { '' }
  $pages.Add([ordered]@{ url=$pageUrl; http_status=$page.status; content_type=$page.content_type; title=$pageTitle; document_link_count=0 })
  if ($page.status -ne 200) { continue }
  $anchorMatches = [regex]::Matches($html, '(?is)<a\b[^>]*?\bhref\s*=\s*(?<quote>["''])(?<href>.*?)\k<quote>[^>]*>(?<text>.*?)</a>')
  foreach ($anchor in $anchorMatches) {
    $rawHref = [Net.WebUtility]::HtmlDecode($anchor.Groups['href'].Value.Trim())
    if (-not $rawHref -or $rawHref -match '^(?i)(javascript:|mailto:|tel:|#)') { continue }
    try { $absolute = [uri]::new([uri]$pageUrl, $rawHref) } catch { continue }
    $kind = Get-DocumentKind $absolute
    if (-not $kind) { continue }
    $visible = Get-VisibleText $anchor.Groups['text'].Value
    $prefix = $html.Substring(0, $anchor.Index)
    $headingMatches = [regex]::Matches($prefix, '(?is)<h[1-4]\b[^>]*>(?<text>.*?)</h[1-4]>')
    $context = if ($headingMatches.Count) { Get-VisibleText $headingMatches[$headingMatches.Count - 1].Groups['text'].Value } else { '' }
    $links.Add([ordered]@{
      page_url = $pageUrl
      page_title = $pageTitle
      visible_item = $visible
      nearest_heading = $context
      url = $absolute.AbsoluteUri
      link_kind = $kind
      is_r2_archive = ($kind -eq 'r2_archive')
      raw_href = $rawHref
    })
    $pages[$pages.Count - 1].document_link_count++
  }
}

$r2Links = @($links | Where-Object is_r2_archive | Sort-Object url, page_url, visible_item)
$documentLinks = @($links | Sort-Object url, page_url, visible_item)
$output = [ordered]@{
  schema_version = 1
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  source = $SitemapUrl
  page_count = $pageUrls.Count
  fetched_page_count = @($pages | Where-Object http_status -eq 200).Count
  document_link_count = $documentLinks.Count
  r2_archive_link_count = $r2Links.Count
  unique_document_url_count = @($documentLinks.url | Sort-Object -Unique).Count
  unique_r2_archive_url_count = @($r2Links.url | Sort-Object -Unique).Count
  pages = @($pages)
  links = $documentLinks
}
$fullPath = [IO.Path]::GetFullPath($OutputPath)
$directory = Split-Path -Parent $fullPath
if ($directory) { New-Item -ItemType Directory -Force -Path $directory | Out-Null }
$temporaryPath = "$fullPath.tmp-$PID"
[IO.File]::WriteAllText($temporaryPath, ($output | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
[pscustomobject]@{
  pages = $output.page_count
  fetched = $output.fetched_page_count
  document_links = $output.document_link_count
  r2_archive_links = $output.r2_archive_link_count
  unique_r2_archives = $output.unique_r2_archive_url_count
  output = $OutputPath
} | ConvertTo-Json -Compress
