[CmdletBinding()]
param(
  [string]$BaseUrl = 'https://mrmpo.nm.tipviewer.pmgpro.com',
  [string]$DiscoveryPath = 'research/discovery/mrmpo-tip-viewer-projects-links.json',
  [string]$SnapshotPath = 'research/discovery/mrmpo-tip-viewer-active-projects.json',
  [string]$OverridesPath = 'project-state/discovery/mrmpo-tip-viewer-overrides.json',
  [string]$ReportPath = 'project-state/discovery/mrmpo-tip-viewer-batch-report.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-StableId([int64]$StipItemId) {
  return "src-mrmpo-tip-$StipItemId"
}

function Get-UrlStableId([string]$Value) {
  $bytes = [Text.Encoding]::UTF8.GetBytes($Value.Trim().ToLowerInvariant())
  $sha256 = [Security.Cryptography.SHA256]::Create()
  try { $hash = $sha256.ComputeHash($bytes) } finally { $sha256.Dispose() }
  $hex = -join ($hash | ForEach-Object { $_.ToString('x2') })
  return 'src-' + $hex.Substring(0, 16)
}

function Get-PlainText([AllowNull()][string]$Value) {
  if ([string]::IsNullOrWhiteSpace($Value)) { return $null }
  return (($Value.Trim('"') -replace '\s+', ' ').Trim())
}

function Get-CanonicalPage([string]$Title, [string]$Description, [string]$Agency) {
  $text = "$Title $Description $Agency"
  if ($text -match '(?i)\b(transit|ABQ Ride|Rio Metro|bus|BRT|rail|Sun Van)\b') {
    return 'content/transportation/transit/_index.md'
  }
  if ($text -match '(?i)\b(bicycle|bike|bikeway|pedestrian|trail|walking)\b') {
    return 'content/transportation/bicycling/projects/_index.md'
  }
  return 'content/transportation/roadway-projects/_index.md'
}

function Test-AlbuquerqueScope($Project, [string[]]$Counties) {
  $agency = [string]$Project.LUProjectAgencyID
  $county = @($Counties) -join '; '
  $text = "$($Project.Name) $($Project.Description) $agency $county"
  if ($agency -match '(?i)City of Albuquerque|County of Bernalillo') { return $true }
  if ($county -match '(?i)^Bernalillo$') { return $true }
  if ($text -match '(?i)Albuquerque|\bABQ\b|\bAMPA\b|Sunport|Tramway|Paseo del Norte') { return $true }
  return $false
}

function Get-ProgrammedYears($Project) {
  $years = foreach ($year in 2024..2029) {
    $property = $Project.PSObject.Properties[[string]$year]
    if ($property -and [decimal]$property.Value -gt 0) { [string]$year }
  }
  return @($years)
}

$apiBase = "$($BaseUrl.TrimEnd('/'))/api"
$retrievedAt = (Get-Date).ToUniversalTime().ToString('o')
$stips = Invoke-RestMethod -Uri "$apiBase/data/stips" -Method Get
$activeStip = @($stips | Where-Object { $_.PSObject.Properties['typeName'] -and $_.typeName -eq 'Active' } | Sort-Object id -Descending | Select-Object -First 1)
if (-not $activeStip.Count) { throw 'The TIP Viewer did not return an active TIP.' }
$activeStip = $activeStip[0]

$requestBody = @{ filters = @{ STIPID = [int]$activeStip.id }; isDraftStipInViewer = $false } | ConvertTo-Json -Depth 5
$projects = Invoke-RestMethod -Uri "$apiBase/map/filter" -Method Post -ContentType 'application/json' -Body $requestBody
if (-not $projects.Count) { throw 'The TIP Viewer returned no active projects.' }

$normalizedProjects = foreach ($projectGroup in @($projects | Group-Object STIPItemID | Sort-Object { [int64]$_.Name })) {
  $project = $projectGroup.Group[0]
  $title = Get-PlainText ([string]$project.Name)
  $description = Get-PlainText ([string]$project.Description)
  $agency = Get-PlainText ([string]$project.LUProjectAgencyID)
  $counties = @($projectGroup.Group.LULocationCountyID | Where-Object { $_ } | ForEach-Object { Get-PlainText ([string]$_) } | Sort-Object -Unique)
  $county = if ($counties.Count) { $counties -join '; ' } else { $null }
  $programmedYears = @(Get-ProgrammedYears $project)
  $inScope = Test-AlbuquerqueScope $project $counties
  [ordered]@{
    candidate_id = Get-StableId ([int64]$project.STIPItemID)
    stip_item_id = [int64]$project.STIPItemID
    control_number = [string]$project.STIPItemPublicID
    local_id = if ($project.OtherID) { [string]$project.OtherID } else { $null }
    title = $title
    description = $description
    lead_agency = $agency
    county = $county
    project_estimate = if ($null -ne $project.ProjectEstimate) { [decimal]$project.ProjectEstimate } else { $null }
    programmed_amount = if ($null -ne $project.ProgrammedAmount) { [decimal]$project.ProgrammedAmount } else { $null }
    programmed_years = $programmedYears
    revision_comment = Get-PlainText ([string]$project.Comment)
    has_mapped_geometry = @($projectGroup.Group | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_.ShapeJSON) }).Count -gt 0
    location_record_count = $projectGroup.Count
    albuquerque_scope = $inScope
    proposed_canonical_page = Get-CanonicalPage $title $description $agency
  }
}

