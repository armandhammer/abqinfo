[CmdletBinding()]
param(
  [string]$VerificationPath = 'project-state/discovery/abq-ride-historic-transit-archive-public-byte-verification-2026-09-21.json',
  [string]$RenderDirectory = 'research/staging/abq-ride-historic-transit-archive-2026-09-21/legacy-word-render'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Utf8Json([object]$Value, [string]$Path) {
  $fullPath = [IO.Path]::GetFullPath($Path)
  $temporaryPath = "$fullPath.tmp-$PID"
  [IO.File]::WriteAllText($temporaryPath, ($Value | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
}

$verification = Get-Content -Raw -Encoding UTF8 -LiteralPath $VerificationPath | ConvertFrom-Json
$items = @($verification.results | Where-Object { $_.r2_key -like '*.doc' })
if ($items.Count -ne 3 -or @($items | Where-Object source_byte_verification -ne 'passed').Count) { throw 'The three legacy Word originals must pass source-byte verification before rendering.' }
New-Item -ItemType Directory -Force -Path $RenderDirectory | Out-Null
$word = $null
try {
  $word = New-Object -ComObject Word.Application
  $word.Visible = $false
  $word.DisplayAlerts = 0
  foreach ($item in $items) {
    $pdfPath = Join-Path $RenderDirectory ([IO.Path]::ChangeExtension([IO.Path]::GetFileName($item.local_path), '.pdf'))
    $document = $null
    try {
      $document = $word.Documents.Open([IO.Path]::GetFullPath($item.local_path), $false, $true)
      $document.ExportAsFixedFormat($pdfPath, 17)
      $pdf = Get-Item -LiteralPath $pdfPath
      $item | Add-Member -NotePropertyName visual_render_pdf_path -NotePropertyValue $pdf.FullName -Force
      $item | Add-Member -NotePropertyName visual_render_inspection -NotePropertyValue 'rendered_pending_human_visual_inspection' -Force
    } finally {
      if ($document) { $document.Close(0) }
    }
  }
} catch {
  $failure = "Legacy Word visual rendering failed: $($_.Exception.Message)"
  foreach ($item in $items) {
    $item | Add-Member -NotePropertyName visual_render_inspection -NotePropertyValue 'failed_renderer_unavailable' -Force
    $item.failure = $failure
  }
  $verification.state = 'blocked_legacy_word_visual_rendering_unavailable_no_r2_mutation'
  $verification.visual_render.status = 'failed'
  $verification.visual_render.failure = $failure
  $verification.summary.failures = @($verification.results | Where-Object failure).Count
  Write-Utf8Json $verification $VerificationPath
  $verification.summary | ConvertTo-Json -Compress
  return
} finally {
  if ($word) { $word.Quit() }
}
$verification.state = 'legacy_word_rendered_awaiting_visual_inspection_no_r2_mutation'
$verification.visual_render.status = 'three_unchanged_legacy_word_originals_rendered_to_ephemeral_pdf_for_visual_inspection'
$verification.visual_render.failure = $null
Write-Utf8Json $verification $VerificationPath
$verification.results | Where-Object { $_.visual_render_pdf_path } | Select-Object id,visual_render_pdf_path | ConvertTo-Json
