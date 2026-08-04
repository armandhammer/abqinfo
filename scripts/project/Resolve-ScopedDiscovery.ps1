[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OutputPath = 'research/discovery/scoped-linked-content.json',
  [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-PlainText([string]$Html) {
  if ([string]::IsNullOrWhiteSpace($Html)) { return '' }
  $value = $Html -replace '(?is)<(script|style)\b.*?</\1>', ' '
  $value = $value -replace '(?is)<[^>]+>', ' '
  $value = [Net.WebUtility]::HtmlDecode($value)
  return ($value -replace '\s+', ' ').Trim()
}

function Get-ContentRegion([string]$Html) {
  $match = [regex]::Match($Html, '(?is)<main\b[^>]*>(?<content>.*?)</main>')
  if (-not $match.Success) { $match = [regex]::Match($Html, '(?is)<article\b[^>]*>(?<content>.*?)</article>') }
  if ($match.Success) { return $match.Groups['content'].Value }
  return $Html
}

function Get-Links([string]$Html, [uri]$BaseUri) {
  $values = foreach ($match in [regex]::Matches($Html, '(?is)<a\b[^>]*?\bhref\s*=\s*(?<quote>["''])(?<href>.*?)\k<quote>[^>]*>(?<text>.*?)</a>')) {
    $href = [Net.WebUtility]::HtmlDecode($match.Groups['href'].Value)
    if (-not $href -or $href -match '^(mailto:|tel:|fax:|javascript:|#)') { continue }
    try { $absolute = [uri]::new($BaseUri, $href).AbsoluteUri } catch { continue }
    if ($absolute -match '(?i)\.(png|jpe?g|gif|svg|webp)(\?|$)') { continue }
    [pscustomobject]@{ url=$absolute; anchor_text=Get-PlainText $match.Groups['text'].Value }
  }
  return @($values | Sort-Object url -Unique)
}

$inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json
$queue = @($inventory.candidates | Where-Object status -eq 'pending review' | Sort-Object id)
$records = [Collections.Generic.List[object]]::new()
if (-not $Force -and (Test-Path -LiteralPath $OutputPath)) {
  $prior = Get-Content -Raw -LiteralPath $OutputPath | ConvertFrom-Json
  foreach ($record in @($prior.records)) { $records.Add($record) }
}
$done = @{}
foreach ($record in $records) { $done[[string]$record.id] = $true }

$directory = Split-Path -Parent $OutputPath
if ($directory) { New-Item -ItemType Directory -Force $directory | Out-Null }

$processed = 0
foreach ($candidate in $queue) {
  if ($done.ContainsKey([string]$candidate.id)) { continue }
  $result = [ordered]@{
    id = $candidate.id
    source_url = $candidate.source_url
    retrieved_at = (Get-Date).ToUniversalTime().ToString('o')
    http_status = $null
    final_url = $null
    title = $candidate.title
    published = $null
    modified = $null
    content_type = $null
    content_length = $null
    text_word_count = 0
    text_excerpt = $null
    outgoing_links = @()
    error = $null
  }
  try {
    $response = Invoke-WebRequest -Uri $candidate.source_url -UseBasicParsing -MaximumRedirection 10
    $result.http_status = [int]$response.StatusCode
    $result.final_url = $response.BaseResponse.ResponseUri.AbsoluteUri
    $result.content_type = [string]$response.Headers['Content-Type']
    $lengthHeader = [string]$response.Headers['Content-Length']
    if ($lengthHeader -match '^\d+$') { $result.content_length = [int64]$lengthHeader }
    $body = [string]$response.Content
    $baseUri = [uri]$result.final_url
    $contentHtml = Get-ContentRegion $body

    $apiMatch = [regex]::Match($body, '(?is)<link\b[^>]*type=["'']application/json["''][^>]*href=["''](?<url>[^"'']+)["''][^>]*>')
    if ($apiMatch.Success) {
      $apiUrl = [Net.WebUtility]::HtmlDecode($apiMatch.Groups['url'].Value)
      $apiPage = Invoke-RestMethod -Uri $apiUrl
      if ($apiPage.content.rendered) { $contentHtml = [string]$apiPage.content.rendered }
      if ($apiPage.title.rendered) { $result.title = Get-PlainText ([string]$apiPage.title.rendered) }
      if ($apiPage.date) { $result.published = [string]$apiPage.date }
      if ($apiPage.modified) { $result.modified = [string]$apiPage.modified }
    } else {
      $heading = [regex]::Match($contentHtml, '(?is)<h1\b[^>]*>(?<title>.*?)</h1>')
      if ($heading.Success) { $result.title = Get-PlainText $heading.Groups['title'].Value }
    }

    $text = Get-PlainText $contentHtml
    $result.text_word_count = if ($text) { @($text -split '\s+' | Where-Object { $_ }).Count } else { 0 }
    $result.text_excerpt = if ($text.Length -gt 1800) { $text.Substring(0,1800) } else { $text }
    $result.outgoing_links = @(Get-Links $contentHtml $baseUri)
  } catch {
    $result.error = $_.Exception.Message
  }
  $records.Add([pscustomobject]$result)
  $done[[string]$candidate.id] = $true
  $processed++
  [ordered]@{
    schema_version = 1
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    queue_count = $queue.Count
    resolved_count = $records.Count
    records = @($records | Sort-Object id)
  } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
  if (($processed % 10) -eq 0) { Write-Host "Resolved $processed new candidates; $($records.Count) saved." }
}

[pscustomobject]@{Queue=$queue.Count;Resolved=$records.Count;NewlyProcessed=$processed;OutputPath=$OutputPath} | ConvertTo-Json -Compress
