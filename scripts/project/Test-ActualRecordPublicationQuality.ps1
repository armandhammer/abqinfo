[CmdletBinding()]
param([Parameter(Mandatory)]$Record, $PreviousRecord)
$ErrorActionPreference = 'Stop'
$temporary = Join-Path ([IO.Path]::GetTempPath()) "abqinfo-quality-$([guid]::NewGuid()).json"
$previousTemporary = "$temporary.previous"
try {
  [IO.File]::WriteAllText($temporary, ($Record | ConvertTo-Json -Depth 30), [Text.UTF8Encoding]::new($false))
  if ($PreviousRecord) {
    [IO.File]::WriteAllText($previousTemporary, ($PreviousRecord | ConvertTo-Json -Depth 30), [Text.UTF8Encoding]::new($false))
    & python "$PSScriptRoot/PublicationQuality.py" --record-file $temporary --previous-record-file $previousTemporary
  } else { & python "$PSScriptRoot/PublicationQuality.py" --record-file $temporary }
  if ($LASTEXITCODE) { throw "Actual-record publication-quality gate rejected '$($Record.id)'." }
} finally {
  if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary }
  if (Test-Path -LiteralPath $previousTemporary) { Remove-Item -LiteralPath $previousTemporary }
}