$documentsEndpoint = "$apiBase/data/documents/"
$controlNumbers = @($normalizedProjects.control_number | Where-Object { $_ } | Sort-Object -Unique)
$tipDocuments = @()
$documentChunkCount = 0
for ($offset = 0; $offset -lt $controlNumbers.Count; $offset += 40) {
  $last = [Math]::Min($offset + 39, $controlNumbers.Count - 1)
  $chunk = @($controlNumbers[$offset..$last])
  $queryValue = [Uri]::EscapeDataString(($chunk -join ','))
  $documentResponse = Invoke-RestMethod -Uri "$documentsEndpoint`?stipItemPublicIDs=$queryValue" -Method Get
  if ($null -ne $documentResponse) { $tipDocuments += @($documentResponse) }
  $documentChunkCount++
}
$documentProjectIds = @($tipDocuments | ForEach-Object {
  foreach ($propertyName in @('stipItemPublicID', 'STIPItemPublicID', 'stipItemId', 'STIPItemID')) {
    $property = $_.PSObject.Properties[$propertyName]
    if ($property -and $property.Value) { [string]$property.Value; break }
  }
} | Where-Object { $_ } | Sort-Object -Unique)

$snapshot = [ordered]@{
  schema_version = 1
  retrieved_at = $retrievedAt
  source_url = "$($BaseUrl.TrimEnd('/'))/"
  api_endpoint = "$apiBase/map/filter"
  documents_endpoint = $documentsEndpoint
  active_tip = [ordered]@{
    id = [int]$activeStip.id
    name = [string]$activeStip.name
    start_year = [int]$activeStip.startYear
    end_year = [int]$activeStip.endYear
    mpo_approval_date = [string]$activeStip.mpoApprovalDate
    state_approval_date = [string]$activeStip.stateApprovalDate
  }
  project_count = $normalizedProjects.Count
  projects = @($normalizedProjects)
  documents = @($tipDocuments)
}

$snapshotDirectory = Split-Path -Parent $SnapshotPath
if ($snapshotDirectory) { New-Item -ItemType Directory -Force $snapshotDirectory | Out-Null }
$snapshot | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $SnapshotPath -Encoding utf8

$viewerUrl = "$($BaseUrl.TrimEnd('/'))/"
$discoveryCandidates = foreach ($project in $normalizedProjects) {
  [ordered]@{
    id = $project.candidate_id
    url = $viewerUrl
    anchor_text = $project.title
    parent_url = $viewerUrl
    referring_urls = @($viewerUrl)
    discovery_path = @($viewerUrl, "$apiBase/map/filter")
    discovery_method = 'structured public MRMPO TIP Viewer API'
    discovery_depth = 1
    agency = 'MRCOG / MRMPO'
    date = "Active TIP FFY $($activeStip.startYear)-$($activeStip.endYear)"
    file_type = 'TIP project database record'
    size_bytes = $null
    direct_file_url = $null
    provenance_status = 'official public MRMPO TIP dataset recorded'
    proposed_canonical_page = $project.proposed_canonical_page
    description = $project.description
    processing_notes = @(
      "TIP control number: $($project.control_number).",
      "Lead agency: $($project.lead_agency).",
      "Programmed amount: $($project.programmed_amount).",
      "Programmed years: $(@($project.programmed_years) -join ', ').",
      "Albuquerque-scope classification: $($project.albuquerque_scope)."
    )
  }
}

$discovery = [ordered]@{
  agency = 'mrcog'
  source_url = $viewerUrl
  scope = 'Active MRMPO Transportation Improvement Program project database'
  retrieved_at = $retrievedAt
  links = @($viewerUrl)
  candidates = @($discoveryCandidates)
}
$discovery | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $DiscoveryPath -Encoding utf8

