# Provider workflow catalog

Load only the workflow relevant to the current request.

- [erpnext-order-to-cash](../../erpnext-order-to-cash/SKILL.md): customer, quotation, sales order, sales invoice and payment entry.
- [erpnext-procure-to-pay](../../erpnext-procure-to-pay/SKILL.md): supplier, purchase invoice, supplier payment.
- [erpnext-inventory](../../erpnext-inventory/SKILL.md): items, stock entries, stock on hand.
- [erpnext-crm-pipeline](../../erpnext-crm-pipeline/SKILL.md): lead, opportunity, sales stage, quotation.
- [erpnext-lead-nurturing](../../erpnext-lead-nurturing/SKILL.md): touches, follow-ups, qualification, won or lost.
- [erpnext-projects](../../erpnext-projects/SKILL.md): projects and tasks.
- [erpnext-hr](../../erpnext-hr/SKILL.md): HR records and which HR workflow to use.
- [erpnext-hire-to-retire](../../erpnext-hire-to-retire/SKILL.md): hire, set up, change and exit an employee.
- [erpnext-leave-approval](../../erpnext-leave-approval/SKILL.md): leave types, allocations, requests and decisions.
- [erpnext-payroll-run](../../erpnext-payroll-run/SKILL.md): salary set-up and a payroll entry (test data only).
- [erpnext-accounting](../../erpnext-accounting/SKILL.md): chart of accounts, ledger and financial reports.
- [erpnext-business-onboarding](../../erpnext-business-onboarding/SKILL.md): repeatable company onboarding with a dry run.

## Tool surface
One typed tool per Frappe operation.

- Generic documents: `erpnext_list_documents`, `erpnext_get_document`,
  `erpnext_create_document`, `erpnext_update_document`, `erpnext_delete_document`,
  `erpnext_submit_document`, `erpnext_cancel_document`, `erpnext_get_count`,
  `erpnext_get_value`, `erpnext_set_value`, `erpnext_rename_document`,
  `erpnext_make_mapped_document`, `erpnext_run_document_method`,
  `erpnext_get_doctype_meta`, `erpnext_run_report`, `erpnext_search_link`,
  `erpnext_upload_file`, `erpnext_call_method` (any other whitelisted method).
- HR: `erpnext_create_employee`, `erpnext_update_employee`, `erpnext_get_employee`,
  `erpnext_list_employees`, `erpnext_relieve_employee`, `erpnext_create_department`,
  `erpnext_list_departments`, `erpnext_create_designation`,
  `erpnext_list_designations`, `erpnext_create_holiday_list`,
  `erpnext_add_holiday_list_weekly_offs`, `erpnext_get_holiday_list`,
  `erpnext_mark_attendance`, `erpnext_mark_bulk_attendance`,
  `erpnext_list_attendance`, `erpnext_add_employee_checkin`,
  `erpnext_create_leave_type`, `erpnext_allocate_leave`, `erpnext_apply_leave`,
  `erpnext_approve_leave_application`, `erpnext_reject_leave_application`,
  `erpnext_get_leave_balance`, `erpnext_create_salary_component`,
  `erpnext_create_salary_structure`, `erpnext_assign_salary_structure`,
  `erpnext_create_payroll_entry`, `erpnext_fill_payroll_employees`,
  `erpnext_create_salary_slips`, `erpnext_submit_salary_slips`,
  `erpnext_list_salary_slips`, `erpnext_get_salary_slip`.
- CRM: `erpnext_create_lead`, `erpnext_update_lead`, `erpnext_qualify_lead`,
  `erpnext_list_leads`, `erpnext_create_opportunity_from_lead`,
  `erpnext_update_opportunity_stage`, `erpnext_declare_opportunity_lost`,
  `erpnext_create_opportunity_lost_reason`, `erpnext_list_opportunities`,
  `erpnext_make_customer_from_lead`, `erpnext_make_customer_from_opportunity`,
  `erpnext_create_sales_stage`, `erpnext_list_sales_stages`,
  `erpnext_create_opportunity_type`, `erpnext_list_opportunity_types`,
  `erpnext_log_communication`, `erpnext_create_follow_up`,
  `erpnext_list_follow_ups`, `erpnext_close_follow_up`.
- Onboarding: `erpnext_get_setup_status`, `erpnext_list_timezones`,
  `erpnext_list_chart_of_accounts_templates`, `erpnext_complete_setup_wizard`,
  `erpnext_create_company`, `erpnext_create_fiscal_year`, `erpnext_create_address`,
  `erpnext_create_bank`, `erpnext_create_bank_account`, `erpnext_set_tax_id`,
  `erpnext_plan_business_onboarding`, `erpnext_apply_business_onboarding`,
  `erpnext_verify_business_onboarding`.
- Session and KG: `erpnext_get_version`, `erpnext_get_logged_user`,
  `erpnext_login`, `erpnext_logout`, `erpnext_ingest`.
