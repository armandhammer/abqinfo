[CmdletBinding()]
param(
  [Parameter(Mandatory)]
  [ValidateNotNullOrEmpty()]
  [string]$Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
  throw "PR description file not found: $Path"
}

$body = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
$problems = [System.Collections.Generic.List[string]]::new()

if ([string]::IsNullOrWhiteSpace($body)) {
  $problems.Add('PR description is empty.')
}
if ($body -match '\\n') {
  $problems.Add('PR description contains a literal \\n escape sequence; use actual line breaks.')
}
if ($body -match '\\[A-Za-z]') {
  $problems.Add('PR description contains an obvious malformed escape prefix (for example, \\requires).')
}

if ($body -notmatch '(?m)^##\s+Summary\s*$') {
  $problems.Add('Missing required section: ## Summary')
}
if ($body -match '(?m)^##\s+Review this change\s*$') {
  if ($body -notmatch '(?m)^\*\*Preview:\*\*\s+https://[a-z0-9-]+\.abqinfo\.pages\.dev/[^\s)]+') {
    $problems.Add('A visible-site PR needs a direct non-production preview page URL on a Preview line.')
  }
  if ($body -match 'https://abqinfo\.com/') {
    $problems.Add('Use the preview page, not the production site, for an unmerged visible change.')
  }
  if ($body -notmatch '(?m)^\s*[-*]\s+(Added|Removed|Renamed|Moved|Cross-listed|Rewritten):\s+\S') {
    $problems.Add('Name at least one actual visible change with an action label.')
  }
} elseif ($body -match '(?ms)^##\s+Visible site changes\s*$\s*None\.\s*(?:$|^##\s)') {
  # Background-only PRs do not need a visible-content review section.
} else {
  $problems.Add('Use ## Review this change for visible content, or mark Visible site changes as None for background-only work.')
}

if ($problems.Count) {
  throw ($problems -join [Environment]::NewLine)
}

[pscustomobject]@{ Path = $Path; Result = 'passed' } | ConvertTo-Json -Compress
