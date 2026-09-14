[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$ResearchPath = 'project-state/discovery/claude-consolidation-2003-general-obligation-bond-program-master-record-2026-09-13.json',
  [string]$FamilyCheckpointPath = 'research/staging/claude-consolidation-checkpoints/2003-general-obligation-bond-program-master-record/items/family-2003-bond-doc.json',
  [string]$WorkDirectory = 'research/staging/go2003-master',
  [string]$OutputPath = 'output/pdf/cabq-2003-general-obligation-bond-program-master-record-abqinfo-compilation.pdf',
  [string]$ValidationPath = 'project-state/discovery/go2003-master-compilation-build-2026-09-13.json',
  [string]$PythonPath = 'C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe',
  [string]$PdfToPpmPath = 'C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$research = Get-Content -Raw -Encoding UTF8 -LiteralPath $ResearchPath | ConvertFrom-Json
$family = Get-Content -Raw -Encoding UTF8 -LiteralPath $FamilyCheckpointPath | ConvertFrom-Json
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
if ([string]$research.recommended_publication_form.form -ne 'consolidated_master') { throw 'Research does not approve a consolidated master.' }
$members = @($research.ordered_members | Sort-Object order)
if ($members.Count -ne 21 -or [int]$research.total_pages -ne 92) { throw 'Expected the complete 21-source, 92-page reviewed family.' }
$familyById = @{}
foreach ($item in @($family.files_reviewed)) { $familyById[[string]$item.candidate_id] = $item }

$sharedRoot = 'C:\Users\ben\Documents\ABQinfo'
$sources = [System.Collections.Generic.List[object]]::new()
foreach ($member in $members) {
  $id = [string]$member.candidate_id
  if (-not $familyById.ContainsKey($id)) { throw "Official-family checkpoint lacks $id." }
  $review = $familyById[$id]
  $candidate = @($inventory.candidates | Where-Object id -eq $id)
  if ($candidate.Count -ne 1) { throw "Expected one inventory candidate for $id." }
  $candidate = $candidate[0]
  if (-not $candidate.r2_url) { throw "$id has not been archived separately to R2." }
  $localPath = [string]$candidate.local_path
  if (-not (Test-Path -LiteralPath $localPath)) { $localPath = Join-Path $sharedRoot $localPath }
  if (-not (Test-Path -LiteralPath $localPath)) { throw "Local byte-identical original is unavailable for $id." }
  $file = Get-Item -LiteralPath $localPath
  $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($file.Length -ne [int64]$review.size_bytes -or $hash -ne [string]$review.checksum_sha256) { throw "Integrity mismatch for $id." }
  $sources.Add([pscustomobject][ordered]@{
    candidate_id = $id
    date = if ($candidate.date) { [string]$candidate.date } else { '2003' }
    title = [string]$candidate.title
    role = [string]$member.role
    local_path = $file.FullName
    source_url = [string]$member.official_url
    archive_url = [string]$candidate.r2_url
    size_bytes = [int64]$file.Length
    checksum_sha256 = $hash
  })
}

New-Item -ItemType Directory -Force -Path $WorkDirectory,(Split-Path -Parent $OutputPath) | Out-Null
$editorialNote = [string](@($research.proposed_table_of_contents | Where-Object section -eq 'Editorial note' | Select-Object -First 1).content)
$manifest = [pscustomobject][ordered]@{
  schema_version = 1
  title = '2003 General Obligation Bond Program: Master Record'
  short_title = '2003 GO Bond Master Record'
  record_label = 'Program record'
  source_record_label = 'Original City program record'
  date_label = 'Record year'
  contents_page_row_counts = @(10, 6, 5)
  keywords = 'Albuquerque, 2003 general obligation bonds, capital improvements, project scopes, governing resolutions, historical compilation'
  coverage_note = 'Complete 92-page program record assembled from 21 City files in the reviewed official source family. The separate Decade Plan criteria extract is omitted because those pages are already contained in R-02-30; the general consultant-compensation regulation is outside the 2003 program record.'
  editorial_note = $editorialNote
  provenance_note = "ABQInfo assembled this browsing compilation after reconciling both pages of the City's official 2003 bond-program directory. Each of the 21 included files remains separately archived byte-for-byte, with its official source URL, byte size, SHA-256, inventory ID, and original title recorded on a provenance sheet. No City source page was altered."
  sources = @($sources)
}
$manifestPath = Join-Path $WorkDirectory 'go2003-manifest.json'
$itemValidationPath = Join-Path $WorkDirectory 'go2003-build-validation.json'
$equivalencePath = Join-Path $WorkDirectory 'go2003-source-equivalence-validation.json'
$manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $manifestPath -Encoding utf8
& $PythonPath "$PSScriptRoot/Build-HistoricalCompilationPdf.py" --manifest $manifestPath --output $OutputPath --validation $itemValidationPath
if ($LASTEXITCODE) { throw 'Compilation builder failed.' }
& $PythonPath "$PSScriptRoot/Test-HistoricalCompilationPdf.py" --manifest $manifestPath --build-validation $itemValidationPath --pdftoppm $PdfToPpmPath --output $equivalencePath
if ($LASTEXITCODE) { throw 'Compilation source-equivalence validation failed.' }
$build = Get-Content -Raw -Encoding UTF8 -LiteralPath $itemValidationPath | ConvertFrom-Json
$equivalence = Get-Content -Raw -Encoding UTF8 -LiteralPath $equivalencePath | ConvertFrom-Json
$artifact = [pscustomobject][ordered]@{
  schema_version = 1
  created_at = (Get-Date).ToUniversalTime().ToString('o')
  status = 'built from exhaustive official-source family research and passed source size/hash, pixel-equivalence, extracted-text, and provenance-link validation; final contact-sheet visual QA required before archival or publication'
  source_family_files_reviewed = 23
  excluded_contained_extract = 'src-74326241e19c1551'
  excluded_general_regulation = 'src-230753126ba3bbf7'
  compilation = $build
  source_equivalence_validation = $equivalence
}
$artifact | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $ValidationPath -Encoding utf8
$artifact | Select-Object @{n='source_documents';e={$_.compilation.source_count}},@{n='source_pages';e={$_.source_equivalence_validation.source_page_count}},@{n='total_pages';e={$_.compilation.page_count}},@{n='total_bytes';e={$_.compilation.size_bytes}},@{n='sha256';e={$_.compilation.checksum_sha256}},status | ConvertTo-Json -Compress
