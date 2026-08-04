[CmdletBinding()]
param(
  [Parameter(Mandatory)][ValidateSet('cabq','bernco','mrcog','nmdot')][string]$Agency,
  [Parameter(Mandatory)][string]$StartUrl,
  [string]$OutputPath = "research/discovery/$Agency-links.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$response = Invoke-WebRequest -Uri $StartUrl -UseBasicParsing
$base = [uri]$StartUrl
$candidateMap = [ordered]@{}
foreach ($link in $response.Links) {
  try { $absoluteUrl = [uri]::new($base,$link.href).AbsoluteUri } catch { continue }
  if (-not $absoluteUrl -or $absoluteUrl -match 'translate\.google|javascript:|mailto:') { continue }
  $innerTextProperty = $link.PSObject.Properties['innerText']
  if ($innerTextProperty) {
    $anchorText = [string]$innerTextProperty.Value
  } else {
    $outerHtmlProperty = $link.PSObject.Properties['outerHTML']
    $anchorText = if ($outerHtmlProperty) { [Net.WebUtility]::HtmlDecode(([string]$outerHtmlProperty.Value -replace '<[^>]+>',' ')) } else { '' }
  }
  $anchorText = ($anchorText -replace '\s+',' ').Trim()
  if (-not $candidateMap.Contains($absoluteUrl) -or (-not $candidateMap[$absoluteUrl] -and $anchorText)) {
    $candidateMap[$absoluteUrl] = $anchorText
  }
}
$links = @($candidateMap.Keys | Sort-Object)
$candidates = @($links | ForEach-Object {
  [ordered]@{url=$_;anchor_text=[string]$candidateMap[$_]}
})
$directory = Split-Path -Parent $OutputPath
if ($directory) { New-Item -ItemType Directory -Force $directory | Out-Null }
[ordered]@{agency=$Agency;source_url=$StartUrl;retrieved_at=(Get-Date).ToUniversalTime().ToString('o');links=$links;candidates=$candidates} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{Agency=$Agency;StartUrl=$StartUrl;Links=$links.Count;OutputPath=$OutputPath}|ConvertTo-Json -Compress

