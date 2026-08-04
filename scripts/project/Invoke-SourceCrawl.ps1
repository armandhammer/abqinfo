[CmdletBinding()]
param(
  [Parameter(Mandatory)][ValidateSet('cabq','bernco','mrcog','nmdot')][string]$Agency,
  [Parameter(Mandatory)][string]$StartUrl,
  [string]$OutputPath = "research/discovery/$Agency-links.json",
  [switch]$MainOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$response = $null
for ($attempt = 1; $attempt -le 5; $attempt++) {
  $response = Invoke-WebRequest -Uri $StartUrl -UseBasicParsing
  if ($response.StatusCode -eq 200 -and $response.Content.Length -gt 1000) { break }
  if ($attempt -lt 5) { Start-Sleep -Seconds 1 }
}
if (-not $response -or $response.StatusCode -ne 200) { throw "Unable to retrieve complete page content from $StartUrl." }
$base = [uri]$StartUrl
$candidateMap = [ordered]@{}
$pageLinks = if ($MainOnly) {
  $contentMatch = [regex]::Match($response.Content, '(?is)<main\b[^>]*>(?<content>.*?)</main>')
  if (-not $contentMatch.Success) {
    # WordPress exposes the authored page body separately from theme navigation.
    $apiMatch = [regex]::Match($response.Content, '(?is)<link\b[^>]*type=["'']application/json["''][^>]*href=["''](?<url>[^"'']+)["''][^>]*>')
    if ($apiMatch.Success) {
      $apiUrl = [Net.WebUtility]::HtmlDecode($apiMatch.Groups['url'].Value)
      $apiPage = Invoke-RestMethod -Uri $apiUrl
      $contentProperty = $apiPage.PSObject.Properties['content']
      $renderedProperty = if ($contentProperty) { $contentProperty.Value.PSObject.Properties['rendered'] } else { $null }
      if ($renderedProperty -and $renderedProperty.Value) {
        $contentMatch = [regex]::Match("<main>$($renderedProperty.Value)</main>", '(?is)<main\b[^>]*>(?<content>.*?)</main>')
      }
    }
  }
  if (-not $contentMatch.Success) {
    # Bernalillo County's Divi pages omit <main>; capture the primary two-thirds
    # content column between the page title and the one-third sidebar.
    $contentMatch = [regex]::Match($response.Content, '(?is)<h1\b[^>]*class=["''][^"'']*\bentry-title\b[^"'']*["''][^>]*>.*?</h1>(?<content>.*?)<div\b[^>]*class=["''][^"'']*\bet_pb_column_1_3\b')
  }
  if (-not $contentMatch.Success) {
    $contentMatch = [regex]::Match($response.Content, '(?is)<article\b[^>]*>(?<content>.*?)</article>')
  }
  if (-not $contentMatch.Success) { throw "No <main> or <article> element found at $StartUrl." }
  $scopedHtml = $contentMatch.Groups['content'].Value
  @([regex]::Matches($scopedHtml, '(?is)<a\b[^>]*?\bhref\s*=\s*(?<quote>["''])(?<href>.*?)\k<quote>[^>]*>(?<text>.*?)</a>') | ForEach-Object {
    $anchorText = [Net.WebUtility]::HtmlDecode(($_.Groups['text'].Value -replace '<[^>]+>', ' '))
    $anchorText = ($anchorText -replace '\s+',' ').Trim()
    if ($anchorText -match '(?i)^(visit the project page|click here|here)(\b|\.)') {
      $prefix = $scopedHtml.Substring(0, $_.Index)
      $headings = [regex]::Matches($prefix, '(?is)<h[2-4]\b[^>]*>(?<text>.*?)</h[2-4]>')
      if ($headings.Count) {
        $contextHeading = [Net.WebUtility]::HtmlDecode(($headings[$headings.Count - 1].Groups['text'].Value -replace '<[^>]+>', ' '))
        $contextHeading = (($contextHeading -replace '[+]',' ') -replace '\s+',' ').Trim()
        if ($contextHeading) { $anchorText = $contextHeading }
      }
    }
    [pscustomobject]@{
      href = [Net.WebUtility]::HtmlDecode($_.Groups['href'].Value)
      innerText = $anchorText
    }
  })
} else {
  @($response.Links)
}
foreach ($link in $pageLinks) {
  try { $absoluteUrl = [uri]::new($base,$link.href).AbsoluteUri } catch { continue }
  if (-not $absoluteUrl -or $absoluteUrl -match 'translate\.google|javascript:|mailto:') { continue }
  $innerTextProperty = $link.PSObject.Properties['innerText']
  if ($innerTextProperty) {
    $anchorText = [string]$innerTextProperty.Value
  } else {
    $outerHtmlProperty = $link.PSObject.Properties['outerHTML']
    $anchorText = if ($outerHtmlProperty) { [Net.WebUtility]::HtmlDecode(([string]$outerHtmlProperty.Value -replace '<[^>]+>',' ')) } else { '' }
  }
  $anchorText = ($anchorText -replace '\s+',' ').Trim()
  if (-not $candidateMap.Contains($absoluteUrl) -or (-not $candidateMap[$absoluteUrl] -and $anchorText)) {
    $candidateMap[$absoluteUrl] = $anchorText
  }
}
$links = @($candidateMap.Keys | Sort-Object)
$candidates = @($links | ForEach-Object {
  [ordered]@{url=$_;anchor_text=[string]$candidateMap[$_]}
})
$directory = Split-Path -Parent $OutputPath
if ($directory) { New-Item -ItemType Directory -Force $directory | Out-Null }
[ordered]@{agency=$Agency;source_url=$StartUrl;scope=if($MainOnly){'main-content'}else{'whole-page'};retrieved_at=(Get-Date).ToUniversalTime().ToString('o');links=$links;candidates=$candidates} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{Agency=$Agency;StartUrl=$StartUrl;Links=$links.Count;OutputPath=$OutputPath}|ConvertTo-Json -Compress

