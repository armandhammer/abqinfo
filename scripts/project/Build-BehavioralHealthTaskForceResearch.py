"""Claude research lane. The second link harvest, second slice: the City and
County Behavioral Health Task Force papers of 2014 and 2015.

These are NOT inventory candidates: none has an inventory id and nothing here can
be applied through Update-Candidate.ps1. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-14.
"""

import collections
import datetime
import glob
import json
import os
import re
import urllib.parse

OUT = (r'C:\Users\ben\Documents\ABQinfo\project-state\discovery'
       r'\behavioral-health-task-force-research-2026-09-14.json')
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
DISC = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\h2')

ABOUT = 'content/about/_index.md'
CITYDATA = 'content/city-data/_index.md'
SAFETY = 'content/city-data/public-safety-data.md'
DEMOG = 'content/city-data/demographics.md'

inv = json.load(open(INV, encoding='utf-8'))

M, MAGIC, URL, CODE, SRC = {}, {}, {}, {}, {}
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    M[p[0]] = {"size_bytes": int(p[2]), "checksum_sha256": p[3]}
    MAGIC[p[0]], URL[p[0]], CODE[p[0]], SRC[p[0]] = p[4], p[5], p[1], p[6].strip()

SLICE = sorted(i for i in M if 'h2-053' <= i <= 'h2-102')

ALL_SHA, ARCH_SHA = {}, {}
for x in inv['candidates']:
    s = x.get('checksum_sha256')
    if s:
        ALL_SHA.setdefault(s, (x['id'], x.get('status')))
        if x.get('status') in ('validated', 'published', 'archived', 'implemented'):
            ARCH_SHA.setdefault(s, x['id'])


def norm(u):
    u = urllib.parse.unquote(u or '').strip()
    if u.endswith('/view'):
        u = u[:-5]
    s = urllib.parse.urlsplit(u)
    return (s.netloc.lower().replace('www.', '') + s.path.rstrip('/')).lower()


INV_URL = {}
for x in inv['candidates']:
    for k in ('direct_file_url', 'source_url'):
        if x.get(k):
            INV_URL.setdefault(norm(x[k]), (x['id'], x.get('status')))

PRIOR_SHA = {}
for f in glob.glob(os.path.join(DISC, '*.json')):
    if os.path.abspath(f) == os.path.abspath(OUT):
        continue
    try:
        d = json.load(open(f, encoding='utf-8-sig'))
    except Exception:
        continue
    if not isinstance(d, dict):
        continue
    for b in ('approved_for_addition', 'duplicate', 'superseded', 'requires_human_review', 'excluded',
              'add_to_inventory', 'do_not_add', 'needs_a_decision_from_a_person'):
        for r in d.get(b) or []:
            if isinstance(r, dict) and r.get('checksum_sha256'):
                PRIOR_SHA.setdefault(r['checksum_sha256'],
                                     (os.path.basename(f), r.get('id') or r.get('local_ref')))

SHA_HIT = {i: ALL_SHA[M[i]['checksum_sha256']] for i in SLICE if M[i]['checksum_sha256'] in ALL_SHA}
URL_HIT = {i: INV_URL[norm(URL[i])] for i in SLICE if norm(URL[i]) in INV_URL}
ART_HIT = {i: PRIOR_SHA[M[i]['checksum_sha256']] for i in SLICE
           if M[i]['checksum_sha256'] not in ALL_SHA and M[i]['checksum_sha256'] in PRIOR_SHA}
BYHASH = collections.defaultdict(list)
for i in SLICE:
    BYHASH[M[i]['checksum_sha256']].append(i)
INTERNAL = {x: sorted(v, key=lambda z: (len(URL[z]), z))[0]
            for v in BYHASH.values() if len(v) > 1
            for x in sorted(v, key=lambda z: (len(URL[z]), z))[1:]}


def pages(i):
    n = len(re.findall(rb'/Type\s*/Page[^s]', open(os.path.join(SP, 'files', i + '.bin'), 'rb').read()))
    return n or None


def text(i):
    p = os.path.join(SP, 'txt', i + '.txt')
    return open(p, encoding='utf-8', errors='replace').read() if os.path.exists(p) else ''


LC = ("HTTP 200 verified 2026-09-14 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes, "
      "container verified by leading bytes, and every PDF tested for its end-of-file marker.")

AG = "task force agendas"
NT = "task force meeting notes"
WG = "working group papers"
RC = "recommendations and funding"
EX = "exhibits presented to the task force"
BG = "commissioned analysis"

R = "read by rendering"


def ag(d, name="Task Force on Behavioral Health"):
    return ("The agenda for the %s meeting of %s, the joint City and County body convened in 2014 to examine how "
            "Albuquerque responds to behavioural health crises." % (name, d))


