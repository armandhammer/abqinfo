[CmdletBinding()]
param(
  [string]$GatePath = 'project-state/discovery/2014-ms4-family-package-gate-2026-09-18.json',
  [string]$DecisionPath = 'project-state/discovery/2014-ms4-package-decision-2026-09-18.json',
  [string]$CandidateMappingPath = 'project-state/discovery/undiscovered-documents-candidate-integration-2026-09-17.json'
)
$ErrorActionPreference = 'Stop'
$gate = Get-Content -Raw -Encoding UTF8 -LiteralPath $GatePath | ConvertFrom-Json -DateKind String
$decision = Get-Content -Raw -Encoding UTF8 -LiteralPath $DecisionPath | ConvertFrom-Json -DateKind String
$mapping = Get-Content -Raw -Encoding UTF8 -LiteralPath $CandidateMappingPath | ConvertFrom-Json -DateKind String
if (@($decision.components).Count -ne 28 -or @($decision.components | Select-Object -ExpandProperty candidate_id -Unique).Count -ne 28) { throw 'MS4 decision must represent every component exactly once.' }
if (@($decision.components | Where-Object role -eq 'main_body').Count -ne 1 -or @($decision.components | Where-Object role -eq 'attachment').Count -ne 27) { throw 'MS4 decision composition must be one main body plus 27 attachments.' }
if ([int64](@($decision.components | Measure-Object -Property size_bytes -Sum).Sum) -ne [int64]$gate.scope.total_verified_source_bytes) { throw 'MS4 decision byte total differs from gate.' }
if ($decision.decision.state -ne 'research_complete_archive_and_publication_externally_gated') { throw 'MS4 decision has an invalid external-gate state.' }
if (@($decision.decision.prohibited_now).Count -lt 3) { throw 'MS4 decision lacks explicit current prohibitions.' }
foreach ($id in @($gate.scope.candidate_ids)) {
  $component = @($decision.components | Where-Object candidate_id -eq $id)
  $saved = @($mapping.records | Where-Object candidate_id -eq $id)
  if ($component.Count -ne 1 -or $saved.Count -ne 1) { throw "MS4 component mapping failure for $id." }
  if ($component[0].checksum_sha256 -ne $saved[0].checksum_sha256 -or [int64]$component[0].size_bytes -ne [int64]$saved[0].size_bytes) { throw "MS4 exact source evidence mismatch for $id." }
}
Write-Output 'PASS: 2014 MS4 decision covers exactly one main body plus 27 attachments with saved exact-source evidence and no current archive/publication authorization.'
