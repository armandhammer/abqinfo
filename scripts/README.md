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

# Discovery crawler validation

The general and scoped crawlers share policy helpers in
`scripts/project/Discovery.Common.ps1`. Relevant links from authoritative
government pages are captured before recursive host restrictions are applied.
Recognized publishing platforms such as ArcGIS Hub are recorded with their
referring page and discovery path, but are not recursively crawled unless their
host is explicitly allowed.

Run the deterministic regression test with:

```powershell
.\scripts\project\Test-DiscoveryCrawlerRegression.ps1
```

The test verifies DMD parent traversal, `Project Maps` relevance, ArcGIS host
classification, external document capture, and non-recursive handling of
external candidates. `Invoke-ProjectValidation.ps1` runs this regression
automatically before the Hugo build.

`Get-ArcGisHubCatalog.ps1` resolves an official Hub site's content groups through
the ArcGIS REST API, records no more than the requested catalog limit, and marks
only the requested number of records for detailed metadata/dependency review.
For the bounded DMD batch:

```powershell
.\scripts\project\Get-ArcGisHubCatalog.ps1 -MaxRecords 100 -ReviewLimit 25
.\scripts\project\Import-MasterInventory.ps1
.\scripts\project\Test-ArcGisHubBatch.ps1 -CheckLinks
```

The MRMPO TIP Viewer catalog script captures the active structured project
database without copying transient map geometry into the project inventory. It
records every project with a stable ID, preserves a compact deterministic
snapshot, and distinguishes Albuquerque-scope records from other regional work:

```powershell
.\scripts\project\Get-MrmpoTipViewerCatalog.ps1
.\scripts\project\Import-MasterInventory.ps1
```
