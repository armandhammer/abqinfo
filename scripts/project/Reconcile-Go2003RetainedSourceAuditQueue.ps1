[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$QueuePath = 'project-state/discovery/retained-source-audit-queue.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$queue = Get-Content -Raw -Encoding UTF8 -LiteralPath $QueuePath | ConvertFrom-Json
$eligible = @($inventory.candidates | Where-Object {
  $_.status -in @('implemented','validated') -and
  $_.source_url -match '^https?://' -and
  $_.source_url -notmatch '^https://files\.abqinfo\.com/' -and
  $_.source_url -notmatch '(?i)\.(pdf|docx?|xlsx?|csv|zip)(?:[?#]|$)' -and
  ($_.file_type -match '(?i)HTML|web page|live service' -or ($_.direct_file_url -match '^https?://' -and $_.source_url -ne $_.direct_file_url))
})
$retired = @(
  'src-cae140d675779242','src-93085b1bc76f4709','src-d86965da6d5d26f2','src-7405cfc41e5500c4','src-57a1e412247c863d',
  'src-3dfd629f27870dc1','src-0782d8521e42a068','src-dc6e3fd3425cb32a','src-6735737588d294e0','src-724dd13839ecb166',
  'src-888427a6abc5edf0','src-96e217080e84c14e','src-ea516f826e5da86a','src-a24b9d451e022e8f','src-e7cd892adf805950',
  'src-321df68eff322421','src-e28f489ec0fba72f','src-6fc996f849849028','src-3c7653f64815b4ad','src-bd084d192e7b78ce',
  'src-3c9907796a0cfaf3','src-74326241e19c1551'
)
$now = (Get-Date).ToUniversalTime().ToString('o')
$removed = 0
$reassigned = 0
$records = foreach ($record in @($queue.records)) {
  if ([string]$record.candidate_id -notin $retired) { $record; continue }
  $replacement = @($eligible | Where-Object { $_.source_url -eq $record.source_url })
  if ($replacement.Count -eq 0) { $removed++; continue }
  $replacement = $replacement | Sort-Object id | Select-Object -First 1
  $record.candidate_id = [string]$replacement.id
  $record.title = [string]$replacement.title
  $record.agency = [string]$replacement.agency
  $record.canonical_page = [string]$replacement.proposed_canonical_page
  $record.updated_at = $now
  $reassigned++
  $record
}
$queue.records = @($records)
$queue.generated_at = $now
$counts = [ordered]@{}
foreach ($status in @($queue.allowed_statuses)) { $counts[$status] = @($queue.records | Where-Object audit_status -eq $status).Count }
$queue.counts = [pscustomobject]$counts
$next = @($queue.records | Where-Object audit_status -eq 'pending descendant crawl' | Select-Object -First 1)
$queue.next_pending_source_url = if ($next.Count) { [string]$next[0].source_url } else { $null }
$fullPath = [IO.Path]::GetFullPath($QueuePath)
$temporaryPath = "$fullPath.tmp-$PID"
[IO.File]::WriteAllText($temporaryPath,($queue | ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
[pscustomobject]@{removed=$removed;reassigned=$reassigned;records=@($queue.records).Count}|ConvertTo-Json -Compress
