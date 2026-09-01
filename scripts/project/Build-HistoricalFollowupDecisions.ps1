[CmdletBinding()]
param(
  [string]$OutputPath = 'project-state/discovery/historical-followup-decisions.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$redevelopment = 'content/development-land-use/redevelopment-plans.md'
$transportPlans = 'content/transportation/transportation-plans.md'
$speed = 'content/transportation/roadway-projects/speed-management.md'

$decisions = @(
  [pscustomobject][ordered]@{
    id='src-f6788a6c210da2d8'; title='Tingley Beach Metropolitan Redevelopment Area Project I Plan Adoption Resolution R-306'; date='1983-05'
    r2_key='development-land-use/redevelopment-plans/cabq-tingley-beach-project-i-plan-adoption-resolution-r-306-1983.pdf'; canonical_page=$redevelopment
    source_page='https://documents.cabq.gov/planning/UDD/MRA/'
    description='Preserves the amended City Council adoption resolution, Metropolitan Redevelopment Commission approval, and attached Project I plan for Tingley Beach, documenting public findings, private redevelopment, displacement, financing, public actions, and statutory approval history.'
  }
  [pscustomobject][ordered]@{
    id='src-dd0447c7c88addd3'; title='Albuquerque Modern Streetcar Technical Presentation'; date='2008-02-05'
    r2_key='transportation/transportation-plans/cabq-modern-streetcar-technical-presentation-2008.pdf'; canonical_page=$transportPlans
    source_page='https://www.cabq.gov/council/projects/completed-projects/2008/21st-century-transportation-task-force'
    description='Explains the proposed Albuquerque modern streetcar system through vehicle, power, track, stop, maintenance, utility, construction, operating, safety, accessibility, cost, schedule, and corridor-design considerations presented to the transportation task force in 2008.'
  }
  [pscustomobject][ordered]@{
    id='src-d1e88b8307e6dcf1'; title='Neighborhood Traffic Management Program Traffic-Calming Toolkit'; date='2015'
    r2_key='transportation/roadway-projects/speed-management/cabq-ntmp-traffic-calming-toolkit-2015.pdf'; canonical_page=$speed
    source_page='https://www.cabq.gov/neighborhood-traffic-management-program/toolkit'
    description="Preserves the City traffic-calming toolkit's illustrated comparisons of enforcement, education, markings, crossings, lane narrowing, speed humps, chokers, circles, diverters, closures, one-way conversions, and other measures, including applications, tradeoffs, effectiveness, and costs."
  }
)

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
foreach ($decision in $decisions) {
  $words = @($decision.description -split '\s+' | Where-Object { $_ }).Count
  if ($words -lt 20 -or $words -gt 50) { throw "$($decision.id) description has $words words." }
  $candidate = @($inventory.candidates | Where-Object id -eq $decision.id)
  if ($candidate.Count -ne 1) { throw "Expected one inventory candidate for '$($decision.id)'; found $($candidate.Count)." }
  $candidate = $candidate[0]
  if (-not $candidate.local_path -or -not (Test-Path -LiteralPath $candidate.local_path)) { throw "Missing local file for '$($decision.id)'." }
  $candidate.status = 'parsed'
  $candidate.title = $decision.title
  $candidate.date = $decision.date
  $candidate.provenance_status = 'official government source page and authoritative file URL recorded'
  $candidate.processing_notes = @(@($candidate.processing_notes) + 'Representative first, midpoint, and final pages visually inspected; PDF rendered successfully.' | Sort-Object -Unique)
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
  $decision | Add-Member -NotePropertyName provenance_status -NotePropertyValue 'official government source page and authoritative file URL recorded'
  $decision | Add-Member -NotePropertyName processing_notes -NotePropertyValue @(
    'Original authoritative government file preserved without modification.',
    'Description reviewed against substantive content and representative visual inspection.'
  )
}

$duplicate = @($inventory.candidates | Where-Object id -eq 'src-337f2c9bfc4efdb2')[0]
$duplicate.status = 'duplicate'
$duplicate.exclusion_reason = 'Duplicate Plone view-page pathway for the same 2015 NTMP traffic-calming toolkit. Canonical inventory record: src-d1e88b8307e6dcf1.'
$duplicate.validation_status = 'duplicate source pathway reconciled'
$duplicate.processing_notes = @(@($duplicate.processing_notes) + 'Duplicate toolkit pathway reconciled during the historical follow-up batch.' | Sort-Object -Unique)
$duplicate.updated_at = (Get-Date).ToUniversalTime().ToString('o')

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
[IO.File]::WriteAllText([IO.Path]::GetFullPath($InventoryPath), ($inventory | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))

[ordered]@{schema_version=1;batch_id='historical-followup-87';decisions=$decisions} |
  ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{Decisions=$decisions.Count;Duplicates=1;OutputPath=$OutputPath}|ConvertTo-Json -Compress
