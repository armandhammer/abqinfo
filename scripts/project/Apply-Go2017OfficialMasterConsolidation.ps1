[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OriginalDecisionsPath = 'project-state/discovery/2017-go-bond-program-decisions-2026-09-09.json',
  [string]$PublicValidationPath = 'project-state/discovery/go2017-official-master-r2-public-validation-2026-09-16.json',
  [string]$OutputPath = 'project-state/discovery/go2017-official-master-consolidation-2026-09-16.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$masterId = 'src-882e9458215c5ce7'
$masterArchive = 'https://files.abqinfo.com/city-data/capital-spending/cabq-2017-2026-decade-plan-mayors-recommendation-2017.pdf'
$officialRecord = 'https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2017-go-program/2017-mayors-recommendation-to-city-council.pdf/view'
$officialPdf = 'https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2017-go-program/2017-mayors-recommendation-to-city-council.pdf'
$officialLibrary = 'https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2017-go-program'
$capitalAnchor = '/city-data/capital-spending/#historical-capital-programs'
$title = '2017-2026 Decade Plan and 2017 General Obligation Bond Program: Mayor''s Recommendation'
$description = 'The City''s comprehensive 2017 volume combines the bond-program introduction, departmental scopes and 2017-2025 funding schedules, mandated programs, summary tables, planning process, operating impacts, EPC record, maps, and governing legislation. It replaces 30 sparse standalone component listings; their original archives remain preserved.'
$locations = @(
  'content/city-data/capital-spending.md',
  'content/city-data/public-safety-data.md',
  'content/public-works/capital-projects.md',
  'content/public-works/city-facilities.md',
  'content/public-works/parks-recreation.md',
  'content/public-works/stormwater-drainage.md',
  'content/transportation/transit/abq-ride.md'
)

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$originalDecisions = Get-Content -Raw -Encoding UTF8 -LiteralPath $OriginalDecisionsPath | ConvertFrom-Json
$componentIds = @($originalDecisions.decisions | ForEach-Object { [string]$_.id })
if ($componentIds.Count -ne 30 -or @($componentIds | Sort-Object -Unique).Count -ne 30) {
  throw 'Expected exactly 30 unique reviewed 2017 component records.'
}

$sharedRoot = 'C:\Users\ben\Documents\ABQinfo'
function Resolve-VerifiedLocalFile($Candidate) {
  $path = [string]$Candidate.local_path
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $path = Join-Path $sharedRoot $path }
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Local original is missing for $($Candidate.id)." }
  $file = Get-Item -LiteralPath $path
  $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($file.Length -ne [int64]$Candidate.size_bytes -or $hash -ne [string]$Candidate.checksum_sha256) {
    throw "Local size or SHA-256 does not match inventory for $($Candidate.id)."
  }
  return [pscustomobject]@{ path=$file.FullName; size_bytes=[int64]$file.Length; checksum_sha256=$hash }
}

$master = @($inventory.candidates | Where-Object id -eq $masterId)
if ($master.Count -ne 1) { throw 'Expected one official 2017 program-book inventory record.' }
$master = $master[0]
$masterFile = Resolve-VerifiedLocalFile $master
if ([string]$master.r2_url -ne $masterArchive -or [string]$master.validation_status -notmatch '^passed:') {
  throw 'The official 2017 program book lacks the previously completed archive verification.'
}
$publicValidation = Get-Content -Raw -Encoding UTF8 -LiteralPath $PublicValidationPath | ConvertFrom-Json
if (-not [bool]$publicValidation.byte_identical -or [string]$publicValidation.id -ne $masterId -or
    [int64]$publicValidation.size_bytes -ne $masterFile.size_bytes -or
    [string]$publicValidation.checksum_sha256 -ne $masterFile.checksum_sha256) {
  throw 'Fresh public R2 validation does not match the official 2017 program book.'
}

