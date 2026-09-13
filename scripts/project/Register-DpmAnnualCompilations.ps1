[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$BuildValidationPath = 'project-state/discovery/dpm-annual-compilations-build-2026-09-13.json',
  [string]$VisualQaPath = 'project-state/discovery/dpm-annual-compilations-visual-qa-2026-09-13.json',
  [string]$ResearchDirectory = 'project-state/discovery',
  [string]$DecisionsPath = 'project-state/discovery/dpm-annual-compilations-decisions-2026-09-13.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$descriptions = @{
  2014 = "Collects five official committee records tracing the committee's launch, the voiding and re-adoption of its first chapter changes, and approval of the Development Process Manual preface and update procedure."
  2015 = 'Collects seven official committee records documenting the planned division of the manual between the Integrated Development Ordinance and a technical standards manual, Chapter 23 subcommittee work, and Chapter 25 revisions.'
  2016 = "Collects nine official committee records tracing Chapter 28's adoption, section-by-section approval of Chapter 22, stormwater modeling discussions, and the appointment of subcommittees for Chapters 24, 25, and 26."
  2017 = 'Collects fifteen official committee records documenting completion of drainage standards, approval of survey, public-transit, parking, pedestrian, pavement, and building-permit provisions, and continuing review of network-connectivity and drafting standards.'
  2018 = 'Collects three official committee minutes plus the April 4 agenda preserved under the missing-minutes policy, documenting network-connectivity, intersection-design, construction-plan, and subdivision-compliance decisions and the final unfinished agenda items.'
}
$locations = @{
  2014 = @('content/development-land-use/development-process.md')
  2015 = @('content/development-land-use/development-process.md')
  2016 = @('content/development-land-use/development-process.md','content/public-works/stormwater-drainage.md')
  2017 = @('content/development-land-use/development-process.md','content/public-works/stormwater-drainage.md','content/transportation/design-references.md')
  2018 = @('content/development-land-use/development-process.md','content/transportation/design-references.md')
}

$build = Get-Content -Raw -Encoding UTF8 -LiteralPath $BuildValidationPath | ConvertFrom-Json
$qa = Get-Content -Raw -Encoding UTF8 -LiteralPath $VisualQaPath | ConvertFrom-Json
if (-not [bool]$qa.all_passed) { throw 'Final visual QA is not recorded as passed.' }
if (@($build.compilations).Count -ne 5) { throw 'Expected five completed annual compilation builds.' }