D = {
 # ---- agendas ------------------------------------------------------------
 'h2-054': ("Task Force on Mental Health agenda, 26 June 2014", AG,
   ag("26 June 2014", "Task Force on Mental Health"),
   "157,474 bytes. Opens: AGENDA TASK FORCE ON MENTAL HEALTH, Thursday, June 26th, 2014, 5:30 p.m. - 7:30 p.m., Albuquerque City Council.",
   ABOUT, [{"page": SAFETY, "reason": "Crisis response and policing."}],
   "The body is named Task Force on Mental Health here and Task Force on Behavioral Health from July onward. Same body, renamed."),
 'h2-057': ("Task Force on Behavioral Health agenda, 16 July 2014", AG, ag("16 July 2014"),
   "144,146 bytes. Opens: AGENDA TASK FORCE ON BEHAVIORAL HEALTH, Wednesday, July 16th, 2014, 5:30 p.m. - 7:30 p.m., Bernalillo County.",
   ABOUT, [{"page": SAFETY, "reason": "Crisis response and policing."}], None),
 'h2-059': ("Task Force on Behavioral Health agenda, 7 August 2014", AG, ag("7 August 2014"),
   "80,882 bytes. Opens: TASK FORCE ON BEHAVIORAL HEALTH AGENDA, Thursday, August 7th, 2014, 5:30 p.m. - 7:30 p.m., City Council Comm.",
   ABOUT, [{"page": SAFETY, "reason": "Crisis response and policing."}], None),
 'h2-058': ("Task Force on Behavioral Health agenda, 21 August 2014", AG, ag("21 August 2014"),
   "66,844 bytes. Opens: TASK FORCE ON BEHAVIORAL HEALTH AGENDA, Thursday, August 21st, 2014, 5:30 p.m. - 7:30 p.m., City Council Com.",
   ABOUT, [{"page": SAFETY, "reason": "Crisis response and policing."}], None),
 'h2-060': ("Task Force on Behavioral Health agenda, 18 September 2014", AG, ag("18 September 2014"),
   ("7,899 bytes, one of the two smallest files in this lane. Opens: TASK FORCE ON BEHAVIORAL HEALTH AGENDA, "
    "Thursday, September 18, 2014, 2:00-6:00 p.m., City Council Committee."),
   ABOUT, [{"page": SAFETY, "reason": "Crisis response and policing."}], None),
 'h2-061': ("Task Force on Behavioral Health agenda, 25 September 2014", AG, ag("25 September 2014"),
   "7,825 bytes, the smallest file in this lane. Opens: TASK FORCE ON BEHAVIORAL HEALTH AGENDA, Thursday, September 25, 2014, 3:30-7:30 p.m., City Council Comm.",
   ABOUT, [{"page": SAFETY, "reason": "Crisis response and policing."}], None),
 'h2-055': ("Task Force on Behavioral Health agenda, 2 October 2014", AG, ag("2 October 2014"),
   "7,234 bytes. Opens: TASK FORCE ON BEHAVIORAL HEALTH AGENDA, Thursday, October 2, 2014, 5:30-7:30 p.m., City Council Committee Room.",
   ABOUT, [{"page": SAFETY, "reason": "Crisis response and policing."}], None),
 'h2-056': ("Task Force on Behavioral Health agenda, 22 January 2015", AG, ag("22 January 2015"),
   "138,165 bytes. Opens: TASK FORCE ON BEHAVIORAL HEALTH AGENDA, Thursday, January 22, 2015, 5:30 p.m. - 7:00 p.m., City Council Comm.",
   ABOUT, [{"page": SAFETY, "reason": "Crisis response and policing."}], None),
 # ---- meeting notes ------------------------------------------------------
 'h2-081': ("Task Force on Mental Health meeting notes, 26 June 2014", NT,
   ("The notes of the task force's first meeting, recording the opening remarks and what members said as the body "
    "began examining Albuquerque's behavioural health response."),
   "207,212 bytes. Opens: Meeting Notes for Task Force on Mental Health for June 26, 2014, Brief Remarks by Mr. Andy Vallejos.",
   ABOUT, [{"page": SAFETY, "reason": "Crisis response and policing."}], None),
 'h2-084': ("Task Force on Behavioral Health meeting notes, 16 July 2014", NT,
   ("The notes of the task force's meeting of 16 July 2014, recording the discussion as the body moved from mental "
    "health to the wider behavioural health remit."),
   "199,555 bytes. Opens: Meeting Notes for Task Force on Behavioral Health for July 16th, 2014, Brief Remarks by Mr. Andy Vall.",
   ABOUT, [{"page": SAFETY, "reason": "Crisis response and policing."}], None),
 'h2-083': ("Task Force on Behavioral Health meeting notes, 7 August 2014", NT,
   ("The notes of the task force's meeting of 7 August 2014, opening with the list of those present and recording "
    "what each working group reported."),
   "353,130 bytes. Opens: Meeting Notes for Task Force on Behavioral Health for August 7, 2014, Present for Meeting.",
   ABOUT, [{"page": SAFETY, "reason": "Crisis response and policing."}], None),
 'h2-082': ("Task Force on Behavioral Health meeting notes, 21 August 2014", NT,
   ("The notes of the task force's meeting of 21 August 2014, recording attendance and the discussion of the "
    "working groups' findings."),
   "220,501 bytes. Opens: Meeting Notes for the Task Force on Behavioral Health, August 21st, 2014, Present for Meeting.",
   ABOUT, [{"page": SAFETY, "reason": "Crisis response and policing."}], None),
 'h2-095': ("Task Force on Behavioral Health meeting notes, 22 January 2015", NT,
   ("The notes of the task force's meeting of 22 January 2015, the last in the published series and the only one "
    "from the year after the body's main work."),
   "211,073 bytes. Opens: Meeting Notes for Task Force on Behavioral Health January 22, 2015, Brief Remarks by Mr. Andy Vallejo.",
   ABOUT, [{"page": SAFETY, "reason": "Crisis response and policing."}], None),
 # ---- working group papers ----------------------------------------------
 'h2-097': ("Task Force on Behavioral Health working groups", WG,
   ("The task force's statement of what its working groups were for and what each was asked to produce, the "
    "structure under which the rest of these papers were written."),
   "252,779 bytes. Opens: Task Force on Behavioral Health Working Groups, The overarching goal of the working groups is to produce.",
   ABOUT, [], None),
 'h2-072': ("Working group 1: gaps analysis summary, 16 July 2014", WG,
   ("The summary of the gaps analysis group's discussion of what services and resources exist and where the gaps "
    "are, naming the members present and absent."),
   ("130,064 bytes. Opens: Summary of Group # 1: Gaps Analysis (Formally known as: Identifying Services and "
    "Resources), Wednesday July 16, 2014, Team Members."),
   ABOUT, [], None),
 'h2-073': ("Working group discussion: interactions with the court systems, 25 July 2014", WG,
   ("The notes of the group's discussion of how behavioural health cases move through the courts, covering "
    "warrants, misdemeanour statutes, competency evaluations and dangerousness."),
   ("280,921 bytes, " + R + " because the file carries no text layer. It opens Discussion July 25, 2014, lists "
    "those present including NM Representative Rick Miera, and is headed Discussion: Interactions with the Court "
    "Systems."),
   ABOUT, [{"page": SAFETY, "reason": "Criminal justice and behavioural health."}], None),
 'h2-079': ("Interaction with court systems: competency discussion, 8 August 2014", WG,
   ("The notes of a working meeting on competency proceedings, recording how evaluations are ordered, who pays for "
    "them and where the delays arise in Metro and District Court."),
   ("959,832 bytes, " + R + ". It is headed Interaction with Court Systems 8/8/14 and lists the participants, "
    "including a Metropolitan Mental Health Specialty Court judge, public defenders, an assistant district "
    "attorney and court programme staff, all named in their professional capacities."),
   ABOUT, [{"page": SAFETY, "reason": "Criminal justice and behavioural health."}],
   "The same file is also published under a copy_of name; that copy is recorded as a duplicate in this artifact."),
 'h2-091': ("Discussion group: interventions with the court system", WG,
   ("The group's written review of how drug courts and mental health courts work in New Mexico, drawing on state "
    "sentencing commission findings and the Bernalillo County Metropolitan Mental Health Specialty Court's own "
    "caseload."),
   ("1,909,671 bytes, " + R + ". Headed Discussion Group: Interventions with the Court System, it cites a 2013 New "
    "Mexico Sentencing Commission report on length of stay and records that the Metropolitan Mental Health "
    "Specialty Court began in 2003 with about 100 defendants participating."),
   ABOUT, [{"page": SAFETY, "reason": "Criminal justice and behavioural health."}], None),
 'h2-074': ("Long-term care and maintenance subcommittee meeting notes, 22 July 2014", WG,
   ("The notes of the subcommittee considering long-term care and maintenance for people with serious behavioural "
    "health conditions, one of the task force's standing groups."),
   "372,141 bytes. Opens: Long term care and maintenance subcommittee of the Behavioral health committee, Meeting notes 7/22/14.",
   ABOUT, [], None),
 'h2-088': ("Summary of recommendations from the long-term services group, 25 September 2014", WG,
   ("The long-term services group's summary of what it recommended to the task force, circulated in draft over the "
    "names of its authors."),
   "331,794 bytes. Opens: Komaromy DRAFT 20140925, Summary of recommendations from long-term services group, Miriam Komaromy.",
   ABOUT, [], "Marked DRAFT in its own first line. Label it a draft."),
 'h2-075': ("Case management in Albuquerque: background paper", WG,
   ("The group's account of how case management was funded and delivered in Albuquerque, tracing what changed when "
    "the state removed case management as a Medicaid service around 2007."),
   "489,353 bytes. Opens: Albuquerque Case Management, Medicaid: Prior to 2007, Case Management was a Medicaid service.",
   ABOUT, [], None),
 'h2-089': ("Case management subgroup paper, 12 September 2014", WG,
   ("The case management subgroup's paper for the task force, setting out what case management is and what the "
    "joint City and County system was providing."),
   "846,246 bytes. Opens: Case Management Subgroup, Bernalillo County/City of Albuquerque Behavioral Health Task Force, What is.",
   ABOUT, [], None),
 'h2-090': ("Case management subgroup executive summary, 12 September 2014", WG,
   ("The executive summary of the case management subgroup's findings, the short form of its paper for the full "
    "task force."),
   "609,781 bytes. Opens: Albuquerque/Bernalillo County BH Task Force, Case Management Subgroup, EXECUTIVE SUMMARY.",
   ABOUT, [], None),
 'h2-077': ("Housing workgroup meeting summaries, July to August 2014", WG,
   ("The housing workgroup's record of three meetings, compiling an inventory of housing programmes and "
    "identifying the gaps in supportive housing available in Albuquerque."),
   ("231,576 bytes, " + R + ". Headed Housing Workgroup, it summarises meetings of July 25th, August 1st and "
    "August 18th, and records that most rental assistance programmes are scattered-site with no supervision."),
   ABOUT, [], None),
 'h2-092': ("Recommendations from the housing workgroup, 12 September 2014", WG,
   ("The housing workgroup's recommendations to the task force, opening from the position that the lack of safe and "
    "affordable housing is one of the central obstacles."),
   "138,868 bytes. Opens: Recommendations from Housing Workgroup, Introduction, The lack of safe and affordable housing is one o.",
   ABOUT, [], None),
 'h2-102': ("Supportive Housing Project presentation", WG,
   ("A single-board presentation setting out the supportive housing proposal - the problem, the programme "
    "structure, the population to be served, the funding requested and the outcomes expected."),
   ("4,068,196 bytes, " + R + ". Titled SUPPORTIVE HOUSING PROJECT, exported from Prezi, it records County funding "
    "requested of $1.1 million for 75 units with intensive services and a City request pending for a further $1.1 "
    "million and 75 units."),
   ABOUT, [], None),
 'h2-094': ("Roadblocks to accessing services: a caregiver's perspective", WG,
   ("A presentation to the task force on what carers encounter when seeking help - the lack of early support, the "
    "paperwork and travel, the absence of a clear route, and the criminalisation of mental illness."),
   ("413,074 bytes. Its text is the slide headings: Roadblocks to Accessing Services, A Caregiver's Perspective, "
    "Process Roadmap Analogy, Impact on families/caretakers, Crisis management, Criminalization, and under "
    "Solutions, Erase the stigma and Decriminalize mental health."),
   ABOUT, [],
   ("General and structural, and it names nobody. Distinct from the individual case narrative in this same set, "
    "which this artifact does not decide.")),
 # ---- recommendations and funding ---------------------------------------
 'h2-071': ("Formal recommendations of the City and County Behavioral Health Task Force", RC,
   ("The task force's own formal recommendations to the City and the County, the output the whole body of working "
    "papers was assembled to produce."),
   "175,634 bytes. Opens: City / County Behavioral Health Task Force Recommendations, Remembering that all the recommendations.",
   ABOUT, [{"page": CITYDATA, "reason": "A City policy recommendation."}], None),
 'h2-067': ("Summary of City, County and state behavioral health task force recommendations", RC,
   ("A consolidated summary of what the City, County and state behavioural health task forces had each "
    "recommended, arranged by theme starting with crisis stabilisation."),
   "397,086 bytes. Opens: SUMMARY OF CITY/COUNTY/STATE BEHAVIORAL HEALTH TASK FORCE RECOMMENDATIONS, A. CRISIS STABILIZATION.",
   ABOUT, [], None),
 'h2-065': ("Proposed funding streams for the task force's recommendations", RC,
   ("The task force's account of where the money for each of its recommendations might come from, organised under "
    "the same headings as the recommendations themselves."),
   "356,484 bytes. Opens: Proposed Funding Streams for the Recommendations of the Task Force on Behavioral Health, A. Crisis St.",
   ABOUT, [{"page": CITYDATA, "reason": "Proposed City spending."}], None),
 'h2-086': ("Final recommendations presented to the task force: crisis stabilization centre", RC,
   ("The presentation of the final recommendations to the task force, centred on a crisis stabilization centre as "
    "the principal proposal of 2014."),
   "564,388 bytes. Opens: Task Force on Behavioral Health 2014, Crisis Stabilization Center.",
   ABOUT, [], None),
 'h2-101': ("Crisis stabilization centre talking points", RC,
   ("The task force's statement of the problem a crisis stabilization centre would solve, written as talking points "
    "about the load currently carried by psychiatric and other emergency rooms."),
   "239,367 bytes. Opens: CRISIS STABILIZATION CENTER, Problem/ Issue, Currently UNM-PSYCHIATRIC Emergency Room, other emergency.",
   ABOUT, [], None),
 'h2-053': ("Talking points on assisted outpatient treatment", RC,
   ("The task force's talking points on assisted outpatient treatment, opening on the question of informed consent "
    "that any discussion of compelled treatment has to address."),
   "252,674 bytes. Opens: TALKING POINTS ON ASSISTED OUTPATIENT TREATMENT, I. Informed Consent, Any meaningful discussion of assisted.",
   ABOUT, [], None),
 'h2-085': ("Draft Senate bill on assisted outpatient treatment, August 2014 version", RC,
   ("The August 2014 draft of a Senate bill on assisted outpatient treatment, prepared for the 2015 legislative "
    "session and circulated to the task force as it considered the question."),
   "111,695 bytes. Opens: 8/5/14, SENATE BILL, 52ND LEGISLATURE - STATE OF NEW MEXICO - FIRST SESSION, 2015, INTRODUCED BY.",
   ABOUT, [],
   "A draft bill circulated to the task force, not an enacted state instrument. Label it a draft working paper of the task force."),
 'h2-087': ("Report on the activities of the Behavioral Health Task Force: crisis encounters and intervention", RC,
   ("The report on what the task force did on crisis encounters and intervention, one of the strands it divided its "
    "work into."),
   "367,769 bytes. Opens: Report on the Activities of the Behavioral Health Task Force: Crisis Encounters/Intervention, Prepare.",
   ABOUT, [{"page": SAFETY, "reason": "Crisis response and policing."}], None),
 # ---- commissioned analysis ---------------------------------------------
 'h2-062': ("Landscape of Behavioral Health in Albuquerque: city project report, October 2014", BG,
   ("The commissioned account of how behavioural health services are arranged in Albuquerque, produced with the "
    "University of New Mexico for the task force."),
   "1,402,830 bytes. Opens: October 15, 2014, Landscape of Behavioral Health in Albuquerque, A collaboration between the UNM Depar.",
   CITYDATA, [{"page": ABOUT, "reason": "Commissioned for a City task force."}],
   "A collaboration with the University of New Mexico. Attribute it to both."),
 'h2-063': ("Landscape of Behavioral Health in Albuquerque and Bernalillo County: gaps analysis", BG,
   ("The companion gaps analysis for Albuquerque and Bernalillo County, written by named academic authors for the "
    "task force alongside the landscape report."),
   "951,011 bytes. Opens: Landscape of Behavioral Health in Albuquerque/ Bernalillo County, Caroline Bonham, Tom Dauphinee, Sam.",
   CITYDATA, [{"page": ABOUT, "reason": "Commissioned for a City task force."}],
   "Named authors. Credit them."),
 'h2-098': ("Behavioral Health Crisis Triage Planning Initiative: crisis triage services continuum, 2004", BG,
   ("The City's 2004 crisis triage planning report, the earlier attempt at the same problem that the 2014 task "
    "force was working over ten years later."),
   "541,851 bytes. Opens: City of Albuquerque Behavioral Health Crisis Triage Planning Initiative, Crisis Triage Services Conti.",
   CITYDATA, [{"page": ABOUT, "reason": "An earlier City initiative on the same question."}],
   "A City report of 2004 republished as task force background. It is the oldest document in this lane by ten years."),
 # ---- exhibits -----------------------------------------------------------
 'h2-096': ("The Friendly Front Door: a community-based crisis service system", EX,
   ("A presentation given to the task force on a community-based crisis service system, delivered by the chief "
    "executive of a comparable programme from outside New Mexico."),
   "3,277,757 bytes. Opens: The Friendly Front Door: An Effective, Community-Based Crisis Service System, Neal Cash CEO Community.",
   ABOUT, [],
   "Presented to the task force by an outside organisation. Keep it as part of the body's record and attribute it to its author."),
 'h2-070': ("Fast Track and Medicaid enrolment for inmates at the Metropolitan Detention Center, 21 August 2014", EX,
   ("A presentation to the task force on the Fast Track programme, which links inmates leaving the Metropolitan "
    "Detention Center into community health and social services."),
   ("663,845 bytes, " + R + ". Its first slide reads Fast Track and Medicaid Enrollment for Inmates at MDC, August "
    "21, 2014, and the programme is described as identifying around 50 inmates a month with high behavioural and "
    "physical health needs."),
   ABOUT, [{"page": SAFETY, "reason": "Detention and re-entry."}], None),
 'h2-069': ("Crisis budgets from a comparable centre, February 2014", EX,
   ("A comparable provider's crisis service budgets, obtained as an exhibit so the task force could see what a "
    "crisis programme of that kind costs to run."),
   "57,631 bytes. Opens: Center for Health Care Services Crisis Budgets, UNIT, Object, Description, Crisis Care, Crisis Woodgroup.",
   ABOUT, [],
   "Another organisation's internal budget, gathered as an exhibit. Attribute it and do not present it as a City figure."),
 'h2-064': ("Construction cost guide used as a costing example", EX,
   ("A federal health network's per-square-foot construction cost guide, annotated as an example and used by the "
    "task force to cost a possible crisis facility."),
   ("986,693 bytes, " + R + ". Its first page is headed VAMC COST GUIDE - BUILDING TYPE, VISN 18: VA Southwest "
    "Health Care Network, valid through October 2014, with Albuquerque, NM as its first row - and is annotated by "
    "hand Example I."),
   ABOUT, [],
   ("A Department of Veterans Affairs document, kept because it is an exhibit inside the task force's own record "
    "and its first data row is Albuquerque. A reader who thinks exhibits by other authorities should be excluded "
    "would drop this one; the reasoning is on the row so the call can be reversed.")),
}

