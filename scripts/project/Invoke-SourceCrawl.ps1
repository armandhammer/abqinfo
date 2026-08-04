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
$links = $response.Links | ForEach-Object {
  try { [uri]::new($base,$_.href).AbsoluteUri } catch { $null }
} | Where-Object { $_ -and $_ -notmatch 'translate\.google|javascript:|mailto:' } | Sort-Object -Unique
$directory = Split-Path -Parent $OutputPath
if ($directory) { New-Item -ItemType Directory -Force $directory | Out-Null }
[ordered]@{agency=$Agency;source_url=$StartUrl;retrieved_at=(Get-Date).ToUniversalTime().ToString('o');links=@($links)} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{Agency=$Agency;StartUrl=$StartUrl;Links=$links.Count;OutputPath=$OutputPath}|ConvertTo-Json -Compress

