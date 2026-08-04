[CmdletBinding()]
param(
  [string]$Bucket = 'abqinfo-bucket',
  [string]$Endpoint = 'https://28e1ba1d2f40f5046283843b8a748256.r2.cloudflarestorage.com',
  [string]$CredentialTarget = 'abqinfo-r2-upload',
  [string]$OutputPath = 'project-state/r2-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
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
  $raw = & $aws.Source s3api list-objects-v2 --bucket $Bucket --endpoint-url $Endpoint --output json
  if ($LASTEXITCODE) { throw 'R2 object listing failed.' }
  $response = $raw | ConvertFrom-Json
  $objects = @($response.Contents | ForEach-Object {
    [ordered]@{key=$_.Key;size_bytes=[int64]$_.Size;last_modified=$_.LastModified;etag=([string]$_.ETag).Trim('"');storage_class=$_.StorageClass;public_url='https://files.abqinfo.com/'+$_.Key}
  } | Sort-Object key)
  [int64]$total = 0
  foreach ($object in $objects) { $total += [int64]$object['size_bytes'] }
  [ordered]@{generated_at=(Get-Date).ToUniversalTime().ToString('o');bucket=$Bucket;object_count=$objects.Count;total_bytes=[int64]$total;objects=$objects} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputPath -Encoding utf8
  [pscustomobject]@{Bucket=$Bucket;Objects=$objects.Count;TotalBytes=[int64]$total;OutputPath=$OutputPath}|ConvertTo-Json -Compress
} finally {
  foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name,$prior[$name],'Process') }
}
