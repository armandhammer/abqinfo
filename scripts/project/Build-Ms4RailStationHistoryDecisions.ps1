[CmdletBinding()]
param(
  [string]$OutputPath = 'project-state/discovery/ms4-rail-station-history-decisions.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$stormwater = 'content/public-works/stormwater-drainage.md'
$rail = 'content/transportation/transit/rail-runner.md'
$redevelopment = 'content/development-land-use/redevelopment-plans.md'

$decisions = @(
  [pscustomobject][ordered]@{
    id='src-5f9bf5a35bdb196e'; title='City of Albuquerque MS4 Annual Report, FY 2018'; date='2018'
    r2_key='public-works/stormwater-drainage/cabq-ms4-annual-report-fy2018.pdf'; canonical_page=$stormwater
    source_page='https://www.cabq.gov/municipaldevelopment/documents/city-of-albuquerque-fy18-ms4-annual-report-nmr04a014.pdf/view'
    description="Documents Albuquerque's FY2018 municipal stormwater permit compliance, including impaired-water priorities, monitoring, illicit-discharge investigations, construction oversight, municipal operations, public education, photographs, laboratory results, inspection records, and extensive supporting appendices."
    large_file_assessment='106,231,387-byte (101.31 MiB) PDF; unusually large because its 1,402 pages contain permit forms, monitoring results, complaint and inspection records, photographs, laboratory reports, chain-of-custody records, and extensive appendices. No smaller authoritative version was identified. Optimization could reduce evidentiary, image, or map fidelity and is not proposed. The user explicitly approved unchanged production archival on August 31, 2026.'
  }
  [pscustomobject][ordered]@{
    id='src-2ce711ded9d1ca82'; title='Belen Station Area Planning Study'; date='2009-02'
    r2_key='transportation/transit/rail-runner/mrcog-belen-station-area-planning-study-2009.pdf'; canonical_page=$rail
    source_page='https://www.mrcog-nm.gov/326/Belen-Plan'
    description="Establishes a transit-oriented development framework around Belen's Rail Runner station, evaluating land use, circulation, market conditions, infrastructure, urban design, public space, redevelopment opportunities, and an illustrative plan for connecting the station with downtown."
  }
  [pscustomobject][ordered]@{
    id='src-132a8105973da62a'; title='Belen Rail Runner Station Infrastructure and Development Workshop'; date='2009-09'
    r2_key='transportation/transit/rail-runner/mrcog-belen-station-infrastructure-development-workshop-2009.pdf'; canonical_page=$rail
    source_page='https://www.mrcog-nm.gov/326/Belen-Plan'
    description='Records the 2009 public workshop that translated the Belen Station Area Planning Study into six priority projects, including Becker Avenue, pedestrian connections, wayfinding, Harvey House access, public spaces, and redevelopment east of the station.'
  }
  [pscustomobject][ordered]@{
    id='src-c4cf54190d8fe881'; title='Coronado Metropolitan Redevelopment Area Enacted Plan Packet'; date='2016'
    r2_key='development-land-use/redevelopment-plans/cabq-coronado-mra-enacted-plan-packet-2016.pdf'; canonical_page=$redevelopment
    source_page='https://documents.cabq.gov/planning/UDD/'
    description='Preserves the complete enacted Coronado MRA packet, combining the redevelopment plan with designation and adoption resolutions R-16-93 and R-16-94, findings of blight, boundaries, public actions, remediation needs, infrastructure recommendations, and financing tools.'
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
  $candidate.exclusion_reason = $null
  $candidate.provenance_status = 'official government source page and authoritative file URL recorded'
  $notes = @($candidate.processing_notes | Where-Object { $_ -notmatch 'no R2 upload is authorized' })
  $notes += 'Representative first, midpoint, and final pages visually inspected; PDF rendered successfully.'
  if ($decision.id -eq 'src-5f9bf5a35bdb196e') {
    $notes += 'User explicitly approved unchanged R2 archival despite the file exceeding the project production-upload threshold on August 31, 2026.'
  }
  $candidate.processing_notes = @($notes | Sort-Object -Unique)
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
  $decision | Add-Member -NotePropertyName provenance_status -NotePropertyValue 'official government source page and authoritative file URL recorded'
  $decision | Add-Member -NotePropertyName processing_notes -NotePropertyValue @(
    'Original authoritative government file preserved without modification.',
    'Description reviewed against substantive content and representative visual inspection.'
  )
}

$excluded = @($inventory.candidates | Where-Object id -eq 'src-cdf0d06ad1801c93')[0]
$excluded.status = 'excluded'
$excluded.exclusion_reason = 'Undated two-page excerpt of City Code section 14-5-6-6; the maintained online City code is more complete, current, and authoritative, while the static excerpt provides no dated adoption or historical context.'
$excluded.validation_status = 'excluded after timeliness, completeness, and informational-value review'
$excluded.processing_notes = @(@($excluded.processing_notes) + 'Representative pages inspected; the excerpt is legible but incomplete and undated, so it will not be archived or implemented.' | Sort-Object -Unique)
$excluded.updated_at = (Get-Date).ToUniversalTime().ToString('o')

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
[IO.File]::WriteAllText([IO.Path]::GetFullPath($InventoryPath), ($inventory | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))

[ordered]@{schema_version=1;batch_id='ms4-rail-station-history-87';decisions=$decisions} |
  ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{Decisions=$decisions.Count;Exclusions=1;OutputPath=$OutputPath}|ConvertTo-Json -Compress