$components = [System.Collections.Generic.List[object]]::new()
foreach ($id in $componentIds) {
  $candidate = @($inventory.candidates | Where-Object id -eq $id)
  if ($candidate.Count -ne 1) { throw "Expected one component inventory record for $id." }
  $candidate = $candidate[0]
  $local = Resolve-VerifiedLocalFile $candidate
  if (-not $candidate.r2_url -or [string]$candidate.validation_status -notmatch '^passed:') {
    throw "Component $id lacks a preserved archive or completed verification result."
  }
  $components.Add([pscustomobject][ordered]@{
    id = $id
    title = [string]$candidate.title
    file_type = [string]$candidate.file_type
    size_bytes = $local.size_bytes
    checksum_sha256 = $local.checksum_sha256
    archive_url = [string]$candidate.r2_url
    official_source_url = [string]$candidate.source_url
  })
}

function Entry-Pattern([string]$ArchiveUrl) {
  $escaped = [regex]::Escape($ArchiveUrl)
  return "(?ms)^- \[[^`r`n]+\]\($escaped\)`r?`n`r?`n.*?(?=^- \[|^#{1,6} |\z)"
}

function Replace-EntryByArchiveUrl([string]$Text,[string]$ArchiveUrl,[string]$Replacement,[string]$Context) {
  $pattern = Entry-Pattern $ArchiveUrl
  $matches = [regex]::Matches($Text,$pattern)
  if ($matches.Count -ne 1) { throw "Expected one entry for $Context; found $($matches.Count)." }
  return [regex]::Replace($Text,$pattern,[System.Text.RegularExpressions.MatchEvaluator]{ param($m) $Replacement.TrimEnd() + "`n`n" })
}

function Remove-EntryByArchiveUrl([string]$Text,[string]$ArchiveUrl,[string]$Context) {
  $pattern = Entry-Pattern $ArchiveUrl
  $matches = [regex]::Matches($Text,$pattern)
  if ($matches.Count -ne 1) { throw "Expected one entry for $Context; found $($matches.Count)." }
  return [regex]::Replace($Text,$pattern,'')
}

function Master-Entry([string]$PageDescription,[bool]$Canonical = $false) {
  $links = if ($Canonical) {
    "[Official City record]($officialRecord) · [Official City PDF]($officialPdf) · [Official component library]($officialLibrary)"
  } else {
    "[Full 2017 program context]($capitalAnchor) · [Official City record]($officialRecord) · [Official City PDF]($officialPdf)"
  }
  return @"
- [$title (Official Program Book, Archived PDF)]($masterArchive)

  $PageDescription

  $links
"@
}

$writes = [System.Collections.Generic.List[object]]::new()
$capitalPath = 'content/city-data/capital-spending.md'
$capital = Get-Content -Raw -Encoding UTF8 -LiteralPath $capitalPath
$capital = Replace-EntryByArchiveUrl $capital $masterArchive (Master-Entry $description $true) 'canonical 2017 official program book'
$sectionPattern = '(?ms)^### 2017 General Obligation Bond Program\r?\n.*?(?=^## )'
$sectionMatches = [regex]::Matches($capital,$sectionPattern)
if ($sectionMatches.Count -ne 1) { throw "Expected one standalone 2017 component section; found $($sectionMatches.Count)." }
$capital = [regex]::Replace($capital,$sectionPattern,'')
$completeBooksEntry = '- [2013–2022 Decade Plan and 2013 General Obligation Bond Program (archived PDF)]'
if ([regex]::Matches($capital,[regex]::Escape($completeBooksEntry)).Count -ne 1) { throw 'Could not uniquely locate the complete-program-book series.' }
$capital = $capital.Replace($completeBooksEntry,"### Complete Program Books`n`n$completeBooksEntry")
$writes.Add([pscustomobject]@{Path=$capitalPath;Text=$capital})

