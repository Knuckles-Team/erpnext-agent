---
name: erpnext-accounting
skill_type: skill
description: >-
  Read the ERPNext (Frappe) books through the erpnext-mcp MCP server: chart of
  accounts, general ledger, trial balance, receivable and payable ageing, and stock
  balance, for one company and period. Use when the agent must answer "what do we
  owe / what are we owed", review postings for a document, or produce period
  figures. Do NOT use to create sales or purchase documents (use
  erpnext-order-to-cash / erpnext-procure-to-pay).
license: MIT
tags: [erpnext, frappe, accounting, ledger, reports, receivable, payable, mcp]
metadata:
  version: '1.0.0'
---
# ERPNext accounting and reports

All reports run with `erpnext_run_report` (`report_name`, `filters`) and return
`message.columns` and `message.result`. Always pass `company`.

| Question | `report_name` | Required filters |
|----------|---------------|------------------|
| Postings in a period | `General Ledger` | `company`, `from_date`, `to_date`, `group_by` (`Group by Voucher (Consolidated)`); optional `voucher_no`, `party_type`, `party` |
| Balances per account | `Trial Balance` | `company`, `fiscal_year`, `from_date`, `to_date` |
| What customers owe | `Accounts Receivable` | `company`, `report_date`, `ageing_based_on` (`Due Date`), `range1`..`range4` (30, 60, 90, 120) |
| What we owe suppliers | `Accounts Payable` | same as receivable |
| Stock value and quantity | `Stock Balance` | `company`, `from_date`, `to_date` |
| Profit and loss | `Profit and Loss Statement` | `company`, `period_start_date`, `period_end_date`, `periodicity` (`Monthly`), `filter_based_on` (`Date Range`), `from_fiscal_year`, `to_fiscal_year` |
| Balance sheet | `Balance Sheet` | same as profit and loss |

## Ledger reads
- Chart of accounts: `erpnext_list_documents` `Account`, `filters`
  `{"company": ...}`, `fields` `["name","root_type","account_type","is_group","parent_account"]`.
- One document's postings: `erpnext_list_documents` `GL Entry`, `filters`
  `{"voucher_no": "<doc>", "is_cancelled": 0}`, `fields`
  `["account","debit","credit","party"]`.
- Fiscal years: `erpnext_list_documents` `Fiscal Year`.

## Gotchas
- A report's filter names come from the report itself; when one is refused the
  error names the missing filter.
- Background ("prepared") reports such as Stock Balance still return rows in
  the same call; a very large period may take up to the 120 s server timeout,
  so narrow the dates.
