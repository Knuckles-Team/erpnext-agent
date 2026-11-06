---
name: erpnext-crm-pipeline
skill_type: skill
description: >-
  Work the ERPNext (Frappe) built-in CRM through the erpnext-mcp MCP server:
  capture a lead, qualify it into an opportunity, and quote it. Use when the agent
  must record an inbound prospect, track a deal toward a quotation, or convert a
  won opportunity into a customer and sales order. Do NOT use for billing or payment
  (use erpnext-order-to-cash).
license: MIT
tags: [erpnext, frappe, crm, lead, opportunity, sales-pipeline, mcp]
metadata:
  version: '1.0.0'
---
# ERPNext CRM pipeline

Lead → Opportunity → Quotation (→ erpnext-order-to-cash).

## Steps
1. **Lead**: `erpnext_create_document` `Lead` with `first_name`, `lead_name`,
   `company_name` (the prospect's organisation), `email_id` if known, and
   `company` (our company). Check duplicates first with `erpnext_search_link`
   `Lead`.
2. **Opportunity**: `erpnext_make_mapped_document` `method`
   `erpnext.crm.doctype.lead.lead.make_opportunity`, `source_name` the lead. Set
   `company` (and `opportunity_amount`, `expected_closing` when known) on the
   returned draft, and set `currency` (the company currency) so the follow-on
   quotation needs no exchange rate; save it with `erpnext_create_document`
   `Opportunity`.
3. **Quotation**: `erpnext_make_mapped_document`
   `erpnext.crm.doctype.opportunity.opportunity.make_quotation` from the
   opportunity, add `items`, save and submit. Continue with
   erpnext-order-to-cash.
4. **Lost**: `erpnext_run_document_method` `Opportunity`, `method`
   `declare_enquiry_lost`, `args` `{"lost_reasons_list": [{"lost_reason": "..."}],
   "competitors": [], "detailed_reason": "..."}` (the reason must exist as an
   `Opportunity Lost Reason`; create it with `erpnext_create_document`).

## Status
- `erpnext_list_documents` `Opportunity` with `fields`
  `["name","party_name","status","opportunity_amount","expected_closing"]`.
- `erpnext_get_count` `Lead` with `filters` `{"status": "Open"}`.

## Overlap
The same pipeline can live in a dedicated CRM. Keep one system the owner of
leads and opportunities; the other reads them. Which one is an owner decision.
