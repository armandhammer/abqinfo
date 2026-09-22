[CmdletBinding()]
param(
  [string]$PreparationPath = 'project-state/discovery/nmdot-statewide-truck-parking-study-archive-preparation-2026-09-21.json',
  [string]$OutputDirectory = 'research/staging/nmdot-statewide-truck-parking-study-archive-preparation-2026-09-21/docx-visual-render'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Utf8Json([object]$Value, [string]$Path) {
  $fullPath = [IO.Path]::GetFullPath($Path)
  [IO.File]::WriteAllText($fullPath, ($Value | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))
}

$preparation = Get-Content -Raw -Encoding UTF8 -LiteralPath $PreparationPath | ConvertFrom-Json
$records = @($preparation.records | Where-Object { $_.container -eq 'OOXML/DOCX' }) | Sort-Object series_order
if ($records.Count -ne 5) { throw 'Expected exactly five DOCX records.' }
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$reportPath = Join-Path $OutputDirectory 'host-docx-render-report.json'
$results = @()
$word = $null
try {
  foreach ($record in $records) {
    $path = [IO.Path]::GetFullPath($record.source_evidence.staged_path)
    if (-not (Test-Path -LiteralPath $path)) { throw "$($record.id): staged original is missing: $path" }
    $file = Get-Item -LiteralPath $path
    $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($file.Length -ne [int64]$record.source_evidence.size_bytes -or $hash -ne $record.source_evidence.sha256) { throw "$($record.id): staged original does not match its recorded source bytes." }
  }
  $word = New-Object -ComObject Word.Application
  $word.Visible = $false
  $word.DisplayAlerts = 0
  foreach ($record in $records) {
    $sourcePath = [IO.Path]::GetFullPath($record.source_evidence.staged_path)
    $pdfPath = Join-Path ([IO.Path]::GetFullPath($OutputDirectory)) ([IO.Path]::ChangeExtension([IO.Path]::GetFileName($sourcePath), '.pdf'))
    $document = $null
    try {
      $document = $word.Documents.Open($sourcePath, $false, $true)
      $document.ExportAsFixedFormat($pdfPath, 17)
      $results += [pscustomobject]@{ id=$record.id; staged_path=$record.source_evidence.staged_path; render_pdf_path=$pdfPath; result='rendered_pending_human_visual_inspection' }
    } finally { if ($document) { $document.Close(0) } }
  }
  $report = [ordered]@{ state='rendered_awaiting_human_visual_inspection'; preparation_path=$PreparationPath; results=$results; failure=$null }
} catch {
  $report = [ordered]@{ state='blocked_word_com_unavailable_or_render_failed'; preparation_path=$PreparationPath; results=$results; failure=$_.Exception.Message; guidance='Run this helper from an interactive Windows PowerShell session where Microsoft Word is available. It verifies every staged DOCX size and SHA-256 before opening it read-only, and exports inspection-only PDFs; the DOCX originals remain the proposed archive objects.' }
} finally { if ($word) { $word.Quit() } }
Write-Utf8Json $report $reportPath
$report | ConvertTo-Json -Depth 12
if ($report.state -ne 'rendered_awaiting_human_visual_inspection') { exit 2 }
