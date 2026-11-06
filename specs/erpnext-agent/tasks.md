# CONN-ERPNEXT-AGENT — Implementation tasks

Governing spec: [spec.md](spec.md). Design: [plan.md](plan.md). Rows: [requirements.md](requirements.md).

Each task line reads `- [ ] T001 [P] [US1] <ID>-R012.4 description`. Order is producer first.

- [x] T001 [US1] CONN-ERPNEXT-AGENT-R001 Connector reports its released version.
- [x] T002 [US1] CONN-ERPNEXT-AGENT-R002 Supplier and purchase-order access fields match served tool data.
- [ ] T003 [US1] CONN-ERPNEXT-AGENT-R003 Supplier table recorded response.
- [ ] T004 [US1] CONN-ERPNEXT-AGENT-R004 Supplier and purchase-order contract fields and recorded fixture.
- [x] T005 [US1] CONN-ERPNEXT-AGENT-R005 Every Frappe business operation is its own typed tool.
- [x] T006 [US1] CONN-ERPNEXT-AGENT-R006 A refused call returns the server's reason.
- [x] T007 [US1] CONN-ERPNEXT-AGENT-R007 Every access contract names a served tool and only its parameters.
- [x] T008 [US1] CONN-ERPNEXT-AGENT-R008 Every HR operation is its own typed tool.
- [x] T009 [US1] CONN-ERPNEXT-AGENT-R009 Every CRM operation is its own typed tool.
- [x] T010 [US1] CONN-ERPNEXT-AGENT-R010 Business onboarding is validated, dry-run first, idempotent and verified.
- [ ] T011 [US1] CONN-ERPNEXT-AGENT-R011 Document lifecycle is one explicit state machine.
- [ ] T012 [US1] CONN-ERPNEXT-AGENT-R011.1 Declare the machine and its single transition function.
- [ ] T013 [US1] CONN-ERPNEXT-AGENT-R011.2 Submit needs a Draft of a submittable doctype.
- [ ] T014 [US1] CONN-ERPNEXT-AGENT-R011.3 Cancel needs a Submitted document with no submitted links and a fresh modified stamp.
- [ ] T015 [US1] CONN-ERPNEXT-AGENT-R011.4 Amend needs a Cancelled document and has its own tool.
- [ ] T016 [US1] CONN-ERPNEXT-AGENT-R011.5 Lifecycle state is one typed field in the knowledge-graph mirror.
- [ ] T017 [US1] CONN-ERPNEXT-AGENT-R011.6 Wiring and hot-path proof: an illegal move never reaches the server.
