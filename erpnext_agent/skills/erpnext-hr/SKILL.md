---
name: erpnext-hr
skill_type: skill
description: >-
  Keep the ERPNext (Frappe) employee master through the erpnext-mcp MCP server:
  create employees for a company, read and count them, and record departments. Use
  when the agent must onboard an employee record, look one up, or report headcount.
  Payroll, leave and attendance need the separate HR app; do NOT use this skill for
  them until that app is installed.
license: MIT
tags: [erpnext, frappe, hr, employee, mcp]
metadata:
  version: '1.0.0'
---
# ERPNext HR basics

The Employee master ships with ERPNext itself. Leave, attendance, salary
structures and payroll come from the separate HR app; check
`erpnext_get_version` for an `hrms` entry before using them.

## Steps
1. **Employee**: `erpnext_create_document` `Employee` with `first_name`,
   `last_name`, `gender` (a `Gender` record: `Male`, `Female`, `Other`, ...),
   `date_of_birth`, `date_of_joining`, `company`, and optionally `department`,
   `designation`, `reports_to`.
2. **Find**: `erpnext_search_link` `Employee` with the person's name; the
   record's `name` is its series id (`HR-EMP-00001`).
3. **Headcount**: `erpnext_get_count` `Employee` with `filters`
   `{"company": ..., "status": "Active"}`.
4. **Leaving**: `erpnext_set_value` `Employee` `relieving_date`, then `status`
   `Left`. Never delete an employee with history.

## Privacy
Employee records are personal data. Request only the fields you need and never
copy them into a public channel.
