# Grant Applier Agent Context and Project Status

This file gives future LLMs and Cursor agents the background needed to continue work in the `grant_applier` repository without losing the purpose of the project.

## Project Purpose

The repository is intended to become an AI-assisted grant application drafting system for St Germaine Data Innovations (SGDI) and partner organizations. The tool should inspect grant opportunity folders, research official funder instructions online, extract requirements, and generate near-submission-ready grant application documents, budgets, and compliance checklists.

The system should support many funders. It is not just an NSF grant writer. It must handle NSF, NIH, Department of Education, USDA/NIFA, DOJ/NIJ, HHS/ACL/NIDILRR, Department of State, and other funders when grants are submitted through Grants.gov.

## Key People and Organizations

Richard St Germaine is the owner of St Germaine Data Innovations (SGDI). He has a PhD in Statistics, MPH in Biostatistics, BS in Biochemistry, and is an enrolled Tribal member of the Lac Courte Oreilles Band of Lake Superior Ojibwe. SGDI is a Tribal data firm that assists Tribes and Tribal nonprofits with data systems, grant writing, evaluation, analytics, data engineering, and grant needs. SGDI has a five-person team: healthcare administrator/grant writer, evaluation director, data scientist, data engineer, and Tribal education administrator.

AAIP is the American Association of Indian Physicians. In the AAIP NSF 26-509 grant, AAIP is intended to be the lead organization and national operator, not a fiscal sponsor. SGDI is the technical operations partner/subaward.

LCOOU refers to Lac Courte Oreilles Ojibwe University. Grants under this folder should generally be treated as LCOOU-led or Tribal college-led opportunities unless eligibility review shows otherwise.

## Repository Structure and Meaning

The repository snapshot inspected from `Grants.zip` contains:

```text
Grants/
  AAIP/
    26-509/
      25-544/
      Drafts/
      NSF 26-509_ Integrated Data Systems & Services (IDSS) ...
      Proposal Requiredment Cat II Guide.docx
      Required NSF 26-509 Proposal Documents.docx
  LCOOU/
    ED-GRANT-26-036/
    NSF 25-543/
    USDA-NIFA-OTHER-011816/
    USDA-NIFA-TCRGP-011697/
  SGDI/
    DFOP0018449/
    HHS-2026-ACL-NIDILRR-REGE-0212/
    NSF 26-508/
    O-NIJ-2025-172615/
    PDR-2600-DC-029Q/
    PDS-UAE-01-FY2026/
    RFA-DE-27-001/
    RFA-HD-27-006/
```

Folder logic:

```text
SGDI/  = grants SGDI may apply to directly as a small business or Tribal data firm.
AAIP/  = grants where AAIP is likely prime or partner; SGDI may support as subaward.
LCOOU/ = grants where LCOOU or a Tribal college/university partner is likely prime.
```

Each grant opportunity folder may contain only a Grants.gov search result PDF. The agent must locate the official funder NOFO/solicitation and any agency-specific application guidance online before drafting final requirements or documents.

## Completed Benchmark: AAIP NSF 26-509

The most important existing example is `AAIP/26-509/`.

The project concept is:

**Indigenous Data Commons: A National Indigenous-Governed Data Infrastructure for AI-Enabled Research, Evaluation, and Education**

This NSF 26-509 Category II proposal reframed a prior NSF 25-544 Category I/IHEART-oriented concept into a leaner three-year Category II transition proposal. The project is an AAIP-led national Indigenous-governed, AI-ready data infrastructure. It uses a cloud-first approach and includes API/Model Context Protocol-compatible access services for governed AI-assisted querying and reporting.

Important strategic decisions already made:

- AAIP is lead organization, national operator, governance convener, prime recipient, and infrastructure contract holder.
- SGDI is the technical operations subaward.
- AAIP should control just over 50% of the budget.
- SGDI should hold technical staff and implementation costs.
- AAIP should hold cloud/security/infrastructure contracts, lead-recipient operations, governance, nonprofit administration, partner engagement, and indirect costs.
- Planning budget is about $8.75M over three years.
- AAIP planned share is about $4.8M, or about 55%.
- SGDI planned subaward is about $3.95M, or about 45%.
- AAIP’s indirect cost rate is believed to be around 33.1%, but this must be confirmed with AAIP’s official negotiated indirect cost rate agreement.
- Cloud-first infrastructure is preferred over a large on-premises server build unless technical/funder review requires equipment.

