Set-StrictMode -Version Latest

$script:MissionScopeProgressStatuses = @(
  'approved for addition', 'downloading', 'downloaded', 'parsed',
  'description drafted', 'placement assigned', 'implemented', 'validated'
)
$script:MissionScopeLegacyStatuses = @('placement assigned', 'implemented', 'validated')
$script:MissionScopeRequiredFields = @(
  'assessed_at', 'geographic_institutional_scope', 'specific_albuquerque_connection',
  'abqinfo_public_information_value', 'general_context_exclusion_test',
  'final_scope_decision', 'substantive_rationale'
)

function Test-PositiveMissionScopeAssessment {
  param($Assessment)
  if ($null -eq $Assessment) { return $false }
  if ($Assessment -is [System.Collections.IDictionary]) { $Assessment = [pscustomobject]$Assessment }
  foreach ($field in $script:MissionScopeRequiredFields) {
    if (-not $Assessment.PSObject.Properties[$field] -or
        [string]::IsNullOrWhiteSpace([string]$Assessment.$field)) { return $false }
  }
  return $Assessment.final_scope_decision -eq 'passes_both_gates'
}

function Read-MissionScopeLegacyRegistry {
  param([string]$Path = 'project-state/discovery/mission-scope-legacy-cutover-2026-09-23.json')
  $registry = Get-Content -Raw -Encoding UTF8 -LiteralPath $Path | ConvertFrom-Json -DateKind String
  $lines = @($registry.records | ForEach-Object { $_.id + [char]124 + $_.status + [char]124 + $_.updated_at })
  $sha = [Security.Cryptography.SHA256]::Create()
  try {
    $bytes = [Text.Encoding]::UTF8.GetBytes(($lines -join [char]10))
    $actualHash = [BitConverter]::ToString($sha.ComputeHash($bytes)).Replace('-','').ToLowerInvariant()
  }
  finally { $sha.Dispose() }
  if ($actualHash -ne '489c5b61fa561fc275e55634a49f92b0b8e6d2322b5ea518d281e2be1c6bbd15') {
    throw 'Mission-scope legacy cutover registry differs from its frozen 2026-09-23 baseline.'
  }
  if ($registry.artifact_type -ne 'mission_scope_legacy_cutover' -or
      $registry.source_commit -ne '3940a2e8037c1ad99d3ca8f76126e73bfb3e5630' -or
      @($registry.records).Count -ne 1628) {
    throw 'Mission-scope legacy cutover registry is missing or has an unexpected baseline.'
  }
  $map = @{}
  foreach ($record in $registry.records) {
    if ($map.ContainsKey($record.id) -or $record.status -notin $script:MissionScopeLegacyStatuses -or
        [string]::IsNullOrWhiteSpace([string]$record.updated_at)) {
      throw "Mission-scope legacy cutover registry has an invalid or duplicate entry: $($record.id)."
    }
    $map[$record.id] = $record
  }
  return $map
}

function Test-MissionScopeLegacyCutover {
  param($Candidate, [hashtable]$LegacyRegistry)
  if ($Candidate.status -notin $script:MissionScopeLegacyStatuses -or
      -not $LegacyRegistry.ContainsKey([string]$Candidate.id)) { return $false }
  $baseline = $LegacyRegistry[[string]$Candidate.id]
  return ($Candidate.status -ceq $baseline.status -and
          [string]$Candidate.updated_at -ceq [string]$baseline.updated_at)
}

function Test-MissionScopeProgressEligible {
  param($Candidate, [hashtable]$LegacyRegistry)
  if ($Candidate.status -notin $script:MissionScopeProgressStatuses) { return $true }
  $assessment = if ($Candidate.PSObject.Properties['scope_assessment']) { $Candidate.scope_assessment } else { $null }
  if (Test-PositiveMissionScopeAssessment $assessment) { return $true }
  return (Test-MissionScopeLegacyCutover $Candidate $LegacyRegistry)
}