$crossListings = @(
  [pscustomobject]@{
    Path='content/city-data/public-safety-data.md'
    ReplaceUrl='https://files.abqinfo.com/city-data/public-safety/cabq-2017-fire-go-bond-project-scopes.pdf'
    RemoveUrls=@('https://files.abqinfo.com/city-data/public-safety/cabq-2017-police-go-bond-project-scopes.pdf')
    Description='The City''s complete 2017 program book includes the Fire and Police scopes and funding schedules within the broader decade plan, alongside selection criteria, operating impacts, maps, appendices, and governing legislation.'
  },
  [pscustomobject]@{
    Path='content/public-works/capital-projects.md'
    ReplaceUrl='https://files.abqinfo.com/public-works/capital-projects/cabq-2017-streets-go-bond-project-scopes.pdf'
    RemoveUrls=@()
    Description='The City''s complete 2017 program book includes the Streets project scopes and 2017-2025 funding schedule, plus selection criteria, operating impacts, maps, appendices, and legislation for the citywide capital program.'
  },
  [pscustomobject]@{
    Path='content/public-works/city-facilities.md'
    ReplaceUrl='https://files.abqinfo.com/public-works/city-facilities/cabq-2017-city-facilities-parking-go-bond-project-scopes.pdf'
    RemoveUrls=@()
    Description='The City''s complete 2017 program book includes the City Facilities, CIP, energy, security, and parking scopes and funding schedule within the broader decade plan, with selection criteria and governing records.'
  },
  [pscustomobject]@{
    Path='content/public-works/parks-recreation.md'
    ReplaceUrl='https://files.abqinfo.com/public-works/parks-recreation/cabq-2017-parks-recreation-go-bond-project-scopes.pdf'
    RemoveUrls=@()
    Description='The City''s complete 2017 program book includes the Parks and Recreation scopes and 2017-2025 funding schedule within the broader decade plan, alongside planning criteria, operating impacts, maps, and legislation.'
  },
  [pscustomobject]@{
    Path='content/public-works/stormwater-drainage.md'
    ReplaceUrl='https://files.abqinfo.com/public-works/stormwater/cabq-2017-storm-drainage-go-bond-project-scopes.pdf'
    RemoveUrls=@()
    Description='The City''s complete 2017 program book includes the Storm Drainage scopes and 2017-2025 funding schedule within the broader decade plan, alongside planning criteria, operating impacts, maps, and legislation.'
  },
  [pscustomobject]@{
    Path='content/transportation/transit/abq-ride.md'
    ReplaceUrl='https://files.abqinfo.com/transportation/transit/cabq-2017-abq-ride-transit-go-bond-project-scopes.pdf'
    RemoveUrls=@()
    Description='The City''s complete 2017 program book includes the ABQ RIDE transit scopes and 2017-2025 funding schedule within the broader decade plan, alongside planning criteria, operating impacts, maps, and legislation.'
  }
)

foreach ($item in $crossListings) {
  $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $item.Path
  $text = Replace-EntryByArchiveUrl $text $item.ReplaceUrl (Master-Entry $item.Description $false) $item.Path
  foreach ($url in @($item.RemoveUrls)) { $text = Remove-EntryByArchiveUrl $text $url "$($item.Path) extra component" }
  $writes.Add([pscustomobject]@{Path=$item.Path;Text=$text})
}

