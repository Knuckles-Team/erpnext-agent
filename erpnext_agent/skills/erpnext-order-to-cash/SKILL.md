---
name: erpnext-order-to-cash
skill_type: skill
description: >-
  Run the ERPNext (Frappe) order-to-cash flow end to end through the erpnext-mcp
  MCP server: customer, quotation, sales order, sales invoice and payment entry,
  each mapped from the one before and submitted so it posts to the ledger. Use when
  the agent must quote a customer, turn an accepted quote into an order, bill it, or
  record the customer's payment against the invoice. Do NOT use for supplier bills
  (use erpnext-procure-to-pay), stock receipts (use erpnext-inventory) or ledger and
  ageing reports (use erpnext-accounting).
license: MIT
tags: [erpnext, frappe, sales, invoice, payment, order-to-cash, mcp]
metadata:
  version: '1.0.0'
---
# ERPNext order to cash

Customer → Quotation → Sales Order → Sales Invoice → Payment Entry. Each later
document is built from the earlier one by `erpnext_make_mapped_document`, so the
items, prices, taxes and links carry over and the chain stays traceable.

## Before you start
- A company must exist (`erpnext_list_documents` on `Company`). Pass `company` on
  every document; do not rely on a user default.
- Look up masters first: `erpnext_search_link` (`doctype` `Customer`, `txt`) finds
  an existing customer; `erpnext_get_doctype_meta` lists a DocType's fields and
  which are required (`reqd: 1`).
- `docstatus`: 0 = Draft, 1 = Submitted, 2 = Cancelled. Only submitted documents
  post to the ledger or can be mapped forward.

## Steps
1. **Customer** (if new): `erpnext_create_document` `doctype` `Customer`, `data`
   `{"customer_name", "customer_group": "All Customer Groups", "territory":
   "All Territories", "customer_type": "Company"}`.
2. **Quotation**: `erpnext_create_document` `Quotation` with `quotation_to`
   `Customer`, `party_name` (the customer name), `company`, `currency`,
   `selling_price_list` and `items` `[{"item_code", "qty", "rate"}]`. Then
   `erpnext_submit_document` (`doctype`, `name`).
3. **Sales Order**: `erpnext_make_mapped_document` `method`
   `erpnext.selling.doctype.quotation.quotation.make_sales_order`, `source_name`
   the quotation. The result (`message`) is an unsaved draft: set `delivery_date`
   on the order and on each item, set `warehouse` on each stock item, then save it
   with `erpnext_create_document` `Sales Order` and submit it.
4. **Sales Invoice**: `erpnext_make_mapped_document` `method`
   `erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice` from the
   order; save with `erpnext_create_document` `Sales Invoice`; submit. Submitting
   posts the receivable and income GL entries.
5. **Payment Entry**: `erpnext_call_method` `method`
   `erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry`,
   `params` `{"dt": "Sales Invoice", "dn": "<invoice>"}` returns a draft that
   already allocates the full outstanding amount to the invoice. Set
   `reference_no` and `reference_date` (required for bank modes), save with
   `erpnext_create_document` `Payment Entry`, then submit.
6. **Verify**: `erpnext_get_value` `Sales Invoice`, `fieldname`
   `["outstanding_amount", "status"]`, `filters` the invoice name, shows
   `outstanding_amount` 0 and `status` `Paid`. `erpnext_run_report`
   `Accounts Receivable` no longer lists it.
7. Optional: attach the signed quote or remittance with `erpnext_upload_file`
   (`attached_to_doctype`, `attached_to_name`, `content_base64`).

## Corrections
- A submitted document cannot be edited. `erpnext_cancel_document` reverses it
  (cancel the payment before the invoice, the invoice before the order); then
  amend by creating a new document.
- A refused call returns the server's reason, for example
  `API error: 417 LinkValidationError: Could not find Customer: X`. Fix the field
  it names and retry; do not retry unchanged.

## Never
- Never send the invoice by email to a real customer from a test run.
- Never delete a submitted document; cancel it.
