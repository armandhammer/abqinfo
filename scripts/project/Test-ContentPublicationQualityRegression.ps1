[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
& python "$PSScriptRoot/Test-PublicationQuality.py"
if ($LASTEXITCODE) { throw 'Publication-quality actual-record regression failed.' }
