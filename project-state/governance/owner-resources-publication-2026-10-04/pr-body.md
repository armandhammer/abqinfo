## Summary

Publishes the six completed interactive-resource reviews, adds the owner's two neighborhood resources, and updates the existing Sunport master-plan entry to its verified archive. Uses seven existing pages with no new pages or navigation.

## Review this change

**Preview:** https://3970ecce.abqinfo.pages.dev/maps-data/maps/#citywide-reference-maps

- Added: City Council Districts, NTMP Eligible Roadways, MRMPO Transportation Equity Assessment, MRMPO Air Quality and Health Equity, and the grouped City Transportation Performance Charts.
- Added: the owner's [Recognized Neighborhood Associations and Coalitions map](https://cabq.maps.arcgis.com/apps/instant/basic/index.html?appid=1eef18dec8844aecabba439823ff9eb2) and [Neighborhood Association Websites directory](https://www.cabq.gov/office-of-neighborhood-coordination/neighborhood-websites), with internal cross-references between their canonical entries.
- Rewritten: Current Bikeways and Trails Data now uses the maintained City GIS resource on both existing pages. The single Sunport entry now downloads the archived canonical original.

| Page and changed heading | Visible change and section preview |
| --- | --- |
| **Maps** / **Citywide Reference Maps** | [Recognized Neighborhood Associations and Coalitions (live City map)](https://3970ecce.abqinfo.pages.dev/maps-data/maps/#citywide-reference-maps): address search, association and coalition geography, and a directory cross-reference. |
| **Maps** / **Citywide Reference Maps → Historical Transportation Maps** | [City Council Districts (live City map)](https://3970ecce.abqinfo.pages.dev/maps-data/maps/#historical-transportation-maps), beside the dated January 2026 archived poster. |
| **Maps** / **City Bicycle Maps and Data** | [Current Bikeways and Trails Data (live City map)](https://3970ecce.abqinfo.pages.dev/maps-data/maps/#city-bicycle-maps-and-data): replaces the obsolete delivery/data endpoint with the official maintained City resource. |
| **Bike Maps** / **City Bicycle Maps** | The same [Current Bikeways and Trails Data replacement](https://3970ecce.abqinfo.pages.dev/transportation/bicycling/bike-maps/#city-bicycle-maps), preserving its existing cross-listing and distinction from 2024 static planning conditions. |
| **Speed Management** / **Neighborhood Traffic Management Program** | [NTMP Eligible Roadways (live City map)](https://3970ecce.abqinfo.pages.dev/transportation/roadway-projects/speed-management/#neighborhood-traffic-management-program): emergency-route constraints and potentially eligible streets, subject to City evaluation. |
| **Dashboards** / **Project, Program, and Safety Dashboards** | [MRMPO Transportation Equity Assessment and City Transportation Performance Charts (historical)](https://3970ecce.abqinfo.pages.dev/maps-data/dashboards/#project-program-and-safety-dashboards). Equity/access analysis uses 2016–2020 ACS data; the seven City charts remain grouped and end FY2018 or FY2020. |
| **Climate & Environment** / **Environmental Justice and Local Conditions** | [MRMPO Air Quality and Health Equity](https://3970ecce.abqinfo.pages.dev/city-data/climate-environment/#environmental-justice-and-local-conditions): six historical modeled indicators using EPA 2021 EJScreen 2.0 and 2016–2020 ACS. Not real-time monitoring, a regulatory determination or an individual health assessment. |
| **Transportation Plans** / **Aviation Planning** | [Albuquerque International Sunport Sustainable Airport Master Plan (December 2019; adopted 2020; archived PDF)](https://3970ecce.abqinfo.pages.dev/transportation/transportation-plans/#aviation-planning): replaces the oversized Legistar delivery link with the archive and removes the obsolete threshold sentence; retains the official City original and R-19-168 matter record. One entry only. |
| **Development Process** / **Current City Review Process** | [Neighborhood Association Websites (live City directory)](https://3970ecce.abqinfo.pages.dev/development-land-use/development-process/#current-city-review-process): direct access to submitted websites of City-recognized associations, with a neighborhood-map cross-reference. Associations maintain their own sites; HOA websites are excluded. |

The completed six-resource reviews remain binding and unchanged. Historical dashboards retain their date and use limitations; maintained maps/directories remain live official links.

## Sunport archive and storage

Phase A was integrated into main as `1e56540c199d26384989074d497a9bffac60e3f4` before this content branch. Under the owner's exception for this exact object, the unchanged 601-page City original was archived at:

`transportation/transportation-plans/cabq-sunport-sustainable-airport-master-plan-2019.pdf`

The complete public GET verified **280,024,902 bytes** and SHA-256 **`d4583c4d9e5e1233c402f64222fd8837ff7f0fc0a352dc2d5153776842f39d02`**. Phase A added **1 object / 280,024,902 bytes**; final R2 accounting is **1,612 objects / 10,971,266,597 bytes**, below the **13,000,000,000-byte** project ceiling. The standing **150,000,000-byte** limit remains unchanged for other objects. Phase B adds no R2 objects; nothing was overwritten or deleted.

## Validation

- Complete project validation, full governance/freshness resolution, mission-scope and publication-quality gates, and sealed historical regressions passed.
- Hugo and rendered link/anchor checks passed. Every changed preview article matches the validated local render; every changed resource was visually inspected in isolated installed desktop Chrome.
- Fresh external GET checks passed for all eight published live source URLs and the official MRCOG parent resource.
- `git diff --check` and PR-description validation passed. The actual final visible diff is limited to the frozen nine-record publication population.

This PR is for owner manual editorial review. It remains unmerged; production publication is not authorized by this handoff.
