[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$SourceRepoRoot = 'C:\Users\ben\Documents\ABQinfo',
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
$ids = @(
  'src-c8a6a02c203d0cd2','src-087842cdf31bbd1c','src-ea48e98a01589ffb','src-73f9afbcaae5d8d2',
  'src-ca86eefe82a821c3','src-21dc013c982971a3','src-ea47d347422e2570','src-bbaad13a047c342c',
  'src-573093423a1bbd50','src-14ba4769fc9b04aa','src-c134c414b9f229c1','src-79f0672eaab3eca0',
  'src-5340531bfdbbe7fb','src-fd0a98e661a8db31','src-adfd6742a595ccf6','src-808550f86ef1cf0e',
  'src-c2f91d09003c2cbe','src-74c9ef9734483c29','src-58104015e9620a4d'
)
$selected = @($ids | ForEach-Object {
  $id = $_
  $matches = @($inventory.candidates | Where-Object id -eq $id)
  if ($matches.Count -ne 1) { throw "Expected one inventory record for $id." }
  $matches[0]
})

New-Item -ItemType Directory -Path $OutputDirectory,$WorkDirectory -Force | Out-Null
$results = [System.Collections.Generic.List[object]]::new()
foreach ($year in 2014..2018) {
  $members = @($selected | Where-Object { [string]$_.date -match "^$year" } | Sort-Object date)
  if (-not $members.Count) { throw "No DPM minutes selected for $year." }
  $manifest = [pscustomobject][ordered]@{
    schema_version = 1
    title = "Development Process Manual Executive Committee Minutes, $year"
    short_title = "DPM Executive Committee Minutes $year"
    coverage_note = "$($members.Count) preserved meeting record$(if ($members.Count -ne 1) {'s'}) currently located for $year, ordered by meeting date. Official-source completeness is independently rechecked before publication."
    provenance_note = 'ABQInfo assembled this browsing copy from the byte-identical City of Albuquerque originals already preserved in R2. Source pages are not rewritten, summarized, or substituted. The introductory and separator pages are ABQInfo-authored navigation and provenance aids.'
    sources = @($members | ForEach-Object {
      $local = Join-Path $SourceRepoRoot ([string]$_.local_path)
      if (-not (Test-Path -LiteralPath $local)) { throw "Missing local original for $($_.id): $local" }
      [pscustomobject][ordered]@{
        candidate_id = [string]$_.id
        date = [string]$_.date
        title = [string]$_.title
        local_path = $local
        size_bytes = [int64]$_.size_bytes
        checksum_sha256 = [string]$_.checksum_sha256
        source_url = [string]$_.source_url
        archive_url = [string]$_.r2_url
      }
    })
  }
  $manifestPath = Join-Path $WorkDirectory "dpm-$year-manifest.json"
  $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8
  $outputPath = Join-Path $OutputDirectory "cabq-dpm-executive-committee-minutes-$year-abqinfo-compilation.pdf"
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
  status = 'built and passed source size/hash, pixel-equivalence, extracted-text, provenance-link, and contact-sheet visual QA; official-source family completeness remains pending before archival or publication'
  compilation_count = $results.Count
  source_document_count = [int](($results | Measure-Object source_count -Sum).Sum)
  total_pages = [int](($results | Measure-Object page_count -Sum).Sum)
  total_bytes = [int64](($results | Measure-Object size_bytes -Sum).Sum)
  compilations = @($results)
}
$summary | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $ValidationPath -Encoding utf8
$summary | Select-Object compilation_count,source_document_count,total_pages,total_bytes,status | ConvertTo-Json -Compress
