[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$SourcePath,
  [Parameter(Mandatory)][uri]$PublicUrl
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) {
  throw "Source file not found: $SourcePath"
}

$source = Get-Item -LiteralPath $SourcePath
$sourceHash = (Get-FileHash -LiteralPath $source.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
$temporaryPath = Join-Path ([IO.Path]::GetTempPath()) ("abqinfo-r2-" + [guid]::NewGuid().ToString('n') + [IO.Path]::GetExtension($source.Name))

try {
  Invoke-WebRequest -Uri $PublicUrl -OutFile $temporaryPath -UseBasicParsing -MaximumRedirection 10 -TimeoutSec 180
  $download = Get-Item -LiteralPath $temporaryPath
  $downloadHash = (Get-FileHash -LiteralPath $download.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($download.Length -ne $source.Length) {
    throw "Public object size mismatch: source $($source.Length) bytes; public download $($download.Length) bytes."
  }
  if ($downloadHash -ne $sourceHash) {
    throw "Public object checksum mismatch: source $sourceHash; public download $downloadHash."
  }

  [pscustomobject]@{
    public_url = $PublicUrl.AbsoluteUri
    size_bytes = [int64]$download.Length
    checksum_sha256 = $downloadHash
    byte_identical = $true
    verified_at = (Get-Date).ToUniversalTime().ToString('o')
  }
}
finally {
  if (Test-Path -LiteralPath $temporaryPath) {
    Remove-Item -LiteralPath $temporaryPath -Force
  }
}
