[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$manifest=Get-Content project-state/discovery/planning-documents-root-r2-upload-preflight-2026-09-26.json -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.state -ne 'upload-ready only after explicit R2 authorization' -or $manifest.records.Count -ne 12 -or $manifest.aggregate_staged_bytes -ne 122249326 -or $manifest.aggregate_pages -ne 928 -or $manifest.r2_mutation) { throw 'Preflight is not complete.' }
& "$PSScriptRoot/Write-ProjectCheckpoint.ps1" -CompletedRange 'Planning documents-root: 13 authoritative source deliveries prepared and QA verified; Barelas delivery src-d9bf34830a9467e2 reconciled as exact duplicate of validated canonical src-28418cab91a745a6. Twelve unique originals / 122,249,326 bytes / 928 pages passed final no-mutation R2 preflight and default-limit WhatIf probes. Inventory counts regenerated: 39 approved / 1,518 duplicates. R2 unchanged at 1,237 objects / 9,218,281,842 bytes; visitor-visible content unchanged.' -Blockers @(
  'Explicit authorization required before exactly 12 unchanged Planning R2 uploads and exact public-byte verification; no current upload authorization.',
  'Later visitor-visible Hugo implementation requires a separate manual-review content PR; preserve the incomplete four-component Planning Impact Area treatment.',
  'Completed later-MS4, PGS, ABQ RIDE and Municipal Development families remain complete; other separately gated families remain outside this batch.'
) -ResumeCommand 'The exact Barelas duplicate is reconciled; do not upload or publish that delivery again. The final 12-object no-mutation manifest is project-state/discovery/planning-documents-root-r2-upload-preflight-2026-09-26.json: 122,249,326 bytes / 928 pages, normal uploader limits, projected 1,249 objects / 9,340,531,168 bytes. Next gate is explicit authorization for these 12 unchanged Planning R2 uploads and exact public-byte verification. Do not repeat source preparation, disposition review, or completed later-MS4 work; later content remains separately manual-review gated.' | Out-Null
Write-Output 'Planning preflight checkpoint saved with regenerated inventory counts.'
