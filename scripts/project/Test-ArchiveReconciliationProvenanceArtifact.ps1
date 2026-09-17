[CmdletBinding()]
param(
    [string]$ManifestPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-repair-manifest-2026-09-17.json',
    [string]$ProvenancePath = 'project-state/discovery/archive-reconciliation-provenance-2026-09-17.json'
)

$ErrorActionPreference = 'Stop'
$manifest = Get-Content -Raw -Encoding UTF8 $ManifestPath | ConvertFrom-Json
$provenance = Get-Content -Raw -Encoding UTF8 $ProvenancePath | ConvertFrom-Json
$expected = @($manifest.actions | Where-Object safety_gate -eq 'blocked_on_provenance_research' | ForEach-Object action_id | Sort-Object)
$actual = @($provenance.cases | ForEach-Object action_id | Sort-Object)
$allowed = @('provenance_reconstructed_safe_for_accounting','provenance_reconstructed_but_noncanonical','provenance_incomplete','requires_user_or_higher_judgment')
if ($expected.Count -ne 27 -or $provenance.case_count -ne 27 -or (Compare-Object $expected $actual).Count -ne 0) { throw 'Provenance artifact does not represent the 27 manifest actions exactly once.' }
if (@($provenance.cases | Where-Object { $allowed -notcontains $_.result }).Count) { throw 'Provenance artifact contains an invalid result classification.' }
if (($provenance.result_counts.PSObject.Properties | ForEach-Object { [int]$_.Value } | Measure-Object -Sum).Sum -ne 27) { throw 'Provenance result counts do not sum to 27.' }
foreach ($case in @($provenance.cases)) {
    if (-not $case.r2_key -or -not $case.identified_document.existing_master_candidate_id -or -not $case.authoritative_direct_file_url -or -not $case.external_read_only_evidence_used.official_and_public_r2_byte_identical) { throw "Provenance case $($case.action_id) lacks required identity evidence." }
}
Write-Output 'Archive-reconciliation provenance artifact validation passed: 27 actions represented exactly once with complete identity evidence.'
