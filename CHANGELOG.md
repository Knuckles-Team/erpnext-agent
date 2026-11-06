# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
