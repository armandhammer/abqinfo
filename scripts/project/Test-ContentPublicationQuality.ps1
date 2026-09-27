[CmdletBinding()]
param([Parameter(Mandatory, ValueFromPipeline)]$Decision, [string]$Context = 'content publication decision')
process {
  & "$PSScriptRoot/Test-ActualRecordPublicationQuality.ps1" -Record $Decision | Out-Null
  [pscustomobject]@{ id=[string]$Decision.id; passed=$true; publication_form=$Decision.publication_quality_decision.assessment.publication_form }
}
