## Summary
Install the final owner-approved ABQ Info favicon unchanged across the site.

## Review this change
**Preview:** https://ddaa4f48.abqinfo.pages.dev/maps-data/maps/

- Added: approved browser-tab icon sitewide, with SVG, PNG and legacy ICO support, iOS home-screen icons, Android normal/maskable icons, and Safari/Windows metadata.
- Rewritten: existing web manifest icon metadata to use the supplied Android assets; the site retains one manifest reference.

[View the supplied icon](https://ddaa4f48.abqinfo.pages.dev/favicon.svg). Artwork remains unchanged and is visible against light and dark backgrounds.

## Validation
Hugo build, all 43 generated HTML heads, image formats/dimensions, manifest references, and Chrome light/dark preview inspection passed. All 23 deployed icon assets returned 200 with appropriate content types and exact approved ZIP bytes. Full project validation was stopped at the owner's explicit request to close out without further testing; it did not complete. Native mobile installation was not device-tested.

Leave unmerged for manual owner review.
