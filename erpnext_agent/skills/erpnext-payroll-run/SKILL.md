---
name: erpnext-payroll-run
skill_type: skill
description: >-
  Run a monthly payroll in ERPNext (Frappe) with the HR app through the
  erpnext-mcp MCP server: salary components, a salary structure and its assignment,
  then a payroll entry that is filled with employees, creates the salary slips and
  submits them. Test data only until the owner approves live payroll. Use when the
  agent must set up pay for a test company, run or re-run a pay period, or read
  salary slips. Do NOT use for the employee record itself (use
  erpnext-hire-to-retire) or for paying suppliers (use erpnext-procure-to-pay).
license: MIT
tags: [erpnext, frappe, hrms, payroll, salary, mcp]
metadata:
  version: '1.0.0'
---
# ERPNext payroll run (test data only)

Salary Component → Salary Structure → Salary Structure Assignment → Payroll
Entry → fill employees → create slips → submit slips.

Run this only on a test company (for example `zz-validation-<date>`) until the
owner approves payroll on real employees.

## Pay set-up
1. **Components**: `erpnext_create_salary_component` for each earning and
   deduction (`component_type` `Earning` or `Deduction`, a short
   `salary_component_abbr`).
2. **Structure**: `erpnext_create_salary_structure` with `company`, `currency`,
   `earnings` (`[{"salary_component": ..., "amount": ...}]` or a `formula` such as
   `base * 0.5` with `amount_based_on_formula` 1) and `deductions`; it is submitted.
3. **Assignment**: `erpnext_assign_salary_structure` per employee with `from_date`,
   `base`, `company`, `currency`; it is submitted.

## Pay run
4. **Accounts**: find the payroll payable ledger and cost center with
   `erpnext_list_documents` (`Account` with `account_type` `Payable`,
   `Cost Center` of the company).
5. **Entry**: `erpnext_create_payroll_entry` with `company`, `posting_date`,
   `start_date`, `end_date`, `currency`, `payroll_payable_account`, `cost_center`.
6. **Employees**: `erpnext_fill_payroll_employees` (refused when no employee has an
   active assignment for the period).
7. **Slips**: `erpnext_create_salary_slips` (submits the entry, which creates the
   draft slips). Check them with `erpnext_list_salary_slips` and
   `erpnext_get_salary_slip`.
8. **Submit slips**: `erpnext_submit_salary_slips` posts the payroll journal.

## Undo (test runs)
Cancel each submitted slip and then the entry with `erpnext_cancel_document`,
then delete drafts with `erpnext_delete_document`. Never delete a submitted
document.

## Guardrails
- Payroll on real employees needs the owner's explicit approval per run.
- Salary data is personal and confidential: never post it anywhere public, and
  never email slips from a test run.
