[CmdletBinding()]
param(
  [string]$BenchmarkPath = 'project-state/discovery/bicycle-history-benchmarks.json',
  [string]$SourceCrawlPath = 'project-state/discovery/cabq-bicycle-history-bounded-collection-crawl.json',
  [string]$SourcePdfPath = 'research/staging/lineage/src-0b1dfe6e620d7fe0.pdf',
  [string]$SourcePdfUrl = 'https://www.cabq.gov/planning/documents/2024-bikeway-and-trail-facilities-plan.pdf',
  [string]$PythonPath = 'python',
  [string]$OutputPath = 'project-state/discovery/cabq-bicycle-history-pdf-lineage-crawl.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-OptionalProperty($Object, [string]$Name) {
  $property = $Object.PSObject.Properties[$Name]
  if ($property) { return $property.Value }
  return $null
}

function Get-CompactEvidence([string]$Text, [string]$Pattern) {
  $match = [regex]::Match($Text, "(?is).{0,220}(?:$Pattern).{0,360}")
  if (-not $match.Success) { return $null }
  return ([regex]::Replace($match.Value, '\s+', ' ')).Trim()
}

$benchmarks = Get-Content -Raw -Encoding UTF8 -LiteralPath $BenchmarkPath | ConvertFrom-Json
$sourceState = Get-Content -Raw -Encoding UTF8 -LiteralPath $SourceCrawlPath | ConvertFrom-Json
$sourceCandidates = @($sourceState.candidates | Where-Object { ([string]$_.url).TrimEnd('/') -eq $SourcePdfUrl.TrimEnd('/') })
if (-not $sourceCandidates.Count) { throw "Source crawl does not contain the official 2024 plan: $SourcePdfUrl" }
$sourceCandidate = $sourceCandidates | Sort-Object { @($_.discovery_path).Count } | Select-Object -First 1

if (-not (Test-Path -LiteralPath $SourcePdfPath)) { throw "Source PDF is missing: $SourcePdfPath" }
$extractorPath = Join-Path $PSScriptRoot 'extract_pdf.py'
$parsed = (& $PythonPath $extractorPath $SourcePdfPath) | ConvertFrom-Json
if (-not $parsed -or -not $parsed.text) { throw "PDF extraction failed for $SourcePdfPath" }

$candidates = [Collections.Generic.List[object]]::new()
$diagnostics = [Collections.Generic.List[object]]::new()
$sourcePath = @($sourceCandidate.discovery_path)
$sourceDepth = [int]$sourceCandidate.discovery_depth

foreach ($benchmark in $benchmarks) {
  $directPattern = [string](Get-OptionalProperty $benchmark 'authoritative_url_pattern')
  $lineagePattern = [string](Get-OptionalProperty $benchmark 'lineage_evidence_pattern')
  $recovered = $false

  if ($directPattern) {
    $matchingLinks = @($parsed.links | Where-Object { [string]$_.url -match $directPattern })
    foreach ($link in $matchingLinks) {
      $candidates.Add([ordered]@{
        url = [string]$link.url
        anchor_text = [string]$benchmark.title
        title = [string]$benchmark.title
        benchmark_id = [string]$benchmark.id
        recovery_kind = 'authoritative file link'
        parent_url = $SourcePdfUrl
        referring_urls = @($SourcePdfUrl)
        discovery_path = @($sourcePath) + @("pdf-embedded-link:page:$([int]$link.page)", [string]$link.url)
        discovery_method = 'PDF embedded-link extraction from blindly graph-discovered official plan'
        discovery_depth = $sourceDepth + 1
        agency = 'City of Albuquerque'
        file_type = 'PDF'
        evidence_url = $SourcePdfUrl
        evidence = "Official 2024 plan embedded PDF link on page $([int]$link.page)."
        provenance_status = 'official City lineage and historical file URL recovered; live-file identity not established'
        processing_notes = @('Recovered from an embedded link in the authoritative 2024 plan without an exact-title or general web search.')
      })
      $recovered = $true
    }
  }

  if (-not $recovered -and $lineagePattern) {
    $evidence = Get-CompactEvidence $parsed.text $lineagePattern
    if ($evidence) {
      $candidates.Add([ordered]@{
        url = $SourcePdfUrl
        anchor_text = [string]$benchmark.title
        title = [string]$benchmark.title
        benchmark_id = [string]$benchmark.id
        recovery_kind = 'official lineage evidence'
        parent_url = $SourcePdfUrl
        referring_urls = @($SourcePdfUrl)
        discovery_path = @($sourcePath) + @("pdf-text:$SourcePdfPath", "lineage:$([string]$benchmark.title)")
        discovery_method = 'PDF text lineage extraction from blindly graph-discovered official plan'
        discovery_depth = $sourceDepth + 1
        agency = 'City of Albuquerque'
        file_type = 'Historical plan named in official successor PDF'
        evidence_url = $SourcePdfUrl
        evidence = $evidence
        provenance_status = 'official City existence and succession confirmed; historical file origin not established'
        processing_notes = @('The official successor plan names this historical plan; this confirms lineage but not the provenance of the preserved R2 file.')
      })
      $recovered = $true
    }
  }

  if (-not $recovered) {
    $diagnostics.Add([ordered]@{
      benchmark_id = [string]$benchmark.id
      title = [string]$benchmark.title
      status = 'not recovered from source PDF'
      notes = 'No matching embedded authoritative-file link or configured lineage-evidence passage was found in the blindly discovered 2024 plan.'
    })
  }
}

$output = [ordered]@{
  agency = 'City of Albuquerque'
  source_url = [string]$sourceState.source_url
  scope = 'bounded bicycle-history PDF lineage expansion'
  retrieved_at = (Get-Date).ToUniversalTime().ToString('o')
  source_pdf_url = $SourcePdfUrl
  source_pdf_path = $SourcePdfPath
  source_discovery_path = @($sourcePath)
  source_pdf_pages = [int]$parsed.pages
  source_pdf_embedded_link_records = @($parsed.links).Count
  candidates = @($candidates)
  diagnostics = @($diagnostics)
}

$output | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $OutputPath -Encoding utf8
$output | ConvertTo-Json -Depth 6 -Compress
