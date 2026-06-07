# Cursor Build Prompt: Grant Applier Cloud Agent

You are working in the GitHub repository:

`https://github.com/stger040/grant_applier`

The repo is a grant-application automation workspace for St Germaine Data Innovations (SGDI). The goal is to build a Cursor Cloud Agent workflow that can inspect grant opportunity folders, research the full funder notice online, extract all application requirements, and generate near-submission-ready grant application document drafts.

## Primary Goal

Build a grant drafting system that can take a folder containing one or more grant opportunity source files, then produce a complete application draft package tailored to that specific funder and opportunity.

The system must support multiple funders, not only NSF. Some local folders contain only a Grants.gov search/detail PDF and do not include the full Notice of Funding Opportunity (NOFO), solicitation, policy guide, application instructions, or agency-specific attachments. When the local folder does not contain full requirements, the system must search the internet for the funder’s official opportunity page, NOFO, application package, agency instructions, and any governing policy manuals.

The system should not submit grants. It should produce high-quality drafts, checklists, budgets, and compliance review materials for human review.

## Current Repository Structure Observed

The uploaded repository snapshot has this top-level structure:

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

Folder meaning:

- `SGDI/` contains grants SGDI may apply to directly as a small business.
- `AAIP/` contains grants where AAIP is the lead applicant or partner organization.
- `LCOOU/` contains grants where Lac Courte Oreilles Ojibwe University or related partners are likely the applicant/partner.
- Each opportunity folder should become a self-contained workspace with sources, extracted requirements, generated drafts, budgets, and compliance checklists.

## Important Benchmark Already Completed

The `AAIP/26-509/` folder is the gold-standard example. A full NSF 26-509 Category II application draft package was created for an AAIP-led Indigenous Data Commons project. Use its structure and quality level as the model for future output.

Completed draft documents in `AAIP/26-509/Drafts/` include:

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

The AAIP/NSF example used the following strategy:

- Treat NSF 26-509 as a Category II operational cyberinfrastructure proposal.
- Use the prior NSF 25-544 materials as historical context.
- Reframe the project around the Indigenous Data Commons, a national Indigenous-governed, AI-ready data infrastructure.
- Position AAIP as lead organization, governance convener, infrastructure contract holder, and national operator.
- Position SGDI as the technical operations subaward for data engineering, AI/MCP services, analytics, evaluation, documentation, and user support.
- Keep AAIP above 50% of the budget and SGDI below 50%, so AAIP clearly appears to lead and control the project.
- Use cloud-first infrastructure unless the funder/project explicitly requires on-prem equipment.
- Produce professional, submission-style documents, not internal reasoning.

## Required Behavior for the Agent

For each grant opportunity folder, the agent must:

1. Inventory local files.
2. Extract the opportunity number, title, funder, due date, award ceiling, cost share/match, applicant eligibility, submission mechanism, and known local source documents.
3. Determine whether the folder contains the full official solicitation/NOFO/application instructions.
4. If the full instructions are missing or incomplete, search the web for the official funder page and authoritative application documents.
5. Download or link official sources where permitted.
6. Extract all required application components, page limits, formatting rules, attachments, forms, budget rules, review criteria, eligibility requirements, indirect cost rules, and submission restrictions.
7. Create a `requirements/` or `analysis/` output containing:
   - `opportunity_profile.yaml`
   - `required_documents.md`
   - `source_index.md`
   - `compliance_checklist.md`
   - `drafting_strategy.md`
8. Generate draft application documents in `Drafts/`, respecting each funder’s structure and page limits.
9. Generate budget workbook(s) and budget justification drafts when the funding opportunity requires them.
10. Generate a final `human_review_todo.md` listing missing facts, unresolved compliance items, and required human decisions.

## Source-of-Truth Priority

Use the following hierarchy:

1. Official funder NOFO/solicitation/application instructions.
2. Official agency policy guide/manual, such as NSF PAPPG, NIH Grants Policy Statement, EDGAR, USDA NIFA Grants.gov guide, DOJ Financial Guide, HHS Grants Policy Statement, DOS NOFO guidance, or other funder-specific guidance.
3. Grants.gov opportunity notice and package details.
4. Local files in the grant folder.
5. Reputable supporting sources only when official sources are insufficient.

Do not rely on Grants.gov search detail PDFs alone if the agency has a fuller NOFO elsewhere.

