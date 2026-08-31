[CmdletBinding()]
param(
  [string]$OutputPath = 'project-state/discovery/safety-capital-history-decisions.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$safety = 'content/transportation/bicycling/safety-crash-data.md'
$capital = 'content/city-data/capital-spending.md'
$abqRide = 'content/transportation/transit/abq-ride.md'
$development = 'content/development-land-use/development-process.md'
$design = 'content/transportation/design-references.md'
$speed = 'content/transportation/roadway-projects/speed-management.md'

$decisions = @(
  [pscustomobject][ordered]@{
    id='src-0fc0e6c184ce2b77'; title='NMDOT Traffic Safety Division Annual Report'; date='2022'
    r2_key='transportation/bicycling/safety-crash-data/nmdot-traffic-safety-annual-report-2022.pdf'; canonical_page=$safety
    source_page='https://www.dot.nm.gov/planning-research-multimodal-and-safety/modal/traffic-safety/'
    description='Documents statewide traffic-safety grants, enforcement, education, DWI courts, crash records, motorcycle and occupant-protection programs, including Albuquerque Police Department cases and Bernalillo County court initiatives during federal fiscal year 2022.'
  }
  [pscustomobject][ordered]@{
    id='src-3b2b9707e1ba4f66'; title='New Mexico Uniform Crash Report Instruction Manual'; date='2019'
    r2_key='transportation/bicycling/safety-crash-data/nmdot-uniform-crash-report-instruction-manual-2019.pdf'; canonical_page=$safety
    source_page='https://www.dot.nm.gov/planning-research-multimodal-and-safety/modal/traffic-safety/traffic-records/'
    description='Defines New Mexico crash-reporting thresholds, terminology, roadway and vehicle fields, pedestrian and bicyclist actions, contributing factors, diagrams, and submission rules underlying Albuquerque-area crash datasets and safety analysis.'
  }
  [pscustomobject][ordered]@{
    id='src-85b380f017be32be'; title='New Mexico Occupant Seat Belt Observation Study'; date='2025'
    r2_key='transportation/bicycling/safety-crash-data/nmdot-occupant-seat-belt-observation-study-2025.pdf'; canonical_page=$safety
    source_page='https://www.dot.nm.gov/planning-research-multimodal-and-safety/modal/traffic-safety/'
    description='Reports statistically designed daytime and nighttime seat-belt observations, statewide trends, vehicle and occupant comparisons, and nighttime sampling that includes Bernalillo County among seven selected New Mexico counties.'
  }
  [pscustomobject][ordered]@{
    id='src-aec47259ed0c7711'; title='NMDOT Transit Compensation Study'; date='2026'
    r2_key='transportation/transit/abq-ride/nmdot-transit-compensation-study-2026.pdf'; canonical_page=$abqRide
    source_page='https://www.dot.nm.gov/planning-research-multimodal-and-safety/modal/transit-rail/transit-bureau/'
    description='Compares NMDOT transit salaries with peer agencies and positions, preserving ABQ RIDE and Rio Metro pay-range benchmarks used to evaluate market competitiveness, recruitment, retention, and potential compensation adjustments.'
  }
  [pscustomobject][ordered]@{
    id='src-8e8e799fe1441d72'; title='Capital Improvements Plan Priorities and Scoring Resolution R-2006-089'; date='2006'
    r2_key='city-data/capital-spending/cabq-capital-improvements-priorities-resolution-r-2006-089.pdf'; canonical_page=$capital
    source_page='https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2007-bond-documents'
    description='Adopts Albuquerque priorities, criteria, weights, and funding allocations for evaluating the 2007 capital program, including infrastructure rehabilitation, adopted plans, public safety, growth, neighborhood needs, and operating-budget effects.'
  }
  [pscustomobject][ordered]@{
    id='src-370fed4be1f1effa'; title='Capital Improvements Plan Priorities and Scoring Resolution R-2008-017'; date='2008'
    r2_key='city-data/capital-spending/cabq-capital-improvements-priorities-resolution-r-2008-017.pdf'; canonical_page=$capital
    source_page='https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2009-go-bond-documents'
    description='Preserves the enacted resolution establishing Albuquerque capital-project priorities, evaluation criteria, scoring weights, set-asides, and proposed allocations for the 2009 General Obligation Bond Program and related decade-plan decisions.'
  }
  [pscustomobject][ordered]@{
    id='src-e6c9a8cffdca81f1'; title='Development Process Manual Chapter 28: Improvements Within the Public Right of Way'; date='2015'
    r2_key='development-land-use/development-process/cabq-dpm-chapter-28-right-of-way-2015.pdf'; canonical_page=$development
    source_page='https://documents.cabq.gov/planning/development-process-manual/'
    description='Preserves the adopted predecessor standards for landscaping, irrigation, street trees, sight-distance triangles, medians, buffers, and maintenance within Albuquerque public rights-of-way before the consolidated 2020 Development Process Manual.'
    implementation_locations=@($development,$design); cross_listing_approved=$true
  }
  [pscustomobject][ordered]@{
    id='src-6b44e57d517969e1'; title='Neighborhood Traffic Management Program Public Meeting Comments'; date='2010'
    r2_key='transportation/roadway-projects/speed-management/cabq-ntmp-public-meeting-comments-2010.doc'; canonical_page=$speed
    source_page='https://www.cabq.gov/council/projects/completed-projects/2015/neighborhood-traffic-management-program-policy-manual'
    description='Preserves questions, concerns, and City responses from four quadrant meetings about speed humps, emergency access, enforcement, neighborhood voting, funding, eligibility, public notice, and development of Albuquerque traffic-calming policy.'
  }
)

foreach ($decision in $decisions) {
  $words = @($decision.description -split '\s+' | Where-Object { $_ }).Count
  if ($words -lt 20 -or $words -gt 50) { throw "$($decision.id) description has $words words." }
  $decision | Add-Member -NotePropertyName provenance_status -NotePropertyValue 'official government source page and authoritative file URL recorded'
  $decision | Add-Member -NotePropertyName processing_notes -NotePropertyValue @(
    'Original authoritative government file preserved without modification.',
    'Description reviewed against extracted text and representative visual inspection where applicable.'
  )
}

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
foreach ($decision in $decisions) {
  $candidate = @($inventory.candidates | Where-Object id -eq $decision.id)
  if ($candidate.Count -ne 1) { throw "Expected one inventory candidate for '$($decision.id)'; found $($candidate.Count)." }
  $candidate = $candidate[0]
  if (-not $candidate.local_path -or -not (Test-Path -LiteralPath $candidate.local_path)) { throw "Missing local file for '$($decision.id)'." }
  if ($decision.id -eq 'src-6b44e57d517969e1') { $candidate.file_type = 'DOC'; $candidate.status = 'parsed' }
  $candidate.provenance_status = [string]$decision.provenance_status
  $inspectionNote = if ($candidate.file_type -eq 'PDF') {
    'Representative first, midpoint, and final pages visually inspected; PDF rendered successfully.'
  } else {
    'Legacy Word document opened read-only with the local Microsoft Word engine and substantive text inspected.'
  }
  $candidate.processing_notes = @(@($candidate.processing_notes) + $inspectionNote | Sort-Object -Unique)
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$superseded = @(
  [pscustomobject]@{id='src-959643609168b387'; canonical='src-ce3c9f54fa83aba9'; reason='February 2014 draft of the Downtown Neighborhood Area Traffic Study; the completed August 2014 report and appendix are already archived and implemented.'}
)
foreach ($item in $superseded) {
  $candidate = @($inventory.candidates | Where-Object id -eq $item.id)[0]
  $candidate.status = 'superseded'
  $candidate.exclusion_reason = "$($item.reason) Canonical final record: $($item.canonical)."
  $candidate.validation_status = 'superseded by later final authoritative report'
  $candidate.processing_notes = @(@($candidate.processing_notes) + 'Reviewed in the safety, capital, and historical-records batch; superseded draft will not be uploaded.' | Sort-Object -Unique)
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$duplicates = @(
  [pscustomobject]@{id='src-bce677e29552aeab'; canonical='src-6479e8efc5bcc2b6'; reason='Duplicate project landing page for the validated North Fourth Street Rank III Corridor Plan City Council draft already archived and implemented.'}
)
foreach ($item in $duplicates) {
  $candidate = @($inventory.candidates | Where-Object id -eq $item.id)[0]
  $candidate.status = 'duplicate'
  $candidate.exclusion_reason = "$($item.reason) Canonical inventory record: $($item.canonical)."
  $candidate.validation_status = 'duplicate source pathway reconciled'
  $candidate.processing_notes = @(@($candidate.processing_notes) + 'Reviewed in the safety, capital, and historical-records batch; duplicate pathway will not be implemented again.' | Sort-Object -Unique)
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$exclusions = @(
  [pscustomobject]@{id='src-d0ebda4d0aec5782'; reason='City Attorney employee-evaluation exhibit; unrelated to ABQInfo transportation, development, public works, budget, mapping, or durable civic-data scope.'}
  [pscustomobject]@{id='src-9241cf6ad86e0d8b'; reason='Generic federal webinar slides explaining nationwide transit-agency safety-plan rules; the material contains no Albuquerque, Rio Metro, or New Mexico analysis or project record.'}
  [pscustomobject]@{id='src-b40aa4022680f9a6'; reason='Blank operational Uniform Crash Report form; the field-by-field instruction manual is the durable explanatory source useful to ABQInfo readers.'}
  [pscustomobject]@{id='src-6abec66e07430172'; reason='Temporary 2023 one-page bridge-construction detour map; it has no durable planning analysis and is obsolete after construction access changed.'}
  [pscustomobject]@{id='src-1e24148e3ff0c970'; reason='Brief South Valley MainStreet program landing page with generic program background; it provides no substantive Albuquerque plan, project analysis, map, dataset, or archival document.'}
)
foreach ($item in $exclusions) {
  $candidate = @($inventory.candidates | Where-Object id -eq $item.id)[0]
  $candidate.status = 'excluded'
  $candidate.exclusion_reason = $item.reason
  $candidate.validation_status = 'excluded after relevance, durability, and informational-value review'
  $candidate.processing_notes = @(@($candidate.processing_notes) + 'Reviewed in the safety, capital, and historical-records batch; excluded under ABQInfo relevance and durability criteria.' | Sort-Object -Unique)
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
[IO.File]::WriteAllText([IO.Path]::GetFullPath($InventoryPath), ($inventory | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))

[ordered]@{schema_version=1;batch_id='safety-capital-history-35';decisions=$decisions} |
  ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{Decisions=$decisions.Count;Duplicates=$duplicates.Count;Superseded=$superseded.Count;Exclusions=$exclusions.Count;OutputPath=$OutputPath}|ConvertTo-Json -Compress
