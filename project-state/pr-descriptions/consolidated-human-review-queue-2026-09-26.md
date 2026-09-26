## Summary

Build a consolidated owner decision queue from all 205 current inventory records requiring human review, grouped into 46 packages. The Markdown review aid and JSON queue include decision questions, affected IDs/titles, saved evidence, source/archive links, automation gates, and options with consequences. Related final parts, enactment instruments, draft families and recovery-policy decisions stay together.

Add deterministic regeneration and freshness/coverage checking to project validation, and point CURRENT.md to the queue. Saved links are explicitly distinguished from live verification. The separate mission-scope-borderline queue remains unchanged.

## Visible site changes

None.

## Validation

- Full Invoke-ProjectValidation.ps1 passed, including inventory, mission-scope, campaign regressions, Hugo and rendered-page checks.
- Queue regeneration/check passed: every current human-review ID appears exactly once, with tracked evidence references.
- Git diff checks passed; inventory dispositions, checkpoint, R2 metadata and content are unchanged. No R2 operations or added storage.

The queue proposes decisions only; it grants no disposition, archive or publication authority.