Completed draft documents in `AAIP/26-509/Drafts/`:

```text
Project Summary.docx
Project Description.docx
References Cited.docx
Data Management and Sharing Plan.docx
Facilities, Equip. Other Resources.docx
AAIP Budget Justification.docx
Detailed Cost Estimate Supplement.docx
AAIP_IDC_CategoryII_Budget.xlsx
SGDI_IDC_CategoryII_Budget.xlsx
```

The AAIP 26-509 package should be used as the quality benchmark for future grant drafting.

## Drafting Style Established

The desired drafting style is professional and submission-ready. Drafts should not include internal reasoning, speculation, or conversational language.

Good style:

```text
AAIP will serve as the lead organization and prime recipient for the Indigenous Data Commons. AAIP will be responsible for award administration, NSF coordination, fiscal oversight, governance coordination, partner engagement, user community coordination, and reporting.
```

Bad style:

```text
This makes AAIP look like it is in control and not just a fiscal sponsor.
```

Use professional funder-facing language.

## Grant Drafting Standard

For every opportunity, the agent must produce:

```text
Analysis/opportunity_profile.yaml
Analysis/required_documents.md
Analysis/eligibility_assessment.md
Analysis/review_criteria.md
Analysis/drafting_strategy.md
Analysis/compliance_checklist.md
Analysis/human_review_todo.md
Sources/source_index.md
Sources/sources.json
Drafts/required document drafts
Budgets/budget workbook(s), if required
Budgets/budget_assumptions.md
Compliance/final_submission_checklist.md
```

Draft documents should follow the funder’s required headings and page limits. If the funder has no explicit structure, use standard grant structure.

## Critical Requirement: Web Research

Many opportunity folders contain only Grants.gov search detail PDFs. The agent must research the official funder notice online. It must not assume Grants.gov search detail contains all requirements.

Use official sources first:
1. Funder NOFO/solicitation/application instructions.
2. Agency policy guide/manual.
3. Grants.gov details.
4. Local files.
5. Other reputable sources only if needed.

Every requirements checklist must include source links or citations.

## Anti-Hallucination Rules

Do not fabricate due dates, award ceilings, match requirements, eligibility, page limits, or required attachments.

Use `[TODO]` or `[CONFIRM]` for missing facts. Add every unresolved item to `human_review_todo.md`.

Do not claim an application is ready to submit until human review confirms:
- applicant eligibility,
- SAM/UEI/Grants.gov registration,
- authorized representative,
- final budget,
- indirect cost rate,
- all required forms,
- all required attachments,
- page limits,
- formatting,
- submission deadline/time zone.

## Recommended Next Development Tasks

1. Add this context file to the repo root.
2. Implement folder inventory.
3. Generate `opportunity_profile.yaml` files for all existing opportunities.
4. Implement source discovery that can detect missing full NOFOs and search online.
5. Build a requirements extractor for local PDFs/DOCX and official sources.
6. Create funder-specific templates for NSF first, then HHS/ACL, USDA/NIFA, ED, DOJ/NIJ, NIH, and DOS.
7. Use `AAIP/26-509/` as the regression test and style benchmark.
8. Generate draft skeletons for `SGDI/NSF 26-508/`.
9. Generate draft skeletons for one non-NSF opportunity, likely `SGDI/HHS-2026-ACL-NIDILRR-REGE-0212/`.
10. Build a compliance validator that checks required docs, page limits, placeholders, and missing source citations.

## Human Review Still Needed for AAIP NSF 26-509

The AAIP package still needs:
- final PI/co-PI names and roles,
- biosketches,
- current and pending/other support,
- collaborators and other affiliations,
- Project Personnel and Partner Organizations supplementary document,
- letters of collaboration,
- human subjects/IRB determination,
- final AAIP indirect cost rate agreement,
- final salary/fringe rates,
- final Research.gov form data,
- final AAIP/SGDI budget reconciliation.

