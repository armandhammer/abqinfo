[CmdletBinding()]
param(
  [Parameter(Mandatory)][string[]]$CrawlPath,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-StableId([string]$Value, [int]$Length = 16) {
  $bytes = [Text.Encoding]::UTF8.GetBytes($Value.Trim().ToLowerInvariant())
  $sha = [Security.Cryptography.SHA256]::Create()
  try { $hash = $sha.ComputeHash($bytes) } finally { $sha.Dispose() }
  return 'src-' + (-join ($hash | ForEach-Object { $_.ToString('x2') })).Substring(0,$Length)
}

function Get-NormalizedUrl([string]$Value) {
  $builder = [UriBuilder]$Value
  $builder.Fragment = ''
  if ([string]::IsNullOrWhiteSpace($builder.Query) -or $builder.Query -eq '?') { $builder.Query = '' }
  return $builder.Uri.AbsoluteUri.TrimEnd('/')
}

function Get-FileType([uri]$Uri) {
  switch -Regex ($Uri.AbsolutePath.ToLowerInvariant()) {
    '\.pdf$' { return 'PDF' }
    '\.docx?$' { return 'DOCX' }
    '\.xlsx?$' { return 'XLSX' }
    '\.csv$' { return 'CSV' }
    '\.zip$' { return 'ZIP' }
    '\.(kml|kmz|shp)$' { return 'Geospatial file' }
    '\.(png|jpe?g|gif|webp)$' { return 'Image' }
    default { return 'Web page or live service' }
  }
}

function Get-Agency([uri]$Uri, [string]$CrawlAgency) {
  if ($Uri.Host -match '(^|\.)bernco\.gov$') { return 'Bernalillo County' }
  if ($Uri.Host -match '(^|\.)flh\.fhwa\.dot\.gov$') { return 'Federal Highway Administration' }
  if ($CrawlAgency -eq 'bernco') { return 'Bernalillo County' }
  return $CrawlAgency
}

function Get-Title([string]$AnchorText, [uri]$Uri) {
  $title = ($AnchorText -replace '<[^>]+>',' ' -replace '\s+',' ').Trim()
  if ($title -and $title -notmatch '^https?://') { return $title }
  $segment = [Uri]::UnescapeDataString($Uri.Segments[-1].Trim('/'))
  if (-not $segment) { return 'Title pending source review' }
  return (($segment -replace '\.[^.]+$','' -replace '[-_]',' ') -replace '\s+',' ').Trim()
}

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$knownUrls = @{}
$knownIds = @{}
foreach ($record in @($inventory.candidates)) {
  $knownIds[[string]$record.id] = $true
  foreach ($url in @($record.source_url,$record.direct_file_url)) {
    if (-not $url -or $url -notmatch '^https?://') { continue }
    try { $knownUrls[(Get-NormalizedUrl ([string]$url)).ToLowerInvariant()] = $true } catch {}
  }
}

$added = [Collections.Generic.List[object]]::new()
$now = (Get-Date).ToUniversalTime().ToString('o')
foreach ($path in $CrawlPath) {
  $crawl = Get-Content -Raw -Encoding UTF8 -LiteralPath $path | ConvertFrom-Json
  foreach ($candidate in @($crawl.candidates)) {
    try {
      $url = Get-NormalizedUrl ([string]$candidate.url)
      $uri = [uri]$url
    } catch { continue }
    if ($uri.Scheme -notin @('http','https')) { continue }
    $key = $url.ToLowerInvariant()
    if ($knownUrls.ContainsKey($key)) { continue }
    $fileType = Get-FileType $uri
    $parentUrl = if ($candidate.parent_url) { [string]$candidate.parent_url } else { [string]$crawl.source_url }
    $id = Get-StableId $url
    if ($knownIds.ContainsKey($id)) { $id = Get-StableId $url 20 }
    $record = [pscustomobject][ordered]@{
      id = $id
      status = 'pending review'
      source_url = $url
      direct_file_url = if ($fileType -notin @('Web page or live service','Image')) { $url } else { $null }
      r2_url = $null
      r2_key = $null
      r2_etag = $null
      r2_last_modified = $null
      agency = Get-Agency $uri ([string]$crawl.agency)
      title = Get-Title ([string]$candidate.anchor_text) $uri
      date = $null
      file_type = $fileType
      size_bytes = $null
      checksum_sha256 = $null
      parent_url = $parentUrl
      referring_urls = @($parentUrl)
      discovery_path = if ($candidate.discovery_path) { @($candidate.discovery_path) } else { @([string]$crawl.source_url,$parentUrl,$url) | Select-Object -Unique }
      discovery_method = if ($candidate.discovery_method) { [string]$candidate.discovery_method } else { 'scoped authored link' }
      crawl_depth = if ($null -ne $candidate.discovery_depth) { [int]$candidate.discovery_depth } else { $null }
      cited_predecessors = @()
      cited_successors = @()
      provenance_status = 'source URL recorded from authoritative project graph'
      proposed_canonical_page = $null
      description = $null
      description_word_count = 0
      processing_notes = @("Imported from deterministic scoped crawl $path.", 'Exact metadata, relevance, and terminal disposition remain pending review.')
      implementation_location = $null
      implementation_locations = @()
      cross_listing_approved = $false
      validation_status = 'not run'
      exclusion_reason = $null
      local_path = $null
      discovered_at = $now
      updated_at = $now
    }
    $added.Add($record)
    $knownUrls[$key] = $true
    $knownIds[$id] = $true
  }
}

if ($added.Count) { $inventory.candidates = @($inventory.candidates) + @($added) | Sort-Object id }
$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = $now
$next = @($inventory.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { [string]$next[0].id } else { $null }

$fullPath = [IO.Path]::GetFullPath($InventoryPath)
$temporaryPath = "$fullPath.tmp-$PID"
[IO.File]::WriteAllText($temporaryPath, ($inventory | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
[pscustomobject]@{Added=$added.Count;Total=@($inventory.candidates).Count;NextPending=$inventory.next_pending_id} | ConvertTo-Json -Compress