EXCLUDE = {
 'h2-066': ("New Mexico Behavioral Health and Health Services Resource Guide",
            "A statewide directory of behavioural health and health services, originally published by a New Mexico state body.",
            ("A standing publication of another authority, gathered by the task force as reference reading rather "
             "than produced by it. Its publisher is its authoritative source, and it is a statewide directory "
             "rather than a record of this body's work."),
            "state resource directory", "third_party_authority"),
 'h2-068': ("New Mexico Behavioral Health Purchasing Collaborative meeting packet, February 2014",
            "The meeting packet of a state purchasing collaborative, held in Santa Fe.",
            ("Another body's own meeting papers, gathered as background. The collaborative is the authoritative "
             "keeper of its own record; this is not a record of the City and County task force."),
            "another body's meeting papers", "third_party_authority"),
 'h2-076': ("House Joint Memorial 17 task force recommendations, November 2011",
            "The recommendations of an earlier state task force created by House Joint Memorial, three years before this one.",
            ("A prior state task force's own report, gathered as background reading. The Legislature is its "
             "authoritative source."),
            "prior state task force report", "third_party_authority"),
 'h2-078': ("Legislative Finance Committee report: Human Services Department behavioural health costs and outcomes",
            "A programme evaluation prepared for the New Mexico Legislative Finance Committee.",
            ("A state legislative committee's own evaluation, gathered as background. Same treatment as the "
             "committee's budget release below, and as the Attorney General's compliance guide excluded in the "
             "Council slice of this harvest."),
            "state legislative evaluation", "third_party_authority"),
 'h2-080': ("Legislative Finance Committee budget recommendation release, 9 January 2015",
            "A press release from the New Mexico Legislative Finance Committee announcing a $6.29 billion budget recommendation.",
            ("A state legislative committee's press release about the state budget, gathered as background. Not a "
             "record of this task force and not a City instrument."),
            "state legislative press release", "third_party_authority"),
 'h2-099': ("Newspaper opinion column on the response to mental illness",
            ("A printout of an Albuquerque Journal opinion column, written by two City Councillors and published "
             "by the newspaper."),
            ("Published by a newspaper, which holds the rights in it. The councillors' authorship does not make the "
             "Journal's publication a City record, and a printed copy of a copyrighted column is not the archive's "
             "to redistribute. If the argument matters, cite the column at its source."),
            "newspaper content", "third_party_copyright"),
}

