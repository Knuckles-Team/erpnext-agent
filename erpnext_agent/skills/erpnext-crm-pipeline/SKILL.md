---
name: erpnext-crm-pipeline
skill_type: skill
description: >-
  Work the ERPNext (Frappe) built-in CRM via erpnext-mcp: capture a lead, qualify it into an opportunity, move it through sales stages, and quote it. Use to record an inbound prospect, track a deal toward a quotation, or convert a won opportunity. Do NOT use for billing or day-to-day follow-ups (erpnext-order-to-cash, erpnext-lead-nurturing).
license: MIT
tags: [erpnext, frappe, crm, lead, opportunity, sales-pipeline, mcp]
metadata:
  version: '2.0.0'
---
# ERPNext CRM pipeline

Scope: Work the ERPNext (Frappe) built-in CRM through the erpnext-mcp MCP server: capture a lead, qualify it into an opportunity, move it through the sales stages, and quote it. Use when the agent must record an inbound prospect, track a deal toward a quotation, or convert a won opportunity into a customer and sales order. For day-to-day touches and follow-ups use erpnext-lead-nurturing. Do NOT use for billing or payment (use erpnext-order-to-cash).

Lead → Opportunity → Quotation (→ erpnext-order-to-cash).

## Steps

1. Check for an existing lead with `erpnext_search_link` `Lead` and verify no record already matches the prospect.
2. Capture it with `erpnext_create_lead` and verify `erpnext_list_leads` returns the new lead.
3. Qualify it with `erpnext_qualify_lead` and verify `erpnext_list_leads` shows it as Qualified.
4. Raise the deal with `erpnext_create_opportunity_from_lead` and verify `erpnext_list_opportunities` shows it with the expected `sales_stage`.
5. Move it with `erpnext_update_opportunity_stage` and verify `erpnext_list_opportunities` shows the new stage.
6. Close it with `erpnext_make_customer_from_opportunity` when won or `erpnext_declare_opportunity_lost` when lost, and verify the opportunity status changed.

## Failure recovery

| Failure | Cause | Recovery |
|---|---|---|
| Duplicate lead | The prospect already exists | Use the lead returned by `erpnext_search_link` `Lead` and skip `erpnext_create_lead` |
| Unknown sales stage or type | The stage or type does not exist in ERPNext | Read `erpnext_list_sales_stages` or `erpnext_list_opportunity_types` and create the missing one with `erpnext_create_sales_stage` or `erpnext_create_opportunity_type` |
| `erpnext_declare_opportunity_lost` refused | A `lost_reasons` entry does not exist | Create it with `erpnext_create_opportunity_lost_reason` and declare the loss again |
| Quotation needs an exchange rate | The opportunity currency differs from the company currency | Pass the company `currency` to `erpnext_create_opportunity_from_lead` |

## Pipeline set-up
- Sales stages: `erpnext_list_sales_stages`; add one with
  `erpnext_create_sales_stage`.
- Opportunity types: `erpnext_list_opportunity_types`; add one with
  `erpnext_create_opportunity_type`.

## Procedure
1. **Lead**: check duplicates with `erpnext_search_link` `Lead`, then
   `erpnext_create_lead` with `first_name`, `company_name` (the prospect's
   organisation), `email_id` if known, and `company` (our company).
2. **Qualify**: `erpnext_qualify_lead`.
3. **Opportunity**: `erpnext_create_opportunity_from_lead` with `company`, the
   company `currency` (so the quotation needs no exchange rate),
   `opportunity_amount`, `expected_closing` and `sales_stage`.
4. **Stage**: `erpnext_update_opportunity_stage` as the deal moves.
5. **Quotation**: `erpnext_make_mapped_document`
   `erpnext.crm.doctype.opportunity.opportunity.make_quotation` from the
   opportunity, add `items`, save with `erpnext_create_document` and submit with
   `erpnext_submit_document`. Continue with erpnext-order-to-cash.
6. **Customer**: `erpnext_make_customer_from_opportunity` when the deal is won.
7. **Lost**: `erpnext_declare_opportunity_lost` with `lost_reasons` (each must
   exist; create it with `erpnext_create_opportunity_lost_reason`).

## Status
- `erpnext_list_opportunities` (by `status` or `sales_stage`).
- `erpnext_list_leads`; `erpnext_get_count` `Lead` with `filters`
  `{"status": "Open"}`.

## Ownership
ERPNext is the CRM of record: leads and opportunities are owned here.
