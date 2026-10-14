# MRCOG map and app coverage - 2026-10-14

This is a coverage snapshot and review recommendation, not authorization to publish or archive the other catalog items. Existing inventory exclusions, aliases and supersessions remain controlling.

## Catalog coverage

- Exhausted explicit organization searches: MRCOG Enterprise returned 480 public items, including 305 bundled Esri items and **175 locally owned items**; MRMPO ArcGIS Online returned **870 public items**. The two sources contain **1,017 distinct local item IDs**, including 28 IDs deployed on both portals. Matching IDs are deployment relationships, not proof of identical bytes or function.
- Enumerated all 13 public MRMPO groups and the Enterprise Featured Maps and Apps group (empty). The official [Maps & GIS catalog](https://www.mrcog-nm.gov/224/Maps-GIS) embeds Featured GIS Gallery, group `a9f4a443fe3f4ee9ad7e83395eee8354`: nine applications plus one code attachment. Six applications already have ABQInfo coverage; three warrant review below.
- A wider `(MRCOG OR MRMPO) AND access:public` search returned 577 items. Of these, 148 IDs are outside the two official catalog populations, including Rogue Valley MPO name collisions and third-party copies. They are cross-check results, not automatically MRCOG publications or ABQInfo gaps. `mrcog.maps.arcgis.com` does not resolve to a separate named MRCOG organization. The actual official AGOL organization is MRMPO (`i3mLmgyL55IkFf81`).
- The bare `mrcogmaps.org` root serves an IIS placeholder; the public content is under `/portal` and maintained short URLs. An unscoped Enterprise public search includes thousands of Esri templates and reaches 10,000: it is not an organizational census. Explicit organization filtering plus owner classification avoids this false denominator.

## Existing coverage and duplicates

| Category | Result |
|---|---|
| Directly linked live catalog apps | Seven identities: Traffic Counts Viewer, Long Range Roadway System, Planned and Potential Transit Service, Pedestrian LTS, Active Transportation Committee portfolio, Transportation Equity Assessment, and Air Quality and Health Equity. |
| Existing live alias / official-page routes | Forecast2045 redirects to Enterprise portfolio `3c27472922ef4a8ca8fbf4600c5101a9`; retain existing `src-98959984b4d407e3`, not a second entry. The maintained HFIN and Road Diet sources expose current apps through already linked MRCOG pages. TAQA is also already represented by its official source page. |
| Components | 111 catalog items are reachable dependencies of existing linked apps, including forecast dashboards, Cyclist LTS and portfolio child maps. Do not count each component as a separate publication gap. |
| Archived static maps/data | 21 relevant inventory rows, **86,199,287 bytes**, all present in the authoritative R2 snapshot dated October 13. These include the AMPA boundary, adopted 2026 roadway/bikeway/pedestrian/transit maps, Greater Albuquerque/East Mountains traffic maps, road-diet map, forecast workbooks and data dictionary, historical CMP maps, and related traffic/count analyses. Fourteen rows already have exact archive links in public content; remaining rows stay inventory-only. |
| Settled duplicate/supersession/exclusion | Preserve the Pedestrian LTS alternate portal URL, PCI alias, superseded 2021 bikeway and road-diet apps, and excluded retired 2015-2019 online crash report. The latter remains linked by an upstream official page; that does not reverse ABQInfo's recorded “Replacement not available” finding. |
| Publication screening exclusions | 305 bundled Esri software/templates are not local map publications. At least 35 local titles explicitly identify tests, drafts, copies, deprecated material or committee-only use; these need no automatic standalone entries. Services, service definitions, code attachments, logos and component maps are not independently approved public resources. |
| Unlinked catalog material | 891 IDs lack a direct inventory/catalog or published-dependency match. This is a discovery remainder, **not 891 worthwhile missing maps**. It includes 325 feature services, 235 web maps, 64 map services, 37 service definitions, 33 code attachments and 127 mapping apps. Each proposed addition still needs scope, quality, family and usability review. |

R2 comparison used the committed local object snapshot, not a fresh storage listing or byte verification. No upload, overwrite, deletion or application mirroring occurred. Same-title static/live resources are complements unless exact content/hash comparison proves duplication. Three public AGOL PDFs were retrieved and SHA-256 compared against inventory: Functional Classification and NHS (2018), Bridge Conditions, and Sandoval County TIP Projects. None has an exact inventory hash match; this does not establish publication eligibility or absence of a differently packaged substantive duplicate.

## Worthwhile missing-map review candidates

| Candidate | Why review / proposed existing placement |
|---|---|
| Supplied Planning Areas and Roadway Functional Classification (`15c077acdfd248aea4d7d15f528f51c1`) | Explicit Albuquerque planning boundary and street classification information; Maps / Regional Long-Range Transportation Maps. Supplied-map review below determines eligibility. |
| Climate Change Hazards Vulnerability Assessment Tool (`00f8cf04c942466fb7a42245d9cc7f62`) | One official-gallery portfolio for regional vulnerability, heat, wildfire and flooding; inspect Albuquerque-specific substance and model vintages. Climate & Environment; represent the portfolio, not four separate children. |
| MRCOG Planning for Equity Communities Viewer (`127b493302544a5d9e9ecd06dbb9ef8b`) | Official-gallery portfolio compares local equity designation with federal screening layers. Compare against the two already published equity portfolios; distinguish historical federal datasets and eligibility caveats. Climate & Environment or Dashboards if independently useful. |
| Natural Resource Inventory (`1f892bd6901e4698858ed94de49f6d00`) | Official-gallery regional environmental inventory; verify material Albuquerque land/water/planning value and actual functionality before any admission. Climate & Environment or Datasets; do not add the accompanying code attachment. |
| Albuquerque housing-displacement portfolio (`6e93abe29d494f5d857ac9b293f882b0`) | Explicit City of Albuquerque risk indices; review historical data, methodology and overlap with dashboard `0e830f54673743f2ba0a48e026949280` and its four index apps as one family. Housing & Homelessness or Demographics if useful. |

None of these recommendations changes an inventory disposition. General regional context, public sharing, a promising title or agency ownership alone cannot pass ABQInfo's two mission gates.

## Supplied map

ArcGIS item title: **Functional Classification and Planning Areas - Sidebar App**. Configured application title: **MRCOG Planning Areas and Roadway Functional Classification**. Public item owner `ssheets_portal`; underlying public Planning Areas Map `8854cd813777456db84f616efa3bc5a3`. App metadata, configuration and all twelve operational service layers are anonymously accessible. The exact item/URL is absent from the baseline inventory, published links and recorded R2 keys; source-derived ID is `src-1a6c3f00995ac229`. It is absent from the current nine-application official gallery as well.

Contents: AMPA, MRCOG and MRRTPO planning regions; Albuquerque/Los Lunas adjusted urban areas; roadway functional classification; modeled road ownership; municipalities; tribal areas; counties; and NMDOT districts. Public queries return 1,034 classification features and an Albuquerque planning-area polygon. The app's explanatory notes identify the 2025 classification update and April 1, 2026 FHWA approval, warn that road ownership is modeled and not authoritative, and say that unshown roads should be considered local. These are publisher statements, not independently established legal determinations.

The map has a direct, material Albuquerque transportation-policy connection and offers substantive public value beyond generic regional context. It complements the archived boundary and adopted future-network maps; functional classification is not the same subject as a planned long-range roadway network. One live-source entry in Maps / Regional Long-Range Transportation Maps is the proposed placement. An interactive application is not an archived static map, and no R2 copy is proposed.

Rendered usability: **passed**. Anonymous installed Chrome displayed the actual map and explanatory notes; Legend exposed Interstate, Principal/Minor Arterial, Major/Minor Collector and Local classes; Layers exposed the ten top-level entries; searching Albuquerque zoomed from regional to city geography. The first short default capture showed a loading spinner, so a longer software-WebGL retry was used and the loaded map was visually inspected. No sign-in was required. The source qualifies for one unmerged content PR; validation/preview/PR receipts record its preparation separately.

## Evidence

`catalog.json` contains paginated query totals/cursors and public item records; `groups.json` contains public group membership; `app-configs.json` retains reference/configuration summaries, omitting geometry; `catalog-pages.json` and `official-pages.json` retain official wrappers; `reconciliation.json` gives per-item deployments, inventory statuses, published-page/dependency matches and static archive keys. `supplied-map.json`, `layer-checks.json`, the existing tool's roadway/planning service audits, `static-item-checks.json` and `render-*.json` support the supplied-map and duplicate checks. Local screenshots are retained with hashes in the render receipts.
