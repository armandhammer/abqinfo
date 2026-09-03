[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$updates = @(
  @{ id='src-9e44e9bc1ed7b70a'; title='Bridge Boulevard at Cortez Intersection'; date='2026'; page='content/transportation/roadway-projects/_index.md'; locations=@('content/transportation/roadway-projects/_index.md'); description='Tracks removal of the westbound slip lane, conversion of the Tower Road connector to two-way travel, new bicycle lanes and drainage, a Tower Road deceleration lane, and a median restricting truck traffic on Cortez Drive.'; note='Current scope, construction information, and project-specific contact verified in the official County page.' },
  @{ id='src-dd3b3cd24c247697'; title='2nd Street ADA Improvements'; date='2025'; page='content/transportation/roadway-projects/_index.md'; locations=@('content/transportation/roadway-projects/_index.md'); description='Tracks accessibility upgrades to sidewalks, transitions, and driveways on the east side of 2nd Street. Phase 1 was completed in June 2025; Phase 2 design is complete and awaits construction funding.'; note='Official project page and separately archived Phase 2 project map verified.' },
  @{ id='src-cff5c8af175867bc'; title='Sunset Road Improvements: Gonzales to Neetsie'; date='2025'; page='content/transportation/roadway-projects/_index.md'; locations=@('content/transportation/roadway-projects/_index.md'); description='Tracks planned roadway reconstruction, bicycle lanes, sidewalk, curb and gutter, infiltration chambers, storm-drain inlets, and a pedestrian safety wall along Sunset Road. Design is complete and the project is in bidding.'; note='Official project page, project-specific contact, and separately archived project map verified.' },
  @{ id='src-e7837973289f5918'; title='4th Street Pavement Preservation'; date='2025'; page='content/transportation/roadway-projects/_index.md'; locations=@('content/transportation/roadway-projects/_index.md'); description='Preserves the completed 2025 milling and repaving project on 4th Street, documenting its roadway-preservation purpose, roughly $3 million construction cost, County bond funding, contractor, schedule, and project contact.'; note='Completion status and project details verified on the official County page.' },
  @{ id='src-219c8ac7cde52685'; title='Barcelona Road Storm Drain Project Phase 2A'; date='2019-2020'; page='content/transportation/roadway-projects/_index.md'; locations=@('content/transportation/roadway-projects/_index.md','content/public-works/stormwater-drainage.md'); description='Preserves the completed 2019-2020 roadway and drainage project between Joe Sanchez and La Junta Roads, which connected runoff to the Armijo Drain and added bicycle lanes, curb and gutter, and sidewalk.'; note='Completed project scope and cost verified on the official County page; cross-listed for roadway and drainage history.' },
  @{ id='src-c6c29c659589329f'; title='Tom Bolack Urban Forest Trail Improvements'; date='2024-2026'; page='content/transportation/bicycling/projects/_index.md'; locations=@('content/transportation/bicycling/projects/_index.md','content/public-works/parks-recreation.md'); description='Documents the completed trail paving and solar-lighting project south of I-40 between Louisiana and San Pedro, including PNM utility coordination, the concrete connection near the dog park, construction sequencing, and before-and-after photographs.'; note='Official City project history verified and cross-listed under bicycling and parks.' }
)

foreach ($update in $updates) {
  $wordCount = @($update.description -split '\s+' | Where-Object { $_ }).Count
  if ($wordCount -lt 20 -or $wordCount -gt 50) { throw "$($update.id) description has $wordCount words." }
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $update.id -InventoryPath $InventoryPath -Set @{
    status = 'validated'
    title = $update.title
    date = $update.date
    file_type = 'HTML'
    provenance_status = 'official government project page verified'
    proposed_canonical_page = $update.page
    description = $update.description
    implementation_location = $update.page
    implementation_locations = $update.locations
    cross_listing_approved = ($update.locations.Count -gt 1)
    validation_status = 'passed: authoritative live government source, 20-50-word description, relevant placement, and current project details validated'
    processing_notes = @($update.note)
  } | Out-Null
}

& "$PSScriptRoot/Update-Candidate.ps1" -Id 'src-ac4426f6f9c5f9e9' -InventoryPath $InventoryPath -Set @{
  status = 'superseded'
  cited_successors = @('src-9c1c7a23d2d20baf')
  exclusion_reason = 'Alternate earlier City-hosted edition of Downtown 2025; ABQInfo already preserves a later, more complete amended official edition and the current Downtown 2050 successor plan.'
  validation_status = 'reviewed and superseded by the implemented amended historical edition and current successor plan'
  processing_notes = @('Complete 104-page text reviewed; retained locally but not separately archived because the implemented official edition is more complete.')
} | Out-Null

& "$PSScriptRoot/Update-Candidate.ps1" -Id 'src-d94e522cdbdb3c94' -InventoryPath $InventoryPath -Set @{
  status = 'superseded'
  cited_successors = @('src-8b49885f46b0b748')
  exclusion_reason = 'Original FFY 2025-2026 NMDOT Planning Work Program superseded by the amended authoritative edition already archived and validated on ABQInfo.'
  validation_status = 'superseded by implemented amended edition'
  processing_notes = @('Not downloaded or archived separately because the later amended edition is the authoritative version currently published by NMDOT.')
} | Out-Null

& "$PSScriptRoot/Update-Candidate.ps1" -Id 'src-cc65d68188a839c9' -InventoryPath $InventoryPath -Set @{
  status = 'excluded'
  exclusion_reason = 'Generic street-level project photograph adds little durable technical or historical information beyond the maintained County project page.'
  validation_status = 'reviewed and excluded for low independent informational value'
  processing_notes = @('Exact 546473-byte source image and checksum remain recorded locally; not uploaded or published.')
} | Out-Null

& "$PSScriptRoot/Update-Candidate.ps1" -Id 'src-458c9158f1dcadf1' -InventoryPath $InventoryPath -Set @{
  status = 'superseded'
  cited_successors = @('src-6fdca53f0eace08c')
  exclusion_reason = 'Earlier PDF archive representation replaced on the site by the original authoritative County PNG with fully reconciled provenance and checksum.'
  validation_status = 'superseded by provenance-complete original-source image'
  processing_notes = @('Legacy R2 object remains preserved, but the original government PNG is now the canonical public link.')
} | Out-Null

& "$PSScriptRoot/Update-Candidate.ps1" -Id 'src-c9c6b977aa13fa5a' -InventoryPath $InventoryPath -Set @{
  processing_notes = @('Parent City page reviewed on 2026-09-02; it primarily routes to a 2026 ArcGIS StoryMap, which remains the next descendant requiring substantive project-level review.')
} | Out-Null

[pscustomobject]@{ validated_web_records=$updates.Count; superseded=3; excluded=1; deferred_descendant=1 }
