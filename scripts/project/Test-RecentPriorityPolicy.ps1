[CmdletBinding()]
param([string]$QueuePath = 'project-state/discovery/pending-review-priority.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$queue = Get-Content -Raw -Encoding UTF8 -LiteralPath $QueuePath | ConvertFrom-Json
$errors = [Collections.Generic.List[string]]::new()
$top = @($queue.queue | Select-Object -First 100)
if (-not $top.Count) { $errors.Add('Priority queue is empty.') }

$recentSubstantive = @($top | Where-Object {
  [int]$_.detected_year -ge 2023 -and
  $_.title -notmatch '(?i)agenda|minutes|meeting amendment|floor substitute|construction notice|closure notice|flyer|door hanger|job aid|checklist'
})
$routineEphemeral = @($top | Where-Object {
  $_.title -match '(?i)agenda|minutes|meeting amendment|floor substitute|construction notice|closure notice|flyer|door hanger|job aid|checklist'
})
if ($recentSubstantive.Count -lt 20) { $errors.Add("Only $($recentSubstantive.Count) recent substantive records appear in the top 100.") }
if ($routineEphemeral.Count -gt 15) { $errors.Add("$($routineEphemeral.Count) routine or ephemeral records appear in the top 100.") }

$result = [ordered]@{
  queue_items = @($queue.queue).Count
  top_sample = $top.Count
  recent_substantive_in_top_100 = $recentSubstantive.Count
  routine_ephemeral_in_top_100 = $routineEphemeral.Count
  errors = @($errors)
}
$result | ConvertTo-Json -Depth 5
if ($errors.Count) { exit 1 }
