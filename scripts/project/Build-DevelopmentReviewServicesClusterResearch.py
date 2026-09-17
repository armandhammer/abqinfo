"""Claude research lane. Reads the inventory and the measurements taken in this
lane, and writes one dated decision artifact. It never modifies
master-inventory.json, checkpoint.json, r2-inventory.json, site content, or R2.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\development-review-services-cluster-research-2026-09-11.json'
B = 'https://documents.cabq.gov/planning/DevelopmentReviewServices/'

SW = 'content/public-works/stormwater-drainage.md'
DP = 'content/development-land-use/development-process.md'
DR = 'content/transportation/design-references.md'
ZO = 'content/development-land-use/zoning-ido.md'
CS = 'content/city-data/capital-spending.md'

LC = 'HTTP 200 verified 2026-09-11 by full GET; size_bytes and checksum_sha256 were measured from the fetched bytes, because the inventory record carried neither'

# SHA-256 computed 2026-09-11 from the bytes fetched from the authoritative URL.
SHA = {
 "src-06fe0a94cdb2ceeb": "8166825c27ecbc5664e6c9fe82e84db515ea051fb87db10fe204dfec4975c04d",
 "src-1117f6aa1effc9ba": "576f1c84611bc25685114b176282645e4a9ee90fb2c6ec192114751f44091326",
 "src-120125d544532b6c": "41113a2bc58f429050f7170efa2b318a67c66c7eb409854c6fd7e3384c12ca73",
 "src-12d5f6e535249d36": "cb3a21bb3461fc91c4e4f7ae0c857ab3a43fcde7e69c5c8a707fb49a51858028",
 "src-150a847f768d749c": "ce477770d0f570293185c2804b5eb133a7e516f8cc8f80b631f9a09ad1b59dea",
 "src-16030da9139693a5": "2ff39ecc1b4544887796bd76e2f919f0a5df47f182c73085b455556e7c1f9907",
 "src-173637dbd07d166f": "15c9dcdbaab7056fe6ea31cc7006f26376e5a6c9d12468f616812553f74c0cf3",
 "src-1edca04e692d021b": "682c5a159e22903e420c27c7754835641844e8a0a81964bb3bfd44fc50cfd174",
 "src-28372ac121eeb0ba": "b8801ce51b57824b36dfeff0ac23a1a81cead30e2a233ccfdf261159087ca5eb",
 "src-2a7170649600ab1b": "92bd4547f5b11c15181e3c94ebdfe60f39b88a3a70e3b4881348e688e662a923",
 "src-2ccd686e55fb1c6e": "3e62bac436863cd720000fa30eaffa1bb7c9c0b7585c343a8a812d690819f302",
 "src-3132dbea44692eec": "848994f00127e4b7b6a92617f5757b8bf228fefed958c8b45f6a2840e385a3f1",
 "src-37c74c1b6b006da9": "e2e24cb25df998b5ef0b1f1c483d0af31cab0389d95158ba2e649f98749198bd",
 "src-3b802b7b341e7d24": "88a14e2fc856181f1126b3cccc66f4e25cb456b20e5045dd591cfefadc1cdec5",
 "src-3bbc15d1914fdad8": "95a3621232f1835899d8c212b20585a3606eb3d5e5e4aa13af4f7c22b9bf5406",
 "src-3c9b9a33f62bd684": "78639f086cfa682f520b7a7ca74dadf380806b0682c7299140820a4644d88eeb",
 "src-3ef55b4cf4a16bd2": "caaba89db59af4933a80c8d36ce9aa66b9bd360b27f15cd35f5fe68fafb9a088",
 "src-42070e2d53434fef": "e05aa6472038627a201ff4b52b0eb573418f3fbf9fa9784cafb47b9196644f7d",
 "src-47e9397facd6b28e": "ece9b1781c4b2676cea77f0b159090dd115cdeb0eb11516698cc144dc845222f",
 "src-49533d311cc95fe9": "6e35f9eb0b7dc6c4397d466c34999d895b9bdfa0a68cad08ef6575fa0c11bbf5",
 "src-49f0ae4d1fedee2a": "04eadf92e6e7b2507b654a5c10f4bfe16893c8beec149d2d95e2b593d99e030c",
 "src-4ea2b255ae80bbcc": "d0cd5141820ef1dd08fd4ae2bdc0dd4348613e3a019193b9cb220a3d20690f39",
 "src-51c3680d973e10d6": "e29ff0855d904662d620b29e55aae6e040062b4614f413fba993a623b9cd8a99",
 "src-53f3375a9829dc10": "0c4f71cc299bd1ea575508eee79522659342a5d9a4f88f3d3e8c6d83dde7a430",
 "src-567244356665a527": "33bf90a36d4c5024cdd42f62705274492f65a6a452c7bf68e293ecc664d0a0e8",
 "src-57c8271474f540b9": "baea288211d8dcdca422cf04c2d36f467bc1bac4aa79c163bba1db40103daf56",
 "src-5e74a3b59f6ef58f": "0cb67120dc2f205c0ee8c3f42942f28e818b43e60d4acf9d219634a24d00b66e",
 "src-64ad8d6862df1b52": "cd5ed50757b69000efb24e39d2307b94f35bcb5a6b5c5a91a26b91aa6db6009d",
 "src-6a1ad16f04f73fbb": "edb40652f45819b9aa35193ad79c874fac0030403f40bb971fa4045d2a913877",
 "src-6cf3784d92bdb096": "197fee938fb36b67f41c12867b9a7cae8634e6c1794237f48b46cb2b23b5a9b2",
 "src-6e87c3ba043d1389": "50867da69981281ab79ca7286a6f5af4ee7b95de6bcea392d1c9335093f39ae4",
 "src-75651a23c90ffb01": "26bb89005e4fe64ae73673a689a4129d0475b18c672965e2e9c034b6a23e015a",
 "src-7600970684c25bea": "12a039432a951801c5a13cf01d33eb369c769fbdec62bcd397dafb3d79add0dc",
 "src-7700b730bdf09a20": "a73ec5781438faa8c707b65b8a2da78a2442f0b3a990ae5a3a02e1140db5462f",
 "src-7c27417fbd191fdf": "d2b6e4465abad0633c3c50c130a7d2cc123af7d4324652817e7fcf73cc25c366",
 "src-7f0d4c4f77185c6f": "b832b8885577c3e0fcced70d284265e3fbdf6a0e6a6f63740bc1b116bb1d036c",
 "src-85425ef5e82d7493": "cffe280cc93949bb2738159281a040243c6ad1e676535ef8ad23e971073fae06",
 "src-873b0267868d115a": "1ecc44536d10ae4775da5d1457369350a8a298d0c485763f0dbe14aa80b1a459",
 "src-878bd0ccb61acb03": "edb40652f45819b9aa35193ad79c874fac0030403f40bb971fa4045d2a913877",
 "src-88f69ed5a5ca0c62": "f3bb3374a11ac28ce70383b8f88902078147df32f19f79e4fe791f2fa56c48da",
 "src-897db84977ca4dbc": "c0c96a3bcbb4fbcc89b7fe14d50406b2955f3bcbacd07e0e425b1204e5c572d8",
 "src-8bc30976a07b48ec": "00afddb1c26cf885b0e5818f7cd181ab5292f73132a3539d9216f936e5866350",
 "src-8d3db8a669ab0f3e": "3f8b6a28c8906b792c5f8c580897b3df35db642ea5805f7fef102a41b4fde203",
 "src-8dd9b882bebaf25e": "287d21caf62c2e7f6d970b40e85991292e6ab686b8d598e63bf132c3e601f6c7",
 "src-8f0894107f8d2c91": "9554c71a2ff2892eb78200dd104814f5c079b8a503cd76327aefee6cb4fff760",
 "src-902641e883401fe8": "70cddea5f45877a90b873d63dc20231e6fef64d073b8f489255b2c719bb6857b",
 "src-9184833c9337a678": "ab0efd50132b04b36c69ee4c91300c3f611d770d3f8c26b19ad68b61fbb4fd24",
 "src-9852cbc3ec84114b": "b11680c541bd2251bbbe2d3eed0be3892efd3e176414a632ffa28eee8b148544",
 "src-98563dab32c38b5c": "fa66ab302187f65371a1aa7f4c6634e67bbde8644722f3ae5982c74d565a3207",
 "src-9b4f21f8f5413c9c": "a59284827cc70b6a88ca10d2710b1680b5f0f0e313d487c2195b7bd4b8cf7d32",
 "src-9e2387f6587cebaa": "caced2b10150962776c7c9aacf46986984200f0d00999d9fe43797ac74877681",
 "src-a066bb85795d81d4": "552f65800d92bc20b0da79e52e3532438c42a9c8b92fde81131f4d8c26f3edf9",
 "src-a1be582c70cb6e9a": "a221916c9e1904d1f60a14e90c250e7602396744a35598a42025e03be8ec9fe0",
 "src-a344172a0fda28e1": "e20edf4b528a010a9e19e9839e5e612c4d073efd1368c919c7e129085a239936",
 "src-aa5007e5f1726a20": "cf1bfba30858f72d557c35332f06140a48ad2e0825b38cf72e17f04f9dc37610",
 "src-ad27cebe79901543": "fd0a038143c803016a9d619d429d4fbbaffaed26d1952845ab8f9a83fcd95faa",
 "src-af234ef141efa037": "b60c6e0402bcf0f2e796e05b133ec8106cfea8a610621b627a27650856cfa673",
 "src-b16ba0152df79e14": "708ba7734a11f6345c64fe13f981f492e8e0ac4ba3fd40cbbb7abf9b4d871a9d",
 "src-b4b360276118a6f3": "ece6307027831e99a8db2395f4fb5a5b41d553f40b0c036a863cc354640bd1eb",
 "src-b4b9d3c500bc8797": "064bfd84b2182708e849fef3b840c18bf878d8268108232cb2f868891d2838f5",
 "src-b5419850966522ad": "b3fe4077574cac39c649970db5ab7725318c2dd120dd787d0383d4004d475bf7",
 "src-bebcf18d811545ae": "7ecdcb77864b2e8ccf6f6c51b16b249c318e9ed9432cdeedab0950a0ce275757",
 "src-bf0ccea6d16d62e1": "5f018421b8bbca130fe495152e89bb4a7aaa16c4c96a76ff3d4a16e86f05093f",
 "src-c0d4f2577674ef0a": "b01db57c1456d75285c1c07db758b8813d13f56da53a673cf748265c14ae8fe1",
 "src-c13b70655151511a": "95f4ba6e377af5d698c13a11038d7e2579b79f3432a19cd5392df42ca41b3eae",
 "src-c647c93bd8561491": "b742856f651f4d08717b244380f115ea8ae105aedbb14c9bd4c2e9cb67bcb5eb",
 "src-ca716d028ed3d575": "cc79e016786548cb2d66a4df71f854174e9f0d4bd164326f5698053d3966b8d8",
 "src-d74108ddea65eb7d": "b3d05ccc954aba6b042d6f08e23c4c3d5be9680a4d20f55dcfe8133ff6d48e8b",
 "src-da3bd2d4d77dbc71": "c857fd4477c8ab60b87e8de67350e2cfa0bc64d9a7e6ef0d93d5b5f6f8a47a3b",
 "src-db74fbcfb6e04b9e": "10374a46901d3fe67238fee4d096a1c112df9b1123acd3d6cb0eaf929464c266",
 "src-e2ff1a4290961461": "738547ff0e0c401061a7ff793bd90074beb08ee37485338f300a290bb1210f20",
 "src-e566c38acdf6409b": "2d1110ecb5a3f463349a8a961275bfe38363c329a70a0da9a099c616ff0cb21a",
 "src-e5b815c2a314724a": "b0878dd3f231113070c5953d222dffe53844d4a462e38888ff4ca9c1dd507050",
 "src-e60c1541be98fd57": "217e273b817a4af443cf652eb33d14de1b2f3565098f02aa8f91fe4d50c189ac",
 "src-ea51f6d14280c5ff": "6658dc3a81aded4fb614b6919446cb71258147c038c375d616e749f95cb62ce0",
 "src-eb52f29134f13a96": "d87636e97dd7ed19c7b7f392148ddfba5588f45c2435f7f4dd4f7de91d418059",
 "src-f0d6744711099a88": "208d542e5a7149eadd56deebdc04222d01d872899c58cbcae236af36522a8362",
 "src-f2f4c53f019ffe80": "6dcc70e6773e9e959ea1d5fa1c2c53f96c4a95eba50ab3e25fa9bcc05c67e3f3",
 "src-f3389ee4d757562d": "951cef9faa3e549bfaa6849b150f8d7b673492942f8cecf80ff71a1c3a30b733",
 "src-fa4cf248a6dd7221": "8d764ac5d9bd56b17f29de279bafc598b1f8ddb5da333319ecb3eb754fdc125a",
 "src-fac9b7369aa53445": "f8acd39c44602a8883040b6fd64ee0b4c4c2adc4e8fbeab5a8eead7edc4c6925"
}



def A(id, file, size, _sha_unused, title, desc, page, pages=None, date=None, date_basis=None,
      why=None, evidence=None, cross=None, kind='PDF'):
    r = {
        "id": id, "file": file, "authoritative_url": B + file,
        "size_bytes": size, "checksum_sha256": SHA[id], "content_kind": kind,
        "link_check": LC, "recommended_status": "approved for addition",
        "title": title, "description": desc,
        "description_word_count": len(desc.split()),
        "proposed_canonical_page": page,
        "cross_listings": cross or [],
    }
    if pages:
        r["pages"] = pages
    if date:
        r["date"] = date
    if date_basis:
        r["date_basis"] = date_basis
    if why:
        r["why_retained"] = why
    if evidence:
        r["evidence"] = evidence
    return r


approved = [
 A("src-d74108ddea65eb7d", "Hydrology-NPDESManual.pdf", 37140337,
   "b1e3c9a0000000000000000000000000000000000000000000000000000000ff",
   "National Pollutant Discharge Elimination System Manual: Storm Water Management Guidelines for Construction and Industrial Activities, Revision 2 (August 2012)",
   "The joint manual of the City, NMDOT, and AMAFCA sets storm water management guidelines for construction and industrial activities in the Albuquerque area, covering permit coverage, pollution prevention plans, best management practices, inspection, and reporting.",
   SW, pages=586, date="2012-08",
   date_basis="The title page reads \"Revision 2 August 2012\".",
   why="The largest and most substantive record in the directory, and the manual the City's own Contractor Affidavit lists as a governing document. Its co-issuers are the New Mexico Department of Transportation, the City of Albuquerque Drainage Section, and the Albuquerque Metropolitan Arroyo Flood Control Authority, so it is the shared regional storm water standard rather than a single department's handout.",
   evidence="586 pages. The inventory already validates a related record, src-64fe15e764b8c334 (NPDES Permit Transitional Update, 2015), on the same page; this is the underlying manual that update refers to."),

 A("src-28372ac121eeb0ba", "Hydro-Bill%20C_S%20O-18-2-Oct-24-18.pdf", 560585,
   "b1e3c9a0000000000000000000000000000000000000000000000000000000ff",
   "Enacted Ordinance O-2018-020: Amending the Drainage Ordinance to Implement Best Practices for Management of New Runoff Associated With Land Development (Council Bill C/S O-18-2)",
   "The enacted City ordinance amends Chapter 14, Article 5, Part 2 of the Revised Ordinances to add stormwater quality purposes, define best management practices, green infrastructure, and the eightieth percentile storm event, and require on-site management of new runoff.",
   SW, pages=21, date="2018",
   date_basis="Rendered and read: the cover sheet carries Council Bill No. C/S O-18-2 and the handwritten Enactment No. O-2018-020, sponsored by Trudy E. Jones.",
   why="An enacted ordinance, not guidance. It is the legal authority behind every erosion, sediment, and stormwater quality requirement elsewhere in this directory, and the inventory holds no other copy of it.",
   evidence="Image-only PDF with no text layer; pages 1 and 2 were rendered and read. Page 1 amends Section 14-5-2-3 Statement of Purpose and Intent to add subsection (F) on stormwater quality; page 2 amends Section 14-5-2-4 Definitions to add BMPs, Construction General Permit, 80th Percentile Storm Event, Erosion and Sediment Control Plan, and GI/LID."),

 A("src-e5b815c2a314724a", "WirelessTelecom-WTRegulations2014.pdf", 591988,
   "b1e3c9a0000000000000000000000000000000000000000000000000000000ff",
   "Enacted Ordinance O-2014-024: Amending the Wireless Telecommunication Regulations and Related Definitions in the Zoning Code (Council Bill F/S O-14-7)",
   "The enacted City ordinance rewrites the Zoning Code wireless telecommunications regulations, replacing the readily visible facility definitions with concealment, collocation, public utility collocation, and free-standing facility definitions, and setting the standards that applied before the Integrated Development Ordinance.",
   ZO, pages=15, date="2014-12-01",
   date_basis="Rendered and read: the transmittal memorandum states the bill \"was passed at the Council meeting of December 1, 2014 by a vote of 9 FOR AND 0 AGAINST\", and the following sheet carries Enactment No. O-2014-024.",
   why="An enacted zoning ordinance with a recorded unanimous vote. It is the legislative source of the codified regulations in src-85425ef5e82d7493, and it is the only record of that amendment anywhere in the inventory.",
   evidence="Image-only PDF, 15 pages, no text layer; pages 1 and 2 were rendered and read. Page 1 is the Council Services transmittal memorandum to Mayor Richard J. Berry; page 2 is the ordinance itself, sponsored by Don Harris and Brad Winter, amending Section 14-16-1-5.",
   cross=[{"page": DP, "reason": "Wireless facility siting is a development-review subject as well as a zoning subject, and the directory this file sits in is the development-review library."}]),

 A("src-85425ef5e82d7493", "WirelessTelecom-Zoning14-6-3-17.pdf", 111696,
   "b1e3c9a0000000000000000000000000000000000000000000000000000000ff",
   "Zoning Code Section 14-16-3-17: Wireless Telecommunications Regulations (pre-Integrated Development Ordinance text)",
   "The codified Albuquerque zoning regulations for wireless telecommunications facilities set concealment requirements, height and setback standards, collocation rules, public utility collocation provisions, application and approval procedures, and abandonment obligations, as they stood before the Integrated Development Ordinance.",
   ZO, pages=8,
   date_basis="No printed date. The text is Zoning Code Part 3 Section 14-16-3-17 as amended by O-2014-024; the sibling staff checklist src-2ccd686e55fb1c6e cites this section at its \"most recent revision effective December 22, 2014\".",
   why="The codified consolidation of the regulations that O-2014-024 enacted, in the form a reader would actually consult. Retaining the enacted ordinance and the resulting code text together is how the inventory already treats adopted legislation elsewhere.",
   evidence="Eight pages of running code text beginning \"PART 3: GENERAL REGULATIONS 14-16-3-17 Wireless Telecommunications Regulations. 3-81\", including subsection (A) Basic Requirements and the concealment rule.",
   cross=[{"page": DP, "reason": "Same reason as the enacting ordinance."}]),

 A("src-db74fbcfb6e04b9e", "DRS-ImpactFees-CCIPLegislation-2016.pdf", 369614,
   "b1e3c9a0000000000000000000000000000000000000000000000000000000ff",
   "Enacted Resolution R-2012-100: Amending the Adopted Component Capital Improvements Plan for Impact Fees, 2012 to 2022 (Council Bill R-12-98)",
   "The enacted City resolution adopts the updated Component Capital Improvements Plan governing how Albuquerque impact fees may be spent for 2012 through 2022, following the impact fee and land use assumption program update prepared by Duncan Associates.",
   CS, pages=7, date="2012",
   date_basis="Rendered and read: Council Bill No. R-12-98, handwritten Enactment No. R-2012-100, Twentieth Council, sponsored by Trudy E. Jones and Brad Winter. See integration_flags: the filename says 2016 and is wrong.",
   why="An enacted resolution that sets the legal list of projects Albuquerque impact fees may fund. Impact fee credits can only be granted against projects on this plan, which makes it the controlling document behind the credit holder summary also retained in this batch.",
   evidence="Image-only PDF, 7 pages; page 1 rendered and read. It recites the State Development Fees Act, records that the CCIP was last amended in F/S R-11-183 with the 2011 General Obligation Bond Capital Program, and adopts the Attachment 1 tables as the CCIP for 2012 to 2022."),

 A("src-f0d6744711099a88", "DRS-ImpactFees-CCIPLegislationAmended-2016.pdf", 267992,
   "b1e3c9a0000000000000000000000000000000000000000000000000000000ff",
   "Enacted Resolution R-2013-115: Amending the Adopted Component Capital Improvements Plan to Restore Unser Boulevard and Escarpment Trail Impact Fee Credits (Council Bill R-13-248)",
   "The enacted City resolution corrects the Component Capital Improvements Plan by restoring two projects inadvertently omitted in the previous update, the Unser Boulevard widening at $782,685.02 and the Petroglyph Escarpment Trail at $56,400, making both eligible for impact fee credits.",
   CS, pages=4, date="2013",
   date_basis="Rendered and read: Council Bill No. R-13-248, handwritten Enactment No. R-2013-115, Twentieth Council, sponsored by Dan Lewis. See integration_flags: the filename says 2016 and is wrong.",
   why="A targeted amendment to the plan adopted in R-2012-100, which it names explicitly. It is not a replacement, so both resolutions are retained and the lineage is recorded rather than one superseding the other.",
   evidence="Image-only PDF, 4 pages; page 1 rendered and read. It recites that the Council last amended the CCIP in R-12-98, that the two projects were inadvertently omitted during the most recent update, and that they were included in the Special Assessment District 228 revenue calculation."),

 A("src-49533d311cc95fe9", "DRS-ImpactFees-CreditHolders-2-18-2020.pdf", 295752,
   "b1e3c9a0000000000000000000000000000000000000000000000000000000ff",
   "Impact Fee Credit Holder Summary, February 18, 2020",
   "The City summary lists every holder of an Albuquerque impact fee credit as of February 18, 2020 by service area code, naming the developer or company and the outstanding credit balance, and marking closed accounts.",
   CS, pages=1, date="2020-02-18",
   date_basis="The sheet's own heading reads \"Credit Holder Summary As Of 02-18-2020\".",
   why="A named-party financial dataset rather than a form: it identifies who holds public impact fee credits and for how much. The code-enforcement lane set the precedent that City data snapshots are retained while forms are not.",
   evidence="Single page listing service area codes such as D-NE-01, D-NW-09, and D-SW-01 against named holders including Llave Development, Capital Alliance, RCS Holdings, JTH, Curb Inc, DR Horton, and Murtagh, with balances up to $1,972,877.00."),

 A("src-16030da9139693a5", "DRC_Jurisdiction.pdf", 21808,
   "b1e3c9a0000000000000000000000000000000000000000000000000000000ff",
   "Design Review and Construction (DRC) Jurisdiction Memorandum, August 25, 2026",
   "The City Planning Department memorandum tells engineers, developers, and contractors exactly which projects require Design Review and Construction plan approval and a City work order, listing twelve triggering thresholds from 500 square feet of new public paving to traffic signal relocation.",
   DP, pages=1, date="2026-08-25",
   date_basis="The memorandum is dated August 25, 2026 on its face.",
   why="The most current record in the directory and a genuine threshold statement: it converts a discretionary-sounding review into twelve measurable triggers. It is signed by the Section Head for Design Review and Construction under Mayor Timothy Keller.",
   evidence="One page. Twelve numbered conditions, including new paving of 500 square feet or more in public right-of-way, 800 feet or more of sidewalk, any curb and gutter unless excepted, and addition or eradication of pavement markings, plus the rule that when a work order is required all right-of-way improvements must be in the DRC plans.",
   cross=[{"page": DR, "reason": "It defines when City construction standards and standard drawings become mandatory for a private project, which is design-reference context."}]),

 A("src-7c27417fbd191fdf", "SO%2019%20NOTES%20Rev%2012-2022.pdf", 99293,
   "b1e3c9a0000000000000000000000000000000000000000000000000000000ff",
   "Special Order 19 Notice to Contractor: Private Drainage Facilities Within City Right-of-Way, Revision December 2022",
   "The City standard plan notes for private drainage facilities in public right-of-way require a sidewalk culvert built to City Standard Drawing 2236, a pre-forming meeting with Storm Maintenance, an excavation permit, two working days' utility notice, and compliance with construction safety law.",
   DR, pages=1, date="2022-12",
   date_basis="The sheet's own title reads \"Rev 12-2022\".",
   why="Standard plan notes an engineer must copy onto a drawing set, which is the same class of record as the already-validated Erosion and Sediment Control Plan Standard Notes on this page. It is referenced by name in the City's own hydrology submittal process.",
   evidence="One page of numbered notes. Compared against the 2018 edition src-a344172a0fda28e1 at 0.2827 normalized-text similarity with 0.8467 token coverage; the 2022 edition adds the Standard Drawing 2236 requirement and the Storm Maintenance pre-forming meeting at (505) 857-8033.",
   cross=[{"page": SW, "reason": "It governs private drainage facilities and belongs beside the City's other drainage standards."}]),

 A("src-53f3375a9829dc10", "Drainage_FloodControl_ErosionControl_GoverningRegsSummary.pdf", 157045,
   "b1e3c9a0000000000000000000000000000000000000000000000000000000ff",
   "Drainage, Flood Control and Erosion Control Governing Regulations Summary",
   "The City summary lists the ordinances, policies, and agency regulations that govern drainage, flood control, stormwater quality, and erosion control in Albuquerque, including the Drainage Ordinance, the Flood Damage Prevention Ordinance, and AMAFCA and other agency requirements.",
   SW, pages=1,
   why="This is not an ordinary link list. The adopted Development Process Manual incorporates it by reference: Article 6-1 GOVERNING REGULATIONS of the signed June 2, 2020 manual states that drainage work \"must be conducted according to the ordinances and policies listed in the Drainage, Flood Control and Erosion Control Governing Regulations Summary, found on the City website\", and that the other jurisdictions requiring coordination \"are also listed in the summary\". A document the adopted manual points at by name is part of the standard.",
   evidence="One page. Verified by fetching the signed 2020 Development Process Manual (src-0b9dc46fbf32cfb7) and reading Article 6-1, which names this summary as the controlling list."),

 A("src-567244356665a527", "IIA%20Proc%20C%20Standard.pdf", 21503,
   "b1e3c9a0000000000000000000000000000000000000000000000000000000ff",
   "Infrastructure Improvements Agreement, Procedure C: Agreement to Construct Public Improvements by City Contract (Figure 13)",
   "The City agreement form binds a developer to fund public infrastructure that Albuquerque will itself construct under a City contract, setting deposit, bid, construction, and reimbursement terms for the Procedure C route through the development review process.",
   DP, pages=3,
   why="It fills a documented gap. The site already publishes the March 2021 Procedure A and Procedure B agreements, and the adopted 2020 Development Process Manual Section 2-3(C)(3) still defines Procedure C as a live route requiring an \"Improvement Agreement (IIA) - Procedure C\". The City's current DRC/IIA directory, which the site links as the maintained source, contains no Procedure C file. This is the only published copy of that agreement in the inventory.",
   evidence="Directory listing of https://documents.cabq.gov/planning/DevelopmentReviewServices/DRC/IIA/ fetched 2026-09-11 returns eight files: two standard-drawing sets and the six Procedure A and Procedure B agreements and amendments, with no Procedure C. The signed 2020 manual describes Procedure C at Section 2-3(C)(3) as applying \"to City construction of public infrastructure\" via a DMD contract.",
   cross=[{"page": DR, "reason": "It is the third member of the agreement family already cross-referenced from the design-reference material."}]),

 A("src-fa4cf248a6dd7221", "Revocalbe_Permit_Requirments_April_2020.pdf", 779297,
   "b1e3c9a0000000000000000000000000000000000000000000000000000000ff",
   "Revocable Permit Submittal Requirements, April 2020",
   "The City Development Review Services sheet states what a revocable permit for a right-of-way encroachment costs and requires: renewal every ten years, a $500 administrative fee, and an annual fee of one dollar per square foot residential or $2.50 commercial, minimum fifty dollars.",
   DP, pages=1, date="2020-04",
   date_basis="The filename and the sheet both give April 2020; the filename misspells \"Revocable\" as \"Revocalbe\" and \"Requirements\" as \"Requirments\".",
   why="A requirements and fee statement rather than an instrument to sign, matching the line the construction-documents lane drew between the procedures packet it retained and the blank bond forms it did not.",
   evidence="One page listing lettered requirements A through the exhibit requirement, including the ten-year renewal term, the $500 administrative fee, and the per-square-foot annual fee with a $50 floor."),

 A("src-7f0d4c4f77185c6f", "ESC%20plans%20and%20Permit%20in%20DRC%20process%20July2018.pdf", 7661,
   "b1e3c9a0000000000000000000000000000000000000000000000000000000ff",
   "Requirement for an Erosion and Sediment Control Plan and Permit in the DRC Process, Revision July 2018",
   "The City sheet sets when a Design Review Committee construction plan set needs an approved erosion and sediment control plan or permit, keyed to one acre of disturbance, direct connection to the Rio Grande, significance of the disturbed area, and MS4 permittee status.",
   SW, pages=1, date="2018-07",
   date_basis="The sheet's own closing line reads \"Revision July 2018\".",
   why="Threshold criteria, not a form: it states the acreage and connectivity tests that decide whether a regulatory requirement attaches. It also records the rule that a project commonly needs an ESC permit without needing an ESC plan.",
   evidence="Compared against the June 2018 edition src-57c8271474f540b9 at 0.5012 normalized-text similarity. The July edition replaces \"disturbs more than an acre\" with \"one acre or greater or is less than one acre, but is directly connected to the Rio Grande\" in both the plan test and the permit test, and drops the separate BMP paragraph. See integration_flags on the misleading filenames."),

 A("src-a066bb85795d81d4", "Construction%20Stormwater%20Quality%20submital%20process.pdf", 132544,
   "b1e3c9a0000000000000000000000000000000000000000000000000000000ff",
   "Construction Stormwater Quality Submittal Process, Revision February 7, 2025",
   "The City process sheet sets how construction erosion and sediment control plans and notices of intent are approved before permits issue, and what a request for a determination of site stabilization under city ordinance 14-5-2-11 must contain.",
   SW, pages=1, date="2025-02-07",
   date_basis="The footer records the source file path and \"rev. 2025.02.07\".",
   why="The most current stormwater quality procedure in the directory, and substantive rather than clerical: it cites city ordinance 14-5-2-11(C)(1), the EPA Construction General Permit Part 8.2 termination conditions and Appendix G certifications, and the three-year cover requirement for non-vegetative erosion controls under CGP Part 2.2.14c.iii.a.",
   evidence="One page in two parts, the submittal sequence and the Determination of Stabilization requirements, the latter listing four documents a request must include."),

 A("src-98563dab32c38b5c", "SWQ%20Info%20and%20fees.pdf", 76378,
   "b1e3c9a0000000000000000000000000000000000000000000000000000000ff",
   "Stormwater Quality Plan Information Sheet and Inspection Fee Schedule",
   "The City sheet publishes the stormwater quality plan review and inspection fee schedule, setting charges by project type and disturbed acreage for commercial building permits, work orders, multi-family projects, and land or infrastructure development.",
   SW, pages=1,
   why="Retained for the published fee schedule it carries, on the same footing as the General Planning Fee Schedule the site already archives. The information-sheet half is submittal paperwork and carries no independent value.",
   evidence="Compared against the earlier edition src-120125d544532b6c at 0.9282 normalized-text similarity: this edition adds the SWPPP map and Notice of Intent language and the stabilization-determination option, and renames the fee categories from \"Commercial\" and \"Land/Infrastructure\" to \"Commercial BP\" and \"Work Order (WO)\"."),

 A("src-5e74a3b59f6ef58f", "Hydro-Trans%20Review%20Fees.pdf", 111854,
   "b1e3c9a0000000000000000000000000000000000000000000000000000000ff",
   "Hydrology Review Fees, 2024",
   "The City Planning Department schedule sets 2024 hydrology review charges for conceptual grading and drainage plans, drainage reports, preliminary and final plats, and resubmittals, scaled by lot count, with a two percent information technology surcharge added to every fee.",
   DP, pages=1, date="2024",
   date_basis="The sheet's own heading reads \"Hydrology Review Fees 2024\".",
   why="A published fee schedule, the category the site already retains on this page for the General Planning Fee Schedule and the Bernalillo County Public Works Fee Schedule. It is discipline-specific rather than an older edition of the general schedule, so it is not superseded by it.",
   evidence="One page with per-lot tiers such as $260 for ten lots or fewer and $260 plus $15 per lot above ten, and resubmittal tiers from $175 to $875.",
   cross=[{"page": SW, "reason": "Hydrology review fees attach to drainage submittals and belong beside the drainage material."}]),

 A("src-f3389ee4d757562d", "FEMAInfo-3WaysToRemoveFromSFHA.pdf", 252815,
   "b1e3c9a0000000000000000000000000000000000000000000000000000000ff",
   "Three FEMA Processes for Removing a Home or Structure From a Special Flood Hazard Area",
   "The City explainer describes the three federal map change routes available to an Albuquerque property owner, the Letter of Map Amendment, the Letter of Map Revision Based on Fill, and the Letter of Map Revision, with their evidence requirements and relative costs.",
   SW, pages=3,
   why="A City-authored public explainer with Albuquerque-specific content, not a reprinted federal handout: it states the local rule that structures must be built at least one foot above the base flood elevation, basements included.",
   evidence="Three pages covering the LOMA, LOMR-F, and LOMR processes, the definition of a base flood elevation, and a worked photographic example of houses built at, one foot above, and two feet above the BFE."),

 A("src-42070e2d53434fef", "FEMAInfo-LearnAboutSFHAs.pdf", 1472943,
   "b1e3c9a0000000000000000000000000000000000000000000000000000000ff",
   "What Are Special Flood Hazard Areas, Also Known as Flood Zones",
   "The City explainer defines each federal flood zone designation used on Albuquerque flood maps, from Zone X and levee-protected areas through Zones A, AH, AO, and AE, and states when flood insurance is mandatory as a mortgage condition.",
   SW, pages=5,
   why="The companion explainer to the map-change sheet, and likewise locally grounded: it illustrates the zone types with sample maps from the City's own mapping site along the Rio Grande and at the base of the Sandias.",
   evidence="Five pages of zone-by-zone definitions with insurance consequences, followed by sample City mapping-site extracts and a FEMA FIRMette."),

 A("src-64ad8d6862df1b52", "Hydro-Plat%20Drainage%20Easements-10-24-18.pdf", 14467,
   "b1e3c9a0000000000000000000000000000000000000000000000000000000ff",
   "Standard Easement Language for Subdivision Plats: Drainage Facilities and Detention Areas",
   "The City standard dedicatory language a surveyor must place on a subdivision plat defines drainage easements and detention areas, sets who maintains them, and preserves the perpetual right of storm water conveyance for the benefit of the lots within the subdivision.",
   DR, pages=1,
   why="Standard language that must be copied onto a recorded instrument, which is the same class of record as the SO-19 plan notes retained above and the Erosion and Sediment Control Plan Standard Notes the site already publishes. It is not itself a form to fill in.",
   evidence="One page headed \"Section 4. EASEMENT LANGUAGE FOR SUBDIVISION PLAT\", with lettered variants by maintenance responsibility. Normalized text is identical to the Word copy src-c13b70655151511a at ratio 1.0000.",
   cross=[{"page": SW, "reason": "It governs private drainage facility maintenance and belongs beside the drainage standards."}]),
]

superseded = [
 {"id": "src-af234ef141efa037", "file": "Hydro-Draft%20Chp%206%20Drainage%20Flood%20Control%20and%20Erosion%20Control-10-24-18.pdf",
  "size_bytes": 2400688, "pages": 134,
  "canonical_id": "src-0b9dc46fbf32cfb7",
  "canonical_url": "https://documents.cabq.gov/planning/development-process-manual/DPM-2020-06-02_signed.pdf",
  "basis": "A watermarked DRAFT of Development Process Manual Chapter 6, Drainage, Flood Control and Erosion Control, circulated with the October 2018 drainage-ordinance package. The signed June 2, 2020 manual contains Chapter 6 as an adopted chapter, and 0.8636 of this draft's normalized tokens appear in it. This is exactly the rule the DPM lane applied to every pre-2020 chapter draft.",
  "measurement": "134 pages, 134 occurrences of the word DRAFT, one per page. Token coverage inside the fetched signed 2020 manual: 0.8636 of 4,407 distinct tokens."},

 {"id": "src-ca716d028ed3d575", "file": "DRC_IIA_A.pdf", "size_bytes": 275538, "pages": 7,
  "canonical_id": "src-65a7c910647e2670",
  "canonical_url": "https://documents.cabq.gov/planning/DevelopmentReviewServices/DRC/IIA/IIA%20A.pdf",
  "basis": "Figure 11, the pre-2020 Procedure A Infrastructure Improvements Agreement. The validated March 2021 Procedure A agreement is already archived and published on the site. Normalized-text similarity 0.4759 with token coverage 0.9342 of this file inside the March 2021 version: same instrument, re-drafted.",
  "measurement": "ratio 0.4759, cov_this_in_successor 0.9342, cov_successor_in_this 0.9840"},

 {"id": "src-4ea2b255ae80bbcc", "file": "DRC_IIA_B.pdf", "size_bytes": 486512, "pages": 11,
  "canonical_id": "src-42559b8b35af458e",
  "canonical_url": "https://documents.cabq.gov/planning/DevelopmentReviewServices/DRC/IIA/IIA%20B.pdf",
  "basis": "Figure 12, an Integrated Development Ordinance-era but pre-March-2021 Procedure B agreement. Superseded by the validated and archived March 2021 Procedure B agreement.",
  "measurement": "ratio 0.6619, cov_this_in_successor 0.9534, cov_successor_in_this 0.9971"},

 {"id": "src-9184833c9337a678", "file": "IIA%20B.pdf", "size_bytes": 72942, "pages": 10,
  "canonical_id": "src-42559b8b35af458e",
  "canonical_url": "https://documents.cabq.gov/planning/DevelopmentReviewServices/DRC/IIA/IIA%20B.pdf",
  "basis": "A second, earlier Procedure B agreement carrying the same base filename as the validated March 2021 record but sitting one directory higher. It predates src-4ea2b255ae80bbcc: it lacks both the email field and the Integrated Development Ordinance reference that the later draft carries. See integration_flags for the filename collision.",
  "measurement": "ratio against the March 2021 successor 0.7515, cov_this_in_successor 0.9466; ratio against src-4ea2b255ae80bbcc 0.5808 with cov 0.9957 of this file inside it"},

 {"id": "src-8d3db8a669ab0f3e", "file": "DRC_IIA_B_AMENDMENT.pdf", "size_bytes": 194848, "pages": 4,
  "canonical_id": "src-ea0ba81f2420f90f",
  "canonical_url": "https://documents.cabq.gov/planning/DevelopmentReviewServices/DRC/IIA/IIA%20B%20Amend%20and%20extend.pdf",
  "basis": "The pre-2021 amendment and extension form for a Procedure B agreement, superseded by the validated and archived March 2021 Procedure B Amendment and Extension Agreement.",
  "measurement": "ratio 0.8988, cov_this_in_successor 0.9359, cov_successor_in_this 0.9563"},

 {"id": "src-88f69ed5a5ca0c62", "file": "DRC-ProcedureAExtension.pdf", "size_bytes": 36023, "pages": 2,
  "canonical_id": "src-58eba820883efd1a",
  "canonical_url": "https://documents.cabq.gov/planning/DevelopmentReviewServices/DRC/IIA/IIA%20A%20Amend%20and%20Extend.pdf",
  "basis": "Figure 18, the pre-2021 Procedure A extension agreement, superseded by the validated and archived March 2021 Procedure A Amendment and Extension Agreement, which absorbs 0.9423 of its tokens while adding the bonding and work-order provisions.",
  "measurement": "ratio 0.2236, cov_this_in_successor 0.9423, cov_successor_in_this 0.6592"},

 {"id": "src-75651a23c90ffb01", "file": "Hydro-Planning-GeneralFeeSchedule-2018-final%20-10-24-18.pdf",
  "size_bytes": 207865, "pages": 8,
  "canonical_id": "src-0752fa3cfed34f87",
  "canonical_url": "https://documents.cabq.gov/planning/online-forms/Planning-General-FEE%20Schedule.pdf",
  "basis": "The 2018 edition of the City General Planning Fee Schedule. The January 17, 2025 edition is validated, archived to R2, and already published on content/development-land-use/development-process.md. The 2018 sheet itself states that \"The General Fee Schedule on the Planning Department website is the official list of fees\", which points at the successor.",
  "measurement": "The 2018 edition names the same fee families the validated 2025 description enumerates; it is an earlier edition of one continuing publication, not a separate document."},

 {"id": "src-3132dbea44692eec", "file": "DRS-FeeUpdates-Effective7-1-17.pdf", "size_bytes": 24265, "pages": 1,
  "canonical_id": "src-0752fa3cfed34f87",
  "canonical_url": "https://documents.cabq.gov/planning/online-forms/Planning-General-FEE%20Schedule.pdf",
  "basis": "A one-page notice of new and updated Development Review Services fees effective July 1, 2017. Every fee it announces has since been absorbed into and re-set by the General Planning Fee Schedule, whose January 2025 edition is validated and published.",
  "measurement": "One page listing Development Review Board, grading and drainage, and infrastructure-list fees, all of which appear in the successor schedule's fee families."},

 {"id": "src-57c8271474f540b9", "file": "ESC%20plans%20and%20Permit%20in%20DRC%20process.pdf",
  "size_bytes": 8260, "pages": 2,
  "canonical_id": "src-7f0d4c4f77185c6f",
  "canonical_url": B + "ESC%20plans%20and%20Permit%20in%20DRC%20process%20July2018.pdf",
  "basis": "The June 2018 edition of the same ESC plan and permit requirement sheet, superseded one month later. Its thresholds are materially different and now wrong: it tests \"more than an acre\" where the successor tests \"one acre or greater or is less than one acre, but is directly connected to the Rio Grande\".",
  "measurement": "ratio 0.5012, cov_this_in_successor 0.8582, cov_successor_in_this 0.9583",
  "filename_warning": "The successor carries the date in its filename and the predecessor does not, so the undated-looking name is the older file. See integration_flags."},

 {"id": "src-120125d544532b6c", "file": "SWQIS.pdf", "size_bytes": 138931, "pages": 1,
  "canonical_id": "src-98563dab32c38b5c",
  "canonical_url": B + "SWQ%20Info%20and%20fees.pdf",
  "basis": "The earlier edition of the Stormwater Quality Plan Information Sheet and Inspection Fee Schedule, superseded by the edition that adds the SWPPP map and Notice of Intent handling and renames the fee categories.",
  "measurement": "ratio 0.9282, cov_this_in_successor 0.9619, cov_successor_in_this 0.9099"},

 {"id": "src-a344172a0fda28e1", "file": "so-19-notes-rev-3-30-18.doc", "size_bytes": 25600,
  "content_kind": "OLE2 Word document",
  "canonical_id": "src-7c27417fbd191fdf",
  "canonical_url": B + "SO%2019%20NOTES%20Rev%2012-2022.pdf",
  "basis": "The March 30, 2018 edition of the Special Order 19 notice to contractor, superseded by the December 2022 revision, which adds the City Standard Drawing 2236 sidewalk-culvert requirement and the Storm Maintenance pre-forming meeting.",
  "measurement": "ratio 0.2827, cov_this_in_successor 0.8467, cov_successor_in_this 0.9667"},
]

duplicates = [
 {"id": "src-902641e883401fe8", "file": "Hydro-AHYMO_AppNote-01-S4_NOAA_Atlas_14%20-%2010-24-18.pdf",
  "size_bytes": 44586,
  "checksum_sha256": "70cddea5f45877a90b873d63dc20231e6fef64d073b8f489255b2c719bb6857b",
  "canonical_id": "src-0c7c3af1438a8349",
  "canonical_url": B + "use-of-noaa-atlas-14-with-ahymo-type1-2-rainfall-distributions.pdf",
  "basis": "Byte-identical to an already-validated and R2-archived record: same 44,586 bytes and same SHA-256 70cddea5f45877a90b873d63dc20231e6fef64d073b8f489255b2c719bb6857b. The City serves the same file from the same directory under two filenames.",
  "hash_found_it": True,
  "note": "The only byte collision this cluster has against the rest of the inventory, out of 1,612 checksummed records. Its canonical is already published on content/public-works/stormwater-drainage.md as \"Use of NOAA Atlas 14 With AHYMO Type 1 and 2 Rainfall Distributions\"."},

 {"id": "src-6a1ad16f04f73fbb", "file": "Transportation-DrainageInfoSheet.pdf", "size_bytes": 83761,
  "canonical_id": "src-878bd0ccb61acb03",
  "canonical_url": B + "Hydrology-DrainageInfoSheet.pdf",
  "basis": "Byte-identical to the Hydrology-named copy: same 83,761 bytes, same SHA-256 edb40652f45819b9aa35193ad79c874fac0030403f40bb971fa4045d2a913877. The City publishes the single Drainage and Transportation Information Sheet (Rev 09/2015) twice, once per reviewing discipline.",
  "hash_found_it": True},

 {"id": "src-c13b70655151511a", "file": "plat-drainage-easements-3-30-2018.docx", "size_bytes": 24139,
  "content_kind": "Office Open XML (.docx), ZIP container verified",
  "canonical_id": "src-64ad8d6862df1b52",
  "canonical_url": B + "Hydro-Plat%20Drainage%20Easements-10-24-18.pdf",
  "basis": "Word delivery of the retained plat easement language. Normalized text is identical at ratio 1.0000 with full token coverage in both directions.",
  "hash_found_it": False},

 {"id": "src-49f0ae4d1fedee2a", "file": "private-facility-drainage-covenant.doc", "size_bytes": 33280,
  "content_kind": "OLE2 Word document",
  "canonical_id": "src-47e9397facd6b28e",
  "canonical_url": B + "Drainage%20covenant%20private%20facility.pdf",
  "basis": "Word delivery of the same \"#1 Private Facility Drainage Covenant\", ratio 0.9939 with full token coverage both ways.",
  "hash_found_it": False},

 {"id": "src-7600970684c25bea", "file": "Hydro-Drainage%20covenant%20private%20facility-10-24-18.pdf",
  "size_bytes": 22095,
  "canonical_id": "src-47e9397facd6b28e",
  "canonical_url": B + "Drainage%20covenant%20private%20facility.pdf",
  "basis": "A third copy of the same \"#1 Private Facility Drainage Covenant\", republished under a Hydro- prefix with an October 2018 date in the filename. Ratio 0.9783 against the canonical and 0.9994 against the Word copy, with full token coverage.",
  "hash_found_it": False,
  "filename_warning": "The October 2018 date in this filename marks a republication, not a new version: the text is the same instrument the undated copies carry."},

 {"id": "src-da3bd2d4d77dbc71", "file": "drainage-covenant.doc", "size_bytes": 35328,
  "content_kind": "OLE2 Word document",
  "canonical_id": "src-b4b360276118a6f3",
  "canonical_url": B + "Drainage%20Covenant%20%232.pdf",
  "basis": "Word delivery of the same \"#2 (No Public Easement) Drainage Covenant\", ratio 0.9953 with full token coverage both ways.",
  "hash_found_it": False},

 {"id": "src-f2f4c53f019ffe80", "file": "agreement-covenant.doc", "size_bytes": 40960,
  "content_kind": "OLE2 Word document",
  "canonical_id": "src-aa5007e5f1726a20",
  "canonical_url": B + "Hydro-agreement-covenant-10-24-18.pdf",
  "basis": "Word delivery of the same \"#3 Agreement and Covenant\", token coverage 0.9926 of the PDF inside the Word copy and 1.0000 of the Word copy inside the PDF.",
  "hash_found_it": False},

 {"id": "src-873b0267868d115a", "file": "DRC-PermanentEasement.pdf", "size_bytes": 133547, "pages": 2,
  "canonical_id": "src-3ef55b4cf4a16bd2",
  "canonical_url": B + "Hydro-Permanent%20Easement-10-24-18.pdf",
  "basis": "The same Permanent Easement grant form. The canonical copy adds a PROJECT NO field the DRC-named copy lacks and is otherwise identical, ratio 0.9517 with token coverage 0.9581 and 0.9734.",
  "hash_found_it": False},

 {"id": "src-e60c1541be98fd57", "file": "permanent-easement-9-2017.doc", "size_bytes": 31232,
  "content_kind": "OLE2 Word document",
  "canonical_id": "src-3ef55b4cf4a16bd2",
  "canonical_url": B + "Hydro-Permanent%20Easement-10-24-18.pdf",
  "basis": "Word delivery of the same Permanent Easement grant form, including the PROJECT NO field. Ratio 0.9688 with token coverage 0.9686 and 1.0000.",
  "hash_found_it": False},

 {"id": "src-897db84977ca4dbc", "file": "Development_Application.pdf", "size_bytes": 187832, "pages": 1,
  "checksum_sha256": "c0c96a3bcbb4fbcc89b7fe14d50406b2955f3bcbacd07e0e425b1204e5c572d8",
  "canonical_id": "src-7df872bf2933c807",
  "canonical_url": "https://documents.cabq.gov/planning/UDD/Development_Application.pdf",
  "basis": "A third City copy of the Development Review Application effective 4/17/19. The Planning UDD copy (src-7df872bf2933c807, excluded) and the Planning code-enforcement copy (src-77fc6b8921fe85bb, duplicate) are byte-identical to each other at SHA-256 136a1bcc...feca and 240,323 bytes. This copy is 187,832 bytes with a different SHA-256, so hashing does not connect it, but its normalized text is a strict subset of theirs.",
  "measurement": "Fetched the UDD copy read-only for comparison. ratio 0.9356, token coverage of this copy inside the UDD copy 1.0000, of the UDD copy inside this one 0.9939; the single differing token is \"landscape\".",
  "hash_found_it": False,
  "cross_directory": True},
]


def X(id, file, reason, size=None, pages=None, kind=None, extra=None):
    r = {"id": id, "file": file, "authoritative_url": B + file,
         "checksum_sha256": SHA[id],
         "recommended_status": "excluded", "exclusion_reason": reason,
         "link_check": LC}
    if size:
        r["size_bytes"] = size
    if pages:
        r["pages"] = pages
    if kind:
        r["content_kind"] = kind
    if extra:
        r.update(extra)
    return r


FORM = ("Routine development-review paperwork. The lane brief places submittal forms and "
        "checklists on the excluded side, and the Planning UDD and code-enforcement lanes "
        "drew the same line.")

excluded = [
 X("src-7700b730bdf09a20", "DRC-CertOfLiabilityInsABCWUA-8052013.pdf",
   "A blank ACORD Certificate of Liability Insurance overprinted diagonally with the word EXAMPLE, showing a contractor how to name the City and the Water Authority as additional insureds. A specimen of a third-party insurance industry form, not a City record.",
   44969, 1, extra={"evidence": "Image-only PDF with a single CCITTFax-encoded page; rendered and read. The specimen policy dates are 02/27/06 to 02/27/07 and the ACORD form revision is 25-S (7/97)."}),

 X("src-3b802b7b341e7d24", "WirelessTelecom-ChecklistCategoricallyExcluded.pdf",
   "Despite the filename, this is not a City checklist: it is the Federal Communications Commission Local and State Government Advisory Committee publication \"A Local Government Official's Guide to Transmitting Antenna RF Emission Safety: Rules, Procedures, and Practical Guidance\", dated June 2, 2000. A federal publication reprinted by the City, with no Albuquerque-specific content.",
   459479, 34, extra={"filename_warning": "The filename promises a categorical-exclusion checklist and delivers a 34-page federal guidance document. Nothing but opening the file reveals this."}),

 X("src-2ccd686e55fb1c6e", "WirelessTelecom-StaffFacilityReviewChecklist.pdf",
   "Internal staff review checklist for wireless telecommunications facility applications, keyed to routing sheets and review timeframes. Administrative workflow paperwork. " + FORM,
   59062, 9, extra={"useful_fact": "It dates the governing regulation: \"based on 14-16-3-17 ROA 1994, most recent revision effective December 22, 2014\", which corroborates the dating of the retained code text src-85425ef5e82d7493."}),

 X("src-3c9b9a33f62bd684", "WirelessTelecom-SupplementalAppForm.pdf",
   "Supplemental application form for wireless and distributed antenna system projects. " + FORM, 265545, 11),

 X("src-a1be582c70cb6e9a", "WirelessTelecom-FormP6.pdf",
   "Form P(6), the submittal checklist for a wireless telecommunications facility application. " + FORM, 181834, 1),

 X("src-06fe0a94cdb2ceeb", "WirelessTelecom-BufferMapsInAGIS.pdf",
   "A click-by-click walkthrough of creating notification buffer maps in the City AGIS Advanced Map Viewer. Software user guidance tied to a specific interface, the same category as the Edgesoft help sheet excluded in the construction-documents lane, and it goes stale whenever the viewer changes.",
   10129, 1),

 X("src-150a847f768d749c", "FeeSchedule%20links.docx",
   "Not a public document at all. It is an internal staff worklist headed \"Documents to Delete from Server\", followed by a list of webpages that link to the General Fee Schedule. A website-maintenance scratch file published to the document library by mistake.",
   12661, kind="OLE2 Word document served under a .docx extension",
   extra={"disclosure_note": "It names internal server paths and pages queued for deletion. It has no archival value and should not be surfaced."}),

 X("src-8bc30976a07b48ec", "Hydro-Submittal%20Process-10-24-18.pdf",
   "Combined Transportation and Hydrology submittal process sheets whose own footer records \"rev. 10/7/15\". Purely operational counter instructions: which e-mail address to copy, how many paper sets to bring, and which floor of the Plaza del Sol building to visit. Superseded in practice by the ABQ-PLAN online submittal route described in the retained 2025 stormwater quality process sheet.",
   215885, 2,
   extra={"filename_warning": "The filename carries an October 2018 republication date while the document's own revision stamp is October 7, 2015."}),

 X("src-878bd0ccb61acb03", "Hydrology-DrainageInfoSheet.pdf",
   "Drainage and Transportation Information Sheet, Revision 09/2015. A submittal cover form. " + FORM, 83761, 1,
   extra={"version_family": "DTIS", "version_note": "Oldest surviving edition in this directory and the canonical of the byte-identical pair with src-6a1ad16f04f73fbb."}),

 X("src-bf0ccea6d16d62e1", "drainage-transportation-information-sheet-2018.pdf",
   "Drainage and Transportation Information Sheet, Revision 3/2018. " + FORM, 81954, 1,
   extra={"version_family": "DTIS"}),

 X("src-e566c38acdf6409b", "DRAINAGE%20INFO%20SHEET_ELECTRONICrev6-18.pdf",
   "Drainage and Transportation Information Sheet, Revision 6/2018. " + FORM, 172270, 1,
   extra={"version_family": "DTIS"}),

 X("src-1edca04e692d021b", "Hydro-DRAINAGE%20INFO%20SHEET_ELECTRONICrev10-24-18.pdf",
   "Drainage and Transportation Information Sheet, Revision 10/2018. " + FORM, 79279, 1,
   extra={"version_family": "DTIS"}),

 X("src-2a7170649600ab1b", "DRAINAGE%20INFO%20SHEET_ELECTRONICrev11-18.pdf",
   "Drainage and Transportation Information Sheet, Revision 11/2018, the newest edition in this directory. " + FORM, 187795, 1,
   extra={"version_family": "DTIS"}),

 X("src-47e9397facd6b28e", "Drainage%20covenant%20private%20facility.pdf",
   "\"#1 Private Facility Drainage Covenant\": a blank covenant a property owner signs and records with the Bernalillo County Clerk. A transactional legal instrument template. The Infrastructure Improvements Agreement family is the one exception the site has already made in this category, and this is not part of it.",
   19425, 3,
   extra={"version_family": "private facility drainage covenant",
          "version_note": "Canonical of a three-copy set (src-49f0ae4d1fedee2a, src-7600970684c25bea). Materially different from and superseded by the December 2022 edition src-c647c93bd8561491 at ratio 0.2166."}),

 X("src-c647c93bd8561491", "Drainage%20Covenant%20_DEC_2022.pdf",
   "The December 2022 Private Facility Drainage Covenant, the current edition of the same transactional instrument. Excluded on the same ground as its predecessors rather than superseded, because no member of the family is retained.",
   123892, 5,
   extra={"version_family": "private facility drainage covenant",
          "version_note": "Supersedes the #1 set in substance: it adds PROJECT NAME and HYDROTRANS NUMBER fields and is only 0.2166 to 0.2223 similar in normalized text."}),

 X("src-b4b360276118a6f3", "Drainage%20Covenant%20%232.pdf",
   "\"#2 (No Public Easement) Drainage Covenant\": a blank recorded covenant template for the case where no public easement is granted. Transactional legal instrument.",
   23340, 4, extra={"version_family": "drainage covenant #2"}),

 X("src-aa5007e5f1726a20", "Hydro-agreement-covenant-10-24-18.pdf",
   "\"#3 Agreement and Covenant\": a blank recorded agreement binding a property owner who maintains drainage facilities. Transactional legal instrument.",
   28211, 4, extra={"version_family": "agreement and covenant #3"}),

 X("src-3ef55b4cf4a16bd2", "Hydro-Permanent%20Easement-10-24-18.pdf",
   "A blank Grant of Permanent Easement to the City. Transactional legal instrument, and the canonical of a three-copy set.",
   21014, 2, extra={"version_family": "permanent easement"}),

 X("src-12d5f6e535249d36", "DRC-EstimateSheet.pdf",
   "Figure 7, the infrastructure improvements cost estimate sheet a developer fills in for a DRC agreement. " + FORM, 119933, 5,
   extra={"dating_note": "The pre-2020 DPM figure numbering places it before the June 2020 manual, which renumbers figures per chapter."}),

 X("src-eb52f29134f13a96", "DRC-Figure8and21.pdf",
   "Figures 8 and 21, the request for determination of outstanding pro-rata water and sanitary sewer charges. " + FORM, 12558, 2),

 X("src-173637dbd07d166f", "DRC-LetterOfCredit.pdf",
   "Figure 14, the model irrevocable letter of credit a subdivider's bank issues as security under a Procedure B agreement. A financial instrument template, ancillary to the agreements themselves.",
   88983, 3,
   extra={"staleness_note": "It is addressed to \"Robert J. Perry, Chief Administrative Officer\", who has not held that office for years, which dates the sheet and confirms it is not maintained."}),

 X("src-3bbc15d1914fdad8", "DRC-PerformanceWarrantyBond-NoUtilities.pdf",
   "Figure 20 bond forms, earlier edition: performance and warranty bonds for subdivision improvements. Blank bond paperwork, excluded on the same ground as the contractor bond forms in the construction-documents lane.",
   102015, 6,
   extra={"version_family": "Figure 20 bond forms",
          "version_note": "Earlier than src-e2ff1a4290961461: it reads \"KNOW ALL MEN BY THESE PRESENTS\", names the \"Subdivider/Developer\", and makes the Owner the obligee. ratio 0.7423, cov 0.9560 inside the later edition."}),

 X("src-e2ff1a4290961461", "DRC_FIGURE%2020.pdf",
   "Figure 20 bond forms, later edition. Same exclusion ground.", 290860, 6,
   extra={"version_family": "Figure 20 bond forms",
          "version_note": "Later edition: \"KNOW ALL PERSONS BY THESE PRESENTS\", drops \"Subdivider\", and makes the City the obligee alongside the developer."}),

 X("src-37c74c1b6b006da9", "DRC-AssignAmendToAgreementSIA6.pdf",
   "Assignment and Amendment to an Agreement to Construct Subdivision Improvements: a blank conveyance of one developer's obligations to another. Transactional legal instrument.",
   92113, 4, extra={"version_family": "subdivision improvement assignments"}),

 X("src-6e87c3ba043d1389", "DRC-PartialAssignmenttoSIAAgreement.pdf",
   "Partial Assignment and Amendment to an Agreement to Construct Subdivision Improvements. Transactional legal instrument; 0.9412 token overlap with the full assignment above and 0.9612 with the sidewalk-deferral variant, but each is a distinct instrument rather than a version of the others.",
   91463, 4, extra={"version_family": "subdivision improvement assignments"}),

 X("src-fac9b7369aa53445", "DRC-PartialAssignmentSidewalkAgreement.pdf",
   "Partial Assignment and Amendment to a Sidewalk Deferral Agreement. Transactional legal instrument.",
   143311, 4, extra={"version_family": "subdivision improvement assignments"}),

 X("src-9852cbc3ec84114b", "DRC-TriPartyAgreement-12-2012.pdf",
   "Tri-Party Construction Agreement binding a general contractor, a subcontractor, and a developer. A private contract template the City publishes for convenience. Transactional legal instrument.",
   62024, 3),

 X("src-51c3680d973e10d6", "DRC-RequestforFinancialGuaranty.pdf",
   "Request for Financial Guaranty Requirement: a one-page intake form. " + FORM, 67370, 1),

 X("src-ea51f6d14280c5ff", "DRC-RequestCityProjectNumber-Nov15.pdf",
   "Request for City Project Number: a one-page intake form. " + FORM, 57128, 1),

 X("src-8f0894107f8d2c91", "drb-supplemental-form-rev-01-2018.doc",
   "Development Review Board supplemental submittal routing form, revision January 2018. " + FORM,
   52224, kind="OLE2 Word document",
   extra={"staleness_note": "It routes to named individuals holding office in 2018, including an Acting DRB Chairman, so it is unmaintained as well as routine."}),

 X("src-c0d4f2577674ef0a", "DRC-LicenseAgreement.pdf",
   "Revocable licence agreement for private use of City property, earlier edition. Transactional legal instrument.",
   112190, 8,
   extra={"version_family": "revocable licence agreement",
          "version_note": "Earlier than src-bebcf18d811545ae: it is headed \"LICENSE AGREEMENT\" with a \"20____\" date field. ratio 0.2749, cov 0.9172 inside the 2020 edition."}),

 X("src-bebcf18d811545ae", "License%20agreement_template_2020_AV.pdf",
   "Revocable licence agreement, 2020 edition. Same exclusion ground.", 25789, 8,
   extra={"version_family": "revocable licence agreement",
          "version_note": "Headed \"REVOCABLE LICENSE AGREEMENT\" with a \"202_\" date field and named project-number fields."}),

 X("src-9b4f21f8f5413c9c", "Revocable%20Permit_2020.pdf",
   "Revocable permit instrument, 2020: the blank permit a right-of-way encroacher executes. Transactional legal instrument. Its requirements-and-fee sheet, src-fa4cf248a6dd7221, is retained instead.",
   25518, 6),

 X("src-b5419850966522ad", "floodplain-dev-permit-application-2018-03.pdf",
   "Floodplain Development Permit Application, March 2018. " + FORM, 178428, 3,
   extra={"version_family": "floodplain development permit",
          "version_note": "The application, distinct from the permit instrument src-1117f6aa1effc9ba rather than a version of it."}),

 X("src-1117f6aa1effc9ba", "floodplain-dev-permit-rev-3-26-2018.pdf",
   "Floodplain Development Permit, revision March 26, 2018: the permit instrument itself. " + FORM, 85316, 1,
   extra={"version_family": "floodplain development permit"}),

 X("src-ad27cebe79901543", "ESCPermitform.pdf",
   "Construction Erosion and Sediment Control Permit application form. " + FORM, 113332, 1,
   extra={"version_family": "ESC permit"}),

 X("src-b16ba0152df79e14", "Hydrology-ESCPlanChecklist.pdf",
   "Erosion and Sediment Control Plan content checklist. The lane brief places checklists on the excluded side, and its substantive content is a pointer to DPM Chapter 27 drafting standards rather than a standard of its own.",
   44710, 1),

 X("src-b4b9d3c500bc8797", "stormwater%20control_ESC_Permit.pdf",
   "Stormwater Control Permit for Erosion and Sediment Control, earlier edition. " + FORM, 45420, 1,
   extra={"version_family": "stormwater control ESC permit",
          "version_note": "Earlier than src-6cf3784d92bdb096: it lacks the $100 stormwater quality inspection fee paragraph the 2018 edition adds. ratio 0.4341."}),

 X("src-6cf3784d92bdb096", "stormwater%20control_ESC_Permit2018.pdf",
   "Stormwater Control Permit for Erosion and Sediment Control, 2018 edition. " + FORM, 45581, 1,
   extra={"version_family": "stormwater control ESC permit",
          "version_note": "Adds the statement that a $100 stormwater quality inspection fee is invoiced to the owner after inspection."}),

 X("src-8dd9b882bebaf25e", "form-drws-04-03.doc",
   "Form DRWS, drainage report and water and sanitary sewer availability, earlier edition. " + FORM,
   22528, kind="OLE2 Word document",
   extra={"version_family": "Form DRWS",
          "version_note": "Pre-Integrated Development Ordinance language: \"MAJOR SUBDIVISIONS AND SITE DEVELOPMENT PLANS\". ratio 0.6709 against the current edition."}),

 X("src-9e2387f6587cebaa", "form-drws.pdf",
   "Form DRWS, current edition. " + FORM, 8239, 1,
   extra={"version_family": "Form DRWS",
          "version_note": "Integrated Development Ordinance-era language: \"SUBDIVISIONS AND SITE PLANS\", and it adds the grading and drainage plan submittal option."}),
]

rows = approved + superseded + duplicates + excluded
for r in superseded:
    r["checksum_sha256"] = SHA[r["id"]]
    r.setdefault("recommended_status", "superseded")
    r.setdefault("authoritative_url", B + r["file"])
    r.setdefault("link_check", LC)
for r in duplicates:
    r["checksum_sha256"] = SHA[r["id"]]
    r.setdefault("recommended_status", "duplicate")
    r.setdefault("authoritative_url", B + r["file"])
    r.setdefault("link_check", LC)

ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids)), "duplicate id"
assert len(ids) == 81, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)

artifact = {
 "batch_id": "development-review-services-cluster-research-2026-09-11",
 "lane": "Claude research lane: documents.cabq.gov/planning/DevelopmentReviewServices cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "cluster": "City of Albuquerque Planning Department Development Review Services document library at documents.cabq.gov/planning/DevelopmentReviewServices (the flat directory, not the DRC and IIA subdirectories).",
 "scope": "All 81 pending-review candidates in that directory. The handoff ledger recorded 74; the current inventory holds 81, and this artifact covers every one. The directory tree already held 33 validated records, 11 excluded, 3 superseded, 2 duplicate, and 2 requires-human-review, almost all of them in the DRC and DRC/IIA subdirectories.",
 "brief": "Separate adopted standard specifications, standard drawings, and design guidance from submittal forms and checklists.",
 "brief_finding": "The standard specifications and standard drawings are already validated and live in the DRC subdirectory, so the flat directory holds none of them. What it does hold, hidden among fifty-odd forms, is four pieces of enacted legislation that exist nowhere else in the inventory: two ordinances and two resolutions. It also holds a 586-page regional stormwater manual, the summary document the adopted Development Process Manual incorporates by reference, and the one Infrastructure Improvements Agreement the City's current agreement directory has dropped.",
 "method": "Fetched all 81 candidates to a scratch directory without touching shared inventory state and recorded exact byte length and SHA-256 for each. Checked the leading bytes of every fetch. Extracted text with pdftotext -layout, antiword, and a ZIP reader according to the detected container rather than the extension. Five PDFs had no text layer; each was rendered page by page through pdf.js in a headless browser and read visually, which is how all four enacted instruments were identified. Ran pairwise normalized-text similarity and token coverage across the whole cluster and hand-read every pair above 0.55 similarity or 0.9 coverage. Compared all 81 SHA-256 values against the 1,612 checksummed records in master-inventory.json. Fetched six out-of-cluster files read-only to settle supersession questions: the signed 2020 Development Process Manual, four March 2021 Infrastructure Improvements Agreements, and the Planning UDD copy of the Development Review Application. Listed the live DRC/IIA directory to confirm what the City still publishes.",
 "classification_only": True,
 "shared_state_written": [],
 "precedent_applied": "Four lines from earlier lanes decide this directory. (1) The form-versus-standard split from the Planning UDD and code-enforcement lanes, extended by this lane's brief to name checklists explicitly. (2) The construction-documents line between a statement of requirements, which is retained, and the blank instrument it describes, which is not. (3) The DPM lane rule that a pre-2020 chapter draft is superseded by the signed June 2, 2020 consolidated manual. (4) The code-enforcement rule that City data snapshots are retained while forms are not.",
 "image_only_records": {
  "count": 5,
  "note": "Five PDFs in this directory carry no text layer at all, and four of them are the most substantive records in it. A pipeline that classifies on extracted text would have scored them as empty and left them pending indefinitely. They were rendered through pdf.js in a headless browser and read.",
  "ids": ["src-28372ac121eeb0ba", "src-e5b815c2a314724a", "src-db74fbcfb6e04b9e", "src-f0d6744711099a88", "src-7700b730bdf09a20"],
  "what_rendering_revealed": "Two enacted ordinances (O-2018-020 and O-2014-024), two enacted resolutions (R-2012-100 and R-2013-115), and one specimen insurance certificate. None of the four enactment numbers appears in any filename."
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 1,
  "cross_inventory_byte_collisions": 1,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 2,
  "relationships_found_by_normalized_text_or_token_coverage": 19,
  "note": "Hashing found 2 of the 21 relationships in this directory. One internal pair is byte-identical (the Hydrology- and Transportation-named copies of the same 2015 information sheet) and one pending file is byte-identical to an already-validated, already-archived record. The other 19 are version chains, format twins, and cross-directory re-encodings that only normalized-text and token-coverage comparison find. The Development Review Application is the sharpest case: a third City copy of a form whose other two copies are byte-identical to each other, re-encoded to a different byte length and a different hash, with exactly one differing word."
 },
 "version_families_resolved": [
  {"family": "Infrastructure Improvements Agreements", "members": 5, "outcome": "Four pre-2021 editions superseded by the validated March 2021 agreements in DRC/IIA; Procedure C retained because the City no longer publishes it and the adopted manual still requires it."},
  {"family": "Drainage and Transportation Information Sheet", "members": 6, "outcome": "One byte-identical duplicate; five editions from 09/2015 through 11/2018, all excluded as submittal forms with the chain recorded."},
  {"family": "Private facility drainage covenant", "members": 4, "outcome": "Three copies of the #1 edition collapsed to one canonical; the December 2022 edition recorded as its substantive successor. All excluded as transactional instruments."},
  {"family": "Permanent easement", "members": 3, "outcome": "Three copies of one instrument collapsed to one canonical."},
  {"family": "ESC plan and permit requirement in the DRC process", "members": 2, "outcome": "June 2018 superseded by July 2018; the July edition retained for its threshold criteria."},
  {"family": "Stormwater quality plan information sheet and fee schedule", "members": 2, "outcome": "Earlier edition superseded; current edition retained for its fee schedule."},
  {"family": "SO-19 notice to contractor", "members": 2, "outcome": "March 2018 superseded by December 2022; the 2022 notes retained as standard plan notes."},
  {"family": "General fee schedule", "members": 2, "outcome": "The 2018 schedule and the 2017 fee-update notice both superseded by the validated January 2025 General Planning Fee Schedule."},
  {"family": "Figure 20 bond forms", "members": 2, "outcome": "Both excluded; the gender-neutral edition that makes the City an obligee identified as the later one."},
  {"family": "Revocable licence agreement", "members": 2, "outcome": "Both excluded; the 2020 edition identified as the later one."},
  {"family": "Stormwater control ESC permit", "members": 2, "outcome": "Both excluded; the 2018 edition adds the $100 inspection fee."},
  {"family": "Form DRWS", "members": 2, "outcome": "Both excluded; the PDF edition identified as post-Integrated Development Ordinance."},
  {"family": "Plat drainage easement language", "members": 2, "outcome": "Word copy duplicate of the retained PDF."}
 ],
 "integration_flags": [
  {"severity": "dating",
   "affects": ["src-db74fbcfb6e04b9e", "src-f0d6744711099a88"],
   "finding": "Both impact-fee files are named ...-2016.pdf and neither is from 2016. DRS-ImpactFees-CCIPLegislation-2016.pdf is enacted Resolution R-2012-100, passed by the Twentieth Council on Bill R-12-98, adopting the CCIP for 2012 to 2022. DRS-ImpactFees-CCIPLegislationAmended-2016.pdf is enacted Resolution R-2013-115, on Bill R-13-248. Neither enactment number, bill number, nor year appears in either filename, and neither file has a text layer, so nothing short of rendering the pages reveals this.",
   "recommended_action": "Title and date both records from the rendered enactment sheets, not the filenames. This is the second directory in two lanes where Municipal Development and Planning filename dates are wrong by years; treat filename dates across documents.cabq.gov as unverified."},
  {"severity": "dating",
   "affects": ["src-7f0d4c4f77185c6f", "src-57c8271474f540b9"],
   "finding": "The filename that carries a date is the newer file and the one that looks undated is the older. \"ESC plans and Permit in DRC process July2018.pdf\" is Revision July 2018; \"ESC plans and Permit in DRC process.pdf\" is Revision June 2018. A reader who assumed the plain name was the current version would apply the wrong disturbance threshold: the June edition tests \"more than an acre\", the July edition tests one acre or greater or any size directly connected to the Rio Grande.",
   "recommended_action": "Supersede the June edition to the July one and never link the plain filename as current."},
  {"severity": "consistency",
   "affects": ["src-9184833c9337a678", "src-42559b8b35af458e"],
   "finding": "Two different documents are published as IIA%20B.pdf. The one in this cluster sits at documents.cabq.gov/planning/DevelopmentReviewServices/IIA%20B.pdf and is a pre-Integrated-Development-Ordinance Procedure B agreement. The one the site already archives and links sits one level deeper at .../DRC/IIA/IIA%20B.pdf and is the March 2021 edition. They differ in bytes, length, and content (ratio 0.7515).",
   "recommended_action": "Keep the full path in any provenance record. A basename-keyed check would treat these as the same file."},
  {"severity": "gap",
   "affects": ["src-567244356665a527"],
   "finding": "The site's Infrastructure Improvements Agreements section publishes Procedure A and Procedure B agreements from the City's maintained DRC/IIA directory. That directory, listed 2026-09-11, contains no Procedure C file, yet the adopted June 2020 Development Process Manual still defines Procedure C at Section 2-3(C)(3) and requires an \"Improvement Agreement (IIA) - Procedure C\" for City construction of public infrastructure by DMD contract.",
   "recommended_action": "Treat src-567244356665a527 as the only published copy of a currently required agreement and place it alongside the Procedure A and B entries, labelled with its Figure 13 provenance and the absence of a newer City edition."},
  {"severity": "storage",
   "affects": ["src-d74108ddea65eb7d"],
   "finding": "The NPDES Manual is 37,140,337 bytes on its own, larger than every other record in this batch combined. The checkpoint already carries an open blocker for 17 originals totalling 67,526,043 bytes awaiting separate explicit R2 upload approval.",
   "recommended_action": "Do not fold this file into a routine upload batch. The combined archive footprint of all 19 approved records is 42,485,572 bytes, of which this single manual is 87 per cent."},
  {"severity": "disclosure",
   "affects": ["src-150a847f768d749c"],
   "finding": "FeeSchedule links.docx is an internal staff worklist headed \"Documents to Delete from Server\" that the City published to its public document library by mistake. It lists internal server paths and pages queued for removal.",
   "recommended_action": "Exclude and do not surface. It is recorded here only so the exclusion is not revisited."}
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "superseded": counts["superseded"],
  "duplicate": counts["duplicate"],
  "excluded": counts["excluded"],
  "requires_human_review": 0
 },
 "link_check": {
  "checked": 81, "http_200": 81, "failed": 0, "size_mismatches": 0,
  "method": "Full HTTP GET with a browser user agent, 2026-09-11.",
  "inventory_gap": "Unlike the construction-documents cluster, every one of these 81 inventory records carries size_bytes null and checksum_sha256 null: none had ever been downloaded. There was therefore no recorded length to check a fetch against, and the size_bytes and checksum_sha256 values in this artifact are first measurements rather than confirmations. Seven records also carry direct_file_url null and are addressed only by source_url; those seven are the Word files, and their authoritative_url here is that source_url, which returned the expected document.",
  "records_with_null_inventory_size": 81,
  "records_with_null_inventory_direct_file_url": 7
 },
 "approved_for_addition": approved,
 "superseded": superseded,
 "duplicate": duplicates,
 "excluded": excluded,
 "archival_note": "All 19 approved records are static PDFs and are therefore inventory-only until an R2 archive object exists for each and its public download, exact size, SHA-256, and authoritative-source provenance are verified. An official cabq.gov link alone is not site-ready. Combined archive footprint if authorized: 42,485,572 bytes, dominated by the 37,140,337-byte NPDES Manual. See integration_flags.",
 "integration_note": "Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. Every superseded and duplicate row carries a canonical_id, and six of those canonicals are already validated records outside this cluster (src-0b9dc46fbf32cfb7, src-65a7c910647e2670, src-42559b8b35af458e, src-ea0ba81f2420f90f, src-58eba820883efd1a, src-0752fa3cfed34f87, src-0c7c3af1438a8349). The 19 approved rows each carry a title, a 20-to-50-word description, a proposed_canonical_page, and cross_listings where a second page applies. This artifact raises no requires-human-review row: every relationship in the directory resolved on measurement.",
 "checksum_note": "Every checksum_sha256 and size_bytes in this artifact was measured on 2026-09-11 from the bytes actually fetched from the authoritative URL. The inventory held no prior value for either field on any of the 81 records, so these are first measurements and Codex should write them into the inventory alongside the status. They are source-of-record checksums for provenance comparison, not R2 object checksums; an R2 archive checksum must still be computed from the uploaded object at archive time.",
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write", "no site content change", "no R2 upload", "no commit, merge, or deploy"]
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
