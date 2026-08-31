[CmdletBinding()]
param(
  [string]$ContentRoot = 'content',
  [string]$OutputPath = 'project-state/discovery/map-dashboard-interactive-audit-queue.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'PowerShell 7 or newer is required to preserve canonical JSON formatting.' }

$pattern = '\[([^\]]+)\]\((https?://[^\s\)]+)\)'
$signals = '(?i)(\bmap\b|\bmaps\b|\bdashboard\b|\bviewer\b|arcgis|experience|hub\.arcgis|dmdmaps|mrcogmaps|tipviewer|stipviewer)'
$records = [System.Collections.Generic.List[object]]::new()
$workspaceRoot = (Get-Location).Path.TrimEnd('\')

foreach ($file in Get-ChildItem -LiteralPath $ContentRoot -Recurse -File -Filter '*.md' | Sort-Object FullName) {
  if (-not $file.FullName.StartsWith("$workspaceRoot\",[StringComparison]::OrdinalIgnoreCase)) { throw "Content file is outside the workspace: $($file.FullName)" }
  $relative = $file.FullName.Substring($workspaceRoot.Length + 1).Replace('\','/')
  $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $file.FullName
  foreach ($match in [regex]::Matches($text,$pattern)) {
    $label = $match.Groups[1].Value.Trim()
    $url = $match.Groups[2].Value.TrimEnd('.')
    if ("$label $url" -notmatch $signals) { continue }
    if ($url -match '(?i)\.(pdf|png|jpe?g|gif|svg)(\?|$)') { continue }
    if ($url -match '(?i)/api/reports/') { continue }
    $records.Add([pscustomobject]@{
      label = $label
      url = $url
      implementation_location = $relative
    })
  }
}

$previous = if (Test-Path -LiteralPath $OutputPath) { Get-Content -Raw -Encoding UTF8 -LiteralPath $OutputPath | ConvertFrom-Json } else { $null }
$previousByUrl = @{}
if ($previous) { foreach ($item in $previous.items) { $previousByUrl[[string]$item.url] = $item } }

$grouped = [System.Collections.Generic.List[object]]::new()
foreach ($group in $records | Group-Object url | Sort-Object Name) {
  $url = [string]$group.Name
  $bytes = [Text.Encoding]::UTF8.GetBytes($url.ToLowerInvariant())
  $sha = [Security.Cryptography.SHA256]::Create()
  try { $hash = $sha.ComputeHash($bytes) } finally { $sha.Dispose() }
  $prior = $previousByUrl[$url]
  $grouped.Add([pscustomobject]@{
    id = 'interactive-' + ([BitConverter]::ToString($hash).Replace('-','').ToLowerInvariant().Substring(0,16))
    url = $url
    labels = @($group.Group.label | Sort-Object -Unique)
    implementation_locations = @($group.Group.implementation_location | Sort-Object -Unique)
    in_current_scope = $true
    audit_status = if ($prior) { [string]$prior.audit_status } else { 'pending interactive review' }
    http_validation = if ($prior) { $prior.http_validation } else { $null }
    rendered_validation = if ($prior) { $prior.rendered_validation } else { $null }
    checked_at = if ($prior) { $prior.checked_at } else { $null }
    notes = if ($prior) { @($prior.notes) } else { @('HTTP success and public ArcGIS metadata are insufficient; confirm that the visible map or dashboard renders usable content and is not a retired, replacement, sign-in, metadata-only, or error page.') }
  })
}
if ($previous) {
  $currentUrls = @{}; foreach ($item in $grouped) { $currentUrls[[string]$item.url] = $true }
  foreach ($prior in $previous.items | Where-Object { -not $currentUrls.ContainsKey([string]$_.url) }) {
    if ([string]$prior.audit_status -in @('pending interactive review','requires human review')) { continue }
    $prior | Add-Member -NotePropertyName in_current_scope -NotePropertyValue $false -Force
    $prior.notes = @($prior.notes) + @('Retained as terminal audit history after the link left the current interactive-map scope.') | Sort-Object -Unique
    $grouped.Add($prior)
  }
}

$statuses = @('pending interactive review','validated usable','retired or broken','metadata only','requires human review')
$counts = [ordered]@{}; foreach ($status in $statuses) { $counts[$status] = @($grouped | Where-Object audit_status -eq $status).Count }
$nextPending = @($grouped | Where-Object audit_status -eq 'pending interactive review' | Select-Object -First 1)
$output = [ordered]@{
  schema_version = 1
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  purpose = 'Rendered-browser audit of every map and dashboard link implemented on ABQInfo.'
  status_definitions = $statuses
  total = @($grouped).Count
  counts = $counts
  next_pending_id = if ($nextPending.Count) { [string]$nextPending[0].id } else { $null }
  items = @($grouped)
}

$json = $output | ConvertTo-Json -Depth 8
$full = [IO.Path]::GetFullPath($OutputPath)
$temporary = "$full.tmp-$PID"
[IO.File]::WriteAllText($temporary,$json,[Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporary -Destination $full -Force
$output | ConvertTo-Json -Compress -Depth 4
