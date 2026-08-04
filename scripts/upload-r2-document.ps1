[CmdletBinding(SupportsShouldProcess)]
param(
  [Parameter(Mandatory)]
  [ValidateNotNullOrEmpty()]
  [string]$SourcePath,

  [Parameter(Mandatory)]
  [ValidateNotNullOrEmpty()]
  [string]$ObjectKey,

  [string]$Bucket = 'abqinfo-bucket',

  [string]$Endpoint = 'https://28e1ba1d2f40f5046283843b8a748256.r2.cloudflarestorage.com',

  [string]$CredentialTarget = 'abqinfo-r2-upload',

  [ValidateRange(1, [Int64]::MaxValue)]
  [Int64]$MaxObjectBytes = 100000000,

  [ValidateRange(1, [Int64]::MaxValue)]
  [Int64]$MaxProjectedStorageBytes = 8000000000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) {
  throw "Source file not found: $SourcePath"
}

if ($ObjectKey.StartsWith('/') -or $ObjectKey.Contains('..')) {
  throw 'ObjectKey must be a relative R2 path and must not contain "..".'
}

if (-not ('AbqInfoCredentialManager' -as [type])) {
  Add-Type @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;

public static class AbqInfoCredentialManager
{
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct Credential
    {
        public UInt32 Flags;
        public UInt32 Type;
        public IntPtr TargetName;
        public IntPtr Comment;
        public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
        public UInt32 CredentialBlobSize;
        public IntPtr CredentialBlob;
        public UInt32 Persist;
        public UInt32 AttributeCount;
        public IntPtr Attributes;
        public IntPtr TargetAlias;
        public IntPtr UserName;
    }

    [DllImport("Advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CredRead(string target, UInt32 type, UInt32 flags, out IntPtr credentialPtr);

    [DllImport("Advapi32.dll", SetLastError = true)]
    private static extern void CredFree(IntPtr credentialPtr);

    public static string[] ReadGenericCredential(string target)
    {
        IntPtr credentialPtr;
        if (!CredRead(target, 1, 0, out credentialPtr))
        {
            throw new Win32Exception(Marshal.GetLastWin32Error(), "Could not read Windows credential: " + target);
        }

        try
        {
            Credential credential = (Credential)Marshal.PtrToStructure(credentialPtr, typeof(Credential));
            string userName = Marshal.PtrToStringUni(credential.UserName);
            string secret = credential.CredentialBlobSize == 0
                ? String.Empty
                : Marshal.PtrToStringUni(credential.CredentialBlob, (int)credential.CredentialBlobSize / 2);
            return new[] { userName, secret };
        }
        finally
        {
            CredFree(credentialPtr);
        }
    }
}
'@
}

$credential = [AbqInfoCredentialManager]::ReadGenericCredential($CredentialTarget)
if ([string]::IsNullOrWhiteSpace($credential[0]) -or [string]::IsNullOrWhiteSpace($credential[1])) {
  throw "Windows credential '$CredentialTarget' must contain an R2 Access Key ID as its username and a Secret Access Key as its password."
}

$aws = Get-Command aws -ErrorAction Stop
$source = Get-Item -LiteralPath $SourcePath
if ($source.Length -gt $MaxObjectBytes) {
  throw "Refusing to upload '$($source.Name)': $($source.Length) bytes exceeds the $MaxObjectBytes-byte limit. Explicit owner approval is required before changing this limit."
}

$contentTypes = @{
  '.csv'  = 'text/csv'
  '.docx' = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  '.json' = 'application/json'
  '.pdf'  = 'application/pdf'
  '.txt'  = 'text/plain'
  '.xlsx' = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  '.zip'  = 'application/zip'
}
$extension = [IO.Path]::GetExtension($source.Name).ToLowerInvariant()
$contentType = if ($contentTypes.ContainsKey($extension)) { $contentTypes[$extension] } else { 'application/octet-stream' }
$hash = (Get-FileHash -LiteralPath $source.FullName -Algorithm SHA256).Hash.ToLowerInvariant()

$previousEnvironment = @{}
foreach ($name in 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION', 'AWS_EC2_METADATA_DISABLED') {
  $previousEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}

try {
  [Environment]::SetEnvironmentVariable('AWS_ACCESS_KEY_ID', $credential[0], 'Process')
  [Environment]::SetEnvironmentVariable('AWS_SECRET_ACCESS_KEY', $credential[1], 'Process')
  [Environment]::SetEnvironmentVariable('AWS_DEFAULT_REGION', 'auto', 'Process')
  [Environment]::SetEnvironmentVariable('AWS_EC2_METADATA_DISABLED', 'true', 'Process')

  $currentStorageRaw = & $aws.Source s3api list-objects-v2 --bucket $Bucket --endpoint-url $Endpoint --query 'sum(Contents[].Size)' --output text
  if ($LASTEXITCODE -ne 0) {
    throw "Could not determine current R2 storage for '$Bucket'. Upload cancelled."
  }
  $currentStorageBytes = if ($currentStorageRaw -eq 'None' -or [string]::IsNullOrWhiteSpace($currentStorageRaw)) { [Int64]0 } else { [Int64]$currentStorageRaw }
  $projectedStorageBytes = $currentStorageBytes + $source.Length
  if ($projectedStorageBytes -gt $MaxProjectedStorageBytes) {
    throw "Refusing to upload '$($source.Name)': projected R2 Standard storage ($projectedStorageBytes bytes) exceeds the $MaxProjectedStorageBytes-byte safety limit."
  }

  $headOutput = & $aws.Source s3api head-object --bucket $Bucket --key $ObjectKey --endpoint-url $Endpoint 2>&1
  if ($LASTEXITCODE -eq 0) {
    throw "Refusing to overwrite existing R2 object: $ObjectKey"
  }
  if (($headOutput | Out-String) -notmatch '(404|Not Found|NoSuchKey)') {
    throw "Could not confirm that R2 object '$ObjectKey' is absent. Upload cancelled. $($headOutput | Out-String)"
  }

  if (-not $PSCmdlet.ShouldProcess("s3://$Bucket/$ObjectKey", "Upload $($source.Name)")) {
    [PSCustomObject]@{
      SourcePath = $source.FullName
      ObjectKey = $ObjectKey
      Bytes = $source.Length
      CurrentR2Bytes = $currentStorageBytes
      ProjectedR2Bytes = $projectedStorageBytes
      Result = 'WhatIf: upload not performed'
    }
    return
  }

  & $aws.Source s3 cp $source.FullName "s3://$Bucket/$ObjectKey" --endpoint-url $Endpoint --content-type $contentType --no-progress
  if ($LASTEXITCODE -ne 0) {
    throw "R2 upload failed for '$ObjectKey'."
  }

  $metadata = & $aws.Source s3api head-object --bucket $Bucket --key $ObjectKey --endpoint-url $Endpoint
  if ($LASTEXITCODE -ne 0) {
    throw "R2 upload could not be verified for '$ObjectKey'."
  }

  [PSCustomObject]@{
    SourcePath = $source.FullName
    ObjectKey = $ObjectKey
    PublicUrl = "https://files.abqinfo.com/$ObjectKey"
    Bytes = $source.Length
    CurrentR2Bytes = $currentStorageBytes
    ProjectedR2Bytes = $projectedStorageBytes
    ContentType = $contentType
    SHA256 = $hash
    R2Metadata = $metadata
  }
}
finally {
  foreach ($name in $previousEnvironment.Keys) {
    [Environment]::SetEnvironmentVariable($name, $previousEnvironment[$name], 'Process')
  }
}

