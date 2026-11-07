---
name: erpnext-procure-to-pay
skill_type: skill
description: >-
  Book supplier purchases in ERPNext (Frappe) through the erpnext-mcp MCP server:
  create the supplier, book the supplier's bill as a purchase invoice against the
  right expense or stock account, submit it to payables, and pay or cancel it. Use
  when the agent must record a vendor bill, check what is owed to a supplier, or pay
  it. Do NOT use for customer billing (use erpnext-order-to-cash) or stock counts
  (use erpnext-inventory).
license: MIT
tags: [erpnext, frappe, purchase, supplier, payables, procure-to-pay, mcp]
metadata:
  version: '1.0.0'
---
# ERPNext procure to pay

Supplier → (Purchase Order, optional) → Purchase Invoice → Payment Entry.

## Steps
1. **Supplier** (if new): `erpnext_search_link` `Supplier` first; otherwise
   `erpnext_create_document` `Supplier` with `supplier_name` and
   `supplier_group` (`All Supplier Groups`).
2. **Purchase Invoice**: `erpnext_create_document` `Purchase Invoice` with
   `supplier`, `company`, `posting_date`, `bill_no` (the supplier's invoice
   number), `currency`, `buying_price_list` and `items`
   `[{"item_code", "qty", "rate", "expense_account"}]`. For a service bill use
   an expense account (`erpnext_list_documents` `Account` with filters
   `[["company","=",...],["root_type","=","Expense"],["is_group","=",0]]`).
3. Submit it with `erpnext_submit_document`; this books the payable.
4. **Pay**: `erpnext_call_method`
   `erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry` with
   `{"dt": "Purchase Invoice", "dn": "<bill>"}`, set `reference_no` and
   `reference_date`, save with `erpnext_create_document` `Payment Entry`,
   submit.
5. **Wrong bill**: `erpnext_cancel_document` (cancel the payment first if one is
   allocated), then book a corrected invoice.

## Document lifecycle
Legal moves: Draft -submit-> Submitted -cancel-> Cancelled -amend-> a new Draft
(`erpnext_amend_document`, which sets `amended_from`). Every other move is
refused before it reaches ERPNext with `STATE_TRANSITION_REFUSED` and one reason:
`NotDraft`, `NotSubmittable`, `NotSubmitted`, `HasSubmittedLinks` (cancel the
linked documents first), `StaleDocument` (re-read the document and pass its
current `modified` to `erpnext_cancel_document`), `NotCancelled` or
`UnknownDocstatus`. To correct a cancelled document, amend it; do not recreate it.

## Verify
- `erpnext_get_value` `Purchase Invoice` `["outstanding_amount", "status"]`.
- `erpnext_run_report` `Accounts Payable` with `company` and `report_date`.

## Gotchas
- `bill_no` + `supplier` should be unique; check with `erpnext_get_count` before
  booking to avoid a duplicate bill.
- A stock item on a purchase invoice only updates stock when `update_stock` is 1;
  otherwise receive it with a Purchase Receipt or Stock Entry.
