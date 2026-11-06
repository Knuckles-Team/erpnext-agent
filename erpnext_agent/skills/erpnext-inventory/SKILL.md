---
name: erpnext-inventory
skill_type: skill
description: >-
  Maintain the ERPNext (Frappe) item catalog and stock through the erpnext-mcp MCP
  server: create items, receive, issue or transfer stock with stock entries, and read
  stock on hand per warehouse. Use when the agent must add a product, record goods
  received or used, move stock between warehouses, or check quantities. Do NOT use
  for selling (use erpnext-order-to-cash) or supplier bills (use
  erpnext-procure-to-pay).
license: MIT
tags: [erpnext, frappe, inventory, stock, item, warehouse, mcp]
metadata:
  version: '1.0.0'
---
# ERPNext inventory

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
