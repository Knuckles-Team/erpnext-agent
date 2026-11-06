# CONN-ERPNEXT-AGENT — Quickstart

The shortest path that shows the served behaviour working.

- `CONN-ERPNEXT-AGENT-R002`: run `pytest tests/test_access_contracts.py::test_served_access_contracts_match_synthetic_provider`.
- `CONN-ERPNEXT-AGENT-R004`: run `pytest tests/test_access_contracts.py::test_supplier_and_purchase_order_fields_match_recorded_fixture`.
- `CONN-ERPNEXT-AGENT-R008`: run `pytest tests/test_hr_operations.py`.
- `CONN-ERPNEXT-AGENT-R009`: run `pytest tests/test_crm_operations.py`.
- `CONN-ERPNEXT-AGENT-R010`: run `pytest tests/test_business_onboarding.py`; against a live site, call `erpnext_plan_business_onboarding` with the skill's `references/onboarding-spec.yaml` (mode `company`), then `erpnext_apply_business_onboarding` with `confirm` true, then plan again and see every step `exists`.