## Internet Research Requirement

The agent must use web search for each opportunity unless the folder already contains the full official funder solicitation and policy guide. Search queries should include:

```text
"<opportunity number>" NOFO
"<opportunity number>" funding opportunity
"<opportunity number>" application instructions
"<opportunity title>" official
site:<agency domain> "<opportunity number>"
site:grants.gov "<opportunity number>"
```

For NSF opportunities, also fetch the applicable NSF solicitation page and current NSF PAPPG.
For NIH opportunities, fetch the Notice of Funding Opportunity page and NIH Grants Policy guidance.
For Department of Education opportunities, fetch the official competition page and EDGAR/application instructions.
For USDA/NIFA opportunities, fetch the official NIFA RFA and Grants.gov package instructions.
For DOJ/NIJ opportunities, fetch the official NIJ/OJP solicitation and DOJ Grants Financial Guide.
For HHS/ACL/NIDILRR opportunities, fetch the official ACL/NIDILRR NOFO and HHS Grants Policy guidance.
For Department of State opportunities, fetch the official embassy/bureau NOFO, Grants.gov page, and DOS financial/NOFO guidance.

Every generated requirements list must cite or link to the source that supports the requirement.

## Core Outputs Per Opportunity

Each opportunity should end up with this structure:

```text
<Applicant>/<Opportunity>/
  Sources/
    downloaded_or_linked_official_sources/
    source_index.md
    sources.json
  Analysis/
    opportunity_profile.yaml
    eligibility_assessment.md
    required_documents.md
    review_criteria.md
    compliance_checklist.md
    drafting_strategy.md
    human_review_todo.md
  Drafts/
    01_Project_Summary_or_Abstract.docx or .md
    02_Project_Narrative_or_Program_Design.docx or .md
    03_Budget_Justification.docx or .md
    04_Data_Management_or_Evaluation_Plan.docx or .md
    05_Facilities_or_Organizational_Capacity.docx or .md
    06_References_Cited.docx or .md
    other required attachments...
  Budgets/
    applicant_budget.xlsx
    subaward_budget.xlsx if applicable
    budget_assumptions.md
  Compliance/
    final_submission_checklist.md
    page_limit_check.md
    missing_items.md
```

Use `.md` drafts first unless a `.docx` or `.xlsx` artifact is explicitly required by the workflow. Budget workbooks should be `.xlsx`.

## Applicant Profile Logic

The agent must infer applicant context from the folder:

### SGDI applications

SGDI stands for St Germaine Data Innovations. SGDI is a Tribal data firm owned by Richard St Germaine, PhD in Statistics, MPH in Biostatistics, BS in Biochemistry, enrolled Tribal member of the Lac Courte Oreilles Band of Lake Superior Ojibwe. SGDI assists Tribes and Tribal nonprofits with data systems, grant writing, evaluation, analytics, data engineering, and AI/data infrastructure. SGDI is a five-employee data firm with roles including healthcare administrator/grant writer, evaluation director, data scientist, data engineer, and Tribal education administrator.

For grants under `SGDI/`, draft as an SGDI-led small business or Tribal data firm application unless eligibility analysis shows SGDI cannot apply directly. If SGDI is not eligible, flag this immediately in `eligibility_assessment.md` and recommend a possible eligible partner/prime.

### AAIP applications

AAIP is the American Association of Indian Physicians. For grants under `AAIP/`, draft AAIP as the likely prime applicant unless the folder or instructions say otherwise. Position SGDI as technical partner/subaward only when appropriate. AAIP should not appear to be merely a fiscal sponsor. AAIP should have meaningful project leadership, governance, community engagement, administration, and operational control.

### LCOOU applications

LCOOU refers to Lac Courte Oreilles Ojibwe University. For grants under `LCOOU/`, draft LCOOU as the likely academic/Tribal college lead unless instructions say otherwise. SGDI may be a technical assistance, data systems, evaluation, analytics, or grant support partner if appropriate.

## Drafting Quality Standards

The agent must draft like an experienced grant writer, not a chatbot. Outputs should be professional, funder-specific, concise, and formatted for direct copy/paste into Word or submission forms.

Do not include internal reasoning in draft documents. Do not say things like “we should” or “this makes it look like.” Use formal applicant language.

Use headings and narrative structure that match the funder’s required sections. If no required structure exists, use standard grant structure:

