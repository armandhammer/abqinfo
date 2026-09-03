[CmdletBinding()]
param([string]$InventoryPath = 'project-state/master-inventory.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$decisions = @(
  @{ id='src-a3e35430bd73ea33'; status='excluded'; reason='Temporary 2026 application-transition notice for Development Review Services; current application requirements belong on the live City service page and the notice has no durable planning value.' },
  @{ id='src-28ce1d8748abb9a2'; status='excluded'; reason='Routine Development Process Manual Executive Committee agenda without an adopted standard, substantive report, or durable project decision.' },
  @{ id='src-5b3bed00b4ee6d7e'; status='excluded'; reason='Administrative permit form for the Shared Active Transportation Program; the owner removed the empty micromobility section and does not want application forms archived as standalone content.' },
  @{ id='src-1bf49e3b3e07a33e'; status='excluded'; reason='Seasonal 2026 Rail Runner timetable; ABQInfo intentionally links to the authoritative live schedule because service times change and static timetables quickly become misleading.' },
  @{ id='src-2d460500edc5acdb'; status='excluded'; reason='Training notes for nonprofit capital-outlay applicants; procedural application guidance is temporary administrative material rather than a durable adopted plan, funding award, or project record.' },
  @{ id='src-556d4b6b3eeccfa8'; status='excluded'; reason='Internal-style project-request-form training presentation for the 2025 capital cycle; the approved program books and allocation records provide the durable public information.' },
  @{ id='src-6a392f48f0c93f81'; status='excluded'; reason='Mid-Region RTPO civil-rights administration plan applies to the rural RTPO rather than the Albuquerque metropolitan planning area and does not materially affect Albuquerque.' },
  @{ id='src-d179cbbc0b1a0bcf'; status='excluded'; reason='Blank nonprofit capital-outlay agreement form; it contains application administration rather than an adopted project, award, plan, study, dataset, or historical record.' },
  @{ id='src-4b1eef3fed31d045'; status='excluded'; reason='Blank City code-enforcement form; operational forms are not archived unless they supply unique substantive data or policy not available from the current service page.' },
  @{ id='src-8ebda64242416f86'; status='excluded'; reason='Blank City code-enforcement form; operational forms are not archived unless they supply unique substantive data or policy not available from the current service page.' },
  @{ id='src-12f44ed31855fcf3'; status='excluded'; reason='Traffic-flow map is limited to rural Sandoval County and does not materially document Albuquerque or Bernalillo County transportation conditions.' },
  @{ id='src-3f5aaf3a3c826190'; status='excluded'; reason='Traffic-flow map covers Torrance and southern Santa Fe counties rather than Albuquerque or transportation facilities materially serving Albuquerque.' },
  @{ id='src-7ebc7c44d732b84e'; status='excluded'; reason='Traffic-flow map is limited to Valencia County and does not materially document Albuquerque or Bernalillo County transportation conditions.' },
  @{ id='src-62bf76e223700d30'; status='excluded'; reason='Temporary nighttime traffic-control plan for utility work; the work-zone information is expired and adds no durable project or planning history.' },
  @{ id='src-bd36c70bb9926b6b'; status='excluded'; reason='Expired September 2024 Bridge Boulevard work-zone map; the underlying project is represented by durable project plans and current project information.' },
  @{ id='src-f4a9c8f5b1c4d9b3'; status='excluded'; reason='Expired October 2024 Bridge Boulevard work-zone map; the underlying project is represented by durable project plans and current project information.' },
  @{ id='src-105101571d543068'; status='excluded'; reason='Northeast RTPO page is outside the Albuquerque metropolitan planning area and does not materially affect Albuquerque.' },
  @{ id='src-722f4ff7284c0632'; status='excluded'; reason='Southwest RTPO page is outside the Albuquerque metropolitan planning area and does not materially affect Albuquerque.' },
  @{ id='src-76fd2ac8d29b4573'; status='excluded'; reason='Northern Pueblos RTPO and Santa Fe MPO page is outside the Albuquerque metropolitan planning area and does not materially affect Albuquerque.' },
  @{ id='src-9ba68b716966c035'; status='excluded'; reason='Southeast RTPO page is outside the Albuquerque metropolitan planning area and does not materially affect Albuquerque.' },
  @{ id='src-a3def853376c23fe'; status='excluded'; reason='South Central RTPO, Mesilla Valley MPO, and El Paso MPO page is outside the Albuquerque metropolitan planning area and does not materially affect Albuquerque.' },
  @{ id='src-7f51d9a1a82e1f84'; status='excluded'; reason='Temporary 2024 Sheridan Transit Center service-change notice concerns Santa Fe service and is outside Albuquerque scope.' },
  @{ id='src-966f98dfd014ba6f'; status='excluded'; reason='Gallup Area Transportation Safety Plan appendices are outside Albuquerque and do not establish statewide policy or materially affect Albuquerque.' },
  @{ id='src-c2c0e4020e4587c1'; status='excluded'; reason='Gallup Area Transportation Safety Plan is outside Albuquerque and does not establish statewide policy or materially affect Albuquerque.' },
  @{ id='src-f92eb5f72214f3f7'; status='excluded'; reason='Temporary NM 599 shuttle route-change notice concerns Santa Fe service and is outside Albuquerque scope.' },
  @{ id='src-44cb7bfc11b70821'; status='excluded'; reason='General 2022 MRCOG organizational annual report is low-information for ABQInfo compared with the agency transportation plans, datasets, budgets, and project records already retained.' },
  @{ id='src-26de43608f0a6f8b'; status='duplicate'; reason='Landing-page record for the excluded 2022 MRCOG general annual report; retained only as discovery provenance.' },
  @{ id='src-8f151b9724497d2e'; status='excluded'; reason='FFY 2020 quarterly planning-work-program expenditure detail is routine federal grant administration and is superseded for public understanding by adopted UPWPs and substantive planning products.' },
  @{ id='src-b4971a7453e334a1'; status='excluded'; reason='FFY 2020 quarterly planning-work-program performance summary is routine federal grant administration and is superseded for public understanding by adopted UPWPs and substantive planning products.' },
  @{ id='src-0dc3db8a2d675286'; status='superseded'; reason='Individual 2023 street and transportation bond-purpose excerpt is fully contained in the validated 2023 General Obligation Bond Program Book (src-af35c3eb64539dab).' },
  @{ id='src-231593450b871d50'; status='superseded'; reason='Individual 2023 storm and sewer bond-purpose excerpt is fully contained in the validated 2023 General Obligation Bond Program Book (src-af35c3eb64539dab).' },
  @{ id='src-3c3332a3772b9afd'; status='superseded'; reason='Individual 2023 community-facilities bond-purpose excerpt is fully contained in the validated 2023 General Obligation Bond Program Book (src-af35c3eb64539dab).' },
  @{ id='src-4f55acacff0c407f'; status='superseded'; reason='Individual 2023 public-safety bond-purpose excerpt is fully contained in the validated 2023 General Obligation Bond Program Book (src-af35c3eb64539dab).' },
  @{ id='src-7c05d94cfc8fd41b'; status='superseded'; reason='Individual 2023 facilities and energy bond-purpose excerpt is fully contained in the validated 2023 General Obligation Bond Program Book (src-af35c3eb64539dab).' },
  @{ id='src-867f790bbe85d947'; status='superseded'; reason='Individual 2023 parks and recreation bond-purpose excerpt is fully contained in the validated 2023 General Obligation Bond Program Book (src-af35c3eb64539dab).' },
  @{ id='src-f98aa55d48cab9ae'; status='superseded'; reason='Individual 2023 library and cultural bond-purpose excerpt is fully contained in the validated 2023 General Obligation Bond Program Book (src-af35c3eb64539dab).' },
  @{ id='src-799985f05af484b0'; status='superseded'; reason='Condensed 2025 bond-purpose question and project list is superseded by the validated detailed approved program book and concise program-by-purpose edition.' },
  @{ id='src-972a9f61b036fc79'; status='superseded'; reason='Individual 2025 community-facilities bond-purpose excerpt is fully contained in the validated 2025 General Obligation Bond Approved Program Book (src-982cc018b0b8fc01).' },
  @{ id='src-b3c417ab23b71a56'; status='superseded'; reason='Individual 2025 museum and cultural bond-purpose excerpt is fully contained in the validated 2025 General Obligation Bond Approved Program Book (src-982cc018b0b8fc01).' },
  @{ id='src-c52a65289534228a'; status='superseded'; reason='Individual 2025 public-safety bond-purpose excerpt is fully contained in the validated 2025 General Obligation Bond Approved Program Book (src-982cc018b0b8fc01).' },
  @{ id='src-f863794284f102c4'; status='superseded'; reason='Individual 2025 library bond-purpose excerpt is fully contained in the validated 2025 General Obligation Bond Approved Program Book (src-982cc018b0b8fc01).' },
  @{ id='src-1ef2800dbb24d0f4'; status='superseded'; reason='The 2023 mayoral recommendation is superseded for canonical use by the validated final 2023 General Obligation Bond Program Book (src-af35c3eb64539dab).' }
)

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$now = (Get-Date).ToUniversalTime().ToString('o')
foreach ($decision in $decisions) {
  $matches = @($inventory.candidates | Where-Object id -eq $decision.id)
  if ($matches.Count -ne 1) { throw "Expected one candidate for '$($decision.id)'; found $($matches.Count)." }
  $candidate = $matches[0]
  $candidate.status = $decision.status
  $candidate.exclusion_reason = $decision.reason
  $candidate.validation_status = "terminal $($decision.status) decision recorded by recent-priority-cleanup5 review"
  $candidate.updated_at = $now
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) {
  $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count
}
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = $now
$next = @($inventory.candidates | Where-Object {
  $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or
  ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed')
} | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { $next[0].id } else { $null }

$json = $inventory | ConvertTo-Json -Depth 12
$fullPath = [IO.Path]::GetFullPath($InventoryPath)
$temporaryPath = "$fullPath.tmp-$PID"
[IO.File]::WriteAllText($temporaryPath, $json, [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force

[pscustomobject]@{
  finalized = $decisions.Count
  excluded = @($decisions | Where-Object status -eq 'excluded').Count
  duplicate = @($decisions | Where-Object status -eq 'duplicate').Count
  superseded = @($decisions | Where-Object status -eq 'superseded').Count
}
