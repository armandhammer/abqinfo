[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/MissionScopePolicy.ps1"
$legacy = Read-MissionScopeLegacyRegistry
$inventory = Get-Content -Raw -Encoding UTF8 'project-state/master-inventory.json' | ConvertFrom-Json -DateKind String
$byId = @{}
foreach ($candidate in $inventory.candidates) { $byId[$candidate.id] = $candidate }
foreach ($id in $legacy.Keys) {
  if (-not $byId.ContainsKey($id) -or -not (Test-MissionScopeProgressEligible $byId[$id] $legacy)) {
    throw "Historical cutover record no longer validates: $id"
  }
}

$new = [pscustomobject]@{
  id = 'test-newly-reviewed-mission-scope'
  status = 'pending review'
  updated_at = '2026-09-23T00:00:00Z'
  scope_assessment = $null
}
foreach ($status in $script:MissionScopeProgressStatuses) {
  $new.status = $status
  if (Test-MissionScopeProgressEligible $new $legacy) { throw "New record bypassed mission scope in $status." }
  $new.scope_assessment = [pscustomobject]@{ final_scope_decision = 'requires_human_scope_review' }
  if (Test-MissionScopeProgressEligible $new $legacy) { throw "Borderline record bypassed mission scope in $status." }
  $new.scope_assessment = $null
}
$new.scope_assessment = [pscustomobject]@{
  assessed_at = '2026-09-23'
  geographic_institutional_scope = 'Specific Albuquerque program.'
  specific_albuquerque_connection = 'A material City decision.'
  abqinfo_public_information_value = 'Explains the City decision.'
  general_context_exclusion_test = 'The City decision is the substance.'
  final_scope_decision = 'passes_both_gates'
  substantive_rationale = 'The decision gives a reader material public information about the City program.'
}
foreach ($status in $script:MissionScopeProgressStatuses) {
  $new.status = $status
  if (-not (Test-MissionScopeProgressEligible $new $legacy)) { throw "Positive scope failed in $status." }
}
$historical = $byId[@($legacy.Keys)[0]]
$formerStatus = $historical.status
$formerUpdated = $historical.updated_at
$historical.status = 'pending review'
if (-not (Test-MissionScopeProgressEligible $historical $legacy)) { throw 'Pending historical record should remain reviewable.' }
$historical.status = if ($formerStatus -eq 'validated') { 'implemented' } else { 'validated' }
if (Test-MissionScopeLegacyCutover $historical $legacy) { throw 'Cutover exception survived a status transition.' }
$historical.status = $formerStatus
$historical.updated_at = '2026-09-23T00:00:00Z'
if (Test-MissionScopeLegacyCutover $historical $legacy) { throw 'Cutover exception survived an update timestamp change.' }
$historical.updated_at = $formerUpdated

$temporaryRoot = Join-Path ([IO.Path]::GetTempPath()) ("abqinfo-mission-scope-transition-$([guid]::NewGuid().ToString('N'))")
New-Item -ItemType Directory -Path $temporaryRoot | Out-Null
try {
  $temporaryInventory = Join-Path $temporaryRoot 'inventory.json'
  $fixture = [ordered]@{
    allowed_statuses = @('pending review','approved for addition','downloading','downloaded','parsed','description drafted','placement assigned','implemented','validated','excluded','duplicate','superseded','blocked','requires human review')
    counts = [pscustomobject]@{ 'pending review' = 1 }
    next_pending_id = $new.id
    generated_at = '2026-09-23T00:00:00Z'
    candidates = @([pscustomobject]@{
      id = $new.id; status = 'pending review'; updated_at = '2026-09-23T00:00:00Z'
      scope_assessment = $null; description = $null; description_word_count = 0; validation_status = $null
    })
  }
  [IO.File]::WriteAllText($temporaryInventory, ($fixture | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))
  foreach ($laterStatus in @('placement assigned','implemented','validated')) {
    try {
      & "$PSScriptRoot/Update-Candidate.ps1" -Id $new.id -Set @{status=$laterStatus} -InventoryPath $temporaryInventory | Out-Null
      throw "State writer accepted a newly reviewed record in $laterStatus without positive scope."
    }
    catch {
      if ($_.Exception.Message -notmatch 'without a complete positive mission scope assessment') { throw }
    }
  }
  $afterRejection = Get-Content -Raw -Encoding UTF8 $temporaryInventory | ConvertFrom-Json -DateKind String
  if ($afterRejection.candidates[0].status -ne 'pending review') { throw 'Rejected state transition mutated the inventory.' }
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $new.id -Set @{status='placement assigned';scope_assessment=$new.scope_assessment} -InventoryPath $temporaryInventory | Out-Null
  $afterApproval = Get-Content -Raw -Encoding UTF8 $temporaryInventory | ConvertFrom-Json -DateKind String
  if ($afterApproval.candidates[0].status -ne 'placement assigned' -or
      $afterApproval.candidates[0].scope_assessment.final_scope_decision -ne 'passes_both_gates') {
    throw 'State writer rejected a complete positive scope assessment.'
  }
  foreach ($laterStatus in @('implemented','validated')) {
    & "$PSScriptRoot/Update-Candidate.ps1" -Id $new.id -Set @{status=$laterStatus} -InventoryPath $temporaryInventory | Out-Null
    $advanced = Get-Content -Raw -Encoding UTF8 $temporaryInventory | ConvertFrom-Json -DateKind String
    if ($advanced.candidates[0].status -ne $laterStatus) { throw "Positive scope did not advance to $laterStatus." }
  }
}
finally {
  Remove-Item -LiteralPath $temporaryRoot -Recurse -Force
}

Write-Output "PASS: $($legacy.Count) frozen historical records validate; new and changed records require positive scope in all $($script:MissionScopeProgressStatuses.Count) progress states."
