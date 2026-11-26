---
name: erpnext-projects
skill_type: skill
description: >-
  Track ERPNext (Frappe) projects and their tasks through the erpnext-mcp MCP
  server: create a project for a company, add tasks, move task status, and read the
  project's completion. Use when the agent must set up client or internal project
  work in the ERP, close tasks, or report project progress. Do NOT use for billing
  the project (use erpnext-order-to-cash).
license: MIT
tags: [erpnext, frappe, projects, tasks, mcp]
metadata:
  version: '1.0.0'
---
# ERPNext projects

## Steps

1. Find an existing project with `erpnext_search_link` `Project` and verify its `name` is the series id such as `PROJ-0001`.
2. Create it with `erpnext_create_document` `Project` and verify `erpnext_get_value` `Project` returns its `status`.
3. Add work with `erpnext_create_document` `Task` and verify `erpnext_list_documents` `Task` lists it under the project.
4. Update progress with `erpnext_set_value` `Task` `fieldname` `status` and verify `erpnext_get_value` shows the new status.
5. Report with `erpnext_get_value` `Project` `fieldname` `["percent_complete", "status"]` and verify `percent_complete` reflects the closed tasks.

## Failure recovery

| Failure | Cause | Recovery |
|---|---|---|
| Project not found by name | `name` is the naming series, not `project_name` | Find it with `erpnext_search_link` `Project` and use the returned series id |
| Task rejected | `project` holds a name that does not exist | Pass the exact project `name` such as `PROJ-0001` from `erpnext_search_link` |
| Status change rejected | The value is not an allowed status | Use one of `Open`, `Working`, `Pending Review`, `Overdue`, `Completed`, `Cancelled` |

## Procedure
1. **Project**: `erpnext_create_document` `Project` with `project_name`,
   `company`, and optionally `customer`, `expected_start_date`,
   `expected_end_date`. `percent_complete_method` defaults to task completion.
2. **Task**: `erpnext_create_document` `Task` with `subject`, `project` (the
   project `name`, for example `PROJ-0001`), and optionally `exp_start_date`,
   `exp_end_date`, `parent_task`.
3. **Progress**: `erpnext_set_value` `Task`, `fieldname` `status`, `value` one
   of `Open`, `Working`, `Pending Review`, `Overdue`, `Completed`, `Cancelled`.
4. **Report**: `erpnext_get_value` `Project`, `fieldname`
   `["percent_complete", "status"]`, `filters` the project name; list open work
   with `erpnext_list_documents` `Task` and `filters`
   `[["project","=","PROJ-0001"],["status","!=","Completed"]]`.

## Gotchas
- A project's `name` is its naming series (`PROJ-0001`), not `project_name`;
  use `erpnext_search_link` `Project` to find it.
- Closing every task sets the project to 100 % and `Completed`.
