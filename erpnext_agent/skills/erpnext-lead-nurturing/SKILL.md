---
name: erpnext-lead-nurturing
skill_type: skill
description: >-
  Nurture leads in ERPNext's built-in CRM via erpnext-mcp: capture, log touches, schedule follow-ups, qualify, raise an opportunity, move it through stages, convert a won deal or mark it lost. Use to work the pipeline day to day or report its state. Do NOT use for quoting and billing (erpnext-order-to-cash).
license: MIT
tags: [erpnext, frappe, crm, lead, opportunity, follow-up, mcp]
metadata:
  version: '1.0.0'
---
# ERPNext lead nurturing

Scope: Nurture leads in ERPNext's built-in CRM through the erpnext-mcp MCP server: capture, log every touch, schedule follow-ups, qualify, raise an opportunity, move it through the sales stages, and convert the won deal into a customer (or mark it lost with a reason). Use when the agent must work the sales pipeline day to day, decide the next action on a lead, or report pipeline state. Do NOT use for quoting and billing (use erpnext-order-to-cash).

Lead → touches and follow-ups → qualified → Opportunity → sales stages →
Customer (won) or Lost.

## Steps

1. Check for an existing lead with `erpnext_search_link` `Lead` and verify no record matches the prospect.
2. Capture the lead with `erpnext_create_lead` and verify `erpnext_list_leads` returns it.
3. Log each touch with `erpnext_log_communication` and verify the call returns the log entry on that lead.
4. Schedule the next action with `erpnext_create_follow_up` and verify `erpnext_list_follow_ups` lists it with the right `date` and `allocated_to`.
5. Qualify the lead with `erpnext_qualify_lead` and verify `erpnext_list_leads` shows it as Qualified.
6. Raise the deal with `erpnext_create_opportunity_from_lead` and verify `erpnext_list_opportunities` shows it.
7. Close it with `erpnext_make_customer_from_opportunity` when won or `erpnext_declare_opportunity_lost` when lost, and verify the opportunity status changed.

## Failure recovery

| Failure | Cause | Recovery |
|---|---|---|
| Duplicate lead | The prospect was not searched first | Use the lead returned by `erpnext_search_link` and update it with `erpnext_update_lead` |
| Unknown sales stage or type | It is not defined in ERPNext | Create it with `erpnext_create_sales_stage` or `erpnext_create_opportunity_type` after checking `erpnext_list_sales_stages` |
| Lost declaration refused | A `lost_reasons` entry does not exist | Create it with `erpnext_create_opportunity_lost_reason` and declare again |
| Outbound message requested | The agent must not message real prospects | Log the touch with `erpnext_log_communication` and leave sending to a person |

## Capture
1. Look for a duplicate: `erpnext_search_link` `Lead` (name or organisation) and
   `erpnext_list_leads`.
2. `erpnext_create_lead` with `first_name`, `company` (ours), `company_name` (the
   prospect's organisation), `email_id`, `source`.

## Touch and follow up
3. Every call, meeting or message: `erpnext_log_communication` on the lead (a log
   entry; nothing is sent).
4. The next action: `erpnext_create_follow_up` with a `date` and the owner in
   `allocated_to`. Work the queue with `erpnext_list_follow_ups` and close done
   items with `erpnext_close_follow_up`.
5. Status changes: `erpnext_update_lead` (`status` `Interested`, `Replied`, `Do
   Not Contact`, ...).

## Qualify and convert
6. `erpnext_qualify_lead` (`qualification_status` `Qualified`, `qualified_on`).
7. `erpnext_create_opportunity_from_lead` with `company`, the company `currency`,
   `opportunity_amount`, `expected_closing`, the first `sales_stage` and an
   `opportunity_type`.
8. Move it: `erpnext_update_opportunity_stage` with the next stage and
   `probability`. Stages come from `erpnext_list_sales_stages`; types from
   `erpnext_list_opportunity_types` (create with `erpnext_create_sales_stage`
   and `erpnext_create_opportunity_type`).
9. **Won**: `erpnext_make_customer_from_opportunity` (or
   `erpnext_make_customer_from_lead`), then quote it with erpnext-order-to-cash.
10. **Lost**: `erpnext_declare_opportunity_lost` with `lost_reasons` (create a
    missing reason with `erpnext_create_opportunity_lost_reason`).

## Report
`erpnext_list_opportunities` by `sales_stage` or `status`; `erpnext_get_count`
`Lead` with `{"qualification_status": "Qualified"}`.

## Guardrails
- Never email or message a real prospect from the agent: log the touch and leave
  the sending to a person, unless the owner approved an outbound channel.
- ERPNext is the one CRM: leads and opportunities are owned here.
