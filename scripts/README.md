# Local R2 uploads

`upload-r2-document.ps1` uploads a local file to the ABQ Info R2 bucket without
writing credentials to the repository or to persistent environment variables.

It reads one Windows generic credential named `abqinfo-r2-upload`:

- **User name:** R2 Access Key ID
- **Password:** R2 Secret Access Key

The credential must be limited to `Object Read & Write` on `abqinfo-bucket`.
The script refuses to overwrite an existing object, calculates SHA-256, verifies
the uploaded object, and prints its public URL.

To store or replace the credential securely, run:

```powershell
.\scripts\set-r2-upload-credential.ps1
```

The script prompts for the Access Key ID and masks the Secret Access Key. Neither
value is added to PowerShell history, an environment variable, or a repository file.

Example:

```powershell
.\scripts\upload-r2-document.ps1 `
  -SourcePath 'C:\records\example.pdf' `
  -ObjectKey 'documents\transportation\example.pdf'
```

