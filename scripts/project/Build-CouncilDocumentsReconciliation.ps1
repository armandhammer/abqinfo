[CmdletBinding()]
param(
  [string]$ResearchPath='project-state/discovery/council-documents-cluster-research-2026-09-11.json',
  [string]$InventoryPath='project-state/master-inventory.json',
  [string]$OutputPath='project-state/discovery/council-documents-cluster-reconciliation-2026-09-20.json'
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$research=Get-Content -Raw -Encoding UTF8 -LiteralPath $ResearchPath|ConvertFrom-Json
$inventory=Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath|ConvertFrom-Json
$byId=@{};foreach($candidate in $inventory.candidates){$byId[$candidate.id]=$candidate}
$sourceRows=@();foreach($bucket in 'approved_for_addition','duplicate','requires_human_review','excluded'){foreach($row in @($research.$bucket)){$sourceRows += [pscustomobject]@{id=$row.id;saved=$bucket}}}
if($sourceRows.Count -ne 107){throw "Expected 107 rows, found $($sourceRows.Count)."}
$records=foreach($source in $sourceRows|Sort-Object id){$current=$byId[$source.id];if(-not $current){throw "Missing inventory record $($source.id)"};$classification=if($source.saved -eq 'approved_for_addition' -and $current.status -eq 'validated'){'approved_and_separately_prepared_or_gated'}elseif($source.saved -eq 'requires_human_review' -and $current.status -eq 'superseded'){'superseded_by_later_family_decision'}elseif($source.saved -eq 'requires_human_review' -and $current.status -eq 'requires human review'){'currently_settled_human_review'}elseif(($source.saved -eq 'excluded' -and $current.status -eq 'excluded') -or ($source.saved -eq 'duplicate' -and $current.status -eq 'duplicate')){'already_terminal_currently_settled'}else{'review_required'};[ordered]@{id=$source.id;saved_recommendation=$source.saved;current_status=$current.status;classification=$classification;updated_at=$current.updated_at;canonical_relationship=$current.exclusion_reason}}
$summary=[ordered]@{};foreach($record in $records){$summary[$record.classification]=1+([int]($summary[$record.classification]??0))}
$artifact=[ordered]@{schema_version=1;artifact_type='council_documents_saved_research_reconciliation';recorded_at='2026-09-20';research_artifact=$ResearchPath;scope='All 107 IDs in the saved Council documents research artifact.';method='Compared each saved ID and recommendation to current authoritative inventory state; no stale saved recommendation overwrote a later decision.';summary=$summary;records=@($records);unresolved_current_ids=@($records|Where-Object classification -eq 'currently_settled_human_review'|ForEach-Object id);safeguards_observed=[ordered]@{r2_mutation=$false;public_content_changed=$false;merge_or_deploy=$false}}
$temp=([IO.Path]::GetFullPath($OutputPath))+'.tmp-'+$PID;try{[IO.File]::WriteAllText($temp,($artifact|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false));Move-Item -LiteralPath $temp -Destination $OutputPath -Force}finally{if(Test-Path $temp){Remove-Item $temp -Force}}
$artifact.summary|ConvertTo-Json
