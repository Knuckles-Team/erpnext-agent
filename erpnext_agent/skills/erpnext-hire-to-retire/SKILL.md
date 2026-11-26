---
name: erpnext-hire-to-retire
skill_type: skill
description: >-
  Run an employee's life cycle in ERPNext (Frappe) via erpnext-mcp: hire, first leave allocation and salary assignment, attendance, role changes, and exit. Use to onboard a hire, move someone to a new role or department, or process a resignation or retirement. Do NOT use for leave decisions (erpnext-leave-approval) or pay runs (erpnext-payroll-run).
license: MIT
tags: [erpnext, frappe, hr, onboarding, offboarding, employee, mcp]
metadata:
  version: '1.0.0'
---
# ERPNext hire to retire

Scope: Run an employee's whole life cycle in ERPNext (Frappe) through the erpnext-mcp MCP server: hire (department, designation, holiday list, employee record), first leave allocation and salary assignment, day-to-day attendance, role changes, and the exit (relieving date, status Left). Use when the agent must onboard a new hire, move someone to a new role or department, or process a resignation or retirement. Do NOT use for approving leave (use erpnext-leave-approval) or for a pay run (use erpnext-payroll-run).

Hire → set up → work → change → exit. The employee record is kept for life:
it is never deleted.

## Steps

1. Search for the person with `erpnext_search_link` `Employee` and verify no duplicate record is returned.
2. Check the HR app with `erpnext_get_version` and verify an `hrms` entry is present.
3. Create the record with `erpnext_create_employee` and verify `erpnext_get_employee` returns it with status Active.
4. Allocate leave with `erpnext_allocate_leave` and verify `erpnext_get_leave_balance` shows the allocated days.
5. Assign pay with `erpnext_assign_salary_structure` from the joining date and verify the assignment is submitted.
6. Process an exit with `erpnext_relieve_employee` and verify `erpnext_get_employee` shows `status` as `Left`.

## Failure recovery

| Failure | Cause | Recovery |
|---|---|---|
| Duplicate employee | The person already exists | Use the record found by `erpnext_search_link` and change it with `erpnext_update_employee` |
| Leave or salary tools unavailable | The HR app is not installed | Stop the leave and salary steps, and report that `erpnext_get_version` lacks `hrms` |
| Department or designation not found | It was never created for the company | Create it with `erpnext_create_department` (named `<department> - <abbr>`) or `erpnext_create_designation` and repeat the hire |
| Exit blocked by open leave or pay | Leave applications or the last pay run are not settled | Decide the open requests with erpnext-leave-approval and finish erpnext-payroll-run, then call `erpnext_relieve_employee` |

## Before you start
- The company exists and has a default holiday list (`erpnext_get_setup_status`
  lists companies). The HR app must be installed for leave and salary steps
  (`erpnext_get_version` shows `hrms`).
- Find the person first with `erpnext_search_link` `Employee` to avoid a duplicate.

## Hire
1. **Department**: `erpnext_list_departments` for the company; create a missing one
   with `erpnext_create_department` (named `<department> - <abbr>`).
2. **Designation**: `erpnext_list_designations`; create with
   `erpnext_create_designation`.
3. **Holiday list**: `erpnext_get_holiday_list`; create a year's list with
   `erpnext_create_holiday_list` (`weekly_off` `Sunday` fills the weekly offs).
4. **Employee**: `erpnext_create_employee` with `first_name`, `gender`,
   `date_of_birth`, `date_of_joining`, `company`, `department`, `designation`,
   `holiday_list` and, if known, `reports_to`.
5. **Leave**: `erpnext_allocate_leave` for each entitled leave type for the year.
6. **Pay**: `erpnext_assign_salary_structure` with the structure, `from_date` (the
   joining date), `base`, `company` and `currency`.

## Work
- Daily attendance: `erpnext_mark_attendance`, or `erpnext_mark_bulk_attendance`
  for a team. Device or app check-ins: `erpnext_add_employee_checkin`.
- Review: `erpnext_list_attendance` for the employee and month.

## Change
- New role, department or manager: `erpnext_update_employee` with the changed
  fields. A pay change is a new `erpnext_assign_salary_structure` from the
  effective date; never edit a submitted assignment.

## Exit
1. Confirm open leave applications are decided (erpnext-leave-approval) and the
   last pay run is done (erpnext-payroll-run).
2. `erpnext_relieve_employee` with `relieving_date` and `reason_for_leaving`
   (status becomes `Left`).
3. Verify with `erpnext_get_employee`: `status` is `Left`.

## Guardrails
- Hiring, pay changes and exits need the HR manager's approval before you write.
- Employee data is personal: read only what the step needs, never post it to a
  public channel, and never email from a test run.
