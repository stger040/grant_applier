# Grant Applier Implementation Specification

This document describes a practical build plan for the `grant_applier` automation system.

## Product Vision

`grant_applier` should become a local and cloud-agent-friendly system that turns a folder of grant opportunity source files into a complete grant drafting workspace. It should support research, requirement extraction, drafting, budgeting, and compliance validation.

The user should be able to run:

```bash
grant-applier inventory
grant-applier analyze SGDI/NSF\ 26-508
grant-applier research SGDI/NSF\ 26-508
grant-applier draft SGDI/NSF\ 26-508
grant-applier budget SGDI/NSF\ 26-508
grant-applier validate SGDI/NSF\ 26-508
```

## Recommended Architecture

```text
grant_applier/
  cli.py
  config.py
  inventory.py
  source_discovery.py
  web_research.py
  grants_gov.py
  document_parser.py
  requirement_extractor.py
  applicant_profiles.py
  strategy.py
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
  schemas/
    opportunity_profile.schema.json
    requirements.schema.json
    budget_model.schema.json
    validation_report.schema.json
```

## Data Files

Every opportunity should have structured intermediate files:

### `Analysis/opportunity_profile.yaml`

```yaml
applicant_folder: SGDI
opportunity_folder: NSF 26-508
likely_applicant: SGDI
opportunity_number: NSF 26-508
opportunity_title: null
funder: National Science Foundation
submission_system: Grants.gov or Research.gov
deadline: null
award_ceiling: null
project_period: null
eligibility:
  sgdi_eligible: null
  notes: []
cost_share_required: null
indirect_cost_rules: null
source_status:
  local_grants_gov_notice_found: true
  full_nofo_found: false
  official_funder_page_found: false
human_review_required: true
```

### `Analysis/requirements.json`

```json
{
  "required_documents": [
    {
      "name": "Project Summary",
      "required": true,
      "page_limit": "1 page",
      "format": "NSF Project Summary with Overview, Intellectual Merit, Broader Impacts",
      "source": "official solicitation URL or local file"
    }
  ],
  "budget_rules": [],
  "eligibility_rules": [],
  "review_criteria": [],
  "formatting_rules": []
}
```

### `Sources/sources.json`

```json
[
  {
    "title": "Official NOFO title",
    "url": "https://...",
    "local_path": "Sources/official_nofo.pdf",
    "source_type": "official_nofo",
    "retrieved_date": "YYYY-MM-DD",
    "notes": "Primary source for requirements"
  }
]
```

### `Compliance/validation_report.json`

```json
{
  "status": "draft_not_submission_ready",
  "missing_items": [],
  "placeholders_remaining": [],
  "page_limit_warnings": [],
  "source_citation_warnings": [],
  "eligibility_warnings": []
}
```

## Source Discovery Rules

The source discovery module should:
1. Parse local filenames and text for opportunity numbers.
2. Detect funder by opportunity prefix or local source.
3. Search official websites for the opportunity number.
4. Save official links and downloaded sources.
5. Report missing full NOFOs.

Use these search patterns:

```text
"<opportunity_number>" NOFO
"<opportunity_number>" funding opportunity
"<opportunity_number>" application instructions
"<opportunity_title>" "<funder>"
site:<agency_domain> "<opportunity_number>"
```

Agency hints:

```yaml
NSF: ["new.nsf.gov", "nsf.gov"]
NIH: ["grants.nih.gov"]
Department of Education: ["ed.gov"]
USDA/NIFA: ["nifa.usda.gov"]
DOJ/OJP/NIJ: ["ojp.gov", "nij.ojp.gov"]
HHS/ACL/NIDILRR: ["acl.gov", "grants.gov"]
Department of State: ["state.gov", "usembassy.gov", "grants.gov"]
```

## Requirement Extraction

