[CmdletBinding()]
param([string]$CheckpointPath='project-state/checkpoint.json',[string]$InventoryPath='project-state/master-inventory.json')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$checkpoint=Get-Content -Raw -Encoding UTF8 -LiteralPath $CheckpointPath|ConvertFrom-Json
$inventory=Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath|ConvertFrom-Json
$checkpoint.recorded_at=(Get-Date).ToUniversalTime().ToString('o')
$checkpoint.completed_item_range='Council closeout: agendas, Council 107 reconciliation, public-body matrix, enactment capture, and bounded unresolved-legislation review'
$checkpoint.total_candidates=@($inventory.candidates).Count
$checkpoint.counts_by_status=$inventory.counts
$checkpoint.remaining_nonterminal=@($inventory.candidates|Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') }).Count
$checkpoint.next_pending_id=$inventory.next_pending_id
$o2024006Blocker='O-2024-006 final enacted file is not downloadable from the authoritative Clerk notice; do not register the available draft.'
$retainedBlockers=@($checkpoint.blockers | Where-Object { $_ -notmatch 'Seven newly identified enacted Council counterparts' })
if ($retainedBlockers -notcontains $o2024006Blocker) { $retainedBlockers += $o2024006Blocker }
$deduplicated=[Collections.Generic.List[string]]::new()
foreach ($blocker in $retainedBlockers) { if ($blocker -and -not $deduplicated.Contains([string]$blocker)) { $deduplicated.Add([string]$blocker) } }
$checkpoint.blockers=@($deduplicated)
$checkpoint.resume_command='Council closeout and the 26-record Municipal Development agenda/minutes family are complete. Skip all listed gates and completed families; recompute the filtered ordinary queue before the next coherent-family review.'
$temporaryPath=([IO.Path]::GetFullPath($CheckpointPath))+'.tmp-'+$PID
try{[IO.File]::WriteAllText($temporaryPath,($checkpoint|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false));Move-Item -LiteralPath $temporaryPath -Destination $CheckpointPath -Force}finally{if(Test-Path $temporaryPath){Remove-Item $temporaryPath -Force}}
$checkpoint|Select-Object total_candidates,counts_by_status,remaining_nonterminal,next_pending_id,resume_command|ConvertTo-Json -Depth 5
