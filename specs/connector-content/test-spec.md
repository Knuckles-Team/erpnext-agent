# CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT — Test specification

Governing spec: [spec.md](spec.md).

| Test ID | Requirement | Proving test | Expected observation |
|---|---|---|---|
| T-001 | `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R001` | `tests/test_default_content_surfaces.py` | The listings include the packaged skills, ontology and prompts. |
| T-002 | `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R002` | connector ontology certification | The connector manifest gate passes; none of the four is `UNRESOLVED`. |
| T-003 | `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R003` | `tests/test_workflow_content.py::test_workflow_skills_are_served_and_name_only_served_tools` | Each workflow skill is a served `skill://` resource and names only served tools. |
| T-004 | `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R004` | `tests/test_workflow_content.py::test_operator_prompt_names_served_tools_and_shipped_workflow_skills` | The prompt's tools are served and its skills are the workflow set. |
| T-005 | `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R005` | `tests/test_surface_ontology.py::test_every_class_rolls_up_to_core_by_subclassing_never_import` | No orphan class; no `owl:imports`. |
| T-006 | `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R006` | `tests/test_surface_ontology.py::test_surface_lists_exactly_the_served_tools_skills_and_prompts` | Surface tools equal served tools; every feature is realised; every tool operates on a class. |
| T-007 | `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R007` | `tests/test_surface_ontology.py::test_every_domain_class_has_a_live_virtual_authority` | Every record class has one virtual authority with one mapping. |
| T-008 | `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R008` | `tests/test_workflow_content.py::test_role_prompts_are_complete_agent_definitions` | Every role prompt names its role, goal, skills, tools, data, guardrails and outputs; its skills ship and its tools are served. |
| T-009 | `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R009.1` | `tests/test_lifecycle_ontology.py::test_lifecycle_classes_extend_core_state_machine_classes` | Machine, state and transition classes each name a core parent; no `owl:imports`. |
| T-010 | `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R009.2` | `tests/test_lifecycle_ontology.py::test_ontology_states_and_transitions_equal_the_code_machine` | The ontology state and transition sets equal the code enum and table. |
| T-011 | `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R009.3` | `tests/test_workflow_content.py::test_lifecycle_guidance_names_amend_and_every_refusal_reason` | The surface, three skills and the prompt name the amend tool and the seven reasons; every tool is served. |
