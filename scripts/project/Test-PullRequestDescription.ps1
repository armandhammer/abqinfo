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

$requiredSections = @('Summary', 'What changed', 'Archive / inventory / provenance', 'Visible site changes', 'Validation', 'Deferred / not included')
foreach ($section in $requiredSections) {
  if ($body -notmatch ('(?m)^##\s+' + [regex]::Escape($section) + '\s*$')) {
    $problems.Add("Missing required section: ## $section")
  }
}

if ($body -match '(?ms)^##\s+Visible site changes\s*$\s*None\.\s*(?:$|^##\s)') {
  # Research/state-only PRs have no page-level enumeration requirement.
} elseif ($body -match '(?m)^##\s+Visible site changes\s*$') {
  if ($body -notmatch 'https://(?:[a-z0-9-]+\.)?abqinfo\.com/') {
    $problems.Add('Visible site changes must include an ABQInfo page or verified preview URL.')
  }
  if ($body -notmatch '(?m)^###\s+') {
    $problems.Add('Visible site changes must use page-and-heading subsections.')
  }
} else {
  $problems.Add('Unable to evaluate the Visible site changes section.')
}

if ($problems.Count) {
  throw ($problems -join [Environment]::NewLine)
}

[pscustomobject]@{ Path = $Path; Result = 'passed' } | ConvertTo-Json -Compress
