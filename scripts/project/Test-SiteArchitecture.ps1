[CmdletBinding()]
param(
  [string]$ContentDirectory = 'content',
  [int]$MaximumDepth = 4,
  [int]$MaximumLeafCategories = 35,
  [int]$ThinPageWordThreshold = 50
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $ContentDirectory).Path
$pages = foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -Filter '*.md' -File) {
  $relativePath = $file.FullName.Substring($root.Length + 1).Replace('\','/')
  $parts = $relativePath.Split('/')
  $isSectionIndex = $file.Name -eq '_index.md'
  $depth = if ($isSectionIndex) { $parts.Count - 1 } else { $parts.Count }
  $raw = Get-Content -Raw -Encoding UTF8 -LiteralPath $file.FullName
  $body = $raw -replace '(?s)^---.*?---',''
  $wordCount = @($body -split '\s+' | Where-Object { $_ }).Count
  [pscustomobject]@{
    path = $relativePath
    depth = $depth
    is_section_index = $isSectionIndex
    word_count = $wordCount
    external_links = ([regex]::Matches($body,'\]\(https?://')).Count
  }
}

$leafPages = @($pages | Where-Object { -not $_.is_section_index -and $_.path -notlike 'about/*' })
$overDepth = @($pages | Where-Object depth -gt $MaximumDepth)
$thinPages = @($leafPages | Where-Object word_count -lt $ThinPageWordThreshold | Sort-Object word_count)
$errors = @()
if ($overDepth.Count) { $errors += "$($overDepth.Count) page(s) exceed maximum depth $MaximumDepth." }
if ($leafPages.Count -gt $MaximumLeafCategories) { $errors += "$($leafPages.Count) leaf categories exceed limit $MaximumLeafCategories." }

$result = [ordered]@{
  markdown_files = @($pages).Count
  section_indexes = @($pages | Where-Object is_section_index).Count
  leaf_categories = $leafPages.Count
  maximum_depth = ($pages | Measure-Object depth -Maximum).Maximum
  over_depth = $overDepth
  thin_pages = $thinPages
  errors = $errors
}
$result | ConvertTo-Json -Depth 6
if ($errors.Count) { exit 1 }
