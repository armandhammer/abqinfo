[CmdletBinding()]
param([Parameter(Mandatory)][string]$RequestsPath)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. "$PSScriptRoot/MissionScopePolicy.ps1"
$requests=Get-Content -LiteralPath $RequestsPath -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
$registry=Read-MissionScopeLegacyRegistry
foreach($r in $requests){
  if(-not (Test-MissionScopeProgressEligible $r.candidate $registry)){
    throw "Candidate '$($r.candidate.id)' cannot enter or remain in '$($r.candidate.status)' after an update without a complete positive mission scope assessment."
  }
}
Write-Output "Validated $(@($requests).Count) candidate updates with existing MissionScopePolicy."
