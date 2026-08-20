[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OutputPath = 'project-state/arroyo-history-decisions-2026-08-20.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$items = @(
  [ordered]@{
    id='lin-a1eb6d3354704e36'; title='Facility Plan for Arroyos'; date='1986'
    r2_key='public-works/parks-recreation/arroyo-plans/cabq-facility-plan-for-arroyos-1986.pdf'
    description='Establishes Albuquerque''s citywide framework for multiple use of arroyos and floodplains, coordinating drainage, trails, recreation, open space, environmental protection, and compatible development.'
  },
  [ordered]@{
    id='lin-25bd3939b1cddc44'; title='Amole Arroyo Resource Management Plan'; date='1991'
    r2_key='public-works/parks-recreation/arroyo-plans/cabq-amole-arroyo-resource-management-plan-1991.pdf'
    description='Sets policies and design standards for the Amole Arroyo, including a conceptual recreation network, drainage management, open-space protection, trail development, and compatible adjacent development.'
  },
  [ordered]@{
    id='lin-83db784b0755f109'; title='Bear Canyon Arroyo Resource Management Plan'; date='1991'
    r2_key='public-works/parks-recreation/arroyo-plans/cabq-bear-canyon-arroyo-resource-management-plan-1991.pdf'
    description='Guides trails, recreation, drainage, open-space conservation, and adjacent development along Bear Canyon Arroyo and nearby tributaries through policies, regulations, design standards, and proposed projects.'
  },
  [ordered]@{
    id='lin-b1becfc139b356e3'; title='Pajarito Arroyo Resource Management Plan'; date='1990'
    r2_key='public-works/parks-recreation/arroyo-plans/cabq-pajarito-arroyo-resource-management-plan-1990.pdf'
    description='Plans Pajarito Arroyo as a major open-space linkage, establishing a trail corridor, drainage-management approach, design criteria, development controls, recreation, conservation, and implementation policies.'
  }
)

$inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json
foreach ($item in $items) {
  $candidate = @($inventory.candidates | Where-Object id -eq $item.id)
  if ($candidate.Count -ne 1) { throw "Expected one candidate for '$($item.id)'." }
  $candidate = $candidate[0]
  if ($candidate.status -in @('downloaded','parsed')) { $candidate.status = 'placement assigned' }
  if ($candidate.status -ne 'placement assigned') { throw "Candidate '$($item.id)' is not ready for placement; status is '$($candidate.status)'." }
  $candidate.title = $item.title
  $candidate.date = $item.date
  $candidate.description = $item.description
  $candidate.description_word_count = @($item.description -split '\s+' | Where-Object { $_ }).Count
  $candidate.implementation_location = 'content/public-works/parks-recreation.md'
  $candidate.implementation_locations = @('content/public-works/parks-recreation.md')
  $candidate.validation_status = 'official source, exact size, SHA-256, representative-page rendering, and description reviewed; R2 upload pending'
  if ($item.id -eq 'lin-25bd3939b1cddc44') {
    $candidate.processing_notes = @($candidate.processing_notes) + @('The legacy PDF has a malformed page tree that pypdf and pdfminer cannot flatten; Poppler rendered it successfully and representative pages were visually reviewed. Preserve the original unchanged.') | Sort-Object -Unique
  }
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$json = $inventory | ConvertTo-Json -Depth 12
$fullPath = [IO.Path]::GetFullPath($InventoryPath)
$temporaryPath = "$fullPath.tmp-$PID"
[IO.File]::WriteAllText($temporaryPath, $json, [Text.UTF8Encoding]::new($false))
[IO.File]::Move($temporaryPath, $fullPath, $true)

$output = [ordered]@{
  batch_id = '2026-08-20-arroyo-planning-history'
  decisions = @($items | ForEach-Object {
    [ordered]@{
      id=$_.id; title=$_.title; date=$_.date; r2_key=$_.r2_key
      canonical_page='content/public-works/parks-recreation.md'
      source_page='https://www.cabq.gov/planning/plans-publications'
      agency='City of Albuquerque'; description=$_.description; decision='approved for addition'
      provenance_status='official City plan index and direct government PDF recorded'
      processing_notes=@('Original authoritative City PDF preserved without modification; exact size, SHA-256, and representative rendered pages reviewed.')
    }
  })
}
$output | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{Decisions=$items.Count;OutputPath=$OutputPath}|ConvertTo-Json -Compress
