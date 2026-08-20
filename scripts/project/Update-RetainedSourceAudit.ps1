[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$SourceUrl,
  [Parameter(Mandatory)][ValidateSet('pending descendant crawl','crawled','requires rendered-browser review','excluded','superseded')][string]$AuditStatus,
  [string]$CrawlOutput,
  [ValidateRange(0,100000)][int]$DiscoveredDocuments = 0,
  [ValidateRange(0,100000)][int]$ArchivedDocuments = 0,
  [string[]]$ProcessingNotes = @(),
  [string]$QueuePath = 'project-state/discovery/retained-source-audit-queue.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$queue = Get-Content -Raw -LiteralPath $QueuePath | ConvertFrom-Json
$record = @($queue.records | Where-Object source_url -eq $SourceUrl)
if ($record.Count -ne 1) { throw "Expected one retained-source record for '$SourceUrl'; found $($record.Count)." }
$record = $record[0]
$record.audit_status = $AuditStatus
$record.crawl_output = if ($CrawlOutput) { $CrawlOutput } else { $record.crawl_output }
$record.discovered_documents = $DiscoveredDocuments
$record.archived_documents = $ArchivedDocuments
$record.processing_notes = @(@($record.processing_notes) + $ProcessingNotes | Sort-Object -Unique)
$record.updated_at = (Get-Date).ToUniversalTime().ToString('o')

$counts = [ordered]@{}
foreach ($status in @($queue.allowed_statuses)) { $counts[[string]$status] = @($queue.records | Where-Object audit_status -eq $status).Count }
$queue.counts = [pscustomobject]$counts
$next = @($queue.records | Where-Object audit_status -eq 'pending descendant crawl' | Sort-Object source_url | Select-Object -First 1)
$queue.next_pending_source_url = if ($next.Count) { [string]$next[0].source_url } else { $null }
$queue.generated_at = (Get-Date).ToUniversalTime().ToString('o')

$fullPath = [IO.Path]::GetFullPath($QueuePath)
$temporaryPath = "$fullPath.tmp-$PID"
[IO.File]::WriteAllText($temporaryPath, ($queue | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
[IO.File]::Move($temporaryPath, $fullPath, $true)
$record | ConvertTo-Json -Depth 8
