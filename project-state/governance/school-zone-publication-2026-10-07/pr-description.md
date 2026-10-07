## Summary

Adds direct school-zone flasher activation schedules to **Safety & Crash Data → School Transportation Safety → School Zone Active Times**: 30 distinct schedules covering 32 named schools and 61 intervals, presented alphabetically with locations and material qualifications.

The source is a 33-page record obtained through an Inspection of Public Records Act (IPRA) request and supplied to ABQInfo. It was reported unavailable on the City/APS public websites. ABQInfo archived the original unchanged and verified the complete public download against its 3,013,109-byte size and SHA-256.

## Review this change

**Preview:** https://65a739de.abqinfo.pages.dev/transportation/safety-crash-data/#school-zone-active-times

- Added: **School Zone Active Times**, with readable school/timing entries and the archived **ABQ Middle School and High School Zone Active Timings** PDF. Existing School Transportation Safety records are unchanged.

These are flasher schedules, not school bell times. The PDF identifies no issuing agency or single effective date and does not confirm that every schedule remains current. Monday-Friday is shown only where the source marks M-F; missing weekday labels, Cibola's lunch interval, McKinley's controller exception, the Hayes location conflict, Jefferson's additional flashers, and the Tony Hillerman / Volcano Vista shared schedule remain explicit. Cleveland's source misspelling is identified. Elementary-school timings are expected later and are not yet included.

## Validation

- Exact original upload and complete public-download size/SHA-256 verification passed; one object and 3,013,109 bytes added.
- Installed Chrome desktop/mobile preview inspection passed: all 30 schedules and 61 intervals, weekday/location/material-note comparisons, archive link/full GET, section anchor, and no horizontal overflow.
- Full normal validation, governance/freshness, sealed-history, checkpoint regressions, Hugo build, PR-description and diff checks passed. Four pre-existing title-case warnings on the unchanged Area & Sector Plans page remain; the new section has none.

This PR remains open and unmerged for manual editorial review. No production deployment is authorized.
