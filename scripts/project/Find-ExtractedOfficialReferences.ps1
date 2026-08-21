[CmdletBinding()]
param(
  [ValidateSet('cabq','bernco','mrcog','nmdot')][string]$Agency = 'cabq',
  [string]$SearchRoot = 'research/staging',
  [string]$OutputPath = 'research/discovery/extracted-official-references-links.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$hostPatterns = @{
  cabq = '(^|\.)(cabq\.gov)$'
  bernco = '(^|\.)(bernco\.gov)$'
  mrcog = '(^|\.)(mrcog-nm\.gov|mrcogshare\.org|riometro\.org)$'
  nmdot = '(^|\.)(dot\.nm\.gov|nmroads\.com)$'
}

$found = [ordered]@{}
foreach ($file in Get-ChildItem -LiteralPath $SearchRoot -Recurse -File -Filter '*.txt' -ErrorAction SilentlyContinue) {
  $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $file.FullName
  # PDF text extraction commonly wraps a URL immediately after a hyphen or slash.
  # Join those URL-safe boundaries before matching so a printed URL is not lost.
  $text = $text -replace '-\r?\n\s*', '-'
  $text = $text -replace '/\r?\n\s*', '/'
  foreach ($match in [regex]::Matches($text, '(?i)https?://[^\s<>"''\(\)]+')) {
    $url = $match.Value.TrimEnd('.',',',';',':',']','}')
    try { $uri = [uri]$url } catch { continue }
    if ($uri.Host -notmatch $hostPatterns[$Agency]) { continue }
    if ($uri.AbsolutePath -notmatch '(?i)\.(pdf|docx?|xlsx?|csv|zip|kml|kmz)$') { continue }
    if (-not $found.Contains($url)) {
      $title = [uri]::UnescapeDataString([IO.Path]::GetFileNameWithoutExtension($uri.AbsolutePath))
      $title = (($title -replace '[-_]',' ') -replace '\s+',' ').Trim()
      $found[$url] = [ordered]@{ url=$url; anchor_text=$title; discovered_in=@() }
    }
    $relative = $file.FullName.Substring((Get-Location).Path.Length + 1).Replace('\','/')
    $found[$url].discovered_in = @($found[$url].discovered_in + $relative | Sort-Object -Unique)
  }
}

$candidates = @($found.Values | Sort-Object url)
$directory = Split-Path -Parent $OutputPath
if ($directory) { New-Item -ItemType Directory -Force $directory | Out-Null }
[ordered]@{
  agency = $Agency
  source_url = $null
  scope = 'official-document-urls-extracted-from-downloaded-source-text'
  retrieved_at = (Get-Date).ToUniversalTime().ToString('o')
  links = @($candidates | ForEach-Object { $_.url })
  candidates = $candidates
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputPath -Encoding utf8

[pscustomobject]@{Agency=$Agency;FilesScanned=@(Get-ChildItem -LiteralPath $SearchRoot -Recurse -File -Filter '*.txt' -ErrorAction SilentlyContinue).Count;References=$candidates.Count;OutputPath=$OutputPath} | ConvertTo-Json -Compress
