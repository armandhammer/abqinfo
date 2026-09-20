# ABQInfo Current Work

This is the compact resume file for normal ABQInfo work. Workflow and context optimization is complete; do not start another optimization project or load historical handoff ledgers during routine startup.

## Startup and workflow

- Read `AGENTS.md`, inspect the current branch and worktree, then use this file. Read `checkpoint.json` or task artifacts only when relevant.
- `project-state/master-inventory.json` is authoritative. Query it selectively unless full-inventory regeneration or validation is required.
- No verification campaign is active; preserve unrelated local files and ignored build output, backups, and temporary files.

## Current state

- Master inventory has 7,136 unique records; status aggregates and `next_pending_id` are generated. R2 contains 1,191 objects / 8,638,742,164 bytes; the 1,180-object live-R2 snapshot remains the immutable archive-reconciliation baseline.
- Archive reconciliation is locally complete without live-R2 mutation. Corrected 2014-2018 DPM packets are local only and externally gated.
- Capital Spending consolidation research is closed by `project-state/discovery/capital-spending-consolidation-closeout-status-2026-09-18.json`; future build, archive/public verification, page edit, merge, or deployment is separately externally gated.

## Ordinary work

The saved terminal City web-page batches, the 34-record Prescription Trails human-review package, the 2014 MS4 package, the code-enforcement Notices and Orders, and the LGCC agenda family remain outside ordinary review unless a new task explicitly scopes them. `src-06d0fc4cd0abdef6` and the seven Administration answers to Council questions records are approved inventory-only and separately archive/publication gated.

The accepted 18-record NMDOT grant-administration-and-application decision is `project-state/discovery/nmdot-grant-administration-and-application-decision-2026-09-19.json`. All 18 are approved inventory-only, placement-unresolved, and behind R2/public-byte-verification and future information-architecture gates. Do not repeat their research or describe any member as the next ordinary review merely because its status is nonterminal.

The seven-part NMDOT statewide truck parking study is approved inventory-only under `project-state/discovery/nmdot-statewide-truck-parking-study-decision-2026-09-19.json`. It is a complete numbered study series; five DOCX originals and two PDFs retain their original containers. Its proposed Roadway Studies placement fits the state-highway-studies scope, but R2 archival, public-byte verification, implementation, validation, and public-content work remain separately gated.

The complete municipal-development procurement cluster is resolved in `project-state/discovery/ordinary-queue-terminal-integration-batch-2026-09-19-municipaldevelopment-procurement.json`: 50 transactional solicitation records are excluded with saved evidence. The two standard-form professional-services agreements are approved and fully prepared in `project-state/discovery/municipaldevelopment-standard-forms-archive-preparation-2026-09-19.json`; do not repeat their research or preparation.

Their next action is the separately and explicitly authorized R2 archive/upload stage, followed by public-byte verification. Public page edits remain gated on that verification; the approved canonical future page is Development Process and the proposed Capital Spending cross-listing was rejected.

The next ordinary family after the Municipal Development gates was the 23-record Planned Growth Strategy (PGS) set, resolved in `project-state/discovery/planned-growth-strategy-decision-2026-09-19.json`. The complete 286-page Part 1 original is approved inventory-only; its seven component deliveries are duplicates. Eleven obtainable Part 2 delivery files are approved inventory-only with a durable missing-Chapter-3.0 warning; the City serves no combined Part 2 original, so do not synthesize one. Three related PGS enactment-bill copies remain requires-human-review until their enacted ordinances are located. All approved PGS originals remain behind separate R2/public-byte-verification and future editorial gates.

The two-record MRA Appeal Form delivery-alias family is resolved in `project-state/discovery/mra-appeal-form-family-decision-2026-09-19.json`: both City URLs serve the same one-page May 2015 transactional appeal intake form and are excluded. This is not a publication or archive candidate.

The June 5, 2025 fiber-rulemaking hearing family is complete in `project-state/discovery/fiber-rulemaking-meeting-records-decision-2026-09-19.json`: final City regulations are approved inventory-only; the unreviewed Otter transcript and Zoom chat log are excluded; the 79 MB correspondence/complaints record remains requires human review for privacy-sensitive publication treatment. No archive or public-content work occurred.

The Council closeout is recorded in `project-state/discovery/council-closeout-status-2026-09-20.json`. The meeting-agenda and 107-record reconciliations remain authoritative; the public-body matrix preserves the agenda/minutes evidence without inferring meeting occurrence, and LGCC remains untouched. Six enacted counterparts are inventory-only registered; O-2024-006 remains source-access blocked. O-23-96 and R-24-17 remain requires human review after bounded primary-source review. No R2 or public action occurred. After all gates and completed families are skipped, the next actionable ordinary family is the AEC agenda/minutes sequence beginning `src-0a03811e298d7753`.

The 26-record Municipal Development agenda/minutes family is resolved in `project-state/discovery/municipaldevelopment-agenda-minutes-family-decision-2026-09-20.json`: 18 records are approved inventory-only (including ten verified orphan agendas with the required missing-minutes label), one duplicate is retained, and seven agendas are excluded where stronger minutes exist or are expected. No R2 or public action occurred. Recompute the filtered ordinary queue before starting the next family.

Archive preparation for all 18 retained Municipal Development agenda/minutes records is complete in `project-state/discovery/municipaldevelopment-agenda-minutes-archive-preparation-2026-09-20.json`; it records source bytes, quality assessments, placement, future archive keys, collision checks, and the exact warnings for ten orphan agendas. The current District 2 Find Your Councilor subtree is terminally resolved in `project-state/discovery/district-2-find-your-councilor-family-decision-2026-09-20.json`: all 14 rows are excluded as live web pages or councillor page furniture. Skip both complete families when selecting the next ordinary review.

The October 14, 2020 Climate Action Task Force opening-meeting family is resolved in `project-state/discovery/climate-action-task-force-opening-meeting-decision-2026-09-20.json`: the six-page City minutes and 16-page City climate-survey presentation are approved inventory-only with full archive preparation and future Climate Environment placement. R2/public-byte verification and public content remain gated. The next actionable family is the remaining District 7 Find Your Councilor subtree, using its complete saved-tree research.

The Council amendment-sheet family above supersedes the prior `src-09a0152fb526fcba` handoff; it is now terminally excluded and must not be reviewed independently.

## External gates

- Do not upload corrected DPM packets, the separate 17-PDF / 67,526,043-byte batch, or any inventory-only NMDOT study originals without explicit authorization.
- Do not upload the two prepared Municipal Development standard-form agreements without explicit authorization, and do not edit public content for them before successful archive public-byte verification.
- Do not modify live R2, delete the noncanonical `mrmppo` duplicate, merge, or deploy merely as cleanup.
