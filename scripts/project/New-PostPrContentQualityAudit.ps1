[CmdletBinding()]
param(
  [int]$FromPr = 132,
  [int]$ToPr = 999999,
  [string]$GitRef = 'origin/main',
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [Parameter(Mandatory)][string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$candidateByUrl = @{}
foreach ($candidate in @($inventory.candidates)) {
  foreach ($candidateUrl in @($candidate.r2_url, $candidate.source_url, $candidate.direct_file_url)) {
    if (-not $candidateUrl) { continue }
    $key = [string]$candidateUrl
    if (-not $candidateByUrl.ContainsKey($key) -or ($candidate.r2_url -and -not $candidateByUrl[$key].r2_url)) {
      $candidateByUrl[$key] = $candidate
    }
  }
}

$mergeRows = & git log $GitRef --merges '--format=%H%x09%s'
$prCommits = @()
foreach ($row in @($mergeRows)) {
  if ($row -match '^([0-9a-f]+)\tMerge pull request #(\d+) ') {
    $number = [int]$Matches[2]
    if ($number -ge $FromPr -and $number -le $ToPr) {
      $prCommits += [pscustomobject]@{ number = $number; commit = $Matches[1] }
    }
  }
}

$entryMap = @{}
foreach ($pr in @($prCommits | Sort-Object number)) {
  $diff = @(& git diff "$($pr.commit)^1" $pr.commit -- 'content/**/*.md')
  $file = ''
  foreach ($line in $diff) {
    if ($line -match '^\+\+\+ b/(.+)$') {
      $file = $Matches[1]
      continue
    }
    if ($line -notmatch '^\+(?!\+)') { continue }
    $matches = [regex]::Matches($line, '\[([^\]]+)\]\((https://[^)]+)\)')
    foreach ($match in $matches) {
      $title = [string]$match.Groups[1].Value
      $url = [string]$match.Groups[2].Value
      $candidate = if ($candidateByUrl.ContainsKey($url)) { $candidateByUrl[$url] } else { $null }
      $candidateType = if ($candidate) { ([string]$candidate.file_type).ToUpperInvariant() } else { '' }
      $isStatic = $candidateType -in @('PDF','DOC','DOCX','XLS','XLSX','CSV','ZIP','TXT','JSON') -or $url -match '(?i)\.(pdf|docx?|xlsx?|csv|zip|txt|json)(?:[/?#]|$)'
      if (-not $isStatic) { continue }
      $key = "$($pr.number)|$file|$url"
      if (-not $entryMap.ContainsKey($key)) {
        $entryMap[$key] = [pscustomobject]@{
          pr = [int]$pr.number
          page = $file
          visible_title = $title
          linked_url = $url
          candidate_id = if ($candidate) { [string]$candidate.id } else { $null }
        }
      }
    }
  }
}

$documentMap = @{}
foreach ($entry in @($entryMap.Values)) {
  $candidate = if ($entry.candidate_id) { @($inventory.candidates | Where-Object id -eq $entry.candidate_id)[0] } else { $null }
  $documentKey = if ($candidate) { [string]$candidate.id } else { [string]$entry.linked_url }
  if (-not $documentMap.ContainsKey($documentKey)) {
    $documentMap[$documentKey] = [ordered]@{
      r2_url = if ($candidate) { [string]$candidate.r2_url } else { $null }
      linked_url = [string]$entry.linked_url
      candidate_id = if ($candidate) { [string]$candidate.id } else { $null }
      title = if ($candidate) { [string]$candidate.title } else { [string]$entry.visible_title }
      file_type = if ($candidate) { [string]$candidate.file_type } else { $null }
      size_bytes = if ($candidate -and $null -ne $candidate.size_bytes) { [int64]$candidate.size_bytes } else { $null }
      date = if ($candidate) { [string]$candidate.date } else { $null }
      source_url = if ($candidate) { [string]$candidate.source_url } else { $null }
      direct_file_url = if ($candidate) { [string]$candidate.direct_file_url } else { $null }
      description = if ($candidate) { [string]$candidate.description } else { $null }
      local_path = if ($candidate) { [string]$candidate.local_path } else { $null }
      introducing_prs = @()
      placements = @()
      quality_review = [ordered]@{
        status = 'pending manual review'
        standalone_value = $null
        information_density = $null
        aggregation_candidate = $null
        recommendation = $null
        rationale = $null
      }
    }
  }
  $document = $documentMap[$documentKey]
  $document.introducing_prs = @($document.introducing_prs + [int]$entry.pr | Sort-Object -Unique)
  $document.placements = @($document.placements + [pscustomobject]@{
    pr = [int]$entry.pr
    page = [string]$entry.page
    visible_title = [string]$entry.visible_title
    linked_url = [string]$entry.linked_url
  } | Sort-Object pr,page,visible_title -Unique)
}

$documents = @($documentMap.Values | ForEach-Object { [pscustomobject]$_ } | Sort-Object { $_.introducing_prs[0] }, title)
$result = [ordered]@{
  schema_version = 1
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  scope = [ordered]@{
    from_pr = $FromPr
    to_pr = $ToPr
    git_ref = $GitRef
    merged_prs_examined = @($prCommits | Sort-Object number)
    documents = $documents.Count
    visible_placements = @($entryMap.Values).Count
  }
  documents = $documents
}

$result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{
  MergedPrs = $prCommits.Count
  Documents = $documents.Count
  VisiblePlacements = @($entryMap.Values).Count
  OutputPath = $OutputPath
} | ConvertTo-Json -Compress
