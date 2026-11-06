# Provider workflow catalog

Load only the workflow relevant to the current request.

- [erpnext-order-to-cash](../../erpnext-order-to-cash/SKILL.md): customer, quotation, sales order, sales invoice and payment entry.
- [erpnext-procure-to-pay](../../erpnext-procure-to-pay/SKILL.md): supplier, purchase invoice, supplier payment.
- [erpnext-inventory](../../erpnext-inventory/SKILL.md): items, stock entries, stock on hand.
- [erpnext-crm-pipeline](../../erpnext-crm-pipeline/SKILL.md): lead, opportunity, quotation.
- [erpnext-projects](../../erpnext-projects/SKILL.md): projects and tasks.
- [erpnext-hr](../../erpnext-hr/SKILL.md): employee master and headcount.
- [erpnext-accounting](../../erpnext-accounting/SKILL.md): chart of accounts, ledger and financial reports.

## Tool surface
One typed tool per Frappe operation: `erpnext_list_documents`,
`erpnext_get_document`, `erpnext_create_document`, `erpnext_update_document`,
`erpnext_delete_document`, `erpnext_submit_document`, `erpnext_cancel_document`,
`erpnext_get_count`, `erpnext_get_value`, `erpnext_set_value`,
`erpnext_rename_document`, `erpnext_make_mapped_document`,
`erpnext_run_document_method`, `erpnext_get_doctype_meta`, `erpnext_run_report`,
`erpnext_search_link`, `erpnext_upload_file`, `erpnext_call_method` (any other
whitelisted method), `erpnext_get_version`, `erpnext_get_logged_user`,
`erpnext_login`, `erpnext_logout` and `erpnext_ingest` (knowledge graph).
