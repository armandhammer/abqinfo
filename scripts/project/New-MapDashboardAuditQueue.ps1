[CmdletBinding()]
param(
  [string]$ContentRoot = 'content',
  [string]$OutputPath = 'project-state/discovery/map-dashboard-interactive-audit-queue.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$pattern = '\[([^\]]+)\]\((https?://[^\s\)]+)\)'
$signals = '(?i)(map|dashboard|viewer|arcgis|experience|hub\.arcgis|dmdmaps|mrcogmaps|tipviewer|stipviewer)'
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
    $records.Add([pscustomobject]@{
      label = $label
      url = $url
      implementation_location = $relative
    })
  }
}

$grouped = foreach ($group in $records | Group-Object url | Sort-Object Name) {
  $url = [string]$group.Name
  $bytes = [Text.Encoding]::UTF8.GetBytes($url.ToLowerInvariant())
  $sha = [Security.Cryptography.SHA256]::Create()
  try { $hash = $sha.ComputeHash($bytes) } finally { $sha.Dispose() }
  [pscustomobject]@{
    id = 'interactive-' + ([BitConverter]::ToString($hash).Replace('-','').ToLowerInvariant().Substring(0,16))
    url = $url
    labels = @($group.Group.label | Sort-Object -Unique)
    implementation_locations = @($group.Group.implementation_location | Sort-Object -Unique)
    audit_status = 'pending interactive review'
    http_validation = $null
    rendered_validation = $null
    checked_at = $null
    notes = @('HTTP success and public ArcGIS metadata are insufficient; confirm that the visible map or dashboard renders usable content and is not a retired, replacement, sign-in, metadata-only, or error page.')
  }
}

$output = [ordered]@{
  schema_version = 1
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  purpose = 'Rendered-browser audit of every map and dashboard link implemented on ABQInfo.'
  status_definitions = @('pending interactive review','validated usable','retired or broken','metadata only','requires human review')
  total = @($grouped).Count
  counts = [ordered]@{'pending interactive review'=@($grouped).Count;'validated usable'=0;'retired or broken'=0;'metadata only'=0;'requires human review'=0}
  next_pending_id = if (@($grouped).Count) { [string]$grouped[0].id } else { $null }
  items = @($grouped)
}

$json = $output | ConvertTo-Json -Depth 8
$full = [IO.Path]::GetFullPath($OutputPath)
$temporary = "$full.tmp-$PID"
[IO.File]::WriteAllText($temporary,$json,[Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporary -Destination $full -Force
$output | ConvertTo-Json -Compress -Depth 4
