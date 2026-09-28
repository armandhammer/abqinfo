"""Regression for PR #198's background-only continuity import."""

from Pr198ContinuityPrMergeLifecycle import guard_current_delta

guard_current_delta()
print('PASS: PR198 continuity import preserves reviewed content, inventory, R2 and manual review gate.')
