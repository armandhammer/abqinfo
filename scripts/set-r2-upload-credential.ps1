[CmdletBinding()]
param(
  [string]$CredentialTarget = 'abqinfo-r2-upload'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not ('AbqInfoCredentialWriter' -as [type])) {
  Add-Type @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;

public static class AbqInfoCredentialWriter
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
    private static extern bool CredWrite(ref Credential credential, UInt32 flags);

    public static void WriteGenericCredential(string target, string userName, string secret)
    {
        IntPtr targetPtr = IntPtr.Zero;
        IntPtr userPtr = IntPtr.Zero;
        IntPtr secretPtr = IntPtr.Zero;
        try
        {
            targetPtr = Marshal.StringToCoTaskMemUni(target);
            userPtr = Marshal.StringToCoTaskMemUni(userName);
            byte[] secretBytes = System.Text.Encoding.Unicode.GetBytes(secret);
            secretPtr = Marshal.AllocCoTaskMem(secretBytes.Length);
            Marshal.Copy(secretBytes, 0, secretPtr, secretBytes.Length);

            Credential credential = new Credential {
                Type = 1,
                TargetName = targetPtr,
                CredentialBlobSize = (UInt32)secretBytes.Length,
                CredentialBlob = secretPtr,
                Persist = 2,
                UserName = userPtr
            };

            if (!CredWrite(ref credential, 0))
            {
                throw new Win32Exception(Marshal.GetLastWin32Error(), "Could not store the Windows credential.");
            }
        }
        finally
        {
            if (targetPtr != IntPtr.Zero) Marshal.FreeCoTaskMem(targetPtr);
            if (userPtr != IntPtr.Zero) Marshal.FreeCoTaskMem(userPtr);
            if (secretPtr != IntPtr.Zero) Marshal.FreeCoTaskMem(secretPtr);
        }
    }
}
'@
}

$accessKey = Read-Host 'R2 Access Key ID'
$secret = Read-Host 'R2 Secret Access Key' -AsSecureString
$secretBstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)

try {
  $secretText = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($secretBstr)
  [AbqInfoCredentialWriter]::WriteGenericCredential($CredentialTarget, $accessKey, $secretText)
}
finally {
  if ($secretBstr -ne [IntPtr]::Zero) {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($secretBstr)
  }
  $secretText = $null
}

Write-Host "Stored R2 upload credential '$CredentialTarget' in Windows Credential Manager."

