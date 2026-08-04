# ABQ Info project state

`master-inventory.json` is the authoritative resumable state for the full-site expansion. Do not process a discovered source outside this inventory.

Run from the repository root:

```powershell
./scripts/project/Import-MasterInventory.ps1
./scripts/project/Get-R2Inventory.ps1
./scripts/project/Test-MasterInventory.ps1
./scripts/project/Find-InventoryDuplicates.ps1
./scripts/project/Invoke-ProjectValidation.ps1
```

Use `Import-MasterInventory.ps1 -Rebuild` only when deliberately reconstructing state from repository content, legacy audit files, staged downloads, and curated overrides. Normal candidate transitions must use `Update-Candidate.ps1` so completed work is preserved.

Resume work from the `next_pending_id` recorded at the top of `master-inventory.json`. Update a candidate immediately after every completed state transition. Terminal statuses are `validated`, `excluded`, `duplicate`, `superseded`, `blocked`, and `requires human review`.
