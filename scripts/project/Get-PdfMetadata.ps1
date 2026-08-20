[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$Id,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Read-InventoryWithRetry([string]$Path) {
  for ($attempt = 1; $attempt -le 8; $attempt++) {
    try { return Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json }
    catch [System.IO.IOException] {
      if ($attempt -eq 8) { throw }
      Start-Sleep -Milliseconds (50 * $attempt)
    }
  }
}

function Write-InventoryWithRetry($Value, [string]$Path) {
  $json = $Value | ConvertTo-Json -Depth 12
  for ($attempt = 1; $attempt -le 8; $attempt++) {
    $fullPath = [IO.Path]::GetFullPath($Path)
    $temporaryPath = "$fullPath.tmp-$PID-$attempt"
    try {
      [IO.File]::WriteAllText($temporaryPath, $json, [Text.UTF8Encoding]::new($false))
      [IO.File]::Move($temporaryPath, $fullPath, $true)
      return
    }
    catch [System.IO.IOException] {
      if (Test-Path -LiteralPath $temporaryPath) { Remove-Item -LiteralPath $temporaryPath -Force }
      if ($attempt -eq 8) { throw }
      Start-Sleep -Milliseconds (50 * $attempt)
    }
  }
}

function Add-ProcessingNote($Candidate, [string]$Note) {
  $existing = @($Candidate.processing_notes) | ForEach-Object { ([string]$_).Trim() } | Where-Object { $_ }
  $Candidate.processing_notes = @(@($existing) + $Note | Sort-Object -Unique)
}

$inventory = Read-InventoryWithRetry $InventoryPath
$candidate = @($inventory.candidates | Where-Object id -eq $Id)
if ($candidate.Count -ne 1) { throw "Expected one candidate for '$Id'; found $($candidate.Count)." }
$candidate = $candidate[0]
if (-not $candidate.local_path -or -not (Test-Path -LiteralPath $candidate.local_path)) { throw "Downloaded file missing for '$Id'." }
$python = 'C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$parsed = (& $python "$PSScriptRoot/extract_pdf.py" $candidate.local_path) | ConvertFrom-Json
$textPath = [IO.Path]::ChangeExtension($candidate.local_path,'.txt')
$parsed.text | Set-Content -LiteralPath $textPath -Encoding utf8
$candidate.status = 'parsed'
$candidate.file_type = 'PDF'
Add-ProcessingNote $candidate "PDF pages: $($parsed.pages); extracted text: $textPath"
$candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$nextCandidates = @($inventory.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') } | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($nextCandidates.Count) { $nextCandidates[0].id } else { $null }
Write-InventoryWithRetry $inventory $InventoryPath
[pscustomobject]@{Id=$Id;Pages=$parsed.pages;TextPath=$textPath;Metadata=$parsed.metadata} | ConvertTo-Json -Depth 5
