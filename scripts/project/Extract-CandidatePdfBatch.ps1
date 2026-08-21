[CmdletBinding()]
param(
  [Parameter(Mandatory)][string[]]$Ids,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$python = 'C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

$results = foreach ($id in $Ids) {
  $candidate = @($inventory.candidates | Where-Object id -eq $id)
  if ($candidate.Count -ne 1) { throw "Expected one candidate for '$id'; found $($candidate.Count)." }
  $candidate = $candidate[0]
  if (-not $candidate.local_path -or -not (Test-Path -LiteralPath $candidate.local_path)) { throw "Downloaded file missing for '$id'." }
  $parsed = (& $python "$PSScriptRoot/extract_pdf.py" $candidate.local_path) | ConvertFrom-Json
  $textPath = [IO.Path]::ChangeExtension($candidate.local_path,'.txt')
  [IO.File]::WriteAllText([IO.Path]::GetFullPath($textPath), [string]$parsed.text, [Text.UTF8Encoding]::new($false))
  $candidate.status = 'parsed'
  $note = "PDF pages: $($parsed.pages); extracted text: $textPath"
  $candidate.processing_notes = @(@($candidate.processing_notes) + $note | Sort-Object -Unique)
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
  [pscustomobject]@{ id=$id; pages=[int]$parsed.pages; text_path=$textPath; embedded_links=@($parsed.links).Count }
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$json = $inventory | ConvertTo-Json -Depth 12
$fullPath = [IO.Path]::GetFullPath($InventoryPath)
for ($attempt = 1; $attempt -le 60; $attempt++) {
  $temporaryPath = "$fullPath.tmp-$PID-$attempt-$([guid]::NewGuid().ToString('n'))"
  try {
    [IO.File]::WriteAllText($temporaryPath, $json, [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
    $results | ConvertTo-Json -Depth 5
    return
  }
  catch {
    $retryable = $_.Exception -is [System.IO.IOException] -or $_.Exception -is [System.UnauthorizedAccessException] -or $_.Exception.InnerException -is [System.IO.IOException] -or $_.Exception.InnerException -is [System.UnauthorizedAccessException]
    if (Test-Path -LiteralPath $temporaryPath) { Remove-Item -LiteralPath $temporaryPath -Force }
    if (-not $retryable -or $attempt -eq 60) { throw }
    Start-Sleep -Milliseconds 500
  }
}
