# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.1] - 2026-11-07

### Added
- Document lifecycle state machine (`erpnext_agent/lifecycle.py`): Draft, Submitted, Cancelled with
  Save, Submit, Cancel and Amend. `erpnext_submit_document` and `erpnext_cancel_document` now refuse an
  illegal move (`STATE_TRANSITION_REFUSED`, reasons NotDraft, NotSubmittable, NotSubmitted,
  HasSubmittedLinks, StaleDocument, NotCancelled) before any write request. Cancel takes an optional
  `modified` stamp. New tool `erpnext_amend_document`. Graph nodes carry `documentState`, not `docStatus`.
- Surface backfill: tool-use contracts for all 87 tools, operator prompt and four role prompts as agent definitions, `erpnext-session` skill, scion-sdk >=0.9.1.

## [2.5.0] - 2026-11-06

### Added
- Typed HR tools (31): employee hire, update, read, list and relieve; departments and
  designations; holiday lists with the server's weekly-off generator; attendance (single
  and bulk) and check-ins; leave types, allocations, applications, approve or reject, and
  balance; salary components, structures and assignments; payroll entry, fill employees,
  create and submit salary slips, and slip reads.
- Typed CRM tools (19) on ERPNext's built-in CRM: lead capture, update and qualification;
  opportunity from lead, stage moves and lost with reasons; customer from lead or
  opportunity; sales stages, opportunity types and lost reasons; communication log and
  follow-up ToDos.
- Business onboarding (13 tools): setup status, time zones, chart templates, setup wizard
  (confirm only), company, fiscal year, address, bank, bank account and tax ID, plus
  plan (validate and dry run), apply (confirm, idempotent) and verify.
- Skills: hire to retire, leave approval, payroll run (test data), lead nurturing and
  business onboarding with its input schema; HR and CRM pipeline skills rewritten for the
  typed tools.
- Prompts as complete agent definitions: HR manager, sales representative and business
  onboarding; the operator prompt names every workflow skill.
- Ontology: 20 HR, CRM and onboarding classes rolled up to medulla core, their links,
  tool-use contracts, live virtual authorities and access contracts; sync presets for
  employees, leads and opportunities.

### Changed
- Leads and opportunities are rank 1 in the federation: ERPNext is the CRM of record.

## [2.4.0] - 2026-11-06

### Added
- Typed tools for every Frappe business operation: submit, cancel, count, get and set value,
  rename, mapped follow-on documents (quotation to order to invoice, lead to opportunity),
  document methods, DocType field metadata, report runs, link search and file upload.
- Workflow skills proven against a live instance: order to cash, procure to pay, inventory,
  CRM pipeline, projects, HR basics and accounting reports.
- Ontology: every class rolls up to medulla core by subclassing; the served surface
  (connector, features, tools, skills, prompt) and the data location and federation
  (one live virtual authority per record class) are declared.

### Changed
- A refused call now returns the server's reason (`API error: 417 LinkValidationError: ...`).
- Access contracts name the served `erpnext_list_documents` tool.
- The operator prompt names the typed tools and the workflow skills.

### Removed
- The alias tools `erpnext_version`, `erpnext_authGetLoggedUser` and
  `erpnext_auth_get_logged_user`, and the unserved action-routed registrations.

## [2.3.6] - 2026-10-30

### Changed
- Migrated to the `scion_sdk` import package; requires `scion-sdk>=0.6.4,<0.7.0`.

## [2.3.5] - 2026-10-26

### Added
- Add the packaged ERPNext connector development skill and its delivery contract.

## [2.3.4] - 2026-10-24

### Changed
- Central connector migration: requires `agent-connector-sdk>=0.5.4`; server bootstrap, version, containers, ontology artifacts, security scaffold and pre-commit config are provided centrally.

## [0.15.0] - 2026-05-25
### Added
- Initial dynamic facade API client implementation.
- FastMCP server entry points and modular tools.
- Rich documentation templates, including standardized environment configuration.
- Complete test suite validating startup and facade execution.
- Standardized MIT License.
