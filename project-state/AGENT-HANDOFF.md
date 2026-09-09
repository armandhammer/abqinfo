# ABQInfo multi-provider agent handoff protocol

This protocol lets Codex, Claude, or another approved coding agent continue ABQInfo work without losing provenance, validation evidence, or Git history. It is intentionally provider-neutral: the repository and GitHub are the shared source of truth, not a chat transcript.

## Non-negotiable rules

1. Only one agent may make content, inventory, or project-state changes in a checkout at a time.
2. Work only from a fresh `origin/main` base on a dedicated branch. Do not continue an old branch after another PR has merged without first integrating current `origin/main`.
3. Before creating a PR, list all open PRs targeting `main`. If another open PR overlaps the planned pages, inventory, scripts, or project state, stop and ask the user whether to wait for it to merge or to integrate it first.
4. Preserve unrelated modified and untracked files. Never stage, commit, reset, checkout, delete, or move them merely to obtain a clean working tree.
5. `project-state/master-inventory.json` and `project-state/checkpoint.json` are durable handoff records. Update candidates promptly through `scripts/project/Update-Candidate.ps1`; do not hand-edit status changes or rebuild the inventory unless the task specifically requires it.
6. Do not merge a PR, deploy the site, overwrite an R2 object, expose credentials, or change access controls without the user's explicit authorization.

## GitHub access for Claude or another external agent

Claude needs a shell-enabled coding environment with filesystem access to the clone (for example, Claude Code or another approved local-agent host). A browser-only chat cannot independently clone, edit, commit, or push this repository. The user must grant the GitHub account that Claude will use at least **write** access to `armandhammer/abqinfo` (or an organization/team role with equivalent repository access). Access must be granted through GitHub's normal invitation, team, or organization controls; no token, password, SSH private key, or credential file belongs in this repository or a prompt.

On Windows, install Git and the GitHub CLI (`gh`) on the machine where Claude will work if they are not already installed:

```powershell
winget install --id Git.Git --exact
winget install --id GitHub.cli --exact
```

Authenticate interactively as the authorized GitHub account and configure Git to use that credential:

```powershell
gh auth login
# Select GitHub.com, HTTPS, then browser or device-code authentication.
gh auth status
gh auth setup-git
```

Set the author identity once if it is not already configured:

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

Clone the repository if needed, then enter it:

```powershell
git clone https://github.com/armandhammer/abqinfo.git
Set-Location abqinfo
git remote -v
```

For every new assignment, update the remote state and check access before making changes:

```powershell
git fetch origin
git status --short --branch
gh repo view armandhammer/abqinfo
gh pr list --base main --state open
```

If `gh auth status`, `gh repo view`, or `git push` fails, stop and ask the user to grant or repair access. Do not work around the failure with someone else's token or by storing secrets in files, environment variables, issue comments, or chat.

R2 uploads require the separately managed Windows credential described in `scripts/README.md`. An agent must not create, export, transmit, or commit that credential. If it is unavailable, complete the non-upload work and report the blocked archival step.

## Start-of-turn checklist

Run these checks before researching or modifying content:

```powershell
git fetch origin
git status --short --branch
Get-Content project-state/checkpoint.json -Raw
Get-Content project-state/master-inventory.json -Raw
if (Test-Path project-state/active-run.json) { Get-Content project-state/active-run.json -Raw }
gh pr list --base main --state open
```

Read `AGENTS.md` and `project-state/README.md`. Treat their repository policies as binding regardless of the agent provider.

When no blocking PR exists, create a new branch from `origin/main`:

```powershell
git switch -c provider/short-batch-name origin/main
```

Use a provider-prefixed branch name such as `codex/...` or `claude/...`. Never commit directly to `main`.

## Working rules

- Begin from `master-inventory.json`'s `next_pending_id` unless the user scopes a different record or batch.
- Prefer existing deterministic scripts for crawling, download, hashing, extraction, deduplication, R2 plans/uploads, inventory updates, link checks, and Hugo validation.
- Record source URLs, dates, byte sizes, SHA-256 hashes, provenance, duplicate/supersession decisions, placements, and validation evidence in the inventory and batch artifacts.
- Treat Legistar attachments as wrappers until their substantive content is compared with City-source copies.
- Do not claim an agenda is minutes. Apply the repository's missing-minutes policy.
- Save meaningful progress immediately. If nearing a provider limit, stop after a completed, durable state transition rather than beginning an uncheckpointed download, upload, bulk edit, or conflict resolution.
- Keep a normal content PR to a coherent 15–30 visible-addition batch across 3–8 appropriate pages unless a documented boundary prevents it.

## Handoff procedure

Before ending work, the departing agent must:

1. Finish or explicitly record the current candidate state; do not leave ambiguous work in memory only.
2. Update `master-inventory.json` through the project script and update `checkpoint.json` with completed range, counts, next ID, blockers, and a paste-ready resume command.
3. Save batch decisions, archive plans, source validation, public byte-identical validation, and any unresolved review evidence under `project-state/discovery/`.
4. Run proportionate validation. For content changes this normally includes `git diff --check`, the project's validation scripts, Hugo build, and a placement check. Record failures plainly.
5. Commit only files belonging to the assignment. Leave unrelated changes unstaged and name them in the handoff.
6. Push the branch and open a PR only after checking open PRs targeting `main`. The PR description must include every modified ABQInfo page's direct `https://abqinfo.com/` URL and exact visible additions, removals, moves, and cross-listings.
7. Give the next provider the completed template in `agent-handoff-template.md`, including the exact branch, commit, PR URL/state, next candidate ID, validation results, and unresolved decisions.

## Receiving a handoff

The receiving agent must not assume the supplied chat summary is current. It must fetch and verify the branch, PR, checkpoint, inventory, and open-PR list itself.

If the handoff branch has an open PR and `main` advanced:

1. Inspect the new `main` commits and the PR's changed files.
2. Integrate current `origin/main` into the handoff branch only after preserving unrelated working-tree changes.
3. Resolve only the actual conflict, re-run validation, and push the resolution.
4. Recheck PR mergeability. Do not merge or deploy unless the user explicitly asks.

## Copy-ready prompts

Use the template in [agent-handoff-template.md](agent-handoff-template.md). A minimal Claude start prompt is:

> You are continuing ABQInfo in the existing repository. Read `AGENTS.md`, `project-state/AGENT-HANDOFF.md`, `project-state/checkpoint.json`, `project-state/master-inventory.json`, and `project-state/README.md`. Fetch `origin`, inspect `git status`, and list open PRs targeting `main` before editing. Preserve unrelated changes. Use a dedicated branch, deterministic project scripts, and durable inventory/checkpoint updates. Do not merge or deploy without explicit user approval. Fill in and follow the current handoff template below.