PERSON = {
 'h2-093': {
  "title_for_reference": "A family member's account of one person's interaction with the system",
  "what_it_is": ("A first-person narrative, submitted to the task force through a family support organisation, "
                 "describing in dated detail a 26-year-old's psychiatric crises, police contacts, incarceration "
                 "and hospital treatment across 2013, written by that person's parent."),
  "why_this_lane_will_not_decide_it": {
   "it_is_health_information_about_a_private_individual": ("The subject is not an official, a company or a public "
                                                           "figure. He is a private person described through "
                                                           "suicidality, mania, psychosis, arrest and hospital "
                                                           "admission, at 7,982 characters of specific dated "
                                                           "detail."),
   "the_anonymisation_is_thin": ("He is called PT and my son, and the author is addressed by first name. But the "
                                 "account fixes dates, a county jail, a named hospital and a sequence of events - "
                                 "the kind of detail that does not need a name to identify someone to those who "
                                 "know them."),
   "the_city_published_it_and_that_is_not_the_same_question": ("It sits on a City task force page, which is an "
                                                               "argument that it is publishable. Whether an archive "
                                                               "should re-publish and index a private person's "
                                                               "psychiatric and criminal history is a different "
                                                               "question, and not one a research lane should "
                                                               "answer on its own."),
  },
  "what_i_am_asking": ("Does this archive re-publish personal health narratives that the City itself published? If "
                       "yes, this belongs with the rest of the task force record. If no, it should be excluded and "
                       "the reason recorded, rather than quietly added with its neighbours."),
  "the_precedent": ("This run has referred four other questions of this shape to a person: the Prescription Trails "
                    "guides, seven code enforcement notices one of which names three natural persons, the 173 "
                    "property flyers, and this. Each was about what the archive is for, not about what the file "
                    "is."),
  "what_this_row_does_not_do": "It does not quote the narrative, name anyone in it, or reproduce any of its detail beyond what is needed to state the question.",
  "package": "personal_health_narrative",
  "priority": 1,
 },
}

