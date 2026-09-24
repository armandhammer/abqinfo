[CmdletBinding()]
param([string]$CheckpointPath = 'project-state/checkpoint.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$prior = Get-Content -Raw -Encoding UTF8 -LiteralPath $CheckpointPath | ConvertFrom-Json -DateKind String
$blockers = @($prior.blockers | ForEach-Object {
  if ([string]$_ -like 'Planned Growth Strategy Hugo implementation is complete*' -or [string]$_ -like 'Planned Growth Strategy PR #168 is open*') {
    'Planned Growth Strategy PR #168 is open for manual review. The direct non-production Citywide Growth Strategy preview is verified; the user must approve before merge or deployment. The 13 records remain implemented, not validated.'
  } else { [string]$_ }
})
if (@($blockers | Where-Object { $_ -like 'Planned Growth Strategy PR #168 is open*' }).Count -ne 1) { throw 'Expected one current PGS checkpoint blocker.' }
& "$PSScriptRoot/Write-ProjectCheckpoint.ps1" -OutputPath $CheckpointPath -CompletedRange 'Opened Planned Growth Strategy PR #168 for manual review after branch implementation and full validation. Verified the non-production Area & Sector Plans Citywide Growth Strategy preview with the complete Part 1 original, 12 separate Part 2 City PDFs, and all 13 archive/official-source link pairs. No merge, production deployment, or status validation.' -Blockers $blockers -ResumeCommand 'Planned Growth Strategy PR #168 is open at https://github.com/armandhammer/abqinfo/pull/168 for the manual user review. Do not merge or deploy without the user approval. The 13 PGS records remain implemented on the branch; preserve the separate Part 2 chapter series and no-verified-combined-original caveat. The three enactment bills remain outside this task. Validation regression anchor: src-09b266eabc8aa975 remains named only to preserve the bounded fiber-rulemaking decision test; it is not an instruction to begin that work.' | Out-Null
