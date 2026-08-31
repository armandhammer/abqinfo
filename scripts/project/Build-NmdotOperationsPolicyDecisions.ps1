[CmdletBinding()]
param(
  [string]$OutputPath = 'project-state/discovery/nmdot-operations-policy-decisions.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$plansPage = 'content/transportation/transportation-plans.md'
$operationsPage = 'content/transportation/operations-data.md'
$planningDivision = 'https://www.dot.nm.gov/planning-research-multimodal-and-safety/planning-division/'
$multimodalBureau = 'https://www.dot.nm.gov/planning-research-multimodal-and-safety/planning-division/multimodal-planning-and-programs-bureau/'
$itsPage = 'https://www.dot.nm.gov/highway-operations-program/operations-support-division-director/intelligent-transportation-systems/'

$decisions = @(
  [pscustomobject][ordered]@{
    id='src-c8d7be8df90dce69'; title='NMDOT Public Involvement Plan'; date='2018'
    r2_key='transportation/transportation-plans/nmdot-public-involvement-plan-2018.pdf'; canonical_page=$plansPage; source_page=$planningDivision
    description="Defines NMDOT's statewide framework for involving communities in transportation decisions, including engagement goals, planning and project-development procedures, underserved populations, tribal consultation, communication tools, evaluation, and federal requirements."
  }
  [pscustomobject][ordered]@{
    id='src-9a20086460b5de27'; title='NMDOT Public Involvement Plan Appendix: Stakeholder and Public Outreach'; date='2018'
    r2_key='transportation/transportation-plans/nmdot-public-involvement-plan-appendix-2018.pdf'; canonical_page=$plansPage; source_page=$planningDivision
    description="Preserves the survey results, stakeholder interviews, and public-comment notice used to update NMDOT's involvement plan, including feedback from metropolitan and regional planning organizations and transportation partners."
  }
  [pscustomobject][ordered]@{
    id='src-e1efccbd14cc5b06'; title='NMDOT Transportation Systems Management and Operations Strategic and Program Plan'; date='2025'
    r2_key='transportation/operations-data/nmdot-tsmo-strategic-program-plan-2025.pdf'; canonical_page=$operationsPage; source_page=$itsPage
    description="Establishes NMDOT's statewide operations strategy, with Albuquerque-specific actions for the Regional Transportation Management Center, traffic signals, incident response, Courtesy Patrol, traveler information, communications infrastructure, performance management, and interagency coordination."
  }
  [pscustomobject][ordered]@{
    id='src-0b0fce00fb5f421e'; title='New Mexico 2045 Freight Plan Update with Freight Investment Plan Amendment 3'; date='2023-2025'
    r2_key='transportation/transportation-plans/nmdot-new-mexico-2045-freight-plan-update-amendment-3-2023-2025.pdf'; canonical_page=$plansPage; source_page=$multimodalBureau
    description="Documents statewide freight conditions and investments through 2045, including Albuquerque's I-40 bottlenecks, Sunport air cargo, rail facilities, economic role, safety needs, truck corridors, performance measures, and federally approved project priorities."
  }
)

foreach ($decision in $decisions) {
  $words = @($decision.description -split '\s+' | Where-Object { $_ }).Count
  if ($words -lt 20 -or $words -gt 50) { throw "$($decision.id) description has $words words." }
  $decision | Add-Member -NotePropertyName provenance_status -NotePropertyValue 'official NMDOT source page and authoritative file URL recorded'
  $decision | Add-Member -NotePropertyName processing_notes -NotePropertyValue @(
    'Original authoritative NMDOT PDF preserved without modification.',
    'Description reviewed against extracted text and representative visual inspection.'
  )
}

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
foreach ($decision in $decisions) {
  $candidate = @($inventory.candidates | Where-Object id -eq $decision.id)
  if ($candidate.Count -ne 1) { throw "Expected one inventory candidate for '$($decision.id)'; found $($candidate.Count)." }
  $candidate = $candidate[0]
  if (-not $candidate.local_path -or -not (Test-Path -LiteralPath $candidate.local_path)) { throw "Missing local file for '$($decision.id)'." }
  $candidate.status = 'parsed'
  $candidate.provenance_status = [string]$decision.provenance_status
  $candidate.processing_notes = @(@($candidate.processing_notes) + 'Representative first, midpoint, and final pages visually inspected; PDF rendered successfully.' | Sort-Object -Unique)
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$exclusions = @(
  [pscustomobject]@{id='src-3517e84cb9d5ee92'; reason='Statewide FTA Title VI administration is primarily generic compliance material and does not add substantive Albuquerque transportation planning content beyond existing regional civil-rights resources.'}
  [pscustomobject]@{id='src-d18f199788a7ebc3'; reason='The group Tier II asset plan covers rural Section 5311 providers and explicitly excludes Rio Metro rail service; it has no material Albuquerque transit-asset content.'}
  [pscustomobject]@{id='src-4decb7030ddd1f66'; reason='Town of Bernalillo station-area development plan is outside Albuquerque and does not establish policy or projects materially affecting the city.'}
  [pscustomobject]@{id='src-6b548f9d3975e5a8'; reason='Town of Bernalillo and Sandoval County station brochure is outside Albuquerque and adds no material city or systemwide Rail Runner planning information.'}
  [pscustomobject]@{id='src-1de48e890d72b668'; reason='Los Lunas station-area plan is outside Albuquerque and does not materially affect Albuquerque transportation policy, projects, or Rail Runner system planning.'}
)

foreach ($exclusion in $exclusions) {
  $candidate = @($inventory.candidates | Where-Object id -eq $exclusion.id)
  if ($candidate.Count -ne 1) { throw "Expected one inventory candidate for '$($exclusion.id)'; found $($candidate.Count)." }
  $candidate = $candidate[0]
  $candidate.status = 'excluded'
  $candidate.exclusion_reason = $exclusion.reason
  $candidate.validation_status = 'excluded after relevance review'
  $candidate.processing_notes = @(@($candidate.processing_notes) + 'Reviewed in the NMDOT operations and policy batch; excluded under ABQInfo relevance criteria.' | Sort-Object -Unique)
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$next = @($inventory.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { $next[0].id } else { $null }
[IO.File]::WriteAllText([IO.Path]::GetFullPath($InventoryPath), ($inventory | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))

[ordered]@{schema_version=1;batch_id='nmdot-operations-policy-33';decisions=$decisions} |
  ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{Decisions=$decisions.Count;Exclusions=$exclusions.Count;OutputPath=$OutputPath}|ConvertTo-Json -Compress