add, skip, person = [], [], []
for i in SLICE:
    r = {"local_ref": i, "inventory_id": None, "authoritative_url": URL[i],
         "filename": urllib.parse.unquote(URL[i].rstrip('/').split('/')[-1]),
         "harvested_from": SRC[i], "link_check": LC, "content_kind": 'PDF',
         "leading_bytes": MAGIC[i], "http_status": CODE[i], **M[i]}
    p = pages(i)
    if p:
        r["page_count"] = p
    if i in PERSON:
        r["recommendation"] = "put to a person before adding"
        r.update(PERSON[i])
        person.append(r)
    elif i in INTERNAL:
        r.update({"recommendation": "do not add",
                  "title_for_reference": "A second copy of the 8 August 2014 court systems notes",
                  "what_it_is": "A copy_of duplicate of the competency discussion notes already in this artifact.",
                  "why_not": ("Byte-identical to %s - the same %s bytes and the same SHA-256 - published under a "
                              "copy_of name by the content management system. Adding both would create two "
                              "candidates for one file." % (INTERNAL[i], format(M[i]['size_bytes'], ','))),
                  "category": "content management duplicate", "package": "duplicate",
                  "byte_identical_to": {"local_ref": INTERNAL[i], "in_this_artifact": True}})
        skip.append(r)
    elif i in EXCLUDE:
        t, what, why, cat, pkg = EXCLUDE[i]
        r.update({"recommendation": "do not add", "title_for_reference": t, "what_it_is": what,
                  "why_not": why, "category": cat, "package": pkg})
        skip.append(r)
    else:
        t, group, desc, ev, canon, cross, caution = D[i]
        r.update({"recommendation": "add to the inventory as a new candidate", "title": t, "group": group,
                  "description": desc, "evidence": ev, "description_word_count": len(desc.split()),
                  "proposed_canonical_page": canon, "cross_listings": cross})
        if caution:
            r["caution"] = caution
        add.append(r)

