[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$Id,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw $InventoryPath | ConvertFrom-Json
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
$candidate.processing_notes += "PDF pages: $($parsed.pages); extracted text: $textPath"
$candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
$inventory | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $InventoryPath -Encoding utf8
[pscustomobject]@{Id=$Id;Pages=$parsed.pages;TextPath=$textPath;Metadata=$parsed.metadata} | ConvertTo-Json -Depth 5
