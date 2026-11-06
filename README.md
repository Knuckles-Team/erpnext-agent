# Erpnext MCP

[![Status](https://img.shields.io/badge/status-active-success)](https://github.com/genius-agents/erpnext-agent)
[![Version](https://img.shields.io/badge/version-0.15.0-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

ERPNext and Frappe Framework enterprise resources planner. Built with the highest architectural standards, incorporating dynamic facades, custom API routing, and FastMCP tool decoration.

> **Documentation** — Installation, deployment, usage across the MCP, API, and CLI
> interfaces, and guidance for provisioning the ERPNext / Frappe platform are
> maintained in the [official documentation](https://knuckles-team.github.io/erpnext-agent/).

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [MCP Tools](#mcp-tools)
- [Architecture](#architecture)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Erpnext MCP provides a high-performance, model-optimized interface to Erpnext capabilities. It isolates the model from underlying API transport complexity, ensuring safe, idempotent, and highly traceable system interactions.

---

## Features

- **Dynamic Facade Orchestration**: Integrates multi-inheritance clients cleanly under a single facade.
- **Battle-Tested Resilience**: Out-of-the-box credential authentication, connection polling, and request retry strategies.
- **FastMCP Declarative Tools**: Fast, native schema registration with full inline validation.
- **Complete Test Intent Diversity**: Deep, automated unit, integration, and mock tests ensuring high code coverage.

---

## ⚙️ Dynamic Tool Selection & Visibility

This MCP server supports dynamic toolset selection and visibility filtering at runtime. This allows the operator to restrict the set of exposed tools to prevent blowing up the LLM's context window.

The operator can configure tool filtering via multiple input channels:

- **CLI Arguments:** Pass `--tools` or `--toolsets` (or their disabled counterparts `--disabled-tools` and `--disabled-toolsets`) during startup.
- **Environment Variables:** Define standard environment variables:
  - `MCP_ENABLED_TOOLS` / `MCP_DISABLED_TOOLS`
  - `MCP_ENABLED_TAGS` / `MCP_DISABLED_TAGS`
- **HTTP SSE Request Headers:** Pass custom headers during transport initialization:
  - `x-mcp-enabled-tools` / `x-mcp-disabled-tools`
  - `x-mcp-enabled-tags` / `x-mcp-disabled-tags`
- **HTTP SSE Request Query Parameters:** Append query parameters directly to the operator's transport connection URL:
  - `?tools=tool1,tool2`
  - `?tags=tag1`

When query strings or parameters are provided, an LLM-free **Knowledge Graph resolution layer** (using `DynamicToolOrchestrator`) matches query intents against known tool tags, names, or descriptions, with safe fallback and automated 24-hour background cache refreshing.

---

## Installation

Pick the extra that matches what the operator want to run:

| Extra | Installs | Use when |
|-------|----------|----------|
| `erpnext-agent[mcp]` | Connector-focused MCP server (`scion-sdk` — FastMCP/FastAPI + `medulla`) | The operator only run the **MCP server** (smallest install / image) |
| `erpnext-agent[all]` | Everything (`mcp` + `agent` + `logfire`) | Development / both surfaces |

```bash
# Connector-focused MCP server (includes the shared graph engine)
uv pip install "erpnext-agent[mcp]"

# Agent runtime (adds model orchestration to the shared graph engine)

# Everything (development)
uv pip install "erpnext-agent[all]"      # or: python -m pip install "erpnext-agent[all]"
```

### Container images (`:mcp`)

One multi-stage `docker/Dockerfile` builds the MCP-only image (`--target mcp`):

| Image tag | Build target | Contents | Entrypoint |
|-----------|--------------|----------|------------|

```bash
```

### Knowledge-graph database (`medulla`)

Scion SDK core dependency (`medulla`). The `[mcp]` extra keeps
deployments can use the bundled engine. For production or shared state, run
**medulla as a dedicated database service** and configure the runtime to use it.
Deployment recipes (single-node + Raft HA), connection configuration, and architecture
diagrams are documented in the
[medulla deployment guide](https://knuckles-team.github.io/medulla/deployment/).

---

## Usage

The operator can start the FastMCP server in stdio mode via Python module execution:

```python
import asyncio
from erpnext_agent.mcp_server import get_mcp_instance

async def main():
    mcp = get_mcp_instance()
    # Execute stdio loop or launch server
    print("MCP Server ready.")

if __name__ == "__main__":
    asyncio.run(main())
```

For direct shell start, ran:

```bash
python -m erpnext_agent.mcp_server
```

---

## Configuration

The package is fully configurable via the environment variables listed below.

### Connection & Credentials
| Variable | Description | Default |
|----------|-------------|---------|
| `ERPNEXT_URL` | ERPNext / Frappe server endpoint URL | Required |
| `ERPNEXT_TOKEN` | API token authentication (`api_key:api_secret`) | — |
| `ERPNEXT_AGENT_USERNAME` | Username for password-based login | — |
| `ERPNEXT_AGENT_PASSWORD` | Password for password-based login | — |
| `TLS_PROFILE` | Named `AgentConfig` transport-security profile; verification is mandatory | — |
| `TLS_PROFILES_REF` | Runtime secret reference for the TLS profile catalog | — |

### MCP server / transport
| Variable | Description | Default |
|----------|-------------|---------|
| `TRANSPORT` | `stdio`, `streamable-http`, or `sse` | `stdio` |
| `HOST` | Bind host (HTTP transports) | `0.0.0.0` |
| `PORT` | Bind port (HTTP transports) | `8000` |
| `MCP_TOOL_MODE` | Tool surface: `condensed`, `verbose`, or `both` | `condensed` |

### Tool toggles
Each action-routed tool can be disabled individually via its toggle env var (set to `false`):
`AUTHENTICATIONTOOL`, `RESOURCETOOL` (see the [MCP Tools](#mcp-tools) table above).

A local template is provided inside [.env.example](.env.example). Copy this file as `.env` and fill out the operator's specific service endpoint parameters before starting execution.

---

## MCP Tools

_Auto-generated from the live MCP server — do not edit by hand._

<!-- MCP-TOOLS-TABLE:START -->

| MCP Tool | Kind | Description |
|----------|------|-------------|
| `erpnext_add_employee_checkin` | write | Log an employee check-in or check-out (``log_type`` IN or OUT). |
| `erpnext_add_holiday_list_weekly_offs` | write | Add every <weekday> between the list's dates as a weekly-off holiday. |
| `erpnext_allocate_leave` | write | Allocate leave days of a type to an employee for a period, then submit. |
| `erpnext_apply_business_onboarding` | write | Apply an approved onboarding plan: create only what is missing, then verify. |
| `erpnext_apply_leave` | write | File a Leave Application (status Open, awaiting the approver). |
| `erpnext_approve_leave_application` | write | Approve an open Leave Application: status Approved, then submit. |
| `erpnext_assign_salary_structure` | write | Assign a Salary Structure to an employee from a date with a base pay, then submit. |
| `erpnext_call_method` | write | Execute dotted path whitelisted RPC methods (covers 100% of custom functions). |
| `erpnext_cancel_document` | write | Cancel a submitted document (docstatus 1 -> 2), reversing its postings. |
| `erpnext_close_follow_up` | write | Close a follow-up ToDo once it is done. |
| `erpnext_complete_setup_wizard` | write | Complete the site's one-time setup wizard: first company, books and regional settings. |
| `erpnext_create_address` | write | Create an Address linked to a Company, Customer, Supplier or Lead. |
| `erpnext_create_bank` | write | Create a Bank master record. |
| `erpnext_create_bank_account` | write | Create a Bank Account; a company account names its GL ledger in ``account``. |
| `erpnext_create_company` | write | Create a Company with its chart of accounts from a template (an extra or test company). |
| `erpnext_create_department` | write | Create a Department of a company (named "<department> - <abbr>"). |
| `erpnext_create_designation` | write | Create a Designation (job title), shared by every company. |
| `erpnext_create_document` | write | Create a new document resource. |
| `erpnext_create_employee` | write | Hire: create an Active Employee of a company. |
| `erpnext_create_fiscal_year` | write | Create a Fiscal Year, optionally limited to some companies. |
| `erpnext_create_follow_up` | write | Schedule a follow-up ToDo on a Lead, Opportunity or Customer for a user. |
| `erpnext_create_holiday_list` | write | Create a Holiday List with dated holidays, optionally adding a weekly off. |
| `erpnext_create_lead` | write | Capture a Lead (a prospect not yet qualified) for our company. |
| `erpnext_create_leave_type` | write | Create a Leave Type (annual, sick, leave without pay, ...). |
| `erpnext_create_opportunity_from_lead` | write | Raise an Opportunity from a Lead and save it. |
| `erpnext_create_opportunity_lost_reason` | write | Create an Opportunity Lost Reason (price, timing, competitor, ...). |
| `erpnext_create_opportunity_type` | write | Create an Opportunity Type (Sales, Support, Maintenance, ...). |
| `erpnext_create_payroll_entry` | write | Create a draft Payroll Entry for a company and pay period. |
| `erpnext_create_salary_component` | write | Create a Salary Component; ``component_type`` is Earning or Deduction. |
| `erpnext_create_salary_slips` | write | Create the draft salary slips of a Payroll Entry. |
| `erpnext_create_salary_structure` | write | Create a Salary Structure from earning and deduction rows, then submit. |
| `erpnext_create_sales_stage` | write | Create a Sales Stage of the pipeline (Prospecting, Proposal, ...). |
| `erpnext_declare_opportunity_lost` | write | Mark an Opportunity Lost with its reasons (each an Opportunity Lost Reason). |
| `erpnext_delete_document` | write | Delete a specific document resource. |
| `erpnext_fill_payroll_employees` | write | Fill a draft Payroll Entry with every employee its filters select, and save. |
| `erpnext_get_count` | read | Count the documents of a DocType that match the filters. |
| `erpnext_get_doctype_meta` | read | Describe a DocType's fields: name, type, label, link target and whether required. |
| `erpnext_get_document` | read | Get a document resource by name. |
| `erpnext_get_employee` | read | Read one Employee record. |
| `erpnext_get_holiday_list` | read | Read a Holiday List with its holidays. |
| `erpnext_get_leave_balance` | read | Read an employee's remaining leave days of a type on a date. |
| `erpnext_get_logged_user` | read | Get the user that is logged in. |
| `erpnext_get_salary_slip` | read | Read one Salary Slip with its earnings and deductions. |
| `erpnext_get_setup_status` | read | Report whether the setup wizard is complete (per app) and list the companies. |
| `erpnext_get_value` | read | Read selected field values of the first document matching the filters. |
| `erpnext_get_version` | read | Get installed app versions. |
| `erpnext_ingest` | write | Natively ingest an ERPNext DocType into medulla as typed nodes. |
| `erpnext_list_attendance` | read | List attendance records by employee, company and date range. |
| `erpnext_list_chart_of_accounts_templates` | read | List the chart-of-accounts templates offered for a country (plus Standard). |
| `erpnext_list_departments` | read | List departments, optionally of one company. |
| `erpnext_list_designations` | read | List designations (job titles). |
| `erpnext_list_documents` | read | List document resources with pagination, filters, and selected fields. |
| `erpnext_list_employees` | read | List employees of a company, by status and department. |
| `erpnext_list_follow_ups` | read | List follow-up ToDos by referenced record, assignee and status. |
| `erpnext_list_leads` | read | List leads by status, qualification and company. |
| `erpnext_list_opportunities` | read | List opportunities by status, sales stage and company. |
| `erpnext_list_opportunity_types` | read | List Opportunity Types. |
| `erpnext_list_salary_slips` | read | List salary slips by payroll entry or employee. |
| `erpnext_list_sales_stages` | read | List the pipeline's Sales Stages. |
| `erpnext_list_timezones` | read | List the time zones the server accepts. |
| `erpnext_log_communication` | write | Record a call, meeting or message against a Lead, Opportunity or Customer. |
| `erpnext_login` | write | Authenticate yourself. |
| `erpnext_logout` | read | Logout from current session. |
| `erpnext_make_customer_from_lead` | write | Convert a Lead into a Customer and save it. |
| `erpnext_make_customer_from_opportunity` | write | Create the Customer of a won Opportunity and save it. |
| `erpnext_make_mapped_document` | write | Build the next document of a business flow from a source document. |
| `erpnext_mark_attendance` | write | Mark one employee's attendance for a day and submit it. |
| `erpnext_mark_bulk_attendance` | write | Mark (and submit) the same attendance status for many employees on one day. |
| `erpnext_plan_business_onboarding` | read | Dry run: validate an onboarding spec and list what exists and what would be created. |
| `erpnext_qualify_lead` | write | Set a Lead's qualification: Unqualified, In Process or Qualified. |
| `erpnext_reject_leave_application` | write | Reject an open Leave Application: status Rejected, then submit. |
| `erpnext_relieve_employee` | write | Retire or separate an employee: set the relieving date and status Left. |
| `erpnext_rename_document` | write | Rename a document, updating every link to it; optionally merge into an existing one. |
| `erpnext_run_document_method` | write | Run a whitelisted controller method of one document. |
| `erpnext_run_report` | read | Run a query or script report and return its columns and rows. |
| `erpnext_search_link` | read | Find documents of a DocType whose name or title fields match the text. |
| `erpnext_set_tax_id` | write | Set the tax ID of a Company, Customer or Supplier. |
| `erpnext_set_value` | write | Set one field of a document and save it (runs the DocType's validation). |
| `erpnext_submit_document` | write | Submit a saved draft (docstatus 0 -> 1), posting its ledger entries. |
| `erpnext_submit_salary_slips` | write | Submit every draft salary slip of a submitted Payroll Entry. |
| `erpnext_update_document` | write | Update a specific document resource. |
| `erpnext_update_employee` | write | Change fields of an Employee (department, designation, contact, ...). |
| `erpnext_update_lead` | write | Change fields of a Lead (status, contact details, notes, ...). |
| `erpnext_update_opportunity_stage` | write | Move an Opportunity to a Sales Stage, with its win probability. |
| `erpnext_upload_file` | write | Upload a file, optionally attaching it to a document. |
| `erpnext_verify_business_onboarding` | read | Check that every record of an onboarding spec exists as specified. |

_86 typed tool(s), one per Frappe operation._
<!-- MCP-TOOLS-TABLE:END -->

### MCP Configuration Examples

<!-- MCP-CONFIG-EXAMPLES:START -->

> **Install the connector-focused `[mcp]` extra.** Examples use `erpnext-agent[mcp]` to add
> FastMCP / FastAPI through `scion-sdk`; the required Scion SDK core
> still carries `medulla`. The `[agent-runtime]` extra additionally
> enables model orchestration.

#### stdio Transport (local IDEs — Cursor, Claude Desktop, VS Code)

```json
{
  "mcpServers": {
    "erpnext-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "erpnext-agent[mcp]",
        "erpnext-mcp"
      ],
      "env": {
        "AUTHENTICATIONTOOL": "True",
        "INGESTTOOL": "True",
        "RESOURCETOOL": "True"
      }
    }
  }
}
```

Runtime references require an alias-aware launcher such as Arbora. Other
launchers must omit those entries and inject the resolved values through their
own runtime secret boundary.

#### Streamable-HTTP Transport (networked / production)

```json
{
  "mcpServers": {
    "erpnext-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "erpnext-agent[mcp]",
        "erpnext-mcp",
        "--transport",
        "streamable-http",
        "--port",
        "8000"
      ],
      "env": {
        "TRANSPORT": "streamable-http",
        "HOST": "127.0.0.1",
        "PORT": "8000",
        "AUTHENTICATIONTOOL": "True",
        "INGESTTOOL": "True",
        "RESOURCETOOL": "True"
      }
    }
  }
}
```

Alternatively, connect to a pre-deployed Streamable-HTTP instance by `url`:

```json
{
  "mcpServers": {
    "erpnext-mcp": {
      "url": "http://localhost:8000/erpnext-mcp/mcp"
    }
  }
}
```

Run a reviewed container image as a least-privilege stdio child (no
listener or published port):

```bash
docker run -i --rm \
  --read-only \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --pids-limit=256 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m \
  -e TRANSPORT=stdio \
  -e AUTHENTICATIONTOOL=True \
  -e INGESTTOOL=True \
  -e RESOURCETOOL=True \
  registry.example.invalid/erpnext-agent@sha256:<digest> erpnext-mcp
```

For containerized network HTTP, supply an authenticated TLS ingress (or
direct server TLS), exact `MCP_ALLOWED_HOSTS`, and an exact trusted-proxy
CIDR policy through the operator-owned deployment profile. The generator
does not emit an unauthenticated non-loopback listener.

_Auto-generated from the code-read env surface (package vars) — do not edit._
<!-- MCP-CONFIG-EXAMPLES:END -->

<!-- BEGIN GENERATED: additional-deployment-options -->
### Additional Deployment Options

`erpnext-agent` can run as a local stdio process or container, or behind a remote
network boundary. The
[Deployment guide](https://knuckles-team.github.io/erpnext-agent/deployment/) carries
the detailed transport contract.

- **Local container** — launch a reviewed immutable image as a least-privilege
  stdio child with no listener or published port.
- **Remote URL** — connect through an operator-supplied authenticated HTTPS
  ingress. Keep its URL, outbound identity references, trust profile, and exact
  `MCP_ALLOWED_HOSTS` in `AgentConfig`.
<!-- END GENERATED: additional-deployment-options -->

## Documentation

The complete documentation is published as the
[official documentation site](https://knuckles-team.github.io/erpnext-agent/) and is
the recommended reference for installation, deployment, and day-to-day operation.

| Page | Contents |
|---|---|
| [Installation](https://knuckles-team.github.io/erpnext-agent/installation/) | pip, source, extras, prebuilt Docker image |
| [Usage](https://knuckles-team.github.io/erpnext-agent/usage/) | the MCP tools, the `Api` client, the CLI |
| [Backing Platform](https://knuckles-team.github.io/erpnext-agent/platform/) | deploy ERPNext / Frappe with Docker |
| [Overview](https://knuckles-team.github.io/erpnext-agent/overview/) | the dynamic facade and FastMCP tool layer |
| [Concepts](https://knuckles-team.github.io/erpnext-agent/concepts/) | concept registry (`CONCEPT:ERPN-*`) |

`AGENTS.md` is the canonical contributor/agent guidance.

---

## Contributing

Please audit all code changes against the repository's contribution and review requirements, and run:

```bash
pre-commit run --all-files
```

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for complete details.

<!-- BEGIN scion-sdk-deployment (generated; do not edit between markers) -->

## Deploy with `scion-sdk-deployment`

Provision this package with the consolidated **`scion-sdk-deployment`**
workflow. It selects an installed-package, editable-source, or immutable-container
path; records only runtime secret and TLS-profile references in `AgentConfig`; and
runs doctor, registration, policy, observability, and rollback gates. Ask your agent
to **"deploy `erpnext-agent` with scion-sdk-deployment"**.

| Install mode | Command |
|------|---------|
| Installed package | `uv tool install "erpnext-agent[mcp]"`, then run `erpnext-mcp` |
| Immutable container | deploy `registry.example.invalid/erpnext-agent@sha256:<digest>` through the operator-selected orchestrator |

The repository embeds no deployment profile, credential value, certificate path, or
environment-specific endpoint. Supply those at runtime through `AgentConfig` and the
configured secret provider.

<!-- END scion-sdk-deployment -->

## Environment Variables

<!-- ENV-VARS-TABLE:START -->

#### Package environment variables

| Variable | Example | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` |  |
| `PORT` | `8000` |  |
| `TRANSPORT` | `stdio` | options: stdio, streamable-http, sse |
| `ERPNEXT_URL` | — | ERPNext / Frappe server endpoint URL (required) |
| `ERPNEXT_TOKEN` | secret-injected | API token authentication (api_key:api_secret) |
| `ERPNEXT_AGENT_USERNAME` | — | Username / password login (alternative to token auth) |
| `ERPNEXT_AGENT_PASSWORD` | secret-injected |  |
| `TLS_PROFILE` | `private-pki` | TLS verification is mandatory. Select a named runtime profile from AgentConfig. |
| `TLS_PROFILES_REF` | `secret://runtime/tls-profiles` |  |
| `AUTHENTICATIONTOOL` | `True` |  |
| `RESOURCETOOL` | `True` |  |
| `ERPNEXT_AGENT_TLS_PROFILE` | — |  |
| `ERPNEXT_AGENT_TLS_PROFILE_REF` | — |  |
| `INGESTTOOL` | `True` |  |
| `ERPNEXT_AGENT_MCP_IMAGE` | — | Required for that Compose deployment; supply image@sha256:digest. |

#### Inherited scion-sdk variables (apply to every connector)

| Variable | Example | Description |
|----------|---------|-------------|
| `MCP_ENABLED_TOOLS` | — | Comma-separated tool allow-list |
| `MCP_DISABLED_TOOLS` | — | Comma-separated tool deny-list |
| `MCP_ENABLED_TAGS` | — | Comma-separated tag allow-list |
| `MCP_DISABLED_TAGS` | — | Comma-separated tag deny-list |
| `EUNOMIA_TYPE` | `none` | Authorization mode: `none` \| `embedded` \| `remote` |
| `EUNOMIA_POLICY_FILE` | `mcp_policies.json` | Embedded Eunomia policy file |
| `EUNOMIA_REMOTE_URL` | — | Remote Eunomia authorization server URL |
| `ENABLE_OTEL` | `False` | Enable OpenTelemetry export |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | — | OTLP collector endpoint |
| `MCP_CLIENT_AUTH` | — | Outbound MCP child auth: `oidc-client-credentials` \| `basic` \| `none` |
| `OIDC_CLIENT_ID` | — | OIDC client id (service-account auth) |
| `OIDC_CLIENT_SECRET_REF` | `secret://identity/oidc-client-secret` | Runtime secret reference for the OIDC service account |
| `MCP_BASIC_AUTH_USERNAME` | — | HTTP Basic username (`MCP_CLIENT_AUTH=basic`) |
| `MCP_BASIC_AUTH_PASSWORD_REF` | `secret://identity/mcp-basic-password` | Runtime secret reference for HTTP Basic auth (`MCP_CLIENT_AUTH=basic`) |
| `DEBUG` | `False` | Verbose logging |
| `PYTHONUNBUFFERED` | `1` | Unbuffered stdout (recommended in containers) |
| `MCP_URL` | `http://localhost:8000/mcp` | URL of the MCP server the agent connects to |
| `PROVIDER` | — | Operator-configured LLM provider for the agent |
| `MODEL_ID` | — | Operator-configured model id for the agent |

_15 package + 20 inherited variable(s). Auto-generated from `.env.example` + the shared scion-sdk set — do not edit._
<!-- ENV-VARS-TABLE:END -->

<!-- GOVERNED-CAPABILITY:START -->
## Governed capability contract

This package ships a compact canonical skill surface with specialist procedures
kept as referenced workflows. The current MCP tools, skill metadata,
`connector_manifest.yml`, ontology, mappings, shapes, fixtures, migrations,
tool-schema fingerprints, and certification metadata form one versioned
capability contract. Validate them together; do not rely on stale tool names or
historical per-task skill wrappers.

Runtime endpoints, credentials, certificate trust, tenant identity, retention,
and observability policy are deployment inputs and are never packaged values.
See [Configuration, trust, and privacy](docs/configuration.md) before enabling a
network transport, connector ingestion, Arbora delegation, or trace export.
<!-- GOVERNED-CAPABILITY:END -->
