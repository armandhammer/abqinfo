[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$AccountGuid,
  [Parameter(Mandatory)][string]$FolderId,
  [Parameter(Mandatory)][string]$WidgetId,
  [switch]$ResolveLinks
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$apiRoot = 'https://klvg4oyd4j.execute-api.us-west-2.amazonaws.com/prod'

function ConvertTo-QueryString([hashtable]$Parameters) {
  return ($Parameters.GetEnumerator() | Sort-Object Key | ForEach-Object {
    '{0}={1}' -f [uri]::EscapeDataString([string]$_.Key), [uri]::EscapeDataString([string]$_.Value)
  }) -join '&'
}

$listingParameters = @{
  accountGUID = $AccountGuid
  folderId = $FolderId
  isPublic = '1'
  rootFolderId = $FolderId
  widgetId = $WidgetId
}
$listingUrl = "$apiRoot/GetWidgetFiles?$(ConvertTo-QueryString $listingParameters)"
$response = Invoke-RestMethod -Uri $listingUrl -Method Get
if ($response.status -ne 'ok' -or $response.message) {
  throw "RealFile widget listing failed: $($response.message)"
}

$documents = foreach ($file in @($response.data.files)) {
  $directUrl = $null
  if ($ResolveLinks) {
    $linkParameters = @{
      accountGUID = $AccountGuid
      fileId = $file.fileId
      fileName = $file.name
      widgetId = $WidgetId
    }
    $linkUrl = "$apiRoot/GetWidgetFileLink?$(ConvertTo-QueryString $linkParameters)"
    $linkResponse = Invoke-RestMethod -Uri $linkUrl -Method Get
    if ($linkResponse.status -ne 'ok' -or $linkResponse.message) {
      throw "RealFile link resolution failed for '$($file.name)': $($linkResponse.message)"
    }
    $directUrl = [string]$linkResponse.data
  }

  [pscustomobject]@{
    name = [string]$file.name
    title = if ($file.title) { [string]$file.title } else { [IO.Path]::GetFileNameWithoutExtension([string]$file.name) }
    file_type = [string]$file.type
    file_id = [string]$file.fileId
    uploaded_unix_ms = [int64]$file.uploaded
    uploaded_utc = [DateTimeOffset]::FromUnixTimeMilliseconds([int64]$file.uploaded).UtcDateTime.ToString('o')
    direct_file_url = $directUrl
    account_guid = $AccountGuid
    folder_id = $FolderId
    widget_id = $WidgetId
  }
}

$documents | ConvertTo-Json -Depth 6
