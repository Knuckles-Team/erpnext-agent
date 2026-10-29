"""Frappe's internal transaction claim for one invoice creation."""

from frappe.model.document import Document


class ScionInvoiceClaim(Document):
    """Never exposed as a user-writable API resource."""
