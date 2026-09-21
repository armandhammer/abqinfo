[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$DecisionPath = 'project-state/discovery/unm-2040-strategic-framework-decision-2026-09-20.json',
  [string]$QueuePath = 'project-state/discovery/ordinary-queue-closeout-2026-09-20-post-unm2040.json',
  [string]$CurrentPath = 'project-state/CURRENT.md',
  [string]$CheckpointPath = 'project-state/checkpoint.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Utf8Json($Value, [string]$Path) {
  [IO.File]::WriteAllText([IO.Path]::GetFullPath($Path), ($Value | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
}

$id = 'src-e0624ecba79f3f17'
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json -DateKind String
$candidate = @($inventory.candidates | Where-Object id -eq $id)
if ($candidate.Count -ne 1) { throw "Expected exactly one candidate for $id." }
if ($candidate[0].status -notin @('parsed', 'excluded')) { throw "Expected $id to be parsed or excluded, found '$($candidate[0].status)'." }
if (-not (Test-Path -LiteralPath $candidate[0].local_path)) { throw "Downloaded source is missing: $($candidate[0].local_path)" }

$note = 'Decision 2026-09-20: reviewed official UNM 2040 Strategic Planning Framework, revised 2022-04-13. It is a polished, high-density 18-page UNM-wide aspirational framework, not a campus master plan or transportation/land-use/infrastructure plan. Its only physical references are generic sustainability, housing, security, and activation aspirations; it contains no locational, capital-program, mobility, land-use, or implementation detail suitable for ABQInfo. Excluded as outside durable ABQInfo public-policy/infrastructure scope. No R2 or public-content action.'
$notes = @($candidate[0].processing_notes | ForEach-Object { [string]$_ } | Where-Object { $_ -notmatch '^Download failed:' } | Select-Object -Unique)
if ($notes -notcontains $note) { $notes += $note }
$set = @{
  status = 'excluded'
  title = 'UNM 2040: Opportunity Defined - Strategic Planning Framework (revised April 13, 2022)'
  date = '2022-04-13'
  provenance_status = 'Official UNM Opportunity Defined PDF linked from UNM Campus Planning and the current official UNM 2040 site.'
  description = 'Official 2022 UNM-wide aspirational framework stating vision, mission, values, five goals, objectives, planning process, and engagement; excluded because it lacks specific Albuquerque public-policy, infrastructure, land-use, or transportation content.'
  proposed_canonical_page = $null
  implementation_location = $null
  implementation_locations = @()
  cross_listing_approved = $false
  validation_status = 'excluded: reviewed official 18-page framework is a university-wide aspirational strategy without a durable ABQInfo scope fit or canonical placement.'
  exclusion_reason = 'University-wide strategic framework, not a campus master plan: polished and substantive but lacks specific transportation, land-use, campus-development, public-infrastructure, locational, capital-program, or implementation content. A standalone ABQInfo entry would stretch the site beyond its Albuquerque public-policy/infrastructure scope.'
  processing_notes = $notes
}
& "$PSScriptRoot/Update-Candidate.ps1" -Id $id -Set $set -InventoryPath $InventoryPath | Out-Null

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json -DateKind String
$candidate = @($inventory.candidates | Where-Object id -eq $id)
if ($candidate.Count -ne 1 -or $candidate[0].status -ne 'excluded') { throw 'Candidate update did not produce the expected excluded disposition.' }

$quality = [ordered]@{
  visual_inspection = 'Rendered selected pages (cover, framework, sustainability goal, timeline, and next-steps page) show a professional, legible UNM-branded publication with consistent hierarchy, photographs, diagrams, and no visible clipping or corruption.'
  page_count = 18
  extractable_words = 4276
  information_density = 'Substantive for institutional strategy: five goal/objective pages plus planning, governance, and stakeholder-engagement narrative. The density is not subject-specific infrastructure or public-policy evidence.'
  document_quality = 'Official, visually polished, text-extractable PDF; 8,896,226 bytes; SHA-256 4757e9d9882608a83768d9cab44509f3c39e141f8dff9bebec605af38c38ae00.'
  standalone_public_value = 'Meaningful to UNM stakeholders and statewide higher-education context, but not independently valuable as an ABQInfo public-policy/infrastructure record.'
  series_component_relationship = 'Canonical high-level UNM 2040 framework, with the official UNM 2040 website providing goal-specific initiatives and implementation context. It is not a component of the UNM Integrated Campus Plan or the 2025-2030 Sustainability Strategic Plan.'
  intended_publication_form = 'None in ABQInfo. Retain the narrower Integrated Campus Plan, Safe Mobility Action Plan, and Sustainability Strategic Plan pathways for separately authorized and independently scoped review.'
  rationale = 'Quality alone does not establish ABQInfo fit. The framework contains generic institutional aspirations rather than durable, independently interpretable Albuquerque policy, transportation, land-use, campus-development, public-infrastructure, project, map, capital-program, or implementation information.'
}

$decision = [ordered]@{
  schema_version = 1
  artifact_type = 'ordinary_queue_one_record_decision'
  recorded_at = '2026-09-20'
  candidate_id = $id
  selection_artifact = 'project-state/discovery/ordinary-queue-next-position-2026-09-20-post-form-based-zones.json'
  retained_source_evidence = @(
    'project-state/discovery/src-87fa3827b36c8915-retained-source-crawl-2026-09-12.json',
    'project-state/discovery/retained-source-audit-queue.json',
    'project-state/discovery/retained-source-audit-2026-09-12-b-summary.json',
    'project-state/discovery/unm-cnm-focused-source-scope.json'
  )
  identity = [ordered]@{
    exact_title = 'UNM 2040: Opportunity Defined - Strategic Planning Framework'
    edition_date = 'Revised April 13, 2022 (the official linked filename is dated May 2022)'
    issuing_body = 'The University of New Mexico'
    document_type = 'University-wide strategic planning framework / long-term aspirational vision'
    authoritative_source = 'https://opportunity.unm.edu/assets/docs/unm2040_strategic_framework_5_2022.pdf'
    authoritative_parent = 'https://css.unm.edu/campus-planning/'
    source_verification = 'The retained Campus Planning crawl recorded the official outbound link. Current official UNM 2040 About and President pages still describe UNM 2040 as the university framework and link the framework/initiative site.'
    bytes = 8896226
    sha256 = '4757e9d9882608a83768d9cab44509f3c39e141f8dff9bebec605af38c38ae00'
  }
  framework_relationship = [ordered]@{
    official_unm_framework = $true
    finding = 'This is the official UNM 2040 high-level framework, not another institution''s planning document and not an UNM campus master plan.'
    unm_2040_role = 'Sets a 20-year aspirational vision, mission, values, five university-level goals, and near-term objectives; the document itself says detailed tactics, accountability, and targets are to be set in the implementation phase.'
    later_or_implementation_material = 'The current UNM 2040 website presents initiatives as the mechanism to achieve the goals; it does not present a later replacement comprehensive framework. The 2025 UNM legislative-priorities material applies the 2040 goals to specific capital and infrastructure requests but is a separate, time-bounded legislative record.'
    stronger_canonical_version = 'No stronger superseding general UNM 2040 framework was found in the bounded official-source review. For physical campus development, the separately retained UNM Integrated Campus Plan is the more specific canonical planning record; for sustainability and mobility, the separately retained 2025-2030 Sustainability Strategic Plan and Safe Mobility Action Plan are more specific records. None is a duplicate or successor to this framework as a whole.'
  }
  subject_scope_review = [ordered]@{
    direct_relevance = @(
      'Goal Four generally calls for sustainable operations, reduced environmental impact, campus wellness, housing, security, and activation of physical and virtual spaces.',
      'Goal One generally refers to economic development and relationships with public agencies and communities.'
    )
    absent_material = @(
      'No transportation mode, route, parking, bicycle, pedestrian, transit, roadway, or mobility policy, program, map, data, project, budget, or implementation measure.',
      'No land-use designation, campus-development plan, facilities inventory, project list, capital program, site plan, infrastructure plan, locational analysis, or project-specific public engagement record.',
      'No Albuquerque-specific policy action beyond general institutional context.'
    )
    abqinfo_scope_finding = 'UNM is a major Albuquerque institution, but that fact alone is insufficient. This university-wide aspirational strategy does not provide a durable ABQInfo public-policy/infrastructure record or support a non-stretched canonical placement.'
    canonical_placement = $null
  }
  quality_assessment = $quality
  disposition = [ordered]@{
    status = 'excluded'
    reason = 'Outside ABQInfo scope despite high publication quality and official status.'
    inventory_only = $true
    archive_or_publication_authorized = $false
    r2_mutation = $false
    hugo_content_changed = $false
    pull_request_created = $false
    merge_or_deploy = $false
  }
  ordinary_queue_closeout = [ordered]@{
    filtered_ordinary_residuals_after_decision = 0
    ordinary_review_queue_exhausted = $true
    method = 'Recomputed pending-review rows after this terminal decision and applied the durable completed-family, requires-human-review, and external-gate filter from the preceding ordinary-queue artifact, CURRENT.md, and checkpoint state.'
    next_logical_project_work_category = 'Separately authorized archive preparation/upload and public-byte verification for already approved inventory-only families, beginning with the prepared Municipal Development standard-form agreements or another explicitly chosen durable archive gate.'
    do_not_begin = 'No archive, R2, Hugo, public-placement, implementation, merge, or deployment work began in this task.'
  }
  validation = [ordered]@{
    source_pdf_downloaded = $true
    pdf_text_extracted = $true
    page_count_verified = $true
    rendered_visual_sample_reviewed = $true
    official_current_framework_pages_checked = $true
    inventory_status_checked = $true
    ordinary_queue_recomputed = $true
  }
}
Write-Utf8Json $decision $DecisionPath

$queue = [ordered]@{
  schema_version = 1
  artifact_type = 'ordinary_queue_filtered_closeout'
  recorded_at = '2026-09-20'
  supersedes = 'project-state/discovery/ordinary-queue-next-position-2026-09-20-post-form-based-zones.json'
  method = 'After applying the UNM 2040 one-record terminal decision, queried the current master inventory pending-review rows and applied the same durable completed-family, requires-human-review, and external-gate filter used by the superseded filtered queue.'
  sources = [ordered]@{ source_inventory = $InventoryPath; source_current = $CurrentPath; source_checkpoint = $CheckpointPath; prior_queue = 'project-state/discovery/ordinary-queue-next-position-2026-09-20-post-form-based-zones.json'; completed_record_decision = $DecisionPath }
  counts = [ordered]@{ pending_review_current = $inventory.counts.'pending review'; completed_or_gated_pending_covered = $inventory.counts.'pending review'; filtered_pending_review = 0; residual_clusters = 0 }
  ordinary_review_queue_exhausted = $true
  residual_clusters = @()
  next_actionable_cluster = $null
  next_logical_project_work_category = [ordered]@{
    category = 'Separately authorized archive preparation/upload and public-byte verification for already approved inventory-only records'
    recommended_start = 'Municipal Development standard-form agreements already prepared for their explicitly authorized archive stage, or another user-selected durable archive gate.'
    authorization_boundary = 'Do not start this category without explicit current authorization for the relevant external archive action.'
  }
  safeguards_observed = [ordered]@{ r2_mutation = $false; hugo_content_changed = $false; pull_request_created = $false; merge_or_deploy = $false }
}
Write-Utf8Json $queue $QueuePath

$current = Get-Content -Raw -Encoding UTF8 -LiteralPath $CurrentPath
$old = 'The Form Based Zones final-parts family is resolved in `project-state/discovery/form-based-zones-final-parts-family-decision-2026-09-20.json`: the April 2, 2009 final Part A and Part C PDFs are genuine complementary components of former Zoning Code Section 14-16-3-22, but not complete independently publishable records. Both are requires human review with final Part B because no combined final document or enacted ordinance was established; this is obsolete pre-IDO material. No R2 or public-content action occurred. The recomputed filtered queue is recorded in `project-state/discovery/ordinary-queue-next-position-2026-09-20-post-form-based-zones.json`; its only ordinary residual is the one-record UNM 2040 strategic framework. Do not begin it without a new task instruction.'
$new = 'The sole remaining ordinary residual, `src-e0624ecba79f3f17`, is resolved in `project-state/discovery/unm-2040-strategic-framework-decision-2026-09-20.json`: the official 18-page UNM 2040 Strategic Planning Framework (revised April 13, 2022) is a polished university-wide aspirational strategy, not a campus master plan. It has no specific transportation, land-use, campus-development, public-infrastructure, locational, capital-program, or implementation content and no durable non-stretched ABQInfo placement, so it is excluded. The recomputed filtered ordinary queue is closed in `project-state/discovery/ordinary-queue-closeout-2026-09-20-post-unm2040.json`: no actionable ordinary residual remains. The next logical category is separately authorized archive preparation/upload and public-byte verification for already approved inventory-only families; do not begin it without the relevant current authorization.'
if ($current.Contains($old)) {
  [IO.File]::WriteAllText([IO.Path]::GetFullPath($CurrentPath), $current.Replace($old, $new), [Text.UTF8Encoding]::new($false))
} elseif (-not $current.Contains($new)) {
  throw 'CURRENT.md ordinary-residual paragraph did not match either the expected prior or completed state.'
}

$checkpoint = Get-Content -Raw -Encoding UTF8 -LiteralPath $CheckpointPath | ConvertFrom-Json -DateKind String
$checkpoint.recorded_at = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$checkpoint.completed_item_range = 'Resolved the sole filtered ordinary residual, src-e0624ecba79f3f17: the official 18-page UNM 2040 Strategic Planning Framework (revised 2022-04-13) is excluded because it is a university-wide aspirational strategy without specific Albuquerque transportation, land-use, campus-development, public-infrastructure, capital-program, or implementation content or a durable ABQInfo placement. No R2, Hugo, PR, merge, or deployment action occurred. The filtered ordinary-review queue is exhausted.'
$checkpoint.total_candidates = @($inventory.candidates).Count
$checkpoint.counts_by_status = $inventory.counts
$checkpoint.remaining_nonterminal = @($inventory.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') }).Count
$checkpoint.next_pending_id = $inventory.next_pending_id
$checkpoint.resume_command = 'Filtered ordinary review is exhausted; do not re-open completed or externally gated work. The next logical category is separately authorized archive preparation/upload and public-byte verification for approved inventory-only families, beginning only after explicit current authorization for the relevant external action.'
Write-Utf8Json $checkpoint $CheckpointPath

Write-Output "PASS: excluded $id; wrote $DecisionPath and $QueuePath; filtered ordinary residuals = 0."
