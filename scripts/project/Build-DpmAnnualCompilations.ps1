[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$SourceRepoRoot = '',
  [string]$ResearchDirectory = 'project-state/discovery',
  [string]$OutputDirectory = 'output/pdf',
  [string]$WorkDirectory = 'research/staging/dpm-annual-compilations',
  [string]$ValidationPath = 'project-state/discovery/dpm-annual-compilations-build-2026-09-13.json',
  [string]$PythonPath = 'C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe',
  [string]$PdfToPpmPath = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
if (-not $PdfToPpmPath) { $PdfToPpmPath = (Get-Command pdftoppm -ErrorAction Stop).Source }
if (-not $SourceRepoRoot) { $SourceRepoRoot = (Get-Location).Path }
$gitCommonDirectory = (& git rev-parse --git-common-dir).Trim()
if ($LASTEXITCODE) { throw 'Could not resolve the shared Git directory for local-source fallback.' }
$gitCommonFullPath = if ([IO.Path]::IsPathRooted($gitCommonDirectory)) { [IO.Path]::GetFullPath($gitCommonDirectory) } else { [IO.Path]::GetFullPath((Join-Path (Get-Location).Path $gitCommonDirectory)) }
$fallbackSourceRepoRoot = Split-Path -Parent $gitCommonFullPath

$researchByYear = @{}
foreach ($year in 2014..2018) {
  $researchPath = Join-Path $ResearchDirectory "claude-consolidation-dpm-$year-2026-09-13.json"
  if (-not (Test-Path -LiteralPath $researchPath)) { throw "Missing completed Claude research result for ${year}: $researchPath" }
  $research = Get-Content -Raw -Encoding UTF8 -LiteralPath $researchPath | ConvertFrom-Json
  if ([string]$research.slice_id -ne "dpm-$year") { throw "Unexpected slice ID in $researchPath." }
  if ([string]$research.recommended_publication_form.form -ne 'consolidated_master') { throw "Claude research does not recommend a consolidated master for $year." }
  if (@($research.unresolved_questions | Where-Object { [string]$_ -match '(?i)missing official file|identity|authenticity|authoritative version' }).Count) {
    throw "Research for $year retains a material provenance question; compilation is blocked."
  }
  $researchByYear[$year] = $research
}

New-Item -ItemType Directory -Path $OutputDirectory,$WorkDirectory -Force | Out-Null
$results = [System.Collections.Generic.List[object]]::new()
foreach ($year in 2014..2018) {
  $research = $researchByYear[$year]
  $members = @($research.ordered_members | Where-Object { -not $_.PSObject.Properties['role'] -or [string]$_.role -eq 'minutes' -or [string]$_.role -eq 'agenda (approved minutes not located)' } | Sort-Object date)
  if (-not $members.Count) { throw "No DPM minutes selected for $year." }
  $editorialNote = @($research.proposed_table_of_contents | Where-Object section -eq 'Editorial note' | Select-Object -First 1).content
  $manifest = [pscustomobject][ordered]@{
    schema_version = 1
    title = if ($year -eq 2018) { "Development Process Manual Executive Committee Meeting Records, $year" } else { "Development Process Manual Executive Committee Minutes, $year" }
    short_title = if ($year -eq 2018) { "DPM Executive Committee Records $year" } else { "DPM Executive Committee Minutes $year" }
    coverage_note = "$($members.Count) eligible meeting record$(if ($members.Count -ne 1) {'s'}) located through an exhaustive review of the official City source family for $year, ordered by meeting date. Any agenda is expressly labelled under the missing-minutes policy."
    editorial_note = [string]$editorialNote
    provenance_note = 'ABQInfo assembled this browsing copy from byte-identical City of Albuquerque originals separately preserved in R2. Source pages are not rewritten, summarized, or substituted. The introductory and separator pages are ABQInfo-authored navigation and provenance aids.'
    sources = @($members | ForEach-Object {
      $id = [string]$_.candidate_id
      $matches = @($inventory.candidates | Where-Object id -eq $id)
      if ($matches.Count -ne 1) { throw "Expected one inventory record for $id." }
      $candidate = $matches[0]
      if (-not $candidate.r2_url) { throw "Original $id is not yet preserved in R2; compilation cannot be built." }
      $local = Join-Path $SourceRepoRoot ([string]$candidate.local_path)
      if (-not (Test-Path -LiteralPath $local)) { $local = Join-Path $fallbackSourceRepoRoot ([string]$candidate.local_path) }
      if (-not (Test-Path -LiteralPath $local)) { throw "Missing local original for ${id}: $local" }
      [pscustomobject][ordered]@{
        candidate_id = $id
        date = [string]$_.date
        title = [string]$_.title
        local_path = $local
        size_bytes = [int64]$candidate.size_bytes
        checksum_sha256 = [string]$candidate.checksum_sha256
        source_url = if ($candidate.direct_file_url) { [string]$candidate.direct_file_url } else { [string]$candidate.source_url }
        archive_url = [string]$candidate.r2_url
      }
    })
  }
  $manifestPath = Join-Path $WorkDirectory "dpm-$year-manifest.json"
  $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8
  $recordLabel = if ($year -eq 2018) { 'records' } else { 'minutes' }
  $outputPath = Join-Path $OutputDirectory "cabq-dpm-executive-committee-$recordLabel-$year-abqinfo-compilation.pdf"
  $itemValidation = Join-Path $WorkDirectory "dpm-$year-build-validation.json"
  & $PythonPath "$PSScriptRoot/Build-HistoricalCompilationPdf.py" --manifest $manifestPath --output $outputPath --validation $itemValidation
  if ($LASTEXITCODE) { throw "Compilation builder failed for $year." }
  $visualValidation = Join-Path $WorkDirectory "dpm-$year-source-equivalence-validation.json"
  & $PythonPath "$PSScriptRoot/Test-HistoricalCompilationPdf.py" --manifest $manifestPath --build-validation $itemValidation --pdftoppm $PdfToPpmPath --output $visualValidation
  if ($LASTEXITCODE) { throw "Compilation source-equivalence validation failed for $year." }
  $item = Get-Content -Raw -Encoding UTF8 -LiteralPath $itemValidation | ConvertFrom-Json
  $equivalence = Get-Content -Raw -Encoding UTF8 -LiteralPath $visualValidation | ConvertFrom-Json
  $item | Add-Member -NotePropertyName source_equivalence_validation -NotePropertyValue $equivalence
  $results.Add($item)
}

$summary = [pscustomobject][ordered]@{
  schema_version = 1
  created_at = (Get-Date).ToUniversalTime().ToString('o')
  status = 'built from exhaustive official-source family research and passed source size/hash, pixel-equivalence, extracted-text, and provenance-link validation; final contact-sheet visual QA required before archival or publication'
  compilation_count = $results.Count
  source_document_count = [int](($results | Measure-Object source_count -Sum).Sum)
  total_pages = [int](($results | Measure-Object page_count -Sum).Sum)
  total_bytes = [int64](($results | Measure-Object size_bytes -Sum).Sum)
  compilations = @($results)
}
$summary | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $ValidationPath -Encoding utf8
$summary | Select-Object compilation_count,source_document_count,total_pages,total_bytes,status | ConvertTo-Json -Compress