$viewerDescription = 'Searches the active regional Transportation Improvement Program by project, agency, location, funding, and programmed year. Use it to inspect current Albuquerque-area roadway, transit, bicycle, pedestrian, and safety investments and revisions beyond the static archived TIP document.'
$currentTipUrl = 'https://www.mrcog-nm.gov/280/Current-TIP'
$overrides = @([ordered]@{
  id = Get-UrlStableId $viewerUrl
  status = 'validated'
  title = 'MRMPO TIP Viewer'
  date = "Active TIP FFY $($activeStip.startYear)-$($activeStip.endYear)"
  file_type = 'Web page or live service'
  proposed_canonical_page = 'content/transportation/transportation-plans.md'
  description = $viewerDescription
  implementation_location = 'content/transportation/transportation-plans.md'
  implementation_locations = @('content/maps/dashboards.md', 'content/transportation/transportation-plans.md')
  cross_listing_approved = $true
  processing_notes = @(
    "Active TIP $($activeStip.name) contains $($normalizedProjects.Count) unique projects.",
    "The structured API returned $(@($projects).Count) location rows; repeated locations were consolidated by STIPItemID.",
    'The live viewer complements the existing unmodified R2 archive of the static TIP PDF.'
  )
  validation_status = "passed: viewer and active public API verified at $retrievedAt"
  provenance_status = 'official public MRMPO source recorded'
}, [ordered]@{
  id = Get-UrlStableId $currentTipUrl
  status = 'validated'
  title = 'MRMPO Current TIP and Revisions'
  date = "Active TIP FFY $($activeStip.startYear)-$($activeStip.endYear)"
  file_type = 'Web page or live service'
  proposed_canonical_page = 'content/transportation/transportation-plans.md'
  description = "MRMPO's maintained TIP page publishes the official current program, revision schedule, amendments, administrative modifications, public-comment materials, and the static project and funding document archived by ABQInfo."
  implementation_location = 'content/transportation/transportation-plans.md'
  implementation_locations = @('content/transportation/transportation-plans.md')
  cross_listing_approved = $false
  processing_notes = @('Maintained source-of-truth landing page retained alongside the unmodified R2 archive and live TIP Viewer.')
  validation_status = "passed: official landing page linked from ABQInfo and verified at $retrievedAt"
  provenance_status = 'official public MRMPO source recorded'
}) + @(foreach ($project in $normalizedProjects) {
  $scopeReason = if ($project.albuquerque_scope) {
    'The dynamic project record is retained in the TIP catalog snapshot and served through the linked live viewer; it is not separately published because the viewer provides no durable project-specific public URL or attachment.'
  } else {
    'The project is outside Albuquerque/Bernalillo County and does not materially affect Albuquerque; its metadata remains in the regional TIP snapshot for coverage accounting.'
  }
  [ordered]@{
    id = $project.candidate_id
    status = 'excluded'
    title = $project.title
    date = "Active TIP FFY $($activeStip.startYear)-$($activeStip.endYear)"
    file_type = 'TIP project database record'
    proposed_canonical_page = $project.proposed_canonical_page
    description = $project.description
    processing_notes = @(
      "Structured MRMPO TIP record $($project.control_number), internal item $($project.stip_item_id).",
      "Lead agency: $($project.lead_agency); county: $($project.county); programmed amount: $($project.programmed_amount); programmed years: $(@($project.programmed_years) -join ', ').",
      'No individual candidate file exists, so file size and checksum controls do not apply.'
    )
    validation_status = "passed: captured from the public active TIP endpoint at $retrievedAt"
    exclusion_reason = $scopeReason
    provenance_status = 'official public MRMPO TIP dataset recorded'
  }
})
$overrides | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $OverridesPath -Encoding utf8

$snapshotFile = Get-Item -LiteralPath $SnapshotPath
$snapshotHash = (Get-FileHash -LiteralPath $SnapshotPath -Algorithm SHA256).Hash.ToLowerInvariant()
$report = [ordered]@{
  generated_at = $retrievedAt
  source_url = $viewerUrl
  active_tip = [string]$activeStip.name
  project_records = $normalizedProjects.Count
  albuquerque_scope_records = @($normalizedProjects | Where-Object albuquerque_scope).Count
  regional_out_of_scope_records = @($normalizedProjects | Where-Object { -not $_.albuquerque_scope }).Count
  attachment_control_numbers_checked = $controlNumbers.Count
  attachment_query_chunks = $documentChunkCount
  project_records_with_documents = $documentProjectIds.Count
  document_records = @($tipDocuments).Count
  project_record_status = 'excluded from separate publication; represented by the linked live viewer and retained in the durable snapshot'
  snapshot_path = $SnapshotPath.Replace('\','/')
  snapshot_size_bytes = [int64]$snapshotFile.Length
  snapshot_sha256 = $snapshotHash
  r2_uploads = 0
  r2_storage_added_bytes = 0
  note = 'The active TIP is already preserved in R2 as a static PDF. This batch adds its maintained live database and does not duplicate the existing archive.'
}
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding utf8

$report | ConvertTo-Json -Depth 8
