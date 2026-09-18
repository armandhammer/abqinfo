#!/usr/bin/env python3
"""Build the durable decision/manifest for the 2011 Capital Spending compilations."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "project-state/discovery/2011-capital-spending-consolidation-manifest-2026-09-18.json"
PAGE = ROOT / "content/city-data/capital-spending.md"
PRE_PLAN = ROOT / "project-state/discovery/2011-go-bond-program-scope-and-schedule-r2-plan.json"
PRE_DECISIONS = ROOT / "project-state/discovery/2011-go-bond-program-scope-and-schedule-decisions.json"
PRE_R2 = ROOT / "project-state/discovery/2011-go-bond-program-scope-and-schedule-r2-validation.json"
PUBLISHED_PLAN = ROOT / "project-state/discovery/go2011-bond-r2-archive-plan-2026-09-11.json"
PUBLISHED_R2 = ROOT / "project-state/discovery/go2011-bond-r2-public-validation-2026-09-11.json"
SCHEDULE_PLAN = ROOT / "project-state/discovery/2011-go-bond-department-schedules-r2-plan.json"
SCHEDULE_R2 = ROOT / "project-state/discovery/2011-go-bond-department-schedules-public-validation.json"
CLUSTER = ROOT / "project-state/discovery/go2011-bond-cluster-research-2026-09-11.json"
VERSION_DECISION = ROOT / "project-state/discovery/go2011-bond-version-decision-2026-09-17.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def public_url(key: str) -> str:
    return "https://files.abqinfo.com/" + key.lstrip("/")


def section_archive_urls(text: str, heading: str) -> list[str]:
    marker = f"### {heading}"
    start = text.index(marker) + len(marker)
    match = re.search(r"^###\s+", text[start:], flags=re.MULTILINE)
    end = start + match.start() if match else len(text)
    return re.findall(r"\]\((https://files\.abqinfo\.com/[^)]+)\)", text[start:end])


def assert_r2_validation(plan_items: list[dict], validation: dict, label: str) -> None:
    results = {item["id"]: item for item in validation["results"]}
    if set(results) != {item["id"] for item in plan_items}:
        raise ValueError(f"{label} R2 validation does not cover the plan exactly")
    for item in plan_items:
        result = results[item["id"]]
        if not result.get("byte_identical"):
            raise ValueError(f"{label} R2 validation failed for {item['id']}")
        if result["size_bytes"] != item["size_bytes"] or result["checksum_sha256"] != item["checksum_sha256"]:
            raise ValueError(f"{label} R2 identity mismatch for {item['id']}")


EXTRA = {
    "src-27bd37adf07104b9": {
        "id": "src-27bd37adf07104b9",
        "title": "2011 Family and Community Services General Obligation Bond Schedule (Initial Version)",
        "date": "2011",
        "source_url": "https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2011-go-bond-documents/1family_summary.pdf/view",
        "direct_file_url": "https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2011-go-bond-documents/1family_summary.pdf",
        "size_bytes": 48532,
        "checksum_sha256": "e2379cac55c54c2757a13f64a3bd130878767c8ed838314eeaad981fcef6f127",
        "r2_key": "city-data/capital-spending/cabq-2011-initial-family-community-services-go-bond-schedule.pdf",
        "implementation_locations": ["content/city-data/capital-spending.md"],
    },
    "src-ca2ae8cb1ef13fdf": {
        "id": "src-ca2ae8cb1ef13fdf",
        "title": "2011-2019 Parks and Recreation General Obligation Bond Schedule (December 2010 City Edition)",
        "date": "2010-12-21",
        "source_url": "https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2011-go-bond-documents/parks_and_rec_summary.pdf/view",
        "direct_file_url": "https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2011-go-bond-documents/parks_and_rec_summary.pdf",
        "size_bytes": 45669,
        "checksum_sha256": "5932cf474f2d67c8af4e3d759d8f1728186f252c0fe748a0d6917afbf9005c49",
        "r2_key": None,
        "proposed_r2_key": "public-works/parks-recreation/cabq-2011-2019-parks-recreation-go-bond-schedule-december-2010-city-edition.pdf",
        "implementation_locations": [],
    },
    "src-20cca95ec6dcbe4f": {
        "id": "src-20cca95ec6dcbe4f",
        "title": "2011 Parks and Recreation General Obligation Bond Project Scopes (December 2010 City Edition)",
        "date": "2010-12-22",
        "source_url": "https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2011-go-bond-documents/parks_and_rec_scope.pdf/view",
        "direct_file_url": "https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2011-go-bond-documents/parks_and_rec_scope.pdf",
        "size_bytes": 44615,
        "checksum_sha256": "4f007d0d30cbbc1b592cab69fef48478276cc458872a2d0053b9390907dfb026",
        "r2_key": None,
        "proposed_r2_key": "public-works/parks-recreation/cabq-2011-parks-recreation-go-bond-project-scopes-december-2010-city-edition.pdf",
        "implementation_locations": [],
    },
    "src-832bc2144296aa51": {
        "id": "src-832bc2144296aa51",
        "title": "2011-2019 Cultural Services General Obligation Bond Schedule (December 2010 City Edition)",
        "date": "2010-12-21",
        "source_url": "https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2011-go-bond-documents/cultural_summary.pdf/view",
        "direct_file_url": "https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2011-go-bond-documents/cultural_summary.pdf",
        "size_bytes": 56940,
        "checksum_sha256": "33f65a176471ac6f54bf3e12ae0e0abeee1fc4be3a2283aed9ebdb8868916d5f",
        "r2_key": None,
        "proposed_r2_key": "city-data/capital-spending/cabq-2011-2019-cultural-services-go-bond-schedule-december-2010-city-edition.pdf",
        "implementation_locations": [],
    },
    "src-9e6cb716ac7c28d9": {
        "id": "src-9e6cb716ac7c28d9",
        "title": "2011 Cultural Services General Obligation Bond Project Scopes (December 2010 City Edition)",
        "date": "2010-12-22",
        "source_url": "https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2011-go-bond-documents/cultural_scope.pdf/view",
        "direct_file_url": "https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2011-go-bond-documents/cultural_scope.pdf",
        "size_bytes": 56890,
        "checksum_sha256": "b9747c25a8cfbde1547f6e84f7336ae6451eefa14e2bb2e82a196cc1ea66fb37",
        "r2_key": None,
        "proposed_r2_key": "city-data/capital-spending/cabq-2011-cultural-services-go-bond-project-scopes-december-2010-city-edition.pdf",
        "implementation_locations": [],
    },
}


PUBLISHED_ORDER = [
    "src-2746069f062780cf",
    "src-65e4a509079e184f", "src-25501032bfbfa682", "src-54665bf864159096",
    "src-8d8336fa08217661",
    "src-b3c2636a2b9c5372", "src-2ed981e6df5e99d2",
    "src-bd60d8eab4edf667", "src-75f032fd59799df5",
    "src-832bc2144296aa51", "src-003fea9b67977cc0", "src-9e6cb716ac7c28d9", "src-afc7fa6f1c4ac06f",
    "src-9eacad9e5872b301", "src-4bafa6f452f2f586",
    "src-27bd37adf07104b9", "src-90969f7fd9f9f810", "src-b08cdbd2624ad1a0", "src-352694313c3e5710",
    "src-542056c326cf2578", "src-38b254217ef6c868", "src-2daae0eb6e136555",
    "src-a547a0278fb86fb9", "src-3d3737d5175c3ef7", "src-e6ca25d4cfa80752", "src-db9fefd23083da69",
    "src-ca2ae8cb1ef13fdf", "src-5d81348c100d185e", "src-20cca95ec6dcbe4f", "src-27d391d187280ced",
    "src-c9af414f77032660", "src-cce2d0242f9145bd", "src-89b36d5577443f99", "src-b7f0628556085641",
    "src-61f62a0f79a49ead", "src-f74d655ffb05fd08",
    "src-4cd84ecef3756fb0", "src-b90b07ac62c4f7fd",
    "src-4c768545506342aa", "src-2663fc607177e07d",
    "src-a31943aca401c7f0", "src-5265cf315f641e6c", "src-be70a79a59ae0915", "src-d30fe509d51eec50",
    "src-04a2e444a39dcd41", "src-b37593a011f57fae",
]


def make_source(item: dict, family: str) -> dict:
    r2_key = item.get("r2_key")
    proposed_key = item.get("proposed_r2_key") or r2_key
    archive_status = "verified_public_r2" if r2_key else "proposed_not_uploaded"
    locations = list(item.get("implementation_locations") or [])
    other_locations = [value for value in locations if value != "content/city-data/capital-spending.md"]
    return {
        "candidate_id": item["id"],
        "title": item["title"],
        "date": item.get("date") or "2011",
        "family": family,
        "source_record_url": item.get("source_url"),
        "source_url": item["direct_file_url"],
        "size_bytes": int(item["size_bytes"]),
        "checksum_sha256": item["checksum_sha256"],
        "r2_key": r2_key,
        "proposed_r2_key": proposed_key,
        "archive_url": public_url(proposed_key),
        "archive_status": archive_status,
        "archive_label": "Byte-identical archived original" if r2_key else "Proposed archive URL - not uploaded",
        "preservation_note": (
            "The complete original document begins on the following page. It remains separately available at the archive URL above."
            if r2_key
            else "The complete verified City original begins on the following page. Its proposed individual archive URL is shown above, but no R2 upload has occurred."
        ),
        "local_path": f"tmp/pdfs/2011-capital-spending/{item['id']}.pdf",
        "current_implementation_locations": locations,
        "future_cross_listing_treatment": {
            "action": "continue_individual_source" if other_locations else "none",
            "locations": other_locations,
        },
        "component_page_count": None,
        "compilation_separator_page": None,
        "compilation_source_page_start": None,
        "compilation_source_page_end": None,
    }


def main() -> None:
    pre_items = load(PRE_PLAN)["items"]
    published_items = load(PUBLISHED_PLAN)["items"]
    schedule_items = load(SCHEDULE_PLAN)["items"]
    assert len(pre_items) == 21 and len(published_items) == 26 and len(schedule_items) == 15
    assert_r2_validation(pre_items, load(PRE_R2), "October 2010")
    assert_r2_validation(published_items, load(PUBLISHED_R2), "published scopes and versions")
    assert_r2_validation(schedule_items, load(SCHEDULE_R2), "published schedules")

    all_items = {item["id"]: item for item in pre_items + published_items + schedule_items}
    all_items.update(EXTRA)
    expected_published = {item["id"] for item in published_items + schedule_items} | set(EXTRA)
    if set(PUBLISHED_ORDER) != expected_published:
        raise ValueError("Published ordering does not cover the 46 selected records exactly")

    preliminary_sources = [make_source(item, "october_2010_preliminary_epc") for item in pre_items]
    published_sources = [make_source(all_items[candidate_id], "2011_published_program") for candidate_id in PUBLISHED_ORDER]

    page_text = PAGE.read_text(encoding="utf-8-sig")
    published_visible = section_archive_urls(page_text, "2011 Published Scope and Version Records")
    october_visible = section_archive_urls(page_text, "October 2010 Program Scope and Schedule Records")
    if len(published_visible) != 26 or len(october_visible) != 37:
        raise ValueError("Capital Spending 2011 section counts changed from the reviewed 26/37 baseline")
    current_r2_urls = {source["archive_url"] for source in preliminary_sources + published_sources if source["archive_status"] == "verified_public_r2"}
    if current_r2_urls != set(published_visible + october_visible):
        raise ValueError("Selected current R2 originals do not exactly cover the 63 visible 2011 links")

    pre_decisions = load(PRE_DECISIONS)
    cluster = load(CLUSTER)
    nonmembers = [
        {
            "candidate_id": item["id"],
            "disposition": "exclude_duplicate_delivery",
            "canonical_id": item["canonical_id"],
            "reason": item["reason"],
        }
        for item in pre_decisions["duplicates"]
    ]
    nonmembers.extend(
        {
            "candidate_id": item["id"],
            "disposition": "exclude_duplicate_delivery",
            "canonical_id": item["canonical_id"],
            "reason": item["evidence"],
        }
        for item in cluster["duplicate"]
    )
    nonmembers.extend(
        {
            "candidate_id": item["id"],
            "disposition": "exclude_non_document",
            "canonical_id": None,
            "reason": item["reason"],
        }
        for item in cluster["excluded"]
    )

    version_decision = load(VERSION_DECISION)
    manifest = {
        "schema_version": 1,
        "artifact_type": "2011_capital_spending_consolidation_decision_manifest",
        "reviewed_at": "2026-09-18",
        "publication_state": "preparation_complete_not_published",
        "scope": {
            "page": "content/city-data/capital-spending.md",
            "reviewed_visible_sections": {
                "2011 Published Scope and Version Records": 26,
                "October 2010 Program Scope and Schedule Records": 37,
            },
            "current_visible_component_links": 63,
            "selected_unique_components": 67,
            "current_individual_r2_originals": 63,
            "selected_originals_pending_r2": 4,
        },
        "decision": {
            "result": "prepare_two_provenance_preserving_historical_compilations",
            "grouping_correction": "The Markdown heading boundary is not the provenance boundary. The October 2010 EPC folder supplies 21 preliminary components. Sixteen later-directory schedules are currently displayed beneath that heading but belong with the 26 published scope/version records. Four additional December 2010 Cultural Services and Parks and Recreation editions are materially distinct and belong in the published compilation without becoming more standalone page entries.",
            "version_rule": "Preserve initial, December 2010, and April 2011 or later-directory editions when saved evidence establishes substantive difference. Chronology does not establish final or adopted precedence.",
            "provenance_rule": "Every original inventory record, official URL, checksum, R2 object, and version relationship remains intact. Consolidation changes only the proposed public browsing form.",
            "r2_boundary": "No compilation or component upload, overwrite, rename, or deletion is authorized by this artifact.",
        },
        "source_artifacts": [
            str(path.relative_to(ROOT)).replace("\\", "/")
            for path in (PRE_PLAN, PRE_DECISIONS, PRE_R2, PUBLISHED_PLAN, PUBLISHED_R2, SCHEDULE_PLAN, SCHEDULE_R2, CLUSTER, VERSION_DECISION)
        ],
        "version_relationships": version_decision["pairs"],
        "other_labeled_initial_versions": [
            source["candidate_id"]
            for source in published_sources
            if "Initial Version" in source["title"]
        ],
        "compilations": [
            {
                "compilation_id": "october_2010_preliminary_epc_program_record",
                "title": "October 2010 Preliminary/EPC 2011 General Obligation Bond Program Record",
                "short_title": "October 2010 Preliminary/EPC Program Record",
                "record_label": "Edition / component",
                "source_record_label": "Original City preliminary-program component",
                "date_label": "Record date",
                "coverage_note": "One citywide allocation summary, 13 department project-scope sheets, and seven department schedules from the City\'s October 2010 Environmental Planning Commission folder.",
                "editorial_note": "This preliminary/EPC package is materially distinct from the later 2011 published directory. It is presented separately and is not described as final or adopted.",
                "provenance_note": "The 21 complete City PDFs follow in the saved folder order: citywide summary, department scopes, then the seven October 2010 schedules. Each original remains individually tracked and publicly byte-verified in R2.",
                "preservation_notice": "This is an ABQInfo historical compilation, not a City-issued single document. Each complete City component follows a provenance sheet. All 21 originals remain separately preserved at their byte-identical archive URLs with official source links, sizes, and SHA-256 checksums.",
                "ordering_rule": "Preserve the settled source-plan order: citywide summary, 13 department scopes, then seven October 2010 schedules.",
                "proposed_filename": "abqinfo-2011-go-bond-october-2010-preliminary-epc-program-record.pdf",
                "proposed_r2_key": "city-data/capital-spending/abqinfo-2011-go-bond-october-2010-preliminary-epc-program-record.pdf",
                "local_output_path": "output/pdf/capital-spending/abqinfo-2011-go-bond-october-2010-preliminary-epc-program-record.pdf",
                "build_validation_path": "project-state/discovery/2011-capital-spending-preliminary-compilation-build-validation-2026-09-18.json",
                "qa_validation_path": "project-state/discovery/2011-capital-spending-preliminary-compilation-pdf-qa-2026-09-18.json",
                "contents_page_row_counts": [11, 10],
                "sources": preliminary_sources,
                "build_result": None,
            },
            {
                "compilation_id": "2011_published_program_record",
                "title": "2011 Published General Obligation Bond Program Record",
                "short_title": "2011 Published Program Record",
                "record_label": "Edition / component",
                "source_record_label": "Original City published-program component",
                "date_label": "Edition",
                "coverage_note": "The citywide totals, department schedules, department scopes, and every materially distinct saved initial, December 2010, and April 2011 or later-directory edition supported by the existing provenance decisions.",
                "editorial_note": "Component order is citywide summary followed by department/program groups alphabetically. Within each group, schedules precede scopes and established earlier editions precede later editions. This ordering is for navigation only and does not imply final or adopted precedence.",
                "provenance_note": "Forty-two selected originals are already individually byte-verified in R2. Four distinct December 2010 Cultural Services and Parks and Recreation originals remain approved inventory records with verified City-source checksums but require separate future R2 authorization before this compilation can be published.",
                "preservation_notice": "This is an ABQInfo historical compilation, not a City-issued single document. Each complete City component follows a provenance sheet. Forty-two originals are already separately archived; four verified December 2010 City editions have proposed archive URLs but have not been uploaded.",
                "ordering_rule": "Citywide summary first; department/program groups alphabetically; schedules before scopes; established earlier editions before later editions, without any final/adopted inference.",
                "proposed_filename": "abqinfo-2011-go-bond-published-program-record.pdf",
                "proposed_r2_key": "city-data/capital-spending/abqinfo-2011-go-bond-published-program-record.pdf",
                "local_output_path": "output/pdf/capital-spending/abqinfo-2011-go-bond-published-program-record.pdf",
                "build_validation_path": "project-state/discovery/2011-capital-spending-published-compilation-build-validation-2026-09-18.json",
                "qa_validation_path": "project-state/discovery/2011-capital-spending-published-compilation-pdf-qa-2026-09-18.json",
                "contents_page_row_counts": [7, 7, 7, 7, 7, 7, 4],
                "sources": published_sources,
                "build_result": None,
            },
        ],
        "nonmember_records": nonmembers,
        "future_visible_page_treatment": {
            "capital_spending_page": "After all 67 originals and both compilations have the required individual/public R2 verification, replace the 63 standalone Capital Spending links in the two reviewed sections with exactly two contextual compilation entries. Do not change the page in this preparation task.",
            "visible_master_count": 2,
            "standalone_component_links_on_capital_spending": 0,
            "official_source_context": "Retain links to the two official City collection contexts and explain the preliminary-versus-published distinction.",
            "cross_listings": "Existing topic-page cross-listings remain pointed to the individually archived source that is useful in that topic. They are recorded per component in future_cross_listing_treatment and are not replaced by the broad compilation.",
            "publication_gate": "The four selected December 2010 City editions and both compilation PDFs must first be archived and publicly byte-verified under separate authorization.",
        },
        "capital_spending_page_audit": [
            {"section": "2003-2004 General Obligation Bond Program", "approximate_visible_records": 5, "candidate": False, "finding": "The 2003 family already has an ABQInfo master. The four 2004 Street Bond records are distinct program, amendment, process-summary, and ballot instruments; no additional compilation is justified without a separate 2004 package review."},
            {"section": "2009 General Obligation Bond Program", "approximate_visible_records": 15, "candidate": True, "finding": "Several short departmental scopes and schedules create the same browsing problem, but the section also contains separate bond authorizations and Urban Enhancement records. A future neutral 2009 program compilation should preserve the settled December 2008/June 2009 version distinctions and exclude unrelated instruments."},
            {"section": "Energy, Water, Public Facilities, and System Modernization Bond Scopes", "approximate_visible_records": 26, "candidate": True, "finding": "This heading mixes six cycle-specific energy/water/public-facilities scopes with 2007 and 2009 program summaries and department records. Consolidation may help, but only as multiple provenance-coherent cycle/program families rather than one 26-file master."},
            {"section": "Department Capital Details", "approximate_visible_records": 10, "candidate": True, "finding": "Ten short 2007-2016 department summaries are components of one decade-plan family and are a strong future compilation candidate, preferably joined to the other 2007-2016 summary components after membership review."},
            {"section": "Impact-Fee Component Plans", "approximate_visible_records": 7, "candidate": True, "finding": "The overview and four 2005-2013 component plans form a plausible historical package; the two GO-bond summaries under the same heading are not impact-fee components and should be treated separately. Topic cross-listings may still justify individual source links."},
            {"section": "2007-2016 Decade Plan", "approximate_visible_records": 4, "candidate": False, "finding": "The records are materially distinct storm-sewer/community-facilities scopes and enacted policy resolutions, not a crowded serial component family."},
            {"section": "Complete Program Books", "approximate_visible_records": 6, "candidate": False, "finding": "These are already comprehensive program-level records or materially distinct purpose views; consolidation would reduce clarity."},
            {"section": "Impact Fee Capital Improvement Plan Records", "approximate_visible_records": 3, "candidate": False, "finding": "Two enacted amendments and one later credit-holder summary are distinct legal/current records and should remain individually visible."},
        ],
        "unresolved_questions": [
            "Future R2 authorization is required for four selected December 2010 City editions and the two compilation outputs.",
            "Temporary deployment review is required before the proposed two-entry Capital Spending presentation can replace the 63 current component links.",
        ],
        "visual_inspection": {
            "status": "pending",
            "method": None,
            "pages_reviewed": [],
            "finding": None,
        },
        "safeguards_observed": {
            "r2_mutation": False,
            "capital_spending_page_modified": False,
            "inventory_modified": False,
            "other_family_modified": False,
            "merge_or_deploy": False,
        },
    }
    OUTPUT.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with 21 preliminary and 46 published components")


if __name__ == "__main__":
    main()
