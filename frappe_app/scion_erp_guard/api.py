"""Atomic ERPNext invoice creation with durable idempotency claims.

Install this optional Frappe app on the ERPNext site before using these RPCs.
The connector still owns host authorization and governed effect receipts.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe

from scion_erp_guard.bindings import _identity, _request


def _user() -> str:
    user = _identity(frappe.session.user)
    if user == "Guest":
        raise PermissionError("authenticated source user required")
    return user


def _tenant_scope(user: str, tenant: str) -> None:
    """Require the site operator's exact source-user to tenant binding."""
    bindings = frappe.conf.get("scion_invoice_tenant_bindings")
    if not isinstance(bindings, dict) or bindings.get(user) != tenant:
        raise PermissionError("source user has no tenant binding")


def _claim_for_update(claim_id: str) -> Any | None:
    """Lock an existing claim until this POST transaction finishes."""
    name = frappe.db.get_value("Scion Invoice Claim", claim_id, "name", for_update=True)
    if not name:
        return None
    return frappe.get_doc("Scion Invoice Claim", claim_id, for_update=True)


def _receipt(
    claim: Any, user: str, company: str, digest: str | None = None
) -> dict[str, str]:
    if (
        claim.source_user != user
        or claim.company != company
        or (digest is not None and claim.request_digest != digest)
    ):
        raise PermissionError("invoice claim does not match")
    if claim.status == "reserved":
        return {
            "outcome": "reserved",
            "claim_id": claim.claim_id,
            "request_digest": claim.request_digest,
        }
    if claim.status != "applied" or not claim.invoice or not claim.invoice_version:
        raise RuntimeError("invoice outcome unavailable")
    document = frappe.get_doc("Sales Invoice", claim.invoice)
    document.check_permission("read")
    return {
        "outcome": "applied",
        "claim_id": claim.claim_id,
        "invoice": claim.invoice,
        "version": claim.invoice_version,
        "request_digest": claim.request_digest,
    }


@frappe.whitelist(methods=["POST"])
def reserve_invoice(
    tenant: str, company: str, idempotency_key: str, invoice: Any
) -> dict[str, str]:
    """Commit one no-effect reservation before any invoice creation."""
    user = _user()
    _tenant_scope(user, _identity(tenant))
    claim_id, company_id, digest, payload = _request(
        tenant, company, idempotency_key, invoice
    )
    document = frappe.get_doc({"doctype": "Sales Invoice", **payload})
    document.check_permission("create")
    claim = _claim_for_update(claim_id)
    if claim is None:
        claim = frappe.get_doc(
            {
                "doctype": "Scion Invoice Claim",
                "claim_id": claim_id,
                "request_digest": digest,
                "company": company_id,
                "source_user": user,
                "status": "reserved",
            }
        )
        claim.insert(ignore_permissions=True)
    return _receipt(claim, user, company_id, digest)


@frappe.whitelist(methods=["POST"])
def create_invoice_once(
    tenant: str, company: str, idempotency_key: str, invoice: Any
) -> dict[str, str]:
    """Lock an exact reservation and create the invoice in the same transaction."""
    user = _user()
    _tenant_scope(user, _identity(tenant))
    claim_id, company_id, digest, payload = _request(
        tenant, company, idempotency_key, invoice
    )
    claim = _claim_for_update(claim_id)
    if claim is None:
        raise PermissionError("invoice reservation required")
    receipt = _receipt(claim, user, company_id, digest)
    if receipt["outcome"] == "applied":
        return receipt
    document = frappe.get_doc({"doctype": "Sales Invoice", **payload})
    document.check_permission("create")
    document.insert()
    if document.company != company_id:
        raise RuntimeError("invoice company changed during creation")
    claim.invoice = _identity(document.name)
    if document.modified is None:
        raise RuntimeError("invoice version unavailable")
    claim.invoice_version = _identity(str(document.modified))
    claim.status = "applied"
    claim.save(ignore_permissions=True)
    return _receipt(claim, user, company_id, digest)


@frappe.whitelist(methods=["POST"])
def reconcile_invoice(
    tenant: str, company: str, idempotency_key: str
) -> dict[str, str]:
    """Lock the source claim and return applied, reserved or unknown."""
    user = _user()
    _tenant_scope(user, _identity(tenant))
    tenant_id, company_id, effect_key = (
        _identity(item) for item in (tenant, company, idempotency_key)
    )
    claim_id = hashlib.sha256(
        json.dumps([tenant_id, company_id, effect_key], separators=(",", ":")).encode()
    ).hexdigest()
    claim = _claim_for_update(claim_id)
    if claim is None:
        return {"outcome": "unknown"}
    return _receipt(claim, user, company_id)
