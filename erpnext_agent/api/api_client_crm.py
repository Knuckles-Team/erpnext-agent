"""Typed CRM operations on ERPNext's built-in CRM (Lead, Opportunity, Customer).

Each public method is one Frappe operation and is served as its own typed
tool. Communications and follow-ups are recorded, never sent: no email leaves
the system from these tools.
"""

from typing import Any

from erpnext_agent.api._docs import compact as _merge
from erpnext_agent.api._docs import message_of
from erpnext_agent.api.api_client_resource import Api as ResourceApi
from erpnext_agent.api.api_client_resource import _doc_path

_LEAD = "erpnext.crm.doctype.lead.lead"
_OPPORTUNITY = "erpnext.crm.doctype.opportunity.opportunity"


class ApiCrm(ResourceApi):
    # --- leads -----------------------------------------------------------

    def create_lead(
        self,
        first_name: str,
        company: str,
        last_name: str | None = None,
        company_name: str | None = None,
        email_id: str | None = None,
        mobile_no: str | None = None,
        source: str | None = None,
        territory: str | None = None,
        lead_owner: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict:
        """Capture a Lead (a prospect not yet qualified) for our company.

        POST /api/resource/Lead

        ``company_name`` is the prospect's organisation; ``company`` is ours.
        """
        doc = _merge(
            {
                "first_name": first_name,
                "last_name": last_name,
                "company_name": company_name,
                "email_id": email_id,
                "mobile_no": mobile_no,
                "source": source,
                "territory": territory,
                "lead_owner": lead_owner,
                "company": company,
                "status": "Lead",
            },
            extra,
        )
        return self.request("POST", _doc_path("Lead"), data=doc)

    def update_lead(self, name: str, data: dict[str, Any]) -> dict:
        """Change fields of a Lead (status, contact details, notes, ...).

        PUT /api/resource/Lead/<name>
        """
        return self.request("PUT", _doc_path("Lead", name), data=data)

    def qualify_lead(
        self,
        name: str,
        qualification_status: str = "Qualified",
        qualified_by: str | None = None,
        qualified_on: str | None = None,
    ) -> dict:
        """Set a Lead's qualification: Unqualified, In Process or Qualified.

        PUT /api/resource/Lead/<name>
        """
        data = _merge(
            {
                "qualification_status": qualification_status,
                "qualified_by": qualified_by,
                "qualified_on": qualified_on,
            },
            None,
        )
        return self.request("PUT", _doc_path("Lead", name), data=data)

    def list_leads(
        self,
        status: str | None = None,
        qualification_status: str | None = None,
        company: str | None = None,
        limit: int = 50,
    ) -> list:
        """List leads by status, qualification and company.

        GET /api/resource/Lead
        """
        filters = _merge(
            {
                "status": status,
                "qualification_status": qualification_status,
                "company": company,
            },
            None,
        )
        return self.list_documents(
            "Lead",
            filters=filters or None,
            fields=[
                "name",
                "lead_name",
                "company_name",
                "status",
                "qualification_status",
                "source",
                "email_id",
            ],
            limit=limit,
        )

    # --- opportunities ---------------------------------------------------

    def create_opportunity_from_lead(
        self,
        lead: str,
        company: str,
        currency: str | None = None,
        opportunity_amount: float | None = None,
        expected_closing: str | None = None,
        sales_stage: str | None = None,
        opportunity_type: str | None = None,
        probability: float | None = None,
    ) -> dict:
        """Raise an Opportunity from a Lead and save it.

        POST /api/method/frappe.model.mapper.make_mapped_doc
        (erpnext.crm.doctype.lead.lead.make_opportunity), then
        POST /api/resource/Opportunity

        Set ``currency`` to the company currency so the follow-on quotation
        needs no exchange rate.
        """
        mapped = self.make_mapped_document(f"{_LEAD}.make_opportunity", lead)
        draft = message_of(mapped)
        draft.update(
            _merge(
                {
                    "company": company,
                    "currency": currency,
                    "opportunity_amount": opportunity_amount,
                    "expected_closing": expected_closing,
                    "sales_stage": sales_stage,
                    "opportunity_type": opportunity_type,
                    "probability": probability,
                },
                None,
            )
        )
        return self.request("POST", _doc_path("Opportunity"), data=draft)

    def update_opportunity_stage(
        self,
        name: str,
        sales_stage: str,
        probability: float | None = None,
        expected_closing: str | None = None,
    ) -> dict:
        """Move an Opportunity to a Sales Stage, with its win probability.

        PUT /api/resource/Opportunity/<name>
        """
        data = _merge(
            {
                "sales_stage": sales_stage,
                "probability": probability,
                "expected_closing": expected_closing,
            },
            None,
        )
        return self.request("PUT", _doc_path("Opportunity", name), data=data)

    def declare_opportunity_lost(
        self,
        name: str,
        lost_reasons: list[str],
        detailed_reason: str | None = None,
        competitors: list[str] | None = None,
    ) -> dict:
        """Mark an Opportunity Lost with its reasons (each an Opportunity Lost Reason).

        POST /api/method/run_doc_method (Opportunity.declare_enquiry_lost)
        """
        return self.run_document_method(
            "Opportunity",
            name,
            "declare_enquiry_lost",
            {
                "lost_reasons_list": [{"lost_reason": r} for r in lost_reasons],
                "competitors": [{"competitor": c} for c in competitors or []],
                "detailed_reason": detailed_reason,
            },
        )

    def create_opportunity_lost_reason(self, lost_reason: str) -> dict:
        """Create an Opportunity Lost Reason (price, timing, competitor, ...).

        POST /api/resource/Opportunity Lost Reason
        """
        return self.request(
            "POST",
            _doc_path("Opportunity Lost Reason"),
            data={"lost_reason": lost_reason},
        )

    def list_opportunities(
        self,
        status: str | None = None,
        sales_stage: str | None = None,
        company: str | None = None,
        limit: int = 50,
    ) -> list:
        """List opportunities by status, sales stage and company.

        GET /api/resource/Opportunity
        """
        filters = _merge(
            {"status": status, "sales_stage": sales_stage, "company": company}, None
        )
        return self.list_documents(
            "Opportunity",
            filters=filters or None,
            fields=[
                "name",
                "opportunity_from",
                "party_name",
                "status",
                "sales_stage",
                "probability",
                "opportunity_amount",
                "expected_closing",
            ],
            limit=limit,
        )

    # --- customers -------------------------------------------------------

    def make_customer_from_lead(
        self,
        lead: str,
        customer_group: str | None = None,
        territory: str | None = None,
        tax_id: str | None = None,
    ) -> dict:
        """Convert a Lead into a Customer and save it.

        POST make_mapped_doc (erpnext.crm.doctype.lead.lead.make_customer),
        then POST /api/resource/Customer
        """
        return self._save_mapped_customer(
            f"{_LEAD}.make_customer", lead, customer_group, territory, tax_id
        )

    def make_customer_from_opportunity(
        self,
        opportunity: str,
        customer_group: str | None = None,
        territory: str | None = None,
        tax_id: str | None = None,
    ) -> dict:
        """Create the Customer of a won Opportunity and save it.

        POST make_mapped_doc (erpnext.crm.doctype.opportunity.opportunity.make_customer),
        then POST /api/resource/Customer
        """
        return self._save_mapped_customer(
            f"{_OPPORTUNITY}.make_customer",
            opportunity,
            customer_group,
            territory,
            tax_id,
        )

    def _save_mapped_customer(
        self,
        method: str,
        source: str,
        customer_group: str | None,
        territory: str | None,
        tax_id: str | None,
    ) -> dict:
        mapped = self.make_mapped_document(method, source)
        draft = message_of(mapped)
        draft.update(
            _merge(
                {
                    "customer_group": customer_group,
                    "territory": territory,
                    "tax_id": tax_id,
                },
                None,
            )
        )
        return self.request("POST", _doc_path("Customer"), data=draft)

    # --- pipeline setup --------------------------------------------------

    def create_sales_stage(self, stage_name: str) -> dict:
        """Create a Sales Stage of the pipeline (Prospecting, Proposal, ...).

        POST /api/resource/Sales Stage
        """
        return self.request(
            "POST", _doc_path("Sales Stage"), data={"stage_name": stage_name}
        )

    def list_sales_stages(self, limit: int = 100) -> list:
        """List the pipeline's Sales Stages.

        GET /api/resource/Sales Stage
        """
        return self.list_documents("Sales Stage", fields=["name"], limit=limit)

    def create_opportunity_type(
        self, name: str, description: str | None = None
    ) -> dict:
        """Create an Opportunity Type (Sales, Support, Maintenance, ...).

        POST /api/resource/Opportunity Type
        """
        return self.request(
            "POST",
            _doc_path("Opportunity Type"),
            data=_merge({"__newname": name, "description": description}, None),
        )

    def list_opportunity_types(self, limit: int = 100) -> list:
        """List Opportunity Types.

        GET /api/resource/Opportunity Type
        """
        return self.list_documents(
            "Opportunity Type", fields=["name", "description"], limit=limit
        )

    # --- communication and follow-up ---------------------------------------

    def log_communication(
        self,
        reference_doctype: str,
        reference_name: str,
        subject: str,
        content: str,
        communication_medium: str = "Phone",
        sent_or_received: str = "Sent",
        sender: str | None = None,
        phone_no: str | None = None,
    ) -> dict:
        """Record a call, meeting or message against a Lead, Opportunity or Customer.

        POST /api/resource/Communication

        The record is a log entry only: nothing is sent to anyone.
        ``communication_medium`` is Phone, Chat, Email, Meeting, SMS, Visit or Other.
        """
        doc = _merge(
            {
                "communication_type": "Communication",
                "communication_medium": communication_medium,
                "sent_or_received": sent_or_received,
                "subject": subject,
                "content": content,
                "reference_doctype": reference_doctype,
                "reference_name": reference_name,
                "sender": sender,
                "phone_no": phone_no,
                "status": "Linked",
            },
            None,
        )
        return self.request("POST", _doc_path("Communication"), data=doc)

    def create_follow_up(
        self,
        reference_doctype: str,
        reference_name: str,
        description: str,
        allocated_to: str,
        date: str | None = None,
        priority: str = "Medium",
    ) -> dict:
        """Schedule a follow-up ToDo on a Lead, Opportunity or Customer for a user.

        POST /api/resource/ToDo
        """
        doc = _merge(
            {
                "reference_type": reference_doctype,
                "reference_name": reference_name,
                "description": description,
                "allocated_to": allocated_to,
                "date": date,
                "priority": priority,
                "status": "Open",
            },
            None,
        )
        return self.request("POST", _doc_path("ToDo"), data=doc)

    def list_follow_ups(
        self,
        reference_doctype: str | None = None,
        reference_name: str | None = None,
        allocated_to: str | None = None,
        status: str | None = "Open",
        limit: int = 50,
    ) -> list:
        """List follow-up ToDos by referenced record, assignee and status.

        GET /api/resource/ToDo
        """
        filters = _merge(
            {
                "reference_type": reference_doctype,
                "reference_name": reference_name,
                "allocated_to": allocated_to,
                "status": status,
            },
            None,
        )
        return self.list_documents(
            "ToDo",
            filters=filters or None,
            fields=[
                "name",
                "reference_type",
                "reference_name",
                "description",
                "allocated_to",
                "date",
                "priority",
                "status",
            ],
            limit=limit,
        )

    def close_follow_up(self, name: str) -> dict:
        """Close a follow-up ToDo once it is done.

        PUT /api/resource/ToDo/<name>
        """
        return self.request("PUT", _doc_path("ToDo", name), data={"status": "Closed"})
