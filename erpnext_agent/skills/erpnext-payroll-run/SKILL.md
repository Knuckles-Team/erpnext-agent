---
name: erpnext-payroll-run
skill_type: skill
description: >-
  Run a monthly payroll in ERPNext (Frappe) with the HR app via erpnext-mcp: salary components, structure and assignment, then a payroll entry that creates and submits salary slips. Test data only until the owner approves live payroll. Use to set up pay or run a period. Do NOT use for employee records or supplier payments.
license: MIT
tags: [erpnext, frappe, hrms, payroll, salary, mcp]
metadata:
  version: '1.0.0'
---
# ERPNext payroll run (test data only)

Scope: Run a monthly payroll in ERPNext (Frappe) with the HR app through the erpnext-mcp MCP server: salary components, a salary structure and its assignment, then a payroll entry that is filled with employees, creates the salary slips and submits them. Test data only until the owner approves live payroll. Use when the agent must set up pay for a test company, run or re-run a pay period, or read salary slips. Do NOT use for the employee record itself (use erpnext-hire-to-retire) or for paying suppliers (use erpnext-procure-to-pay).

Salary Component → Salary Structure → Salary Structure Assignment → Payroll
Entry → fill employees → create slips → submit slips.

Run this only on a test company (for example `zz-validation-<date>`) until the
owner approves payroll on real employees.

## Steps

1. Create each pay component with `erpnext_create_salary_component` and verify `erpnext_list_documents` `Salary Component` lists it.
2. Create the structure with `erpnext_create_salary_structure` and verify the response shows it submitted.
3. Assign it with `erpnext_assign_salary_structure` for each employee and verify the assignment is submitted with the right `from_date`.
4. Open the run with `erpnext_create_payroll_entry` and verify the response returns the entry name for the period.
5. Load the staff with `erpnext_fill_payroll_employees` and verify the entry lists every assigned employee.
6. Generate the slips with `erpnext_create_salary_slips` and verify `erpnext_list_salary_slips` shows one draft per employee.
7. Post them with `erpnext_submit_salary_slips` and verify `erpnext_get_salary_slip` shows a submitted slip.

## Failure recovery

| Failure | Cause | Recovery |
|---|---|---|
| `erpnext_fill_payroll_employees` refused | No employee has an active assignment for the period | Create the assignment with `erpnext_assign_salary_structure` with a `from_date` inside the period and fill again |
| Payroll payable account or cost center unknown | The wrong ledger or cost center was passed | Find them with `erpnext_list_documents` (`Account` with `account_type` `Payable`, and `Cost Center`) and pass them to `erpnext_create_payroll_entry` |
| Run requested on real employees | Payroll is test-data only until the owner approves | Stop and ask the owner for explicit approval for that run before any write |
| Wrong run posted | Submitted slips cannot be edited | Cancel each slip, then the entry, with `erpnext_cancel_document`, and delete drafts with `erpnext_delete_document` |

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
