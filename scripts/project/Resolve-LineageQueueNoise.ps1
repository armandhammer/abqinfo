[CmdletBinding()]
param([string]$InventoryPath = 'project-state/master-inventory.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json
$lineage = @($inventory.candidates | Where-Object { $_.id -like 'lin-*' -and $_.status -eq 'pending review' })
$duplicateCount = 0
$excludedCount = 0

function Normalize-Title([string]$Title) {
  return (($Title.ToLowerInvariant() -replace '[^a-z0-9]+', ' ').Trim())
}

foreach ($group in @($lineage | Group-Object { Normalize-Title $_.title })) {
  $ordered = @($group.Group | Sort-Object @(
    @{Expression={ if ($_.parent_url -like 'https://www.cabq.gov/*' -or $_.parent_url -like 'https://documents.cabq.gov/*') { 0 } elseif ($_.parent_url -like 'https://files.abqinfo.com/*') { 2 } else { 1 } }},
    @{Expression='id'}
  ))
  $canonical = $ordered[0]
  foreach ($candidate in @($ordered | Select-Object -Skip 1)) {
    $candidate.status = 'duplicate'
    $candidate.exclusion_reason = "Duplicate lineage reference for '$($canonical.title)'; canonical queue record is $($canonical.id)."
    $candidate.validation_status = 'terminal duplicate lineage decision recorded'
    $candidate.processing_notes = @($candidate.processing_notes) + @("Same normalized referenced-document title as $($canonical.id); alternate referring path retained on the canonical record where applicable.") | Sort-Object -Unique
    $canonical.referring_urls = @($canonical.referring_urls) + @($candidate.referring_urls) + @($candidate.parent_url) | Where-Object { $_ } | Sort-Object -Unique
    $canonical.discovery_path = @($canonical.discovery_path) + @($candidate.discovery_path) | Where-Object { $_ } | Sort-Object -Unique
    $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
    $duplicateCount++
  }
}

$genericPatterns = @(
  '^(the )?ordinance$',
  '^(the )?(2015|2024|previous) plan( see appendix)?$',
  '^(transportation|facility|feasibility|review) (plan|study|report)$',
  '^unpaved trails see appendix$',
  '^(prd|city council|planning|coordinating agency) [0-9]+ (plan|program)$',
  '^several arroyo corridor plan$',
  '^initiate bike rack program$',
  '^permit program$',
  '^rank (i|ii).*plan$',
  '^(mr?cog|dmd) [0-9]+ plan$',
  '^(page|programs|implementation programs|ongoing studies|regional planning efforts|quicker implementation|use strava data|appendices appendix) ',
  '^(new program|community plan|action plan|see appendix|safe system|design guide|appendices appendix)$',
  '^(1999 )?aashto guide$',
  '^nacto urban bikeway design guide$',
  '^shared use paths chapter ',
  '^(capital improvement|streets maintenance|annual complete streets maintenance|complete streets annual maintenance|non motorized traffic counts|bike rack|shared active transportation|sustainable vision zero|travel demand management) program$',
  '^agency bollard standard details appendix$',
  '^albuquerque standard detail appendix$',
  '^way accessibility guide$',
  '^active transportation plan$'
)

$canonicalAliases = @{
  'development process manual' = 'src-51d5f0b8ea9585e1'
  'the development process manual' = 'src-51d5f0b8ea9585e1'
  'albuquerque development process manual' = 'src-51d5f0b8ea9585e1'
  'metropolitan transportation plan' = 'src-ca3eb3cd65860dce'
  'vision zero action plan' = 'src-1ab4b8188d3eeda8'
  'comprehensive on street bicycle plan' = 'src-0f60535452ac9154'
  'trail crossing guide' = 'src-14839f6b5ae5f9f1'
  'trail crossings guide' = 'src-14839f6b5ae5f9f1'
  'long range bikeway system' = 'src-cf6fa82eb6524971'
  'the long range bikeway system' = 'src-cf6fa82eb6524971'
  'mrcog long range bikeway system' = 'src-cf6fa82eb6524971'
  'bikeways facility plan' = 'src-27b939c34a1c59fc'
  'trails facility plan' = 'src-395957636cb2fed0'
  'trail facilities plan' = 'src-395957636cb2fed0'
  'trails facilities plan' = 'src-395957636cb2fed0'
  'master recreational trails plan' = 'src-395957636cb2fed0'
  'transportation improvement program' = 'src-d307ff22691b3f3b'
  'albuquerque neighborhood traffic management program' = 'src-936ffac8c8c90741'
  'review report action plan' = 'src-a81d8f2eb8de8c03'
  'albuquerque vision zero year in review action plan' = 'src-a81d8f2eb8de8c03'
  'comprehensive plan' = 'lin-c0f031ceb3a62c28'
  'complete streets ordinance the complete streets ordinance' = 'lin-35f34ee150b3cd76'
  'bike boulevard toolkit' = 'src-d6e142c608f6a2de'
  'regional transportation safety action plan' = 'src-9b3a3aad50ad0c65'
  'pedestrian safety action plan' = 'src-db5a082a44bc115e'
  'arroyo facilities plan' = 'lin-a1eb6d3354704e36'
  'complete streets ordinance' = 'src-301604ce13d0f06e'
  'albuquerque bernalillo county comprehensive plan' = 'src-34f5e43d0fd0f2d0'
}

$aliasCandidates = @($inventory.candidates | Where-Object { $_.id -like 'lin-*' -and $_.status -eq 'pending review' })
foreach ($candidate in $aliasCandidates) {
  $normalized = Normalize-Title $candidate.title
  if ($canonicalAliases.ContainsKey($normalized)) {
    $canonicalId = $canonicalAliases[$normalized]
    if (@($inventory.candidates | Where-Object id -eq $canonicalId).Count -ne 1) { throw "Missing canonical alias target '$canonicalId'." }
    $candidate.status = 'duplicate'
    $candidate.exclusion_reason = "Referenced document is already represented by canonical inventory record $canonicalId."
    $candidate.validation_status = 'terminal cross-inventory lineage duplicate recorded'
    $candidate.processing_notes = @($candidate.processing_notes) + @("Reconciled by reviewed title alias to existing canonical record $canonicalId.") | Sort-Object -Unique
    $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
    $duplicateCount++
  }
}

$policyExclusions = @{
  'active transportation ordinance' = 'Shared-micromobility permitting regulation is outside the curated site scope after removal of the empty Micromobility section; the maintained City program page remains in the broader discovery inventory.'
}
foreach ($candidate in @($inventory.candidates | Where-Object { $_.id -like 'lin-*' -and $_.status -eq 'pending review' })) {
  $normalized = Normalize-Title $candidate.title
  if ($policyExclusions.ContainsKey($normalized)) {
    $candidate.status = 'excluded'
    $candidate.exclusion_reason = $policyExclusions[$normalized]
    $candidate.validation_status = 'terminal relevance exclusion recorded'
    $candidate.processing_notes = @($candidate.processing_notes) + @('Excluded under the user-approved high-relevance curation policy; no site content or R2 object created.') | Sort-Object -Unique
    $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
    $excludedCount++
  }
}

$retained = @($inventory.candidates | Where-Object { $_.id -like 'lin-*' -and $_.status -eq 'pending review' })
foreach ($candidate in $retained) {
  $normalized = Normalize-Title $candidate.title
  if (@($genericPatterns | Where-Object { $normalized -match $_ }).Count) {
    $candidate.status = 'excluded'
    $candidate.exclusion_reason = 'Generic phrase or table/text fragment misidentified as a distinct named document by lineage extraction.'
    $candidate.validation_status = 'terminal lineage-noise exclusion recorded'
    $candidate.processing_notes = @($candidate.processing_notes) + @('Excluded by deterministic lineage-noise rules; the referring plan remains preserved and searchable.') | Sort-Object -Unique
    $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
    $excludedCount++
  }
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$next = @($inventory.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { $next[0].id } else { $null }

$json = $inventory | ConvertTo-Json -Depth 12
$fullPath = [IO.Path]::GetFullPath($InventoryPath)
$temporaryPath = "$fullPath.tmp-$PID"
[IO.File]::WriteAllText($temporaryPath, $json, [Text.UTF8Encoding]::new($false))
[IO.File]::Move($temporaryPath, $fullPath, $true)

[pscustomobject]@{
  InputPendingLineage = $lineage.Count
  DuplicatesResolved = $duplicateCount
  GenericFragmentsExcluded = $excludedCount
  RemainingPendingLineage = @($inventory.candidates | Where-Object { $_.id -like 'lin-*' -and $_.status -eq 'pending review' }).Count
  NextPending = $inventory.next_pending_id
} | ConvertTo-Json -Compress
