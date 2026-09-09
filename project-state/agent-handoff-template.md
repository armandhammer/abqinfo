# ABQInfo agent handoff template

Copy this template into the next provider's first prompt and replace every bracketed value. Do not include credentials, tokens, passwords, private keys, or personally sensitive data.

```text
ABQInfo handoff

Provider departing: [Codex / Claude / other]
Provider receiving: [Codex / Claude / other]
Repository: https://github.com/armandhammer/abqinfo
Branch: [branch name]
Commit: [full or short SHA]
PR: [URL, state, and mergeability; or "none"]
Base verified: [origin/main SHA and fetch time]

Task scope: [one-sentence description]
Completed: [records, pages, R2 objects, and decisions completed]
Next candidate or batch: [inventory ID / exact next action]
Checkpoint: [recorded_at timestamp and resume_command]

Validation completed:
- Source checks: [result]
- Hash/R2 checks: [result, exact object count and bytes if applicable]
- Hugo/build checks: [result]
- Placement/link checks: [result]
- Git diff check: [result]

Unresolved decisions or blockers:
- [none, or explicit record IDs and reason]

Open PR gate:
- Open PRs targeting main reviewed: [numbers/titles or none]
- Required action before new PR: [wait / integrate PR # / none]

Working-tree protection:
- Unrelated modified files: [paths or none]
- Unrelated untracked files/directories: [paths or none]
- Do not stage, delete, reset, or overwrite them.

Receiver instructions:
1. Read AGENTS.md, project-state/AGENT-HANDOFF.md, checkpoint.json, master-inventory.json, and project-state/README.md.
2. Run git fetch origin, git status --short --branch, and gh pr list --base main --state open.
3. Verify this handoff against repository state before acting; the chat summary is not authoritative.
4. Continue only the stated scope or ask the user before expanding it.
5. Do not merge, deploy, publish externally, or change credentials without explicit user approval.
```
