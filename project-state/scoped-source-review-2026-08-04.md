# Scoped CABQ and Bernalillo County source review

Recorded: 2026-08-04

## Scope and method

Whole-site crawling is paused. This review is limited to the twelve starting pages selected by the user: six City of Albuquerque pages and six Bernalillo County Public Works pages.

- Extracted 339 authored main-content links: 201 CABQ and 138 Bernalillo County.
- Reconciled 228 previously untracked URLs into the authoritative master inventory.
- Resolved 226 candidate pages locally for title, source text, dates, response metadata, and nested document links.
- Four targets returned unusable responses: an obsolete CABQ school-crossing PDF view, a Cloudflare email-protection link, the unrelated ABQToDo page, and an old County bus-shelter endpoint.
- The built-in browser verified the County project indexes and recovered 39 current and 74 finished project titles from generic “Visit the project page” links.
- The local resolver artifact is `research/discovery/scoped-linked-content.json`; research artifacts remain excluded from the production Hugo build.

## Highest-value additions identified

### Bicycling

- [City bicycle laws](https://www.cabq.gov/bikes/bike-laws)
- [City bike maps and trail guides](https://www.cabq.gov/bikes/bike-maps)
- [Biking for transportation](https://www.cabq.gov/bikes/biking-for-transportation)
- [City bicycle programs and plans](https://www.cabq.gov/bikes/city-plans-docs-support-bike-friendly-community)
- [E-bike and e-scooter information](https://www.cabq.gov/bikes/ebike-escooter-info)
- [Free community bike shop and resources](https://www.cabq.gov/bikes/free-community-bike-shop-resources)

### City Council and civic process

- [Agendas, minutes, and legislation](https://www.cabq.gov/council/agendas-minutes-legislation)
- [Legislative process](https://www.cabq.gov/council/legislation)
- [Council committees](https://www.cabq.gov/council/committees)
- [Find your councilor](https://www.cabq.gov/council/find-your-councilor)
- [Public comment](https://www.cabq.gov/council/find-your-councilor/public-comments)
- [Land-use appeals to the City Council](https://www.cabq.gov/council/appeals-of-land-use-decisions-to-the-city-council)
- [Public Improvement Districts](https://www.cabq.gov/council/public-improvement-districts)
- [Council projects and initiatives](https://www.cabq.gov/council/projects)

These resources reveal a genuine missing subject area. A compact City Government section is preferable to scattering Council links through unrelated categories.

### Traffic operations and speed management

- [NTMP pending traffic requests](https://www.cabq.gov/neighborhood-traffic-management-program/pending-traffic-requests)
- [NTMP completed studies](https://www.cabq.gov/neighborhood-traffic-management-program/studies)
- [NTMP traffic-calming request](https://www.cabq.gov/neighborhood-traffic-management-program/submit-a-traffic-calming-request)
- [NTMP traffic-calming toolkit](https://www.cabq.gov/neighborhood-traffic-management-program/toolkit)
- [Bernalillo County automated photo speed enforcement](https://www.bernco.gov/public-works/automated-photo-speed-enforcement/)
- [Bernalillo County street maintenance](https://www.bernco.gov/public-works/public-works-services/road-safety-conditions/streets-traffic-signals/street-maintenance/)
- [Bernalillo County traffic engineering](https://www.bernco.gov/public-works/public-works-services/road-safety-conditions/streets-traffic-signals/traffic-engineering/)

### Plans, standards, and projects

- [Bernalillo County transportation plans](https://www.bernco.gov/public-works/transportation-planning/transportation-plans/)
- [Bernalillo County transportation project planning](https://www.bernco.gov/public-works/transportation-planning/transportation-project-planning/)
- [Bernalillo County Complete Streets planning](https://www.bernco.gov/public-works/transportation-planning/complete-streets-planning/)
- [Bernalillo County traffic-impact analysis](https://www.bernco.gov/public-works/transportation-planning/traffic-impact-analysis/)
- [Bernalillo County technical standards](https://www.bernco.gov/public-works/development-review/tech-standards/)
- [Bernalillo County current projects](https://www.bernco.gov/public-works/current-projects/)
- [Bernalillo County finished projects](https://www.bernco.gov/public-works/finished-projects/)
- [West Central Complete Streets](https://www.cabq.gov/municipaldevelopment/featured-projects/west-central-complete-streets-project)
- [2nd Street rehabilitation, sidewalks, and lighting](https://www.cabq.gov/municipaldevelopment/featured-projects/2nd-street-rehab-sidewalk-and-lighting-improvements-project-cn-a302300)
- [MLK Jr. Avenue separated bicycle-lane pilot](https://www.cabq.gov/municipaldevelopment/featured-projects/dr-martin-luther-king-jr-blvd-separated-bicycle-lane-pilot-project)

The County current and finished indexes are better public entry points than copying every small project card. Individual project pages should be added only when they contain lasting plans, studies, maps, or meaningful current construction information.

### Parks and public space

- [City parks](https://www.cabq.gov/parksandrecreation/parks)
- [City Open Space](https://www.cabq.gov/parksandrecreation/open-space)
- [Recreation facilities and programs](https://www.cabq.gov/parksandrecreation/recreation)
- [Parks projects and improvements](https://www.cabq.gov/parksandrecreation/featured-projects)
- [Park rules, requirements, and permits](https://www.cabq.gov/parksandrecreation/resources-rules)
- [Urban Forestry](https://www.cabq.gov/parksandrecreation/urban-forest)

## Current-site links proposed for removal or replacement

No public links were removed during this review. The complete external-link check returned HTTP success for every current validated source; the concerns below are usefulness and placement, not broken-link status.

### Remove outright

1. [NMDOT Adopt a Highway](https://www.dot.nm.gov/adopt-a-highway) — a volunteer-program page given disproportionate prominence on the Transportation landing page.
2. [Request NMDOT public records](https://www.dot.nm.gov/contact-us/inspection-of-public-records) — a statewide agency request form placed on the City Data landing page without Albuquerque-specific data.
3. [Albuquerque Community Safety Department overview](https://www.cabq.gov/acs/services/overview) — an agency overview, not a public-safety dataset; it does not belong under Public Safety Data.
4. [Request an NMDOT map](https://www.dot.nm.gov/travel-information/request-a-map) — a form for requesting printed statewide maps, not a substantive map resource.
5. [New Mexico Transportation Commission](https://www.dot.nm.gov/contact-us/transportation-commission) — commission administration and meeting material, not a transportation plan.
6. [NMDOT Public Involvement Portal and Toolbox](https://www.dot.nm.gov/projects/public-involvement-portal) — practitioner guidance, not an active Albuquerque roadway project.
7. [NMDOT Transportation Regulation Bureau](https://www.dot.nm.gov/trb) — commercial carrier, ambulance, railroad, and towing regulation; it is not a transit-rider resource.
8. [NMDOT ePermitting](https://www.dot.nm.gov/epermitting) — a permit-application portal rather than a transportation design reference.
9. [NMDOT Tribal and Local Public Agency documents](https://www.dot.nm.gov/business-support/project-oversight-division/t-lpa-documents-and-information) — administrative project-oversight material for agencies, too broad for the public design-reference page.
10. [City open-data catalog](https://data.cabq.gov/) — the target is only an unannotated `Index of /` directory and does not function as a catalog.
11. [Safety Planning Assistance](https://www.mrcog-nm.gov/638/Safety-Planning-Assistance) — technical-assistance program material for local agencies, not safety or crash data.

### Replace with a public-facing viewer or remove

12. [Bernalillo County Comprehensive Plan Development Areas](https://pdsgismaps.bernco.gov/server/rest/services/BERNCO/ComprehensivePlanDevelopmentAreas/MapServer)
13. [Bernalillo County Bikeways](https://pdsgismaps.bernco.gov/server/rest/services/BERNCO/Bikeways/MapServer)
14. [Bernalillo County Multi-Use Trails](https://pdsgismaps.bernco.gov/server/rest/services/BERNCO/Multi_Use_Trails/MapServer)
15. [Bernalillo County Open Space Holdings](https://pdsgismaps.bernco.gov/server/rest/services/BERNCO/Open_Space/MapServer)

These links open raw ArcGIS REST service metadata, not usable maps for ordinary visitors. They should be replaced with official interactive viewers if available; otherwise remove them from the public site while retaining the endpoints internally as data provenance.

### Consolidate or demote

16. [Peak Hour versus Peak Period](https://www.mrcog-nm.gov/624/Peak-Hour-vs-Peak-Period) — a narrow explanatory page that is overstated as a primary Traffic Operations resource.
17. [Historical turning movement counts](https://www.mrcog-nm.gov/538/Turning-Movement-Counts) — old reports and pandemic-era guidance; retain only if clearly labeled as an archive and paired with a current count source.
18. [COVID-19 and Travel](https://www.mrcog-nm.gov/633/COVID-19-and-Travel) — substantive historical analysis, but not current traffic operations; move to a clearly historical subsection or remove from the main operations page.
19. [Environmental Justice](https://www.mrcog-nm.gov/579/Environmental-Justice) and [MRCOG Title VI](https://www.mrcog-nm.gov/460/Title-VI-EEO) — administrative/general background is overrepresented on Transportation Plans. Retain one broader equity-planning entry and remove the redundant standalone links.
20. [MRCOG Economic Development](https://www.mrcog-nm.gov/355/Economic-Development) and [Workforce Connection](https://www.mrcog-nm.gov/354/Workforce) — generic program homepages supporting an otherwise thin Economy & Workforce page. Replace them with actual Albuquerque-area reports or datasets before treating that page as substantive.