The extractor should identify:
- opportunity number,
- title,
- deadline,
- eligibility,
- award ceiling/floor,
- number of awards,
- project period,
- match/cost share,
- indirect cost rules,
- required documents,
- page limits,
- font/margin/formatting,
- budget forms,
- application forms,
- review criteria,
- attachments,
- reporting requirements,
- submission portal,
- registration requirements.

If the extractor is uncertain, it must use `[CONFIRM]`.

## Draft Generation

The drafting module should use funder-specific templates. It should generate concise, professional drafts with no internal reasoning.

Template families:

```text
NSF:
  Project Summary
  Project Description
  References Cited
  Data Management and Sharing Plan
  Facilities, Equipment, and Other Resources
  Budget Justification
  Detailed Cost Estimate
  Project Personnel and Partner Organizations
  Letters of Collaboration

NIH:
  Project Summary / Abstract
  Project Narrative
  Specific Aims
  Research Strategy
  Facilities and Other Resources
  Equipment
  Budget Justification
  Resource Sharing / Data Management and Sharing Plan
  Biosketch guidance placeholders

Department of Education:
  Abstract
  Project Narrative aligned to selection criteria
  Management Plan
  Evaluation Plan
  Budget Narrative
  GEPA / required assurances placeholders

USDA/NIFA:
  Project Summary
  Project Narrative
  Management Plan
  Evaluation Plan
  Data Management Plan if required
  Budget Justification
  Matching/cost share docs if required

DOJ/NIJ:
  Proposal Abstract
  Program Narrative
  Goals/Objectives/Deliverables
  Capabilities and Competencies
  Plan for Collecting Data
  Budget Detail Worksheet/Narrative

HHS/ACL/NIDILRR:
  Project Abstract
  Project Narrative
  Work Plan
  Evaluation Plan
  Organizational Capacity
  Budget Narrative

Department of State:
  Proposal Summary
  Statement of Need
  Project Goals and Objectives
  Project Activities
  Monitoring and Evaluation Plan
  Sustainability Plan
  Budget Narrative
```

## Budget Generation

The budget module should generate `.xlsx` workbooks using formulas and assumptions sheets. It should:
- mirror funder budget categories,
- include salary, fringe, travel, equipment, supplies, consultants, contractual/subawards, other direct costs, indirect costs,
- include assumptions,
- include a summary by year,
- include a work-area cost estimate where useful,
- flag unconfirmed rates.

For AAIP + SGDI:
- AAIP should usually hold more than 50% if AAIP is prime.
- SGDI should be a technical operations subaward.
- AAIP should hold cloud/infrastructure contracts if the project is AAIP-led.
- SGDI should hold technical staff.

For SGDI-led applications:
- SGDI staff should be direct personnel.
- Include SGDI indirect/overhead only if allowed.
- Ensure small business eligibility and indirect rules are verified.

## Validation

The validator should check:
- all required documents exist,
- drafts match required headings,
- page limits are approximated by word count,
- placeholders remain listed,
- budget total does not exceed award ceiling,
- match/cost share is addressed,
- indirect rates are flagged if unconfirmed,
- eligibility risks are listed,
- source URLs exist for all major requirements,
- no forbidden letters/support docs are included,
- draft status is marked correctly.

Validation output should never say “ready to submit” unless there are no missing items and all human confirmations are complete.

## Initial Milestones

### Milestone 1: Inventory and profiles
- scan all folders,
- create opportunity profiles,
- identify funders and opportunity numbers.

### Milestone 2: Source discovery
- research official NOFOs,
- build source index,
- flag missing sources.

### Milestone 3: NSF template proof
- use AAIP/26-509 as regression benchmark,
- produce a comparable skeleton for SGDI/NSF 26-508.

### Milestone 4: Non-NSF proof
- process one HHS/ACL or USDA/NIFA opportunity,
- verify non-NSF requirements extraction.

### Milestone 5: Draft + budget generation
- generate draft documents,
- generate budget workbooks,
- create compliance report.

## Safety and Quality

This tool supports human grant writing. It does not replace human review. It must not submit applications, sign certifications, or represent that an application is complete without human confirmation.
