[CmdletBinding(SupportsShouldProcess)]
param(
  [Parameter(Mandatory)][string]$Key,
  [Parameter(Mandatory)][int64]$ExpectedSize,
  [string]$Bucket = 'abqinfo-bucket',
  [string]$Endpoint = 'https://28e1ba1d2f40f5046283843b8a748256.r2.cloudflarestorage.com',
  [string]$CredentialTarget = 'abqinfo-r2-upload'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($Key) -or $Key.StartsWith('/') -or $Key.EndsWith('/')) {
  throw 'Key must identify one exact R2 object, not a prefix.'
}

if (-not ('AbqInfoCredentialManager' -as [type])) {
  Add-Type @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
public static class AbqInfoCredentialManager {
  [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
  private struct Credential { public UInt32 Flags; public UInt32 Type; public IntPtr TargetName; public IntPtr Comment; public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten; public UInt32 CredentialBlobSize; public IntPtr CredentialBlob; public UInt32 Persist; public UInt32 AttributeCount; public IntPtr Attributes; public IntPtr TargetAlias; public IntPtr UserName; }
  [DllImport("Advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)] private static extern bool CredRead(string target, UInt32 type, UInt32 flags, out IntPtr credentialPtr);
  [DllImport("Advapi32.dll", SetLastError = true)] private static extern void CredFree(IntPtr credentialPtr);
  public static string[] ReadGenericCredential(string target) {
    IntPtr pointer; if (!CredRead(target, 1, 0, out pointer)) throw new Win32Exception(Marshal.GetLastWin32Error(), "Could not read Windows credential: " + target);
    try { Credential credential=(Credential)Marshal.PtrToStructure(pointer, typeof(Credential)); return new[]{Marshal.PtrToStringUni(credential.UserName), credential.CredentialBlobSize==0 ? String.Empty : Marshal.PtrToStringUni(credential.CredentialBlob,(int)credential.CredentialBlobSize/2)}; }
    finally { CredFree(pointer); }
  }
}
'@
}

$credential = [AbqInfoCredentialManager]::ReadGenericCredential($CredentialTarget)
$aws = Get-Command aws -ErrorAction Stop
$names = @('AWS_ACCESS_KEY_ID','AWS_SECRET_ACCESS_KEY','AWS_DEFAULT_REGION','AWS_EC2_METADATA_DISABLED')
$prior = @{}
foreach ($name in $names) { $prior[$name] = [Environment]::GetEnvironmentVariable($name,'Process') }
try {
  [Environment]::SetEnvironmentVariable('AWS_ACCESS_KEY_ID',$credential[0],'Process')
  [Environment]::SetEnvironmentVariable('AWS_SECRET_ACCESS_KEY',$credential[1],'Process')
  [Environment]::SetEnvironmentVariable('AWS_DEFAULT_REGION','auto','Process')
  [Environment]::SetEnvironmentVariable('AWS_EC2_METADATA_DISABLED','true','Process')
  $headRaw = & $aws.Source s3api head-object --bucket $Bucket --key $Key --endpoint-url $Endpoint --output json
  if ($LASTEXITCODE) { throw "R2 object '$Key' was not found." }
  $head = $headRaw | ConvertFrom-Json
  if ([int64]$head.ContentLength -ne $ExpectedSize) {
    throw "R2 object '$Key' is $($head.ContentLength) bytes, not the expected $ExpectedSize bytes; refusing deletion."
  }
  if ($PSCmdlet.ShouldProcess("s3://$Bucket/$Key", "Delete exact R2 object ($ExpectedSize bytes)")) {
    & $aws.Source s3api delete-object --bucket $Bucket --key $Key --endpoint-url $Endpoint --output json | Out-Null
    if ($LASTEXITCODE) { throw "R2 deletion failed for '$Key'." }
    [pscustomobject]@{ bucket=$Bucket; key=$Key; deleted=$true; size_bytes=$ExpectedSize } | ConvertTo-Json -Compress
  }
} finally {
  foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name,$prior[$name],'Process') }
}