foreach ($write in $writes) {
  $fullPath = [IO.Path]::GetFullPath([string]$write.Path)
  $temporaryPath = "$fullPath.tmp-$PID"
  [IO.File]::WriteAllText($temporaryPath,[string]$write.Text,[Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
}

$priorMasterValidation = [string]$master.validation_status
$master.status = 'validated'
$master.title = $title
$master.description = $description
$master.description_word_count = @($description -split '\s+' | Where-Object { $_ }).Count
$master.proposed_canonical_page = $locations[0]
$master.implementation_location = $locations[0]
$master.implementation_locations = $locations
$master.cross_listing_approved = $true
$master.cited_predecessors = @(@($master.cited_predecessors) + $componentIds | Sort-Object -Unique)
$master.validation_status = 'passed: authoritative City program book provenance, exact local size and SHA-256, fresh public byte-identical R2 download, complete 144-page visual review, 30 archived component relationships, description, and seven page placements verified'
$master.processing_notes = @(@($master.processing_notes) + @(
  "Prior completed verification preserved during consolidation: $priorMasterValidation",
  'The official City program book is the canonical 2017 master record; its table of contents covers the introduction, every department program, mandated programs, summary tables, planning process, operating impacts, EPC record, maps, and legislation.',
  'No new compilation or R2 object was created because the authoritative City already published the complete program book.'
) | Sort-Object -Unique)
$master.updated_at = (Get-Date).ToUniversalTime().ToString('o')

foreach ($id in $componentIds) {
  $candidate = @($inventory.candidates | Where-Object id -eq $id)[0]
  $prior = [string]$candidate.validation_status
  $candidate.status = 'excluded'
  $candidate.implementation_location = $null
  $candidate.implementation_locations = @()
  $candidate.cross_listing_approved = $false
  $candidate.cited_successors = @(@($candidate.cited_successors) + $masterArchive | Sort-Object -Unique)
  $candidate.exclusion_reason = 'Excluded from standalone site publication after official source-family review; retained byte-identically in R2 and presented through the authoritative 2017 City program book.'
  $candidate.validation_status = 'passed: authoritative provenance, exact original size and SHA-256, and public byte-identical archive were previously verified; retained as a source component with no standalone site entry'
  $candidate.processing_notes = @(@($candidate.processing_notes) + @(
    "Prior completed verification preserved during consolidation: $prior",
    'Standalone listing removed under the approved sparse historical-record consolidation policy; original archive object remains unchanged.',
    "Canonical official program book: $masterId."
  ) | Sort-Object -Unique)
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$next = @($inventory.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { $next[0].id } else { $null }
$inventoryJson = $inventory | ConvertTo-Json -Depth 14
$inventoryFullPath = [IO.Path]::GetFullPath($InventoryPath)
$inventoryTemporaryPath = "$inventoryFullPath.tmp-$PID"
[IO.File]::WriteAllText($inventoryTemporaryPath,$inventoryJson,[Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $inventoryTemporaryPath -Destination $inventoryFullPath -Force

$artifact = [pscustomobject][ordered]@{
  schema_version = 1
  created_at = (Get-Date).ToUniversalTime().ToString('o')
  batch_id = 'go2017-official-master-consolidation-2026-09-16'
  decision = 'Use the authoritative City program book as the single visible 2017 master record; preserve all 30 short component originals and completed verification results in inventory and R2 without standalone site entries.'
  master = [pscustomobject][ordered]@{
    id = $masterId
    title = $title
    archive_url = $masterArchive
    official_record_url = $officialRecord
    official_pdf_url = $officialPdf
    official_library_url = $officialLibrary
    local_path = $masterFile.path
    size_bytes = $masterFile.size_bytes
    checksum_sha256 = $masterFile.checksum_sha256
    public_archive_validation = $publicValidation
    pdf_page_count = 144
    layout_note = 'The City PDF is a two-up landscape scan; its internal table of contents runs beyond page 200 while the PDF contains 144 sheets.'
    visual_review = [pscustomobject][ordered]@{
      contact_sheet_pages_reviewed = 144
      high_resolution_pages_reviewed = @(3,4)
      all_pages_legible_at_contact_sheet_scale = $true
      table_of_contents_verified_at_high_resolution = $true
      observed_sections = @(
        'Introduction',
        'G.O. Bond Program Summary',
        'DMD Streets',
        'DMD Storm Drainage',
        'Parks and Recreation',
        'Public Safety Fire',
        'Public Safety Police',
        'ABQ Ride Transit',
        'Community Facilities',
        'Mandated Programs',
        'Summary Tables',
        'Planning Process',
        'Operating and Maintenance Impacts',
        'EPC Decision and Public Hearing',
        'Appendix A Committee Members',
        'Appendix B Maps',
        'Appendix C Legislation'
      )
    }
    implementation_locations = $locations
  }
  component_count = $components.Count
  components = @($components)
  site_changes = [pscustomobject][ordered]@{
    modified_pages = @($writes.Path)
    removed_standalone_component_records = 30
    visible_master_record_links = 7
    r2_uploads = 0
    preserved_original_r2_objects = 30
  }
  unresolved_questions = @()
}
$artifactJson = $artifact | ConvertTo-Json -Depth 14
$artifactFullPath = [IO.Path]::GetFullPath($OutputPath)
$artifactTemporaryPath = "$artifactFullPath.tmp-$PID"
[IO.File]::WriteAllText($artifactTemporaryPath,$artifactJson,[Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $artifactTemporaryPath -Destination $artifactFullPath -Force

[pscustomobject]@{
  master = $masterId
  components_preserved = $components.Count
  modified_pages = @($writes.Path)
  r2_uploads = 0
  output = $OutputPath
} | ConvertTo-Json -Depth 5 -Compress
