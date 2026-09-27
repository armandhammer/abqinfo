function Assert-TaskGovernance {
  param([Parameter(Mandatory)][string]$ToolPath, [hashtable]$Parameters = @{})
  $repositoryRoot = [IO.Path]::GetFullPath("$PSScriptRoot/../..")
  $relative = [IO.Path]::GetRelativePath($repositoryRoot, [IO.Path]::GetFullPath($ToolPath)).Replace('\','/')
  $manifest = Get-Content -Raw -LiteralPath "$repositoryRoot/project-state/governance/entrypoints.json" | ConvertFrom-Json -AsHashtable
  $tool = $manifest.tools[$relative]
  if (-not $tool) { throw "Substantive tool is not classified: $relative" }
  function Test-FixtureInventory([string]$Path) {
    $data = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json -AsHashtable
    if (-not $data.ContainsKey('candidates') -or -not $data.candidates.Count) { return $false }
    foreach ($record in $data.candidates) {
      if (-not ([string]$record.id).StartsWith('test-') -and [string]$record.source_url -notmatch '/test/|example\.' -and ([string]($record.processing_notes -join ' ')) -notmatch '(?i)fixture') { return $false }
    }
    return $true
  }
  # Deterministic regressions with explicitly separate tmp inventory/checkpoint roots
  # have no authority over project records. There is no environment skip flag.
  foreach ($name in @('InventoryPath','MasterPath','CheckpointPath')) {
    if ($Parameters.ContainsKey($name)) {
      $target = [IO.Path]::GetFullPath([string]$Parameters[$name])
      $fixtureRoot = [IO.Path]::GetFullPath("$PSScriptRoot/../../tmp") + [IO.Path]::DirectorySeparatorChar
      $isFixtureLocation = $target.StartsWith($fixtureRoot, [StringComparison]::OrdinalIgnoreCase)
      $systemFixtureRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
      $projectRoot = [IO.Path]::GetFullPath("$PSScriptRoot/../..") + [IO.Path]::DirectorySeparatorChar
      $isFixtureLocation = $isFixtureLocation -or ($target.StartsWith($systemFixtureRoot, [StringComparison]::OrdinalIgnoreCase) -and -not $target.StartsWith($projectRoot, [StringComparison]::OrdinalIgnoreCase))
      if ($isFixtureLocation -and ($tool.operation_class -notin @('document_review','family_review','quality_assessment') -or (Test-FixtureInventory $target))) { return }
    }
  }
  if ($ToolPath.EndsWith('Set-ActiveParallelVerificationCampaign.ps1') -and $Parameters.ContainsKey('ActiveRunPath')) {
    $target = [IO.Path]::GetFullPath([string]$Parameters.ActiveRunPath)
    $temporaryRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if ($target.StartsWith($temporaryRoot,[StringComparison]::OrdinalIgnoreCase)) { return }
  }
  if ($Parameters.ContainsKey('ManifestPath') -and $ToolPath.Contains('ParallelVerification')) {
    $manifestPath = [IO.Path]::GetFullPath([string]$Parameters.ManifestPath)
    $temporaryRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    $projectRoot = [IO.Path]::GetFullPath("$PSScriptRoot/../..") + [IO.Path]::DirectorySeparatorChar
    if ($manifestPath.StartsWith($temporaryRoot,[StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $manifestPath)) {
      $fixtureManifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json -AsHashtable
      if ($fixtureManifest.ContainsKey('inventory_path')) {
        $fixtureInventory = [IO.Path]::GetFullPath([string]$fixtureManifest.inventory_path)
        if ($fixtureInventory.StartsWith($temporaryRoot,[StringComparison]::OrdinalIgnoreCase) -and -not $fixtureInventory.StartsWith($projectRoot,[StringComparison]::OrdinalIgnoreCase) -and (Test-FixtureInventory $fixtureInventory)) { return }
      }
    }
  }
  $repositoryRoot = [IO.Path]::GetFullPath("$PSScriptRoot/../..")
  $relative = [IO.Path]::GetRelativePath($repositoryRoot, [IO.Path]::GetFullPath($ToolPath)).Replace('\','/')
  $manifest = Get-Content -Raw -LiteralPath "$repositoryRoot/project-state/governance/entrypoints.json" | ConvertFrom-Json -AsHashtable
  $tool = $manifest.tools[$relative]
  if (-not $tool) { throw "Substantive tool is not classified: $relative" }
  $arguments = @('active','--phase','review','--operation',[string]$tool.operation_class)
  if ($tool.operation_class -notin @('document_review','family_review','quality_assessment')) { $arguments[2] = 'mutation' }
  foreach ($id in $tool.candidate_ids) { $arguments += @('--candidate',[string]$id) }
  foreach ($page in $tool.pages) { $arguments += @('--page',[string]$page) }
  & python "$PSScriptRoot/Resolve-TaskGovernance.py" @arguments | Out-Null
  if ($LASTEXITCODE) { throw "Task governance gate failed before $relative" }
}
