"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-13. The Mid-Region Council of Governments DocumentCenter set.
"""

import collections
import datetime
import glob
import json
import os
import re

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\mrcog-documentcenter-cluster-research-2026-09-13.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\mrcog')

TRANSPO = 'content/transportation/_index.md'
ROADWAY = 'content/transportation/roadway-projects/_index.md'
STUDIES = 'content/transportation/roadway-projects/studies.md'
OPSDATA = 'content/transportation/operations-data.md'
SAFETY = 'content/transportation/safety-crash-data.md'
BIKE = 'content/transportation/bicycling/bike-plans.md'
TRANSIT = 'content/transportation/transit/abq-ride.md'
DESIGNREF = 'content/transportation/design-references.md'
DEMO = 'content/city-data/demographics.md'
CLIMATE = 'content/city-data/climate-environment.md'
AREAPLANS = 'content/development-land-use/area-sector-plans.md'
DEVPROC = 'content/development-land-use/development-process.md'
MAPS = 'content/maps-data/maps.md'

FULL2040 = 'src-d651356cdad0e349'   # Connections 2040 MTP full document, validated with an r2_url
PED2030 = 'src-00edbf1ee3434578'    # MRCOG 2030 MTP Pedestrian Element, validated with an r2_url

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, URL = {}, {}, {}
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    i, c, s, h, mag, raw, final = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag
    URL[i] = raw

SLICE = [l.split('\t')[0] for l in open(os.path.join(SP, 'urls.tsv'), encoding='utf-8')]

PRIOR = set()
for f in glob.glob(r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\*.json'):
    if os.path.abspath(f) == os.path.abspath(OUT):
        continue
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    if not isinstance(d, dict):
        continue
    for b in ('approved_for_addition', 'duplicate', 'superseded', 'requires_human_review', 'excluded'):
        for r in d.get(b) or []:
            if isinstance(r, dict) and r.get('id'):
                PRIOR.add(r['id'])
assert not (set(SLICE) & PRIOR), sorted(set(SLICE) & PRIOR)

CONTAINER = {'25504446': 'PDF', '504b0304': 'OOXML', 'ffd8ffe0': 'JPEG', '0d0a0d0a': 'HTML'}

LC = ("HTTP 200 verified 2026-09-13 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes. "
      "Container verified by leading bytes, not by extension - three records in this lane return HTML despite "
      "sitting under a DocumentCenter path, and one file whose URL slug ends -PDF is a JPEG.")


def title(i):
    return (IDX[i].get('title') or '').strip()


def docnum(i):
    m = re.search(r'/View/(\d+)', URL[i])
    return int(m.group(1)) if m else None


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": CONTAINER[MAGIC[i]], "leading_bytes": MAGIC[i],
         "publisher": "Mid-Region Council of Governments"}
    if docnum(i):
        r["mrcog_document_number"] = docnum(i)
    r.update(M[i])
    return r


# ---------------------------------------------------------------- URL twins
BYHASH = collections.defaultdict(list)
for i in SLICE:
    BYHASH[M[i]['checksum_sha256']].append(i)

URL_TWINS = {}          # bare -> slugged
CROSS_ID_DUP = {}       # copy -> canonical
for h, v in BYHASH.items():
    if len(v) != 2:
        continue
    a, b = v
    na, nb = docnum(a), docnum(b)
    if na == nb:
        bare = a if URL[a].rstrip('/').endswith(str(na)) else b
        slug = b if bare == a else a
        URL_TWINS[bare] = slug
    else:
        lo, hi = (a, b) if (na or 0) < (nb or 0) else (b, a)
        CROSS_ID_DUP[hi] = lo

INDEX_PAGES = [i for i in SLICE if MAGIC[i] == '0d0a0d0a']

C2040_PARTS = ['src-e8199f46117036ea', 'src-1bf2536a93473437', 'src-143f1db147b19cb8', 'src-f034cd622ebbfc5e',
               'src-fdd0c18070add4ac', 'src-6c40ac1b6d84a381', 'src-64f908e03def4c17', 'src-d702f6086f192aed',
               'src-b560646871dfde9f', 'src-4386ba18e2709210', 'src-d31fc6e10c5abacf']

MTP2030 = ['src-a1f621d5eb91c420', 'src-90c5665545b9991e', 'src-84c4dd82cc737bb3', 'src-437b8dda846d4989',
           'src-46ac5779e0d7ff15', 'src-2fa9c37bc0cc1e2e', 'src-122524ebaecabdfe', 'src-b1dd650fabc9c406',
           'src-1b4f9fe87a5e6422', 'src-87aecb70fc3cd5b3', 'src-d0e8e7bc436424a7', 'src-77a504c84cffee27',
           'src-d8b7b5acf48f4b5b', 'src-ffd9bf769ec5eec3']

C2040_APPENDIX = {'src-55a8e87de2bd9c0c': 'F', 'src-7a90167f2ad9a83e': 'H',
                  'src-c58ea51f5773870b': 'J', 'src-a3654251040b0e8f': 'K'}

JURISDICTION_PLANS = ['src-3f2c545431e92ccf', 'src-4ac298fa08915be0', 'src-e32a53bd7c0f75da', 'src-7f4153f5f4410382',
                      'src-c0a43352ee9019d3', 'src-87be309995431a1b', 'src-eaaf848105f8ebe6', 'src-6e8c3298d040c3ad',
                      'src-ae49b4a8f31c9095', 'src-6718ebc5cd6e3080', 'src-65d660d2d2eb926a', 'src-1e75dd14b75fb520']

# group assignment for everything else
CMP = ['src-4cf5a76755a10649', 'src-626c4fe29594ef93', 'src-7ce916875ee7f34d', 'src-593e66c54f094b9e',
       'src-6f6b92cc874357f3', 'src-7fb03c21b5865567', 'src-dbbf53edc60f2575', 'src-f37001702294a0ff',
       'src-af4390a0e3f55e39', 'src-e4a3db937cacced8', 'src-7fb3fb614466759b', 'src-592a83e48d7489d9',
       'src-b9f68064d83c5038', 'src-d5e398345f6eec6b', 'src-cecbd18d97a13794', 'src-ba0a4030fcc63e6e']

FORMS = ['src-ed40148d74571564', 'src-606ceff8ec912ce2', 'src-99d89b03829df2bb', 'src-c4fac6267f953c60',
         'src-71fa5f5fce3711e5', 'src-bce376528f3a3ada', 'src-34ee4b2c84a342d8', 'src-384dded430f29489',
         'src-3baada7c229ec6f7', 'src-b2269aea55f5f21f', 'src-57681c0da369110b']

TARGETS = ['src-a0c6e7c7373f96e9', 'src-847128e19ed57c31', 'src-723506be046c2a25', 'src-ccc675d20b2e7b79',
           'src-ec0b0407d09f87f9', 'src-d48a6f2fcde56ce0']

RESOLUTIONS = ['src-880f10ac96b754dd', 'src-99a8c847c0ec87c8', 'src-12bdf1e9036ee327', 'src-b94bb22557b167e3',
               'src-c19104a123d87ad1', 'src-4c9f1c66d314608a', 'src-f9b2e06b5c9647dd']

GOVERNANCE = ['src-f25dc11c3d8b673b', 'src-20c3f514e7895774', 'src-9a6ccd270761d9bf', 'src-77aae725936eb26c',
              'src-6ec8b354bc98031c']

GROUP_PAGE = {
 "congestion management process": (STUDIES, [{"page": OPSDATA, "reason": "Corridor congestion measurement."}]),
 "2030 Metropolitan Transportation Plan": (TRANSPO, [{"page": ROADWAY, "reason": "The plan that programmes the region's roadway work."}]),
 "Connections 2040 appendices": (TRANSPO, [{"page": STUDIES, "reason": "Methodology and sources behind the plan's analysis."}]),
 "programme forms and guides": (DEVPROC, [{"page": TRANSPO, "reason": "The application route for regional transportation funding."}]),
 "federal performance targets": (SAFETY, [{"page": OPSDATA, "reason": "The measured basis of the targets."}]),
 "resolutions and conformity": (TRANSPO, [{"page": CLIMATE, "reason": "Air quality conformity is an environmental determination."}]),
 "agency governance": (TRANSPO, []),
 "analyses, surveys and charts": (OPSDATA, [{"page": STUDIES, "reason": "Regional travel analysis."}]),
}

GROUP_FRAME = {
 "congestion management process": ("The Mid-Region Council of Governments' congestion management record: %s, part of the "
                                   "series by which the region measures where its corridors are congested and what it "
                                   "proposes to do about it."),
 "2030 Metropolitan Transportation Plan": ("The %s element of the Mid-Region Council of Governments' 2030 Metropolitan "
                                           "Transportation Plan, one of the fourteen numbered elements in which the "
                                           "adopted regional plan was published."),
 "Connections 2040 appendices": ("Appendix %s to the Connections 2040 Metropolitan Transportation Plan, the adopted "
                                 "regional plan for the Albuquerque metropolitan planning area, supplying supporting "
                                 "material the plan itself refers to."),
 "programme forms and guides": ("The Mid-Region Council of Governments' %s, part of the paperwork by which local "
                                "governments apply for and account for federal transportation money distributed "
                                "through the regional planning organisation."),
 "federal performance targets": ("The Mid-Region Council of Governments' %s, part of the federal performance "
                                 "management regime under which the region sets targets for its transportation "
                                 "system and reports progress against them."),
 "resolutions and conformity": ("The Mid-Region Council of Governments' %s, a formal act of the regional board or a "
                                "determination made on the record about the region's transportation programme."),
 "agency governance": ("The Mid-Region Council of Governments' %s, recording how the regional planning organisation "
                       "is run, who sits on it, or what it has committed to do."),
 "analyses, surveys and charts": ("The Mid-Region Council of Governments' %s, a measured account of how the "
                                  "Albuquerque region actually travels, published as regional transportation "
                                  "evidence."),
}

assigned = {}
for i in CMP:
    assigned[i] = "congestion management process"
for i in MTP2030:
    assigned[i] = "2030 Metropolitan Transportation Plan"
for i in C2040_APPENDIX:
    assigned[i] = "Connections 2040 appendices"
for i in FORMS:
    assigned[i] = "programme forms and guides"
for i in TARGETS:
    assigned[i] = "federal performance targets"
for i in RESOLUTIONS:
    assigned[i] = "resolutions and conformity"
for i in GOVERNANCE:
    assigned[i] = "agency governance"

HANDLED = set(INDEX_PAGES) | set(URL_TWINS) | set(CROSS_ID_DUP) | set(C2040_PARTS) | set(JURISDICTION_PLANS)
for i in SLICE:
    if i in HANDLED or i in assigned:
        continue
    assigned[i] = "analyses, surveys and charts"

approved, duplicate, rhr, excluded = [], [], [], []

MTP2030_NAME = {
 'src-a1f621d5eb91c420': 'table of contents', 'src-90c5665545b9991e': 'introduction',
 'src-84c4dd82cc737bb3': 'our metro area today and tomorrow', 'src-437b8dda846d4989': 'transportation challenges',
 'src-46ac5779e0d7ff15': 'mission and goals', 'src-2fa9c37bc0cc1e2e': 'roadways',
 'src-122524ebaecabdfe': 'public transportation', 'src-b1dd650fabc9c406': 'bicycle',
 'src-1b4f9fe87a5e6422': 'transportation systems management and operations',
 'src-87aecb70fc3cd5b3': 'freight and commercial goods', 'src-d0e8e7bc436424a7': 'safety',
 'src-77a504c84cffee27': 'transportation security',
 'src-d8b7b5acf48f4b5b': 'evaluation of the transportation system',
 'src-ffd9bf769ec5eec3': 'public participation',
}

for i in SLICE:
    if i in HANDLED:
        continue
    g = assigned[i]
    canon, cross = GROUP_PAGE[g]
    if g == "2030 Metropolitan Transportation Plan":
        subject = MTP2030_NAME[i]
        t = "MRCOG 2030 Metropolitan Transportation Plan: %s" % title(i).replace(' (PDF)', '')
        ev = ("Published at DocumentCenter/View/%d as %s. Its running head is set in a display font whose "
              "text layer is shifted one character position, extracting as .FUSPQPMJUBO5SBOTQPSUBUJPO1MBO and "
              "decoding to Metropolitan Transportation Plan."
              % (docnum(i), os.path.basename(URL[i])))
    elif g == "Connections 2040 appendices":
        subject = C2040_APPENDIX[i]
        t = "Connections 2040 Appendix %s: %s" % (subject, title(i).replace(' (PDF)', '').split('- ', 1)[-1].replace('Appendix %s ' % subject, ''))
        ev = ("Headed Appendix %s on its own first page and naming Connections 2040 in its text. Tested against the "
              "archived full plan: token coverage %s and not one contiguous fifty-word run present, so it is not "
              "bound into the document the archive already holds."
              % (subject, {'F': '0.9220', 'H': '0.8447', 'J': '0.8800', 'K': '0.9622'}[subject]))
    else:
        subject = title(i).replace(' (PDF)', '').replace(' (DOCX)', '').replace(' (JPG)', '')
        t = subject
        ev = "Published by the Mid-Region Council of Governments at DocumentCenter/View/%d as %s." % (
            docnum(i), os.path.basename(URL[i]))
    desc = GROUP_FRAME[g] % subject
    words = desc.split()
    if len(words) > 50:
        desc = ' '.join(words[:48]).rstrip(',.;') + '.'
    r = row(i, "approved for addition")
    r.update({"title": t, "description": desc, "evidence": ev, "group": g,
              "proposed_canonical_page": canon, "cross_listings": cross,
              "description_word_count": len(desc.split())})
    if g == "2030 Metropolitan Transportation Plan":
        r["completes_record"] = PED2030
    if g == "Connections 2040 appendices":
        r["completes_record"] = FULL2040
    approved.append(r)

# ------------------------------------------------------------------ duplicate
for bare, slug in sorted(URL_TWINS.items()):
    r = row(bare, "duplicate")
    r.update({"canonical_id": slug,
              "title_for_reference": "DocumentCenter/View/%d, bare form" % docnum(bare),
              "relationship": "The same object as its canonical, reached by the DocumentCenter id without the document slug.",
              "how_it_was_established": ("Byte-identical: both return %s bytes with the same SHA-256. The publisher "
                                         "serves one document at two URL shapes, /View/<id> and /View/<id>/<Slug>."
                                         % format(M[bare]['size_bytes'], ',')),
              "why_this_one_is_the_copy": "The slugged form names the document; the bare form is an opaque id. Archive the form that says what it is.",
              "group": "url twins"})
    duplicate.append(r)

for copy, canon in sorted(CROSS_ID_DUP.items()):
    r = row(copy, "duplicate")
    r.update({"canonical_id": canon,
              "title_for_reference": title(copy) + ", second publication",
              "relationship": "The same file published twice under two different DocumentCenter ids.",
              "how_it_was_established": ("Byte-identical: %s bytes and the same SHA-256 at /View/%d and /View/%d. "
                                         "Unlike the eleven URL twins, these are genuinely two document records for "
                                         "one file."
                                         % (format(M[copy]['size_bytes'], ','), docnum(canon), docnum(copy))),
              "why_this_one_is_the_copy": "The lower document number is the original publication.",
              "group": "url twins"})
    duplicate.append(r)

C2040_LABEL = {
 'src-e8199f46117036ea': 'Chapter 1: Introduction', 'src-1bf2536a93473437': 'Chapter 2: Current and Future State of the Region',
 'src-143f1db147b19cb8': 'Chapter 3: The Target Scenario', 'src-f034cd622ebbfc5e': 'Chapter 4: Optimized Mobility',
 'src-fdd0c18070add4ac': 'Chapter 5: Active Transportation', 'src-6c40ac1b6d84a381': 'Chapter 6: Economic Linkages',
 'src-64f908e03def4c17': 'Chapter 7: Environmental Resiliency', 'src-d702f6086f192aed': 'Chapter 8: Financial Analysis',
 'src-b560646871dfde9f': 'Chapter 9: Plan Implementation and Evaluation',
 'src-4386ba18e2709210': 'Executive Summary', 'src-d31fc6e10c5abacf': 'Cover and Table of Contents',
}
C2040_COV = {'src-4386ba18e2709210': '0.9990'}
for i in C2040_PARTS:
    r = row(i, "duplicate")
    r.update({"canonical_id": FULL2040,
              "title_for_reference": "Connections 2040 MTP, " + C2040_LABEL[i],
              "relationship": ("A part of the Connections 2040 Metropolitan Transportation Plan, which the archive "
                               "already holds in full, validated with an r2_url, as " + FULL2040 + "."),
              "how_it_was_established": ("The archived full document was fetched - 59,514,796 bytes, 348 pages - and "
                                         "its text compared with this part's. Token coverage %s, and three separate "
                                         "sixty-word contiguous runs taken from this part appear verbatim in the full "
                                         "plan. It is bound into the document the archive holds."
                                         % C2040_COV.get(i, '1.0000')),
              "why_this_one_is_the_copy": "The archive holds the whole plan. A chapter of it adds nothing and would be archived twice.",
              "group": "Connections 2040 parts"})
    duplicate.append(r)

# ---------------------------------------------------- requires human review
for n, i in enumerate(JURISDICTION_PLANS, 1):
    r = row(i, "requires human review")
    r.update({"draft_title": title(i).replace(' (PDF)', ''),
              "question_for_human": "Decide whether this archive holds other jurisdictions' comprehensive plans.",
              "why_not_decided_here": ("It is a comprehensive or growth plan for a municipality or county in the "
                                       "region that is not Albuquerque, hosted by the regional planning organisation "
                                       "because the region publishes its members' plans. The archive's existing "
                                       "MRCOG holdings - 117 validated records - are regional analyses, regional "
                                       "plans and regional data, not other towns' comprehensive plans. Whether the "
                                       "scope extends to them is a question about what this archive is for, not a "
                                       "question about the document."),
              "measurement": "Born-digital PDF, %s bytes, at DocumentCenter/View/%d." % (
                  format(M[i]['size_bytes'], ','), docnum(i)),
              "distinguishing_content": title(i).replace(' (PDF)', ''),
              "package": "member_jurisdiction_comprehensive_plans",
              "priority": n})
    rhr.append(r)

# ------------------------------------------------------------------- excluded
for i in INDEX_PAGES:
    r = row(i, "excluded")
    r.update({"title_for_reference": "DocumentCenter Index page: " + title(i),
              "what_it_is": "A folder listing page in the publisher's document centre.",
              "exclusion_reason": ("Not a document. Despite sitting under a DocumentCenter path the URL returns an "
                                   "HTML page - the fetched bytes begin with blank lines and then <!DOCTYPE html>, "
                                   "which is why the leading-bytes check reads 0d0a0d0a rather than a document "
                                   "signature. It is the index of a folder, not anything in it."),
              "category": "directory listing, not a document",
              "package": "not_a_document"})
    excluded.append(r)

rows = approved + duplicate + rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids)), [k for k, v in collections.Counter(ids).items() if v > 1]
assert set(ids) == set(SLICE), (sorted(set(SLICE) - set(ids))[:8], sorted(set(ids) - set(SLICE))[:8])
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
dup_bytes = sum(r["size_bytes"] for r in duplicate)
bygroup = collections.Counter(r["group"] for r in approved)
bycontainer = collections.Counter(r["content_kind"] for r in rows)

artifact = {
 "batch_id": "mrcog-documentcenter-cluster-research-2026-09-13",
 "lane": "Claude research lane: the Mid-Region Council of Governments DocumentCenter set",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-13.",
 "cluster": ("Everything still uncovered under www.mrcog-nm.gov/DocumentCenter: two metropolitan transportation "
             "plans published in parts, a six-cycle congestion management series, the region's federal performance "
             "reporting, its funding application paperwork, its members' comprehensive plans, and a long run of "
             "regional travel analyses."),
 "scope": "All 119 uncovered candidates in the tree. The coverage gate is asserted in the generator.",
 "brief": ("These are a partner agency's records rather than the City's, so establish for each whether MRCOG is the "
           "authoritative publisher and whether the City adopted or merely received it, and apply the third-party "
           "rule already recorded for USDA-NRCS, NMAC and PNM."),
 "the_brief_was_wrong_and_the_inventory_says_so": {
  "what_the_brief_assumed": ("That MRCOG material should be tested against the third-party rule that excluded the "
                             "USDA-NRCS soil loss note, the NMAC contractor licensing rule and the PNM streetlighting "
                             "tariff: not a City record, authoritative publisher elsewhere, cite rather than "
                             "archive."),
  "what_is_actually_true": ("The archive already holds 117 validated MRCOG records, most of them with an r2_url, and "
                            "publishes them across ten content pages including demographics, maps, dashboards, "
                            "design references, operations data, safety and crash data, speed management, studies, "
                            "bike maps and zoning. MRCOG is not a third party to this archive; it is the region's "
                            "metropolitan planning organisation and the archive treats it as in scope."),
  "why_the_distinction_holds": ("USDA-NRCS, NMAC and PNM publish material the City merely relies on. MRCOG publishes "
                                "the adopted regional plans that govern how federal transportation money reaches "
                                "Albuquerque streets. The rule was never about who else publishes a document; it was "
                                "about whether the document is a record of governance here."),
  "what_changed_as_a_result": "Nothing in this lane is excluded on third-party grounds. The only exclusions are three folder listing pages.",
 },
 "two_plans_held_two_different_ways": {
  "the_finding": ("Both metropolitan transportation plans in this lane are published as parts. The archive holds one "
                  "of them whole and the other almost not at all, and the correct recommendation is opposite in each "
                  "case."),
  "connections_2040": {
   "what_the_archive_holds": ("The full document, %s, validated with an r2_url: 59,514,796 bytes, 348 pages. Plus "
                              "appendices A, B, C, D, E, G and I, each validated with an r2_url." % FULL2040),
   "what_this_lane_found": "Chapters 1 to 9, the Executive Summary, and the Cover and Table of Contents, published separately.",
   "the_test": ("Each part was compared against the full document twice over: token coverage, and whether three "
                "separate sixty-word contiguous runs from the part appear verbatim in the plan. Every one of the "
                "eleven returned coverage 1.0000 - the Executive Summary 0.9990 - with three runs out of three "
                "present."),
   "the_decision": "All eleven recommended duplicate. They are bound into a document the archive already has.",
   "what_it_saves": "%s bytes of redundant archive footprint, and eleven records that would have been archived twice." % format(sum(M[i]['size_bytes'] for i in C2040_PARTS), ','),
   "and_four_that_are_not": ("Appendices F, H, J and K are also in this lane and are recommended for addition, not as "
                             "duplicates. Coverage against the full plan runs 0.8447 to 0.9622 and not one "
                             "contiguous fifty-word run is present in any of them. They are not bound in. With the "
                             "seven the archive holds they complete the appendix set A to K."),
  },
  "the_2030_plan": {
   "what_the_archive_holds": "One element: the Pedestrian Element, %s, validated with an r2_url." % PED2030,
   "what_this_lane_found": ("The other fourteen. The plan is published as a table of contents plus numbered elements "
                            "1 to 14 at DocumentCenter/View/2254 to 2268, and the archive holds only 2262. This lane "
                            "supplies 2254 through 2261 and 2263 through 2268."),
   "the_decision": "All fourteen recommended for addition. Together with the element already held they are the whole plan.",
   "no_full_document_exists": "Unlike Connections 2040, this plan has no single full-document publication in the set; the elements are how it exists.",
  },
  "the_lesson_the_pair_teaches": ("Coverage alone cannot tell a bound-in chapter from a companion appendix. The "
                                  "appendices score up to 0.9622 coverage and are not in the plan; the chapters score "
                                  "1.0000 and are. What separates them is whether a long contiguous run of the part's "
                                  "own words appears verbatim in the parent. **Test containment with a contiguous run, "
                                  "not with a token set.**"),
 },
 "a_text_layer_that_is_enciphered": {
  "what_was_found": ("All fourteen 2030 plan elements carry a running head set in a display font whose text layer "
                     "is shifted one character position: it extracts as .FUSPQPMJUBO5SBOTQPSUBUJPO1MBO, each letter "
                     "one higher than the letter shown, decoding to Metropolitan Transportation Plan. Body text in "
                     "the same files extracts normally; it is the display font that is shifted."),
  "why_it_matters": ("In eleven of the fourteen the plan's name is nowhere in the extracted text in readable form "
                     "- only three repeat it in body prose. A pass that searched text for the plan's name would "
                     "therefore miss eleven of its own elements, and a pass that titled any element from its "
                     "running head would produce nonsense. The measurement is exact: 14 of 14 carry the shifted "
                     "running head, 3 of 14 also state the name readably, 11 do not state it readably anywhere."),
  "how_they_were_identified": ("By their DocumentCenter numbering, which runs consecutively with the element the "
                               "archive already holds, and by decoding the shift. The Mission and Goals element, "
                               "decoded, states that the 2030 MTP is the defining vision for the metropolitan area's "
                               "transportation systems."),
  "the_family_this_belongs_to": ("The run has now met three ways a document can hide from text search: no text "
                                 "layer at all, as in the scanned ordinances; a thin text layer that omits the title "
                                 "block, as in the solar reports; and now a text layer that is present and complete "
                                 "but whose headings are systematically wrong."),
 },
 "the_url_twins": {
  "count": len(URL_TWINS),
  "what_they_are": ("The publisher serves each document at two URL shapes, /View/<id> and /View/<id>/<Slug>, and the "
                    "crawl captured both for eleven documents. Byte-identical in every case."),
  "the_canonical_rule": "The slugged form is canonical: it names the document, the bare form is an opaque id.",
  "one_that_is_not_a_url_twin": ("Project-Feasibility-Form-PFF-DOCX is served at /View/6498 and /View/6504 - two "
                                 "different document records for one 59,280-byte file. That is a genuine duplicate "
                                 "publication, not a URL shape."),
  "a_slug_that_lies": ("2014-CMP-Corridor-Rankings-Map-JPG is registered in the inventory with the title 2014 CMP "
                       "Corridor Rankings Map (PDF). Its leading bytes are ffd8ffe0: it is a JPEG. The title is "
                       "wrong and the slug is right, and only the bytes settle it."),
  "another_slug_that_lies": ("/View/2062/2014-CMP-Strategies-Matrix-PDF is registered with the title 2016 CMP "
                             "Strategies Matrix (PDF), while its URL twin at /View/2062 is registered as 2014. Same "
                             "bytes, two different years claimed. The 2014 reading is recommended because it is what "
                             "the publisher's own slug says; flagged for integration."),
 },
 "method": ("Fetched all 119 candidates and measured byte length, SHA-256 and leading bytes from the fetched bytes. "
            "Grouped by checksum, then separated URL-shape twins from genuine cross-id duplicates by comparing "
            "document numbers. Extracted text with the right reader for each container. Fetched the archived "
            "Connections 2040 full document, 59.5 MB and 348 pages, and tested every candidate part against it with "
            "token coverage and a three-point contiguous-run test. Matched the 2030 plan elements by their "
            "consecutive DocumentCenter numbering against the element the archive already holds, and decoded their "
            "shifted text layer to confirm the plan they belong to. Checked the whole lane against the 117 validated "
            "MRCOG records the archive already holds."),
 "classification_only": True,
 "shared_state_written": [],
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds, against the published site, and against anything recommended earlier in the same batch.",
  "cross_inventory_byte_collisions": 0,
  "internal_byte_collisions": len(URL_TWINS) + len(CROSS_ID_DUP),
  "containment_tests_against_an_archived_parent": 16,
  "parts_found_to_be_inside_an_archived_document": len(C2040_PARTS),
  "result": ("Eleven candidates are inside a document the archive already holds and are recommended duplicate. "
             "Nothing else in the lane duplicates the archive."),
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": len(URL_TWINS) + len(CROSS_ID_DUP),
  "cross_inventory_byte_collisions": 0,
  "url_collisions_in_this_slice": len(URL_TWINS),
  "checksums_compared_against": 1612,
  "relationships_found": len(duplicate),
  "found_by": ("Twelve by byte hashing, eleven by containment testing against an archived parent that hashing could "
               "not reach."),
  "note": ("The eleven containment duplicates are the important half. No hash comparison could have found them: they "
           "are different files with different bytes, and the relationship is that one is printed inside the other."),
 },
 "integration_flags": [
  {"severity": "scope-correction",
   "affects": [],
   "finding": "This lane's brief assumed MRCOG material should be tested against the third-party rule. The inventory contradicts that: the archive already holds 117 validated MRCOG records with r2_urls and publishes them across ten content pages. MRCOG is the region's metropolitan planning organisation, not a third party.",
   "recommended_action": "Record the distinction: the third-party rule is about whether a document is a record of governance here, not about who else publishes it."},
  {"severity": "avoids-duplicate-archival",
   "affects": C2040_PARTS,
   "finding": f"Eleven Connections 2040 parts - nine chapters, the Executive Summary and the Cover and Table of Contents - are bound into the 348-page full plan the archive already holds validated with an r2_url. Coverage 1.0000 and three of three contiguous sixty-word runs present verbatim for every one.",
   "recommended_action": f"Apply duplicate with canonical {FULL2040}. This avoids {format(sum(M[i]['size_bytes'] for i in C2040_PARTS), ',')} bytes of redundant archival."},
  {"severity": "completes-an-archived-record",
   "affects": MTP2030,
   "finding": f"The MRCOG 2030 Metropolitan Transportation Plan is published as a table of contents plus fourteen numbered elements at DocumentCenter/View/2254-2268. The archive holds exactly one of them, the Pedestrian Element ({PED2030}). This lane supplies the other fourteen.",
   "recommended_action": "Approve all fourteen and publish them as one plan with the element already held."},
  {"severity": "completes-an-archived-record",
   "affects": sorted(C2040_APPENDIX),
   "finding": "Connections 2040 appendices F, H, J and K, which are not bound into the full plan - coverage 0.8447 to 0.9622 with no contiguous run present. With appendices A, B, C, D, E, G and I already validated and archived, these complete the set A to K.",
   "recommended_action": "Approve. Publish under the plan's entry alongside the seven already held."},
  {"severity": "extraction-trap",
   "affects": MTP2030,
   "finding": "All fourteen 2030 plan elements carry a running head whose text layer is shifted one character by the embedded display font, extracting as .FUSPQPMJUBO5SBOTQPSUBUJPO1MBO. In eleven of the fourteen the plan's name appears nowhere in readable extracted text; only three repeat it in body prose.",
   "recommended_action": "Title these from this artifact, not from their text. Any future full-text index over the archive should decode them or index the rendered page instead."},
  {"severity": "title-from-the-bytes",
   "affects": ['src-af4390a0e3f55e39', 'src-4f9236689bfbc235'],
   "finding": "2014 CMP Corridor Rankings Map is registered in the inventory as a PDF and is a JPEG, leading bytes ffd8ffe0. The publisher's own URL slug says JPG.",
   "recommended_action": "Correct the content kind from the bytes."},
  {"severity": "judgment-needed",
   "affects": JURISDICTION_PLANS,
   "finding": "Twelve comprehensive and growth plans for other jurisdictions in the region - Belen, Moriarty, Bernalillo, Edgewood, Peralta, Bosque Farms, Corrales and Valencia County - hosted by MRCOG because the region publishes its members' plans.",
   "recommended_action": "Decide whether this archive's scope extends to other jurisdictions' comprehensive plans. The existing MRCOG holdings are regional analyses and regional plans, not member towns' comprehensive plans."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "requires_human_review": counts["requires human review"],
  "excluded": counts["excluded"],
  "approved_by_group": dict(bygroup),
  "containers": dict(bycontainer),
 },
 "link_check": {"checked": len(rows), "http_200": len(rows), "failed": 0,
                "http_200_but_not_a_document": len(INDEX_PAGES),
                "method": "Full HTTP GET with a browser user agent, 2026-09-13.",
                "additional_fetches": "The archived Connections 2040 full document, 59,514,796 bytes, fetched for the containment tests.",
                "containers_verified": ("%d PDFs, %d OOXML files, %d JPEG and %d HTML pages by leading bytes."
                                        % (bycontainer['PDF'], bycontainer['OOXML'], bycontainer['JPEG'],
                                           bycontainer['HTML']))},
 "approved_for_addition": approved,
 "duplicate": duplicate,
 "requires_human_review": rhr,
 "excluded": excluded,
 "archival_note": (f"All {len(approved)} approved records are inventory-only until an R2 archive object exists for "
                   f"each and its public download, exact size, SHA-256, and authoritative-source provenance are "
                   f"verified. Combined archive footprint if authorized: {approved_bytes:,} bytes. The "
                   f"{len(duplicate)} duplicate records, {dup_bytes:,} bytes, must not be archived: eleven of them "
                   f"are already inside a document the archive holds. Six approved records are OOXML and should be "
                   f"archived in their original format. One is a JPEG despite an inventory title calling it a PDF."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                     "scripts/project/Update-Candidate.ps1 only. Twenty-three rows carry a canonical_id. Twelve of "
                     "those canonicals are rows in this artifact; eleven point at " + FULL2040 + ", a record already "
                     "validated and archived, which is deliberate - a part cannot be canonical over the whole it is "
                     "printed in. Every approved row carries a group and a publisher. Rows completing an archived "
                     "plan carry completes_record naming it. Every row carries a leading_bytes field and, where the "
                     "URL has one, the publisher's document number. Sizes and checksums are first measurements; the "
                     "inventory held none."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the archived full plan was fetched read-only and its inventory record was not touched"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items()
                                            if k not in ('approved_by_group', 'containers')}}))