```text
Project Summary / Abstract
Statement of Need
Goals and Objectives
Project Design / Work Plan
Applicant Capacity
Partnerships
Evaluation Plan
Sustainability Plan
Budget Justification
References
```

For NSF, preserve required NSF headings.
For NIH, preserve NIH Research Strategy and SF424 structure where applicable.
For ED, preserve selection criteria and absolute/competitive priority language.
For USDA/NIFA, preserve RFA narrative sections and evaluation criteria.
For DOJ/NIJ, preserve goals/objectives/deliverables/capabilities/plan for collecting data.
For HHS/ACL, preserve project narrative and review criteria headings.

## Budget Rules

The agent should create budgets that match funder requirements and applicant reality.

For AAIP + SGDI projects:
- AAIP should usually control more than 50% of the total budget if AAIP is prime.
- SGDI should hold technical staff and implementation costs through subaward.
- AAIP should hold lead organization operations, grants management, governance, partner engagement, infrastructure contracts, cloud/security contracts, and indirect costs where appropriate.
- Use AAIP’s indirect cost rate only if confirmed; provisional planning may use 33.1% but must be flagged for confirmation.

For SGDI-led applications:
- Put SGDI staff on payroll lines.
- Include fringe, indirect/overhead, travel, supplies, consultants, software/cloud, and participant support only when allowable.
- If the funder restricts for-profit indirect costs or small business fees, follow that funder’s rules.

For all grants:
- Never include voluntary committed cost share unless required.
- Flag required match/cost share.
- Verify indirect cost rules from the funder’s official guidance.
- Keep budget narrative professional and source-aligned.
- Produce `budget_assumptions.md` listing all provisional rates and missing values.

## Compliance and Anti-Hallucination Rules

The system must never fabricate application requirements, due dates, eligibility, page limits, award ceilings, match requirements, or policy rules.

If a requirement is unknown, write `[CONFIRM]` or `[TODO]` and list it in `human_review_todo.md`.

Every requirements checklist must show the source document or URL for each major requirement.

Generated drafts may include placeholder text such as `[INSERT ORGANIZATION ADDRESS]`, `[CONFIRM PI NAME]`, `[INSERT INDIRECT COST RATE]`, or `[CONFIRM PARTNER]`.

The agent must distinguish:
- grant drafting content,
- source-supported requirements,
- inferred strategy,
- unknowns requiring human confirmation.

Do not claim an application is ready to submit until all required forms, registrations, dates, budgets, attachments, and authorized representative details are confirmed.

## Recommended Implementation

Build a Python-based CLI and/or agent workflow with these commands:

```bash
python -m grant_applier inventory
python -m grant_applier analyze --opportunity "SGDI/NSF 26-508"
python -m grant_applier research --opportunity "SGDI/NSF 26-508"
python -m grant_applier requirements --opportunity "SGDI/NSF 26-508"
python -m grant_applier draft --opportunity "SGDI/NSF 26-508"
python -m grant_applier budget --opportunity "SGDI/NSF 26-508"
python -m grant_applier validate --opportunity "SGDI/NSF 26-508"
```

Use a modular architecture:

```text
grant_applier/
  __init__.py
  cli.py
  inventory.py
  source_discovery.py
  grants_gov.py
  web_research.py
  document_parser.py
  requirement_extractor.py
  applicant_profiles.py
  drafting.py
  budget.py
  validation.py
  renderers/
    markdown.py
    docx.py
    xlsx.py
  templates/
    nsf/
    nih/
    ed/
    usda_nifa/
    doj_nij/
    hhs_acl/
    state_dos/
    generic/
```

Use structured intermediate files so a human or LLM can review the work:

```text
opportunity_profile.yaml
requirements.json
sources.json
draft_plan.json
budget_model.json
validation_report.json
```

The agent should be able to resume from these files without starting over.

## First Development Target

Start by implementing the analyzer and generator for the existing `AAIP/26-509/` folder, because it contains a completed benchmark. Then generalize to `SGDI/NSF 26-508/`, then to one non-NSF grant such as `SGDI/HHS-2026-ACL-NIDILRR-REGE-0212/`.

The first working version should:
1. Inventory all opportunities.
2. Create opportunity profiles.
3. Identify missing official sources.
4. Produce requirements checklists.
5. Generate professional draft skeletons using funder-specific headings.
6. Produce a validation report with missing items and human review needs.

