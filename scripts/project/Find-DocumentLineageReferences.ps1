[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$SourceCandidateId,
  [Parameter(Mandatory)][string]$TextPath,
  [string]$SourceUrl,
  [string]$OutputPath = 'project-state/discovery/pdf-lineage-references.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $TextPath)) { throw "Text extraction not found: $TextPath" }

function Get-StableId([string]$Value) {
  $bytes = [Text.Encoding]::UTF8.GetBytes($Value)
  $sha = [Security.Cryptography.SHA256]::Create()
  try { $hash = $sha.ComputeHash($bytes) } finally { $sha.Dispose() }
  $hex = -join ($hash | ForEach-Object { $_.ToString('x2') })
  return 'lin-' + $hex.Substring(0,16)
}

$relationPattern = '(?i)\b(update[sd]?|amend(?:s|ed)?|replace[sd]?|supersed(?:e[sd]?|ing)|consolidat(?:e[sd]?|ing)|implement(?:s|ed|ing)?|adopt(?:s|ed|ing)?\s+by|appendix|supporting\s+stud(?:y|ies)|previous\s+plan|combined\s+and\s+updated|maintained\s+from)\b'
$documentPattern = '\b(?<title>(?:[A-Z0-9][A-Za-z0-9&/\-’'']*\s+){1,11}(?:Plan|Study|Report|Manual|Guide|Toolkit|Ordinance|Resolution|Appendix|System|Program))(?:\s*\((?<year>(?:19|20)\d{2})\))?'
$lines = @(Get-Content -LiteralPath $TextPath)
$references = [ordered]@{}

for ($i = 0; $i -lt $lines.Count; $i++) {
  $line = $lines[$i].Trim()
  if (-not $line -or $line -notmatch $relationPattern) { continue }
  $windowStart = [Math]::Max(0, $i - 4)
  $windowEnd = [Math]::Min($lines.Count - 1, $i + 4)
  $evidence = (($lines[$windowStart..$windowEnd] -join ' ') -replace '-\s+([a-z])','$1' -replace '\s+',' ').Trim()
  foreach ($match in [regex]::Matches($evidence, $documentPattern)) {
    $title = ($match.Groups['title'].Value -replace '\s+',' ').Trim()
    $year = $match.Groups['year'].Value
    if ($title.Length -lt 8 -or $title.Length -gt 140) { continue }
    $relationMatch = [regex]::Match($line, $relationPattern)
    $relation = if ($relationMatch.Success) { $relationMatch.Value.ToLowerInvariant() } else { 'referenced' }
    $key = "$SourceCandidateId|$title|$year|$relation"
    $id = Get-StableId $key
    if (-not $references.Contains($id)) {
      $references[$id] = [ordered]@{
        id = $id
        source_candidate_id = $SourceCandidateId
        source_document_url = $SourceUrl
        source_url = $null
        direct_file_url = $null
        parent_url = $SourceUrl
        referring_urls = @($SourceUrl)
        discovery_path = @($SourceUrl, "pdf-text:$($TextPath.Replace('\','/'))", "lineage:$title")
        extracted_text_path = $TextPath.Replace('\','/')
        agency = if ($SourceUrl -match '(?i)cabq\.gov') { 'City of Albuquerque' } else { 'Pending source review' }
        title = $title
        referenced_title = $title
        date = if ($year) { $year } else { $null }
        referenced_date = if ($year) { $year } else { $null }
        file_type = 'Unknown referenced document type'
        size_bytes = $null
        checksum_sha256 = $null
        relation = $relation
        evidence = $evidence
        discovery_method = 'PDF text lineage extraction'
        crawl_depth = $null
        cited_predecessors = @()
        cited_successors = @()
        proposed_canonical_page = $null
        processing_notes = @('Named document reference extracted from an in-scope official plan; authoritative source lookup remains queued.')
        exclusion_reason = $null
        status = 'pending review'
        discovered_at = (Get-Date).ToUniversalTime().ToString('o')
      }
    }
  }
}

$existing = @()
if (Test-Path -LiteralPath $OutputPath) {
  $parsed = Get-Content -Raw -LiteralPath $OutputPath | ConvertFrom-Json
  $existing = @($parsed.references | Where-Object { $_.source_candidate_id -ne $SourceCandidateId })
}
$combined = [ordered]@{}
foreach ($item in @($existing) + @($references.Values)) { $combined[[string]$item.id] = $item }

$directory = Split-Path -Parent $OutputPath
if ($directory) { New-Item -ItemType Directory -Force $directory | Out-Null }
[ordered]@{
  schema_version = 1
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  references = @($combined.Values | Sort-Object referenced_title, referenced_date)
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8

[pscustomobject]@{
  SourceCandidateId = $SourceCandidateId
  ReferencesFound = $references.Count
  TotalReferences = $combined.Count
  OutputPath = $OutputPath
} | ConvertTo-Json -Compress
