# CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT — Quickstart

The shortest path that shows the served behaviour working.

- `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R003`: run `pytest tests/test_workflow_content.py::test_workflow_skills_are_served_and_name_only_served_tools`; scenario: list the server's resources and read `skill://erpnext-business-onboarding/SKILL.md`.
- `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R004`: run `pytest tests/test_workflow_content.py::test_operator_prompt_names_served_tools_and_shipped_workflow_skills`.
- `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R008`: run `pytest tests/test_workflow_content.py::test_role_prompts_are_complete_agent_definitions`; scenario: list the server's prompts and get `hr_manager`.
- `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R005` to `R007`: run `pytest tests/test_surface_ontology.py`.
