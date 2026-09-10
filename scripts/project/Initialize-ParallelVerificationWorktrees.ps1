[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$ManifestPath,
  [Parameter(Mandatory)][string]$WorktreeRoot,
  [string]$Ref,
  [switch]$PlanOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/ParallelVerification.Common.ps1"

$manifest = Read-ParallelVerificationJson -Path ([IO.Path]::GetFullPath($ManifestPath))
$manifestErrors = @(Test-ParallelVerificationManifestObject -Manifest $manifest)
if ($manifestErrors.Count) { throw "Manifest validation failed: $($manifestErrors -join '; ')" }
if (-not $Ref) { $Ref = [string]$manifest.base_commit }

$repositoryRoot = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE) { throw 'Unable to resolve the repository root.' }
$repositoryRoot = [IO.Path]::GetFullPath($repositoryRoot).TrimEnd('\','/')
$rootFullPath = [IO.Path]::GetFullPath($WorktreeRoot).TrimEnd('\','/')
if ($rootFullPath -eq $repositoryRoot -or $rootFullPath.StartsWith("$repositoryRoot\", [StringComparison]::OrdinalIgnoreCase)) {
  throw 'WorktreeRoot must be outside the repository so worktrees cannot pollute the coordinator checkout.'
}

$resolvedRef = (& git rev-parse "$Ref^{commit}").Trim()
if ($LASTEXITCODE) { throw "Unable to resolve worktree ref: $Ref" }
if ($resolvedRef -ne [string]$manifest.base_commit) { throw 'Worktree ref must resolve to the manifest base commit.' }

$inventoryPath = [string]$manifest.inventory_path
if (-not [IO.Path]::IsPathRooted($inventoryPath)) { $inventoryPath = Join-Path $repositoryRoot $inventoryPath }
if ((Get-ParallelVerificationFileHash -Path $inventoryPath) -ne [string]$manifest.inventory_sha256) {
  throw 'Coordinator inventory does not match the manifest snapshot.'
}

$plans = foreach ($worker in @($manifest.workers)) {
  [pscustomobject][ordered]@{
    worker_id = [string]$worker
    path = Join-Path (Join-Path $rootFullPath ([string]$manifest.run_id)) ([string]$worker)
    commit = $resolvedRef
    mode = 'detached read-only worker checkout'
  }
}
if (-not $PlanOnly) {
  foreach ($plan in $plans) {
    if (Test-Path -LiteralPath $plan.path) { throw "Worktree path already exists: $($plan.path)" }
  }
  New-Item -ItemType Directory -Path (Join-Path $rootFullPath ([string]$manifest.run_id)) -Force | Out-Null
  foreach ($plan in $plans) {
    & git worktree add --detach $plan.path $resolvedRef
    if ($LASTEXITCODE) { throw "Unable to create worktree for $($plan.worker_id)." }
  }
}
[pscustomobject][ordered]@{ run_id=$manifest.run_id; manifest_path=[IO.Path]::GetFullPath($ManifestPath); plan_only=[bool]$PlanOnly; worktrees=@($plans) } | ConvertTo-Json -Depth 6
