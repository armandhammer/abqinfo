[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$path='project-state/discovery/approved-backlog-background-archive-campaign-2026-09-26.json'
$d=Get-Content $path -Raw -Encoding utf8 | ConvertFrom-Json -DateKind String
$done=@(@($d.records)+@($d.generated_packages) | Where-Object outcome -eq 'archive_complete')
$bytes=[int64]($done | Measure-Object size_bytes -Sum).Sum
$originals=@($d.records | Where-Object outcome -eq 'archive_complete').Count
$summary="Background archive campaign: 27 approved originals exact-source prepared; $originals unchanged originals and $($done.Count-$originals) generated packages public-byte verified, $bytes added bytes. Three originals prepared only with unresolved archive namespace. DPM 2018 deferred for conflicting March 21 agenda/missing-minutes evidence. No visitor-visible content changed. Evidence: $path."
$resume=if($d.state -eq 'complete_background_campaign'){'Campaign complete. No ungated background campaign unit remains. Three prepared originals need an owner-approved namespace/IA; DPM 2018 requires human disposition of conflicting agenda evidence. Content implementation and manual-review gates remain deferred; do not start publication.'}else{'Resume bounded campaign phases from saved upload intents and public-byte results. Never repeat complete objects or publish content. Complete remaining packages, final R2 reconciliation, regression/full validation and background integration.'}
& "$PSScriptRoot/Write-ProjectCheckpoint.ps1" -CompletedRange $summary -Blockers @('Three approved originals have unresolved canonical homes and independent archive namespaces.','DPM 2018 includes src-7e7af2af147d96d7, still requires human review; saved research says the March 21 meeting appears not held.','No visitor-visible implementation authorized; future content must pass manual PR review. Unrelated completed/gated families remain untouched.') -ResumeCommand $resume | Out-Null
Write-Output "Campaign checkpoint saved: $($done.Count) verified objects / $bytes bytes."
