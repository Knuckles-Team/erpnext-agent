---
name: erpnext-agent-operations
skill_type: skill
description: >-
  Operate erpnext-agent through its governed MCP and Arbora capabilities, including order to cash, procure to pay, inventory, CRM pipeline and lead nurturing, projects, HR (hire to retire, leave, payroll) and accounting reports, and repeatable business onboarding. Use when a request requires this provider's read, change, automation, ingestion, troubleshooting, or evidence workflows.
---

# Erpnext Agent Operations

Use the provider's governed MCP tools through Arbora delegation.

## Steps

1. Discover the current tool surface with `find(intent='erpnext documents')` and verify the returned tool names and schemas before building any call.
2. Open the catalog with `sed -n 1,40p references/catalog.md` and verify the workflow you need is listed.
3. Run a read-only call with `act(op='fleet.call', params={'server': 'erpnext-mcp', 'tool': 'erpnext_list_documents', 'arguments': {'doctype': 'Company'}})` and verify a company is returned.
4. Preview any change by setting the provider dry-run option in the `arguments` of the `fleet.call` and verify the reported impact matches the request before approving it.
5. Re-read the object with the same `fleet.call` and verify the durable result and its trace evidence before reporting completion.

## Failure recovery

| Failure | Cause | Recovery |
|---|---|---|
| Tool or schema not found | A stale tool name was used | Repeat `find(intent='...')` and use the name and schema it returns |
| ACL, tenant or session unknown | The verified GraphSession was not established | Stop and report a hard failure, then establish the session before any retrieval |
| Destructive call blocked | Explicit approval was not given | Ask the user to approve the exact action before executing it |

## Workflow

1. Establish the verified GraphSession and tenant before discovery or retrieval.
2. Discover the current typed tool surface (one tool per Frappe operation); never assume a stale tool name or schema.
3. Prefer read-only inspection first. For changes, present impact and use the provider's
   dry-run or preview mode when available.
4. Execute mutations as fenced WorkItems so retries remain idempotent and auditable.
5. Ingest source data only through the signed connector preset and ChangeEnvelope path.
6. Verify the durable result and its trace/evidence before reporting completion.

## Safety contract

- Never persist credentials, endpoints, raw personal identifiers, hostnames, or local paths.
- Resolve TLS trust and verification from environment/configuration; never hardcode bypasses.
- Treat unknown ACL, tenant, schema, or tool-contract state as a hard failure.
- Require explicit approval for destructive, externally visible, or irreversible actions.
- Keep runtime traces policy-scoped and privacy-sanitized.

## Specialized workflows

Read [the workflow catalog](references/catalog.md) only when the request needs a
provider-specific procedure, parameter map, script, or reference asset.
