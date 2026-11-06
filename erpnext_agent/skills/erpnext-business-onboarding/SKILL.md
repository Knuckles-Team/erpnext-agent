---
name: erpnext-business-onboarding
skill_type: skill
description: >-
  Onboard a business into ERPNext (Frappe) through the erpnext-mcp MCP server,
  repeatably and idempotently: collect the inputs (legal name, abbreviation,
  country, currency, fiscal year, time zone, chart of accounts, tax ID, address,
  bank, holiday list, departments, designations, CRM stages), validate them on the
  server, show a dry-run plan of what exists and what will be created, apply only
  after approval (setup wizard on a fresh site, otherwise company-level records),
  then verify. Re-running changes nothing. Use when the agent must set up a new or
  extra company, or check that a company's set-up is complete.
license: MIT
tags: [erpnext, frappe, onboarding, company, setup-wizard, idempotent, mcp]
metadata:
  version: '1.0.0'
---
# ERPNext business onboarding

Collect → validate → dry run → approve → apply → verify. One input document
drives every step: [the onboarding spec](references/onboarding-spec.yaml).

## 1. Collect
Fill the spec with the owner. Required: `company.name`, `company.abbr`,
`company.country`, `company.currency`, `company.chart_of_accounts`,
`fiscal_year.start_date`, `fiscal_year.end_date`, `time_zone`. Optional:
`company.tax_id`, `address`, `bank`, `hr` (holiday list, departments,
designations), `crm` (sales stages, opportunity types), `admin` (wizard only).
Help the owner pick valid values:
- time zones: `erpnext_list_timezones`;
- chart templates for the country: `erpnext_list_chart_of_accounts_templates`;
- countries and currencies: `erpnext_search_link` `Country` / `Currency`.

## 2. Validate and dry run
`erpnext_get_setup_status` shows whether the site's setup wizard is complete and
which companies exist. Then `erpnext_plan_business_onboarding` with the spec:
- `valid` false lists every input problem in `errors` (unknown country,
  currency, time zone or chart template; missing fields; an existing company
  with another abbreviation). Fix and re-plan.
- `steps` lists every record with `status` `exists`, `create` or `update`, and
  `mode`: `setup_wizard` (fresh site, spec `mode` `auto`) or `company`.
Show the plan to the owner and stop for approval.

## 3. Apply (approved only)
`erpnext_apply_business_onboarding` with the same spec and `confirm` true. It
creates or updates only the pending steps, in order: setup wizard or company,
fiscal year, tax ID, address, bank, bank ledger and bank account, holiday list
(and the company default), departments, designations, sales stages, opportunity
types. It returns `applied`, then `verified` and `missing`.
- A fresh site's wizard runs through `erpnext_complete_setup_wizard` semantics:
  it is site-wide and one-time. Only run it with the owner's approval of the
  real legal details; for an extra or test company set `mode` `company`.

## 4. Verify and re-run
`erpnext_verify_business_onboarding` must report `verified` true with no
`missing` steps. Running the plan again shows every step as `exists`; running
apply again applies nothing.

## Single records (outside a full onboarding)
`erpnext_create_company`, `erpnext_create_fiscal_year`, `erpnext_create_address`,
`erpnext_create_bank`, `erpnext_create_bank_account`, `erpnext_set_tax_id`,
`erpnext_create_holiday_list`, `erpnext_create_department`,
`erpnext_create_designation`, `erpnext_create_sales_stage`,
`erpnext_create_opportunity_type`.

## Guardrails
- Dry run first, every time. Apply only after approval of that plan.
- Never complete the real site's setup wizard without the owner's legal details
  and explicit approval. Test companies are named `zz-validation-<date>` and are
  removed afterwards (`erpnext_delete_document`, newest records first).
- Never invent tax IDs or bank numbers; leave them out until the owner gives them.