rows = add + skip + person
assert len(rows) == len(SLICE), (len(rows), len(SLICE))
bygroup = collections.Counter(r['group'] for r in add)
add_bytes = sum(r['size_bytes'] for r in add)
agn = [r for r in add if r['group'] == AG]
ntn = [r for r in add if r['group'] == NT]
notext = [i for i in SLICE if len(re.sub(r'\s+', '', text(i))) < 40]

artifact = {
 "batch_id": "behavioral-health-task-force-research-2026-09-14",
 "lane": "Claude research lane: the City and County Behavioral Health Task Force papers, 2014-2015",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-14. This completes the second link harvest.",
 "THIS_ARTIFACT_IS_NOT_A_TRIAGE_OF_CANDIDATES": {
  "what_that_means": "None of these files has an inventory id. Every row carries inventory_id: null and a recommendation rather than a recommended_status.",
  "the_three_values_used": "add to the inventory as a new candidate; do not add; and put to a person before adding, used for exactly one file.",
  "so_it_cannot_be_applied_the_usual_way": "Update-Candidate.ps1 cannot act on any row here.",
 },
 "cluster": ("The working record of the joint City and County Behavioral Health Task Force, convened in 2014 after "
             "Albuquerque's response to people in mental health crisis came under sustained scrutiny."),
 "scope": "All %d task force files from the second harvest." % len(SLICE),
 "what_is_in_it": {
  "agendas": len(agn),
  "meeting_notes": len(ntn),
  "working_group_papers": bygroup.get(WG, 0),
  "recommendations_and_funding": bygroup.get(RC, 0),
  "commissioned_analysis": bygroup.get(BG, 0),
  "exhibits_presented_to_it": bygroup.get(EX, 0),
  "the_arc": ("Eight agendas from June 2014 to January 2015, five sets of meeting notes, the working groups' own "
              "papers on courts, case management, housing and long-term care, then the formal recommendations, the "
              "proposed funding streams and the crisis stabilization centre proposal they converged on."),
 },
 "this_body_kept_notes_as_well_as_agendas": {
  "what": "Five of the eight published meetings have meeting notes published beside the agenda.",
  "why_it_matters": ("This run has invoked the missing-minutes exception four times. The Council slice of this same "
                     "harvest found a body with a complete agenda-and-minutes series. This one is in between: it "
                     "published notes for most meetings but not all, and calls them meeting notes rather than "
                     "minutes."),
  "the_three_meetings_with_no_notes_published": ("18 September 2014, 25 September 2014 and 2 October 2014 have "
                                                 "agendas here and no corresponding notes. Whether notes were "
                                                 "taken and not published, or not taken, this page does not say - "
                                                 "and no exhaustive search has been run for them."),
  "so_no_exception_is_claimed": ("The agendas are recommended as agendas, on their own merits as records of what "
                                 "the body set out to discuss, not under the missing-minutes exception."),
 },
 "THE_ONE_FILE_THIS_LANE_WILL_NOT_DECIDE": {
  "what_it_is": ("A parent's dated, first-person account of a 26-year-old's psychiatric crises, police contacts, "
                 "incarceration and hospital treatment, submitted to the task force through a family support "
                 "organisation."),
  "why_it_is_different_from_everything_else_here": ("Every other paper in this set describes a system. This one "
                                                    "describes a person - a private individual, not an official or "
                                                    "a company - through the most sensitive facts there are."),
  "what_i_am_asking": "Whether this archive re-publishes personal health narratives that the City itself published.",
  "what_this_artifact_does_not_do": "It does not quote the narrative, name anyone in it, or reproduce its detail beyond what is needed to state the question.",
  "the_companion_that_is_recommended": ("A caregiver's perspective presentation in the same set is recommended "
                                        "without hesitation: it is general and structural and names nobody. That "
                                        "is the line."),
 },
 "the_rule_applied_to_everything_else": {
  "the_question": ("Half of these files were written by somebody other than the City. Which of them belong to the "
                   "task force's record and which merely sat on its reading list?"),
  "the_rule": ("A document is kept if the task force produced it, commissioned it, or was given it as an exhibit - "
               "because that is what a body's record consists of. A document is not added if it is a standing "
               "publication of another authority that the task force merely gathered as background, because its "
               "publisher is its authoritative source."),
  "kept_under_it": ("The University of New Mexico landscape and gaps reports (commissioned), the 2004 City crisis "
                    "triage report (a City report), an out-of-state crisis programme presentation and a comparable "
                    "provider's budgets (exhibits), the Fast Track detention presentation (an exhibit), and a "
                    "federal construction cost guide annotated Example I and used to cost a facility."),
  "not_added_under_it": ("A statewide services directory, a state purchasing collaborative's own meeting packet, a "
                         "2011 state task force report, a Legislative Finance Committee evaluation, and that "
                         "committee's budget press release."),
  "and_one_on_a_different_ground": ("A printout of an Albuquerque Journal opinion column. Two City Councillors "
                                    "wrote it, but the newspaper published it and holds the rights; a printed copy "
                                    "of a copyrighted column is not the archive's to redistribute. Cite it at "
                                    "source."),
  "where_this_could_reasonably_be_drawn_differently": ("The federal cost guide is the closest call. It is another "
                                                       "authority's publication and an exhibit at the same time. "
                                                       "Its row says so, so the call can be reversed without "
                                                       "re-reading the file."),
 },
 "method": ("Fetched and measured every file, verified each container by leading bytes, tested every PDF for its "
            "end-of-file marker, counted pages from the file structure, extracted text from all of them, rendered "
            "the seven that yielded none and read the renders, and swept every checksum against all checksummed "
            "inventory records, every inventory URL and every row of every saved artifact."),
 "classification_only": True,
 "shared_state_written": [],
 "already_archived_check": {
  "rule_applied": "For proposed additions, test against every inventory record rather than only the archived ones, and by URL as well as by checksum.",
  "cross_inventory_byte_collisions": len(SHA_HIT),
  "cross_inventory_url_collisions": len(URL_HIT),
  "collisions_with_earlier_artifacts_in_this_run": len(ART_HIT),
  "internal_byte_collisions": len(INTERNAL),
  "archived_records_compared_against": len(ARCH_SHA),
  "all_checksummed_records_compared_against": len(ALL_SHA),
  "inventory_urls_compared_against": len(INV_URL),
  "artifact_rows_compared_against": len(PRIOR_SHA),
  "result": "Nothing here is in the inventory. The only byte collision is a copy_of duplicate inside the lane.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": len(INTERNAL),
  "note": ("One pair: the 8 August 2014 court systems notes are published twice, once plain and once under a "
           "copy_of name, byte-identical. The plainer name is taken as the record and the copy is recorded as a "
           "duplicate - the same treatment this run has given copy_of prefixes throughout."),
 },
 "integration_flags": [
  {"severity": "needs-a-person",
   "affects": ['h2-093'],
   "finding": "A private individual's psychiatric and criminal history, in a parent's first-person account, published by the City on a task force page.",
   "recommended_action": "Decide whether this archive re-publishes personal health narratives before this file is added or excluded."},
  {"severity": "not-applicable-through-update-candidate",
   "affects": [],
   "finding": "No file in this artifact has an inventory id.",
   "recommended_action": "Create the additions as candidates first; they then fall under the ordinary archival gate."},
  {"severity": "substantive-find",
   "affects": ['h2-071', 'h2-062', 'h2-063', 'h2-065', 'h2-098'],
   "finding": ("The task force's formal recommendations, the commissioned University of New Mexico landscape and "
               "gaps reports, the proposed funding streams, and the City's own 2004 crisis triage report that the "
               "2014 work was revisiting."),
   "recommended_action": "Add them, and keep the 2004 report beside the 2014 papers; the pair is the point."},
  {"severity": "label-as-draft",
   "affects": ['h2-088', 'h2-085'],
   "finding": "A long-term services summary marked DRAFT in its first line, and an August 2014 draft of a Senate bill circulated to the task force.",
   "recommended_action": "Label both as drafts; neither is a settled position."},
  {"severity": "third-party-authority",
   "affects": sorted(k for k, v in EXCLUDE.items() if v[4] == 'third_party_authority'),
   "finding": "Five standing publications of other authorities, gathered by the task force as background reading.",
   "recommended_action": "Do not add; their publishers are the authoritative source. The rule and the borderline case are set out in the_rule_applied_to_everything_else."},
  {"severity": "third-party-copyright",
   "affects": ['h2-099'],
   "finding": "A printout of an Albuquerque Journal opinion column, authored by two City Councillors but published by the newspaper.",
   "recommended_action": "Do not add. Cite it at source if the argument matters."},
 ],
 "counts": {
  "reviewed": len(rows),
  "add_to_the_inventory_as_a_new_candidate": len(add),
  "do_not_add": len(skip),
  "put_to_a_person_before_adding": len(person),
  "by_group": dict(bygroup),
  "files_with_no_text_layer": len(notext),
 },
 "link_check": {"checked": len(rows), "http_200": sum(1 for i in SLICE if CODE[i] == '200'),
                "failed": sum(1 for i in SLICE if CODE[i] != '200'),
                "method": "Full HTTP GET with a browser user agent, 2026-09-14.",
                "integrity": "Every row rehashed against its file on disk; every PDF tested for its end-of-file marker.",
                "containers_verified": "%d PDF, by leading bytes." % len(SLICE)},
 "add_to_inventory": add,
 "do_not_add": skip,
 "needs_a_decision_from_a_person": person,
 "archival_note": (f"None of the {len(add)} proposed additions is site-ready, and none is a candidate yet. Once "
                   f"created, each remains inventory-only until an R2 archive object exists and its public "
                   f"download, exact size, SHA-256 and authoritative-source provenance are verified. Combined "
                   f"footprint if all are added and archived: {add_bytes:,} bytes."),
 "integration_note": ("Codex integration lane: this artifact creates nothing and changes nothing. Every row carries "
                      "the authoritative URL, the measured size, the SHA-256, the leading bytes, the page count and "
                      "harvested_from. Every row carries inventory_id: null. The single human-review row must be "
                      "decided before it is either added or dropped."),
 "the_second_harvest_is_now_complete": {
  "pages_re_fetched": 220,
  "parsed": 219,
  "document_links_found": 159,
  "absent_from_the_inventory": 106,
  "decided_across_two_lanes": {
   "second-harvest-council-research-2026-09-14.json": 56,
   "behavioral-health-task-force-research-2026-09-14.json": len(SLICE),
  },
 },
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "no inventory candidate created"],
}

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items() if k != 'by_group'}}))
