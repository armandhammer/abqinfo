[CmdletBinding()]
param([string]$ContentPath = 'content')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$errors = [Collections.Generic.List[string]]::new()
$allowedNestedResourcePages = @(
  'transportation/bicycling/bike-plans.md',
  'transportation/transportation-plans.md'
)
$minorHeadingWords = @(
  'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'from', 'in', 'into',
  'de', 'del', 'la', 'las', 'los', 'nor', 'of', 'on', 'or', 'over', 'per', 'the',
  'to', 'up', 'via', 'with', 'without'
)

function Get-MarkdownBody([string[]]$Lines) {
  if ($Lines.Count -ge 2 -and $Lines[0].Trim() -eq '---') {
    for ($index = 1; $index -lt $Lines.Count; $index++) {
      if ($Lines[$index].Trim() -eq '---') {
        if ($index + 1 -ge $Lines.Count) { return @() }
        return @($Lines[($index + 1)..($Lines.Count - 1)])
      }
    }
  }
  return @($Lines)
}

function Test-HeadingCapitalization([string]$Heading) {
  # Parenthetical dates and archival-format notes are metadata rather than
  # part of the displayed title, so Title Case is enforced on the title text.
  $titleText = ($Heading -replace '\s*\([^\)]*\)', '').Trim()
  $words = @($titleText -split '\s+')
  for ($index = 0; $index -lt $words.Count; $index++) {
    $word = $words[$index].Trim('"', "'", '(', ')', '[', ']', ':', ',', '.')
    if ([string]::IsNullOrWhiteSpace($word) -or $word -eq '&' -or $word -notmatch '[\p{L}\p{N}]') { continue }
    if ($word -match '^\d' -or $word -cmatch '^[A-Z0-9-]+$') { continue }
    $segments = @($word -split '-')
    for ($segmentIndex = 0; $segmentIndex -lt $segments.Count; $segmentIndex++) {
      $segment = $segments[$segmentIndex]
      if ([string]::IsNullOrWhiteSpace($segment)) { continue }
      $isMinor = $segments.Count -eq 1 -and $index -gt 0 -and $segmentIndex -eq 0 -and $minorHeadingWords -contains $segment.ToLowerInvariant()
      if ($isMinor) {
        if ($segment -cne $segment.ToLowerInvariant()) { return $false }
      }
      elseif ($segment[0] -cnotmatch '[A-Z]') { return $false }
    }
  }
  return $true
}

$files = @(Get-ChildItem -LiteralPath $ContentPath -Recurse -Filter '*.md' -File | Sort-Object FullName)
$resolvedContentPath = (Resolve-Path -LiteralPath $ContentPath).Path.TrimEnd('\') + '\'
foreach ($file in $files) {
  $relativePath = $file.FullName.Substring($resolvedContentPath.Length).Replace('\', '/')
  $body = @(Get-MarkdownBody (Get-Content -LiteralPath $file.FullName))
  for ($index = 0; $index -lt $body.Count; $index++) {
    $line = $body[$index]
    $lineNumber = $index + 1

    if ($line -match '^(#{2,6})\s+(.+?)\s*$') {
      $heading = $Matches[2] -replace '\s+#+$', ''
      if (-not (Test-HeadingCapitalization $heading)) {
        $errors.Add("Section heading is not in the approved title-style capitalization: $relativePath body-line $lineNumber = $heading")
      }
    }

    if ($line -match '^\s*[-*+]\s+\[(?<label>[^\]]+)\]\(https?://') {
      $label = $Matches['label']
      if ($label -notmatch '(?i)\ben español\b|\bPDF archivado\b' -and -not (Test-HeadingCapitalization $label)) {
        $errors.Add("Resource-link label is not in the approved Title Case: $relativePath body-line $lineNumber = $label")
      }
    }

    if ($line -match '^\s{4,}[-*+]\s+') {
      $errors.Add("Third-level bullet is not allowed: $relativePath body-line $lineNumber")
      continue
    }

    if ($line -match '^\s{2,3}[-*+]\s+(.+)$') {
      $item = $Matches[1]
      if ($relativePath -notin $allowedNestedResourcePages) {
        $errors.Add("Nested bullet is not an approved resource exception: $relativePath body-line $lineNumber")
      }
      elseif ($item -notmatch '^\[[^\]]+\]\(https?://') {
        $errors.Add("Nested descriptions must be plain paragraphs, not bullets: $relativePath body-line $lineNumber")
      }
    }
  }
}

$result = [ordered]@{
  markdown_files = $files.Count
  allowed_nested_resource_pages = $allowedNestedResourcePages
  errors = @($errors)
}
$result | ConvertTo-Json -Depth 5
if ($errors.Count) { exit 1 }
