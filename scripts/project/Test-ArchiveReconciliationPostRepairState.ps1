[CmdletBinding()]
param(
    [string]$StatePath = 'project-state/discovery/archive-reconciliation-post-repair-state-2026-09-17.json',
    [string]$UnresolvedPath = 'project-state/discovery/archive-reconciliation-unresolved-review-2026-09-17.json'
)

$ErrorActionPreference = 'Stop'
$state = Get-Content -Raw -Encoding UTF8 $StatePath | ConvertFrom-Json
$unresolved = Get-Content -Raw -Encoding UTF8 $UnresolvedPath | ConvertFrom-Json
if (@($state.cases).Count -ne 27 -or $state.safe_provenance_repairs_completed -ne 24 -or $state.unresolved_provenance_cases -ne 3 -or $state.previously_completed_safe_bookkeeping_repairs_intact -ne 14) { throw 'Post-repair state counts are inconsistent.' }
if (@($state.cases | Where-Object no_longer_unaccounted).Count -ne 24 -or @($state.cases | Where-Object { $_.provenance_result -eq 'provenance_reconstructed_safe_for_accounting' -and -not $_.master_r2_linkage_exact }).Count) { throw 'Safe provenance repairs are not fully reconciled.' }
if ($unresolved.unresolved_count -ne 3 -or @($unresolved.cases).Count -ne 3) { throw 'Unresolved review artifact count is inconsistent.' }
if (@($unresolved.cases | Where-Object result -ne 'requires_user_or_higher_judgment').Count) { throw 'Unresolved review artifact contains an unexpected classification.' }
Write-Output 'Archive-reconciliation post-repair state validation passed: 24 safe repairs reconciled, 3 unresolved cases isolated, and 14 prior repairs intact.'
