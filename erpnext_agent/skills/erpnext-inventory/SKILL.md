---
name: erpnext-inventory
skill_type: skill
description: >-
  Maintain the ERPNext (Frappe) item catalog and stock via erpnext-mcp: create items, receive, issue or transfer stock with stock entries, read stock on hand per warehouse. Use to add a product, record goods received or used, move stock, or check quantities. Do NOT use for selling (erpnext-order-to-cash) or supplier bills (erpnext-procure-to-pay).
license: MIT
tags: [erpnext, frappe, inventory, stock, item, warehouse, mcp]
metadata:
  version: '1.0.0'
---
# ERPNext inventory

Scope: Maintain the ERPNext (Frappe) item catalog and stock through the erpnext-mcp MCP server: create items, receive, issue or transfer stock with stock entries, and read stock on hand per warehouse. Use when the agent must add a product, record goods received or used, move stock between warehouses, or check quantities. Do NOT use for selling (use erpnext-order-to-cash) or supplier bills (use erpnext-procure-to-pay).

## Steps

1. List the item groups with `erpnext_list_documents` `Item Group` and verify the group you need exists.
2. Create the item with `erpnext_create_document` `Item` and verify `erpnext_list_documents` `Item` returns it.
3. Draft the movement with `erpnext_create_document` `Stock Entry` and verify the response shows a draft with the intended `items`.
4. Post it with `erpnext_submit_document` and verify the document is submitted.
5. Read the quantity with `erpnext_get_value` `Bin` and `fieldname` `["actual_qty", "projected_qty"]` and verify `actual_qty` matches the expected stock.

## Failure recovery

| Failure | Cause | Recovery |
|---|---|---|
| Warehouse not found | Warehouses are per company, for example `Stores - <abbr>` | List them with `erpnext_list_documents` `Warehouse` and `filters` `{"company": ...}` and use the exact name |
| Wrong entry posted | A submitted Stock Entry has wrong quantities | Call `erpnext_cancel_document` on it and enter a corrected Stock Entry |
| Item rejected | A required field such as `stock_uom` or `item_group` is missing | Set `item_code`, `item_name`, `item_group`, `stock_uom` and `is_stock_item` and create the item again |
| Stock Balance report slow or empty | The period or company filter is wrong | Pass `company`, `from_date` and `to_date` to `erpnext_run_report` `Stock Balance` |

## Item
`erpnext_create_document` `Item` with `item_code`, `item_name`, `item_group`
(`Products`, `Services`, ... ; list with `erpnext_list_documents` `Item Group`),
`stock_uom` (`Nos`, `Kg`, ...), `is_stock_item` (1 for stocked goods, 0 for
services) and `standard_rate`.

## Stock movement
1. `erpnext_create_document` `Stock Entry` with `company`, `stock_entry_type`
   (`Material Receipt`, `Material Issue`, `Material Transfer`) and `items`
   `[{"item_code", "qty", "t_warehouse" (receipt/transfer target),
   "s_warehouse" (issue/transfer source), "basic_rate" (receipt valuation)}]`.
   Warehouses are per company, for example `Stores - <abbr>`
   (`erpnext_list_documents` `Warehouse` with `filters` `{"company": ...}`).
2. `erpnext_submit_document` writes the stock ledger and, with perpetual
   inventory, the stock GL entries.
3. A wrong entry: `erpnext_cancel_document`, then enter it again.

## Stock on hand
- One item in one warehouse: `erpnext_get_value` `Bin`, `fieldname`
  `["actual_qty", "projected_qty"]`, `filters` `{"item_code", "warehouse"}`.
- Everything: `erpnext_run_report` `Stock Balance` with `company`, `from_date`,
  `to_date` (runs synchronously even though the report is a background report).

## Knowledge graph
`erpnext_ingest` with `doctype` `Item` pushes the catalog as `:Item` nodes.
