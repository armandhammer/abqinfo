[CmdletBinding()]
param([string]$CheckpointPath='project-state/checkpoint.json',[string]$InventoryPath='project-state/master-inventory.json')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$checkpoint=Get-Content -Raw -Encoding UTF8 -LiteralPath $CheckpointPath|ConvertFrom-Json
$inventory=Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath|ConvertFrom-Json
$checkpoint.recorded_at=(Get-Date).ToUniversalTime().ToString('o')
$checkpoint.completed_item_range='Council closeout checkpoint: meeting agenda family, Council 107 reconciliation, and six final enacted counterparts'
$checkpoint.total_candidates=@($inventory.candidates).Count
$checkpoint.counts_by_status=$inventory.counts
$checkpoint.remaining_nonterminal=@($inventory.candidates|Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') }).Count
$checkpoint.next_pending_id=$inventory.next_pending_id
$checkpoint.blockers=@($checkpoint.blockers|Where-Object {$_ -notmatch 'Seven newly identified enacted Council counterparts'}) + @('O-2024-006 final enacted file is not downloadable from the authoritative Clerk notice; do not register the available draft.')
$checkpoint.resume_command='Complete the bounded missing-minutes/public-body matrix, then deepen final-disposition research for O-23-96 and F/S R-24-17. Six counterpart final files are already inventory-only registered; O-2024-006 remains a source-access blocker. Do not begin another ordinary family before those scoped Council stages are complete.'
$temporaryPath=([IO.Path]::GetFullPath($CheckpointPath))+'.tmp-'+$PID
try{[IO.File]::WriteAllText($temporaryPath,($checkpoint|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false));Move-Item -LiteralPath $temporaryPath -Destination $CheckpointPath -Force}finally{if(Test-Path $temporaryPath){Remove-Item $temporaryPath -Force}}
$checkpoint|Select-Object total_candidates,counts_by_status,remaining_nonterminal,next_pending_id,resume_command|ConvertTo-Json -Depth 5
