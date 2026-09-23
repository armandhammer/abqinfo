[CmdletBinding()]
param(
  [string]$PagePath = 'content/development-land-use/area-sector-plans.md',
  [string]$PreparationPath = 'project-state/discovery/planned-growth-strategy-archive-preparation-2026-09-23.json',
  [string]$VerificationPath = 'project-state/discovery/planned-growth-strategy-archive-public-byte-verification-2026-09-23.json',
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OutputPath = 'project-state/discovery/planned-growth-strategy-hugo-implementation-2026-09-23.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$prepared = Get-Content -Raw -Encoding UTF8 -LiteralPath $PreparationPath | ConvertFrom-Json
$verified = Get-Content -Raw -Encoding UTF8 -LiteralPath $VerificationPath | ConvertFrom-Json
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json -DateKind String
$page = Get-Content -Raw -Encoding UTF8 -LiteralPath $PagePath
$heading = '## Citywide Growth Strategy'
$start = $page.IndexOf($heading, [StringComparison]::Ordinal)
if ($start -lt 0 -or $page.LastIndexOf($heading, [StringComparison]::Ordinal) -ne $start) { throw 'Expected one Citywide Growth Strategy section.' }
$next = $page.IndexOf("`n## ", $start + $heading.Length, [StringComparison]::Ordinal)
$section = if ($next -lt 0) { $page.Substring($start) } else { $page.Substring($start, $next - $start) }
if (@($prepared.records).Count -ne 13 -or $verified.state -ne 'complete_all_13_public_byte_verified_and_inventory_reconciled' -or @($verified.results).Count -ne 13) { throw 'The exact 13-original archival prerequisite is incomplete.' }
if ($section -notmatch '11 named chapters' -or $section -notmatch '12 files' -or $section -notmatch 'No verified complete combined Part 2 original' -or $section -notmatch 'documented order') { throw 'Part 2 publication limitation is absent.' }
if ($section -match '/Part1-[^\s)]*\.pdf|/Part2\.pdf|Chapter 3(?:\.0)? (?:is )?(?:missing|unavailable)') { throw 'A duplicate, unrelated, or stale-gap link or claim appears in the PGS section.' }

foreach ($record in @($prepared.records)) {
  $result = @($verified.results | Where-Object id -eq $record.id)
  $candidate = @($inventory.candidates | Where-Object id -eq $record.id)
  if ($result.Count -ne 1 -or $candidate.Count -ne 1) { throw "PGS inventory/verification identity missing: $($record.id)" }
  $result = $result[0]; $candidate = $candidate[0]
  if (-not $result.byte_identical -or $candidate.status -notin @('placement assigned','implemented') -or $candidate.scope_assessment.final_scope_decision -ne 'passes_both_gates') { throw "PGS record not eligible for local implementation: $($record.id)" }
  if ($candidate.r2_url -cne $record.proposed_future_archive_url -or $candidate.direct_file_url -cne $record.authoritative_original_url) { throw "PGS source or archive URL changed: $($record.id)" }
  foreach ($url in @($record.proposed_future_archive_url,$record.authoritative_original_url)) {
    if ($section.Split($url, [StringSplitOptions]::None).Count -ne 2) { throw "PGS section must contain URL exactly once: $url" }
  }
}

foreach ($record in @($prepared.records)) {
  $candidate = @($inventory.candidates | Where-Object id -eq $record.id)[0]
  $note = 'PGS Hugo implementation 2026-09-23: one curated Citywide Growth Strategy section presents the complete Part 1 original and 12 separate Part 2 City originals covering all 11 named chapters; no verified complete combined Part 2 original exists. Local branch only; PR, preview, merge, deployment, and production verification not performed.'
  $notes = @($candidate.processing_notes)
  if ($note -notin $notes) { $notes += $note }
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $record.id -InventoryPath $InventoryPath -Set @{
    status='implemented';implementation_location=$PagePath;implementation_locations=@($PagePath)
    proposed_canonical_page=$PagePath;cross_listing_approved=$false
    validation_status='Hugo Citywide Growth Strategy section implemented on planning branch; archive bytes verified; PR/preview and production verification pending'
    processing_notes=$notes
  } | Out-Null
}

$artifact = [ordered]@{
  schema_version=1;artifact_type='planned_growth_strategy_hugo_implementation'
  recorded_at=(Get-Date).ToUniversalTime().ToString('o');state='implemented_on_planning_branch_not_live'
  page=$PagePath;section='Citywide Growth Strategy'
  page_url_after_publication='https://abqinfo.com/development-land-use/area-sector-plans/'
  preparation_artifact=$PreparationPath;public_byte_verification_artifact=$VerificationPath
  implemented_inventory_ids=@($prepared.records.id)
  presentation='One curated family: the complete 286-page Part 1 City original, followed by 12 separate official Part 2 PDF deliveries in chapter order covering all 11 named chapters.'
  part_2_limit='No verified complete combined Part 2 original exists; the chapter PDFs are not a synthetic or original combined volume.'
  section_sha256=(Get-FileHash -InputStream ([IO.MemoryStream]::new([Text.Encoding]::UTF8.GetBytes($section))) -Algorithm SHA256).Hash.ToLowerInvariant()
  archive_links=13;official_city_source_links=13
  inventory_status='implemented';r2_mutation=$false;pr_created=$false;merge_or_deploy=$false;production_verified=$false
  next_stage='Separately authorized PR and preview review before any merge or deployment.'
}
$full = [IO.Path]::GetFullPath($OutputPath)
$temporary = "$full.tmp-$PID"
[IO.File]::WriteAllText($temporary, ($artifact | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporary -Destination $full -Force
$artifact | ConvertTo-Json -Compress -Depth 8
