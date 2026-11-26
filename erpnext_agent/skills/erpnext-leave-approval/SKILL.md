---
name: erpnext-leave-approval
skill_type: skill
description: >-
  Handle leave in ERPNext (Frappe) with the HR app via erpnext-mcp: leave types, yearly allocations, a leave application, the approver's decision and the remaining balance. Use to set up entitlements, file or decide a leave request, or answer how many days are left. Do NOT use for attendance corrections or pay.
license: MIT
tags: [erpnext, frappe, hrms, leave, approval, mcp]
metadata:
  version: '1.0.0'
---
# ERPNext leave approval

Scope: Handle leave in ERPNext (Frappe) with the HR app through the erpnext-mcp MCP server: leave types, yearly allocations, an employee's leave application, the approver's decision (approve or reject, then submit) and the remaining balance. Use when the agent must set up leave entitlements, file a leave request, decide an open request or answer "how many days does this person have left". Do NOT use for attendance corrections (use erpnext-hire-to-retire) or pay (use erpnext-payroll-run).

Leave Type → Leave Allocation → Leave Application (Open) → Approved or
Rejected → submitted.

## Steps

1. Check the entitlement with `erpnext_get_leave_balance` and verify the balance covers the requested days.
2. File the request with `erpnext_apply_leave` and verify `erpnext_get_document` `Leave Application` shows status Open.
3. Review it with `erpnext_list_documents` `Leave Application` filtered to `status` `Open` and verify no clashing request exists.
4. After the named approver agrees, call `erpnext_approve_leave_application` and verify the application status is Approved.
5. Confirm the effect with `erpnext_get_leave_balance` and verify the balance dropped by the approved days.

## Failure recovery

| Failure | Cause | Recovery |
|---|---|---|
| Balance too low | The request exceeds the allocation and the type disallows negative balance | Refuse the request, or add an allocation with `erpnext_allocate_leave` if the HR manager approves |
| Leave type missing | No `Leave Type` record exists | Create it with `erpnext_create_leave_type` and allocate leave again |
| Decision without authority | The caller is not the named leave approver or HR manager | Stop and ask the approver, then call `erpnext_approve_leave_application` or `erpnext_reject_leave_application` on their instruction |
| Wrong application submitted | A submitted application cannot be edited | Call `erpnext_cancel_document` on it and file a new application with `erpnext_apply_leave` |

## Set up (once per year)
1. **Leave type**: `erpnext_list_documents` `Leave Type`; create a missing one
   with `erpnext_create_leave_type` (`max_leaves_allowed`, `is_lwp` for unpaid
   leave, `is_carry_forward`).
2. **Allocation**: `erpnext_allocate_leave` per employee and leave type with the
   period's `from_date`, `to_date` and `new_leaves_allocated`; it is submitted.

## Request
3. **Balance first**: `erpnext_get_leave_balance` for the employee, leave type and
   start date. Refuse a request larger than the balance unless the type allows
   negative balance.
4. **Apply**: `erpnext_apply_leave` with `employee`, `leave_type`, `from_date`,
   `to_date`, `company` and the `leave_approver`. It stays Open (draft).

## Decide
5. Read the request with `erpnext_get_document` `Leave Application`; check the
   team calendar with `erpnext_list_attendance` and other open requests with
   `erpnext_list_documents` `Leave Application` (`status` `Open`).
6. **Approve**: `erpnext_approve_leave_application`; **reject**:
   `erpnext_reject_leave_application`. Each sets the status and submits.
7. Verify: `erpnext_get_leave_balance` dropped by the approved days.

## Guardrails
- Only the named leave approver (or the HR manager) decides. The agent prepares
  the decision and asks before calling approve or reject.
- A submitted application is changed only by `erpnext_cancel_document`, then a new
  application.
