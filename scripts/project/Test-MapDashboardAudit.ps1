[CmdletBinding()]
param(
  [string]$QueuePath = 'project-state/discovery/map-dashboard-interactive-audit-queue.json',
  [string]$ContentRoot = 'content'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$queue = Get-Content -Raw -Encoding UTF8 -LiteralPath $QueuePath | ConvertFrom-Json
$allowed = @('validated usable','retired or broken','metadata only')
$issues = [System.Collections.Generic.List[string]]::new()
if (@($queue.items).Count -ne 66) { $issues.Add("Expected 66 audited links, found $(@($queue.items).Count).") }
foreach ($item in $queue.items) {
  if ([string]$item.audit_status -notin $allowed) { $issues.Add("$($item.id) has nonterminal status '$($item.audit_status)'.") }
  if (-not $item.checked_at -or -not $item.rendered_validation) { $issues.Add("$($item.id) lacks rendered validation evidence.") }
}
$content = (Get-ChildItem -LiteralPath $ContentRoot -Recurse -File -Filter '*.md' | ForEach-Object { Get-Content -Raw -Encoding UTF8 -LiteralPath $_.FullName }) -join "`n"
foreach ($item in $queue.items | Where-Object audit_status -eq 'retired or broken') {
  if ($content.Contains([string]$item.url)) { $issues.Add("Broken link remains implemented: $($item.url)") }
}
[pscustomobject]@{
  Links = @($queue.items).Count
  ValidatedUsable = @($queue.items | Where-Object audit_status -eq 'validated usable').Count
  MetadataOnly = @($queue.items | Where-Object audit_status -eq 'metadata only').Count
  RemovedBroken = @($queue.items | Where-Object audit_status -eq 'retired or broken').Count
  Issues = $issues.Count
} | ConvertTo-Json -Compress
if ($issues.Count) { $issues | ForEach-Object { Write-Error $_ }; exit 1 }
