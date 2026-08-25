[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OutputPath = 'project-state/discovery/retained-source-audit-queue.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$allowedStatuses = @('pending descendant crawl','crawled','requires rendered-browser review','excluded','superseded')
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$existingMap = @{}
if (Test-Path -LiteralPath $OutputPath) {
  $prior = Get-Content -Raw -Encoding UTF8 -LiteralPath $OutputPath | ConvertFrom-Json
  foreach ($record in @($prior.records)) { $existingMap[[string]$record.source_url] = $record }
}

$now = (Get-Date).ToUniversalTime().ToString('o')
$records = foreach ($candidate in @($inventory.candidates | Where-Object {
  $_.status -in @('implemented','validated') -and
  $_.source_url -match '^https?://' -and
  $_.source_url -notmatch '^https://files\.abqinfo\.com/' -and
  $_.source_url -notmatch '(?i)\.(pdf|docx?|xlsx?|csv|zip)(?:[?#]|$)' -and
  ($_.file_type -match '(?i)HTML|web page|live service' -or
    ($_.direct_file_url -match '^https?://' -and $_.source_url -ne $_.direct_file_url))
})) {
  $sourceUrl = [string]$candidate.source_url
  if ($existingMap.ContainsKey($sourceUrl)) {
    $prior = $existingMap[$sourceUrl]
    if ([string]$prior.audit_status -notin $allowedStatuses) { throw "Invalid audit status for $sourceUrl." }
    $prior
    continue
  }
  [pscustomobject][ordered]@{
    candidate_id = [string]$candidate.id
    source_url = $sourceUrl
    title = [string]$candidate.title
    agency = [string]$candidate.agency
    canonical_page = [string]$candidate.proposed_canonical_page
    audit_status = 'pending descendant crawl'
    crawl_output = $null
    discovered_documents = 0
    archived_documents = 0
    processing_notes = @('A retained active source page must be recursively reviewed for relevant child pages and attached files before its descendant pathway is considered exhausted.')
    created_at = $now
    updated_at = $now
  }
}

$records = @($records | Group-Object source_url | ForEach-Object { $_.Group | Select-Object -First 1 } | Sort-Object source_url)
$counts = [ordered]@{}
foreach ($status in $allowedStatuses) { $counts[$status] = @($records | Where-Object audit_status -eq $status).Count }
$next = @($records | Where-Object audit_status -eq 'pending descendant crawl' | Select-Object -First 1)
$queue = [ordered]@{
  schema_version = 1
  generated_at = $now
  policy = 'Every retained active government webpage is a document-discovery root. Recursively review relevant child pages and archive qualifying attached documents; access-controlled pages require rendered-browser review rather than silent completion.'
  allowed_statuses = $allowedStatuses
  counts = $counts
  next_pending_source_url = if ($next.Count) { [string]$next[0].source_url } else { $null }
  records = $records
}

$directory = Split-Path -Parent $OutputPath
if ($directory) { New-Item -ItemType Directory -Force $directory | Out-Null }
$fullPath = [IO.Path]::GetFullPath($OutputPath)
$temporaryPath = "$fullPath.tmp-$PID"
[IO.File]::WriteAllText($temporaryPath, ($queue | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
[pscustomobject]@{Records=$records.Count;Pending=$counts['pending descendant crawl'];OutputPath=$OutputPath}|ConvertTo-Json -Compress
