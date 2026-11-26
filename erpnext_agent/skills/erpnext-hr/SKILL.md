---
name: erpnext-hr
skill_type: skill
description: >-
  Keep the ERPNext (Frappe) HR records via erpnext-mcp: employees, departments, designations, holiday lists, attendance, leave and salary set-up, one typed tool per operation. Use to look up or change an HR record, report headcount, or pick the right HR workflow. For hire or exit use erpnext-hire-to-retire; for pay erpnext-payroll-run.
license: MIT
tags: [erpnext, frappe, hr, employee, attendance, leave, mcp]
metadata:
  version: '2.0.0'
---
# ERPNext HR

Scope: Keep the ERPNext (Frappe) HR records through the erpnext-mcp MCP server: employees, departments, designations, holiday lists, attendance, leave and the salary set-up, with one typed tool per operation. Use when the agent must look up or change an HR record, report headcount, or pick the right HR workflow. For a full hire or exit use erpnext-hire-to-retire; for leave decisions erpnext-leave-approval; for a pay run erpnext-payroll-run.

Employee, Department, Designation and Holiday List ship with ERPNext. Leave,
attendance, salary and payroll come from the HR app: check `erpnext_get_version`
for an `hrms` entry before using them.

## Steps

1. Check the HR app with `erpnext_get_version` and verify an `hrms` entry is present before using leave, salary or payroll tools.
2. Find the person with `erpnext_search_link` `Employee` and verify the returned `name` is the series id such as `HR-EMP-00001`.
3. Report headcount with `erpnext_get_count` `Employee` and `filters` `{"company": ..., "status": "Active"}` and verify a numeric count is returned.
4. Change a record with `erpnext_update_employee` and verify `erpnext_get_employee` shows the new values.
5. Record a departure with `erpnext_relieve_employee` and verify `erpnext_get_employee` shows `status` as `Left`.

## Failure recovery

| Failure | Cause | Recovery |
|---|---|---|
| Leave or salary tool not available | `hrms` is not installed on the site | Limit the work to Employee, Department, Designation and Holiday List records and report the missing app |
| Duplicate employee created | The search step was skipped | Search with `erpnext_search_link` `Employee` first and update the existing record |
| Department not found | Departments are per company and named `<department> - <abbr>` | Create it with `erpnext_create_department` using that name and retry the change |
| Employee removal requested | Employees with history must not be deleted | Use `erpnext_relieve_employee` to set the relieving date and status `Left` |

## Records and their tools
| Record | Create / change | Read |
|---|---|---|
| Employee | `erpnext_create_employee`, `erpnext_update_employee`, `erpnext_relieve_employee` | `erpnext_get_employee`, `erpnext_list_employees` |
| Department | `erpnext_create_department` | `erpnext_list_departments` |
| Designation | `erpnext_create_designation` | `erpnext_list_designations` |
| Holiday List | `erpnext_create_holiday_list`, `erpnext_add_holiday_list_weekly_offs` | `erpnext_get_holiday_list` |
| Attendance | `erpnext_mark_attendance`, `erpnext_mark_bulk_attendance` | `erpnext_list_attendance` |
| Check-in | `erpnext_add_employee_checkin` | `erpnext_list_documents` `Employee Checkin` |
| Leave | `erpnext_create_leave_type`, `erpnext_allocate_leave`, `erpnext_apply_leave`, `erpnext_approve_leave_application`, `erpnext_reject_leave_application` | `erpnext_get_leave_balance` |
| Salary | `erpnext_create_salary_component`, `erpnext_create_salary_structure`, `erpnext_assign_salary_structure` | `erpnext_get_salary_slip`, `erpnext_list_salary_slips` |

## Procedure
1. **Find before you create**: `erpnext_search_link` `Employee` with the
   person's name; the record's `name` is its series id (`HR-EMP-00001`).
2. **Headcount**: `erpnext_get_count` `Employee` with `filters`
   `{"company": ..., "status": "Active"}`.
3. **Departments** are per company and named `<department> - <abbr>`;
   designations are shared by every company.
4. **Leaving**: `erpnext_relieve_employee` sets the relieving date and status
   `Left`. Never delete an employee with history.

## Privacy
Employee records are personal data. Request only the fields you need and never
copy them into a public channel.