$decisions = [System.Collections.Generic.List[object]]::new()
foreach ($year in 2014..2018) {
  $buildTitle = if ($year -eq 2018) { "Development Process Manual Executive Committee Meeting Records, $year" } else { "Development Process Manual Executive Committee Minutes, $year" }
  $item = @($build.compilations | Where-Object title -eq $buildTitle)
  if ($item.Count -ne 1) { throw "Expected one build result for $year." }
  $item = $item[0]
  $qaItem = @($qa.compilations | Where-Object year -eq $year)
  if ($qaItem.Count -ne 1 -or -not [bool]$qaItem[0].passed) { throw "Visual QA is incomplete for $year." }
  if ([string]$qaItem[0].checksum_sha256 -ne [string]$item.checksum_sha256) { throw "Visual QA checksum does not match the final $year PDF." }
  $file = Get-Item -LiteralPath ([string]$item.output_path)
  $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($file.Length -ne [int64]$item.size_bytes -or $hash -ne [string]$item.checksum_sha256) { throw "Final PDF integrity mismatch for $year." }

  $researchPath = Join-Path $ResearchDirectory "claude-consolidation-dpm-$year-2026-09-13.json"
  $research = Get-Content -Raw -Encoding UTF8 -LiteralPath $researchPath | ConvertFrom-Json
  $members = @($research.ordered_members | Where-Object { -not $_.PSObject.Properties['role'] -or [string]$_.role -eq 'minutes' -or [string]$_.role -eq 'agenda (approved minutes not located)' } | Sort-Object date)
  $memberIds = @($members.candidate_id)
  $builtIds = @($item.sources.candidate_id)
  if ($memberIds.Count -ne [int]$item.source_count -or ($builtIds -join '|') -ne ($memberIds -join '|')) {
    throw "Final $year PDF does not contain exactly the research-approved members in chronological order."
  }
  $extractedWords = 0
  foreach ($id in $memberIds) {
    $checkpoint = Get-Content -Raw -Encoding UTF8 -LiteralPath "research/staging/claude-consolidation-checkpoints/dpm-$year/items/$id.json" | ConvertFrom-Json
    $extractedWords += [int]$checkpoint.quality_assessment.extracted_word_count
  }

  $recordLabel = if ($year -eq 2018) { 'records' } else { 'minutes' }
  $r2Key = "development-land-use/development-process/cabq-dpm-executive-committee-$recordLabel-$year-abqinfo-compilation.pdf"
  $publicUrl = "https://files.abqinfo.com/$r2Key"
  $title = if ($year -eq 2018) { "Development Process Manual Executive Committee Meeting Records, $year - ABQInfo Historical Compilation" } else { "Development Process Manual Executive Committee Minutes, $year - ABQInfo Historical Compilation" }
  $candidateJson = & "$PSScriptRoot/Add-InventoryCandidate.ps1" -SourceUrl $publicUrl -DirectFileUrl $publicUrl -Agency 'ABQInfo compilation of City of Albuquerque originals' -Title $title -Date ([string]$year) -FileType PDF -ParentUrl 'https://documents.cabq.gov/planning/development-process-manual/' -DiscoveryMethod 'approved provenance-preserving ABQInfo annual compilation' -InventoryPath $InventoryPath
  $candidate = $candidateJson | ConvertFrom-Json
  $notes = @(
    'ABQInfo-created browsing compilation; not a single publication issued by the City of Albuquerque.',
    "Contains $($memberIds.Count) complete City originals in chronological order, each preceded by a provenance sheet; component inventory IDs: $($memberIds -join ', ').",
    'Every component remains separately preserved with its original source URL, byte size, SHA-256, and inventory history.',
    "Final PDF source-equivalence and visual QA: $($VisualQaPath.Replace('\','/'))."
  )
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $candidate.id -Set @{
    status = 'approved for addition'
    source_url = $publicUrl
    direct_file_url = $publicUrl
    agency = 'ABQInfo compilation of City of Albuquerque originals'
    title = $title
    date = [string]$year
    file_type = 'PDF'
    size_bytes = [int64]$file.Length
    checksum_sha256 = $hash
    parent_url = 'https://documents.cabq.gov/planning/development-process-manual/'
    provenance_status = 'ABQInfo compilation derived from separately archived and verified authoritative City originals; exact component provenance embedded in the PDF'
    proposed_canonical_page = 'content/development-land-use/development-process.md'
    description = [string]$descriptions[$year]
    processing_notes = @($notes)
    implementation_locations = @($locations[$year])
    cross_listing_approved = [bool](@($locations[$year]).Count -gt 1)
    validation_status = 'final compilation size, SHA-256, source-page equivalence, provenance links, and visual QA passed; R2 upload pending'
    local_path = $file.FullName.Substring((Get-Location).Path.Length + 1).Replace('\','/')
  } -InventoryPath $InventoryPath | Out-Null

  $quality = [pscustomobject][ordered]@{
    reviewed_document_content = $true
    visual_inspection_completed = $true
    standalone_public_value = 'high'
    information_density = 'substantial'
    series_relationship = 'serial'
    publication_form = 'consolidated_master'
    rationale = "The annual compilation preserves the complete $year meeting sequence in one usable record while eliminating sparse standalone listings and retaining exact provenance for every City original."
    aggregation_rationale = "These short minutes form one chronological decision record whose meaning depends on continuances, corrections, approvals, and later actions across meetings; an annual master is the appropriate public presentation."
    page_count = [int]$item.page_count
    extracted_word_count = $extractedWords
  }
  $decisions.Add([pscustomobject][ordered]@{
    id = [string]$candidate.id
    title = $title
    date = [string]$year
    source_page = 'https://documents.cabq.gov/planning/development-process-manual/'
    direct_file_url = 'https://documents.cabq.gov/planning/development-process-manual/'
    agency = 'ABQInfo compilation of City of Albuquerque originals'
    canonical_page = 'content/development-land-use/development-process.md'
    description = [string]$descriptions[$year]
    r2_key = $r2Key
    provenance_status = 'ABQInfo compilation derived from separately archived and verified authoritative City originals; exact component provenance embedded in the PDF'
    processing_notes = @($notes)
    implementation_locations = @($locations[$year])
    cross_listing_approved = [bool](@($locations[$year]).Count -gt 1)
    quality_assessment = $quality
  })
}

$artifact = [pscustomobject][ordered]@{
  schema_version = 1
  created_at = (Get-Date).ToUniversalTime().ToString('o')
  batch_id = 'dpm-annual-compilations-2026-09-13'
  purpose = 'Register five user-approved annual browsing compilations only after all component originals are separately archived and the final compiled PDFs pass integrity, provenance, source-equivalence, and visual QA.'
  decisions = @($decisions)
}
$artifact | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $DecisionsPath -Encoding utf8
$artifact | Select-Object @{n='compilation_count';e={@($_.decisions).Count}},@{n='output_path';e={$DecisionsPath}} | ConvertTo-Json -Compress
