"""Source guard logic; real Frappe transaction qualification remains required."""

from __future__ import annotations

import copy
import importlib
import sys
import types

import pytest


class FakeDocument:
    def __init__(self, source, values):
        self.source = source
        self.__dict__.update(values)

    def check_permission(self, operation):
        if operation not in self.source.permissions:
            raise PermissionError("source permission denied")

    def insert(self, *, ignore_permissions=False):
        if self.doctype == "Sales Invoice":
            self.check_permission("create")
            if self.source.fail_invoice:
                raise RuntimeError("source failed")
            self.name = f"invoice-{len(self.source.invoices) + 1}"
            self.modified = "v1"
            self.source.invoices[self.name] = self
        else:
            if not ignore_permissions:
                raise PermissionError("claim is internal")
            self.name = self.claim_id
            if self.name in self.source.claims:
                raise ValueError("duplicate claim")
            self.source.claims[self.name] = self
        return self

    def save(self, *, ignore_permissions=False):
        if not ignore_permissions:
            raise PermissionError("claim is internal")
        self.source.claims[self.name] = self


class FakeFrappe(types.ModuleType):
    def __init__(self):
        super().__init__("frappe")
        self.session = types.SimpleNamespace(user="source-user")
        self.conf = {"scion_invoice_tenant_bindings": {"source-user": "tenant"}}
        self.permissions = {"create", "read"}
        self.claims = {}
        self.invoices = {}
        self.fail_invoice = False
        self.db = types.SimpleNamespace(get_value=self.get_value)

    def whitelist(self, **kwargs):
        assert kwargs == {"methods": ["POST"]}
        return lambda function: function

    def get_value(self, doctype, name, field, *, for_update=False):
        assert doctype == "Scion Invoice Claim" and field == "name" and for_update
        return name if name in self.claims else None

    def get_doc(self, doctype, name=None, **kwargs):
        if isinstance(doctype, dict):
            return FakeDocument(self, doctype)
        if doctype == "Scion Invoice Claim":
            return self.claims[name]
        assert doctype == "Sales Invoice"
        return self.invoices[name]

    def call(self, function, *args):
        """Model Frappe's POST commit/rollback at the boundary, not its database."""
        claims, invoices = copy.deepcopy((self.claims, self.invoices), {id(self): self})
        try:
            return function(*args)
        except Exception:
            self.claims, self.invoices = claims, invoices
            raise


@pytest.fixture
def source(monkeypatch):
    fake = FakeFrappe()
    monkeypatch.setitem(sys.modules, "frappe", fake)
    sys.modules.pop("scion_erp_guard.api", None)
    api = importlib.import_module("scion_erp_guard.api")
    yield fake, api
    sys.modules.pop("scion_erp_guard.api", None)


def invoice():
    return {
        "company": "Company",
        "customer": "Customer",
        "currency": "USD",
        "items": [{"item_code": "item", "qty": 1, "rate": 5}],
    }


def test_create_replay_and_reconcile_bind_exact_claim(source):
    fake, api = source
    reservation = fake.call(api.reserve_invoice, "tenant", "Company", "key", invoice())
    assert reservation["outcome"] == "reserved"
    first = fake.call(api.create_invoice_once, "tenant", "Company", "key", invoice())
    replay = fake.call(api.create_invoice_once, "tenant", "Company", "key", invoice())
    assert first == replay == api.reconcile_invoice("tenant", "Company", "key")
    assert len(fake.invoices) == len(fake.claims) == 1
    changed = {**invoice(), "currency": "EUR"}
    with pytest.raises(PermissionError):
        fake.call(api.create_invoice_once, "tenant", "Company", "key", changed)
    assert len(fake.invoices) == 1


def test_refused_scope_permissions_payload_and_missing_outcome(source):
    fake, api = source
    assert api.reconcile_invoice("tenant", "Company", "missing") == {
        "outcome": "unknown"
    }
    with pytest.raises(PermissionError):
        fake.call(api.reserve_invoice, "other", "Company", "key", invoice())
    with pytest.raises(ValueError):
        fake.call(api.reserve_invoice, "tenant", "Other", "key", invoice())
    with pytest.raises(ValueError):
        fake.call(
            api.create_invoice_once,
            "tenant",
            "Company",
            "key",
            {**invoice(), "flags": {"ignore_permissions": True}},
        )
    fake.permissions.remove("create")
    with pytest.raises(PermissionError):
        fake.call(api.reserve_invoice, "tenant", "Company", "key", invoice())
    assert not fake.claims and not fake.invoices


def test_transaction_failure_does_not_expose_completed_claim(source):
    fake, api = source
    fake.call(api.reserve_invoice, "tenant", "Company", "key", invoice())
    fake.fail_invoice = True
    with pytest.raises(RuntimeError):
        fake.call(api.create_invoice_once, "tenant", "Company", "key", invoice())
    assert len(fake.claims) == 1 and not fake.invoices
    assert api.reconcile_invoice("tenant", "Company", "key")["outcome"] == "reserved"


def test_duplicate_insert_collision_aborts_before_second_invoice(source, monkeypatch):
    fake, api = source
    fake.call(api.reserve_invoice, "tenant", "Company", "key", invoice())
    original = fake.call(api.create_invoice_once, "tenant", "Company", "key", invoice())
    monkeypatch.setattr(fake.db, "get_value", lambda *_args, **_kwargs: None)
    with pytest.raises(ValueError, match="duplicate claim"):
        fake.call(api.reserve_invoice, "tenant", "Company", "key", invoice())
    assert len(fake.invoices) == 1
    monkeypatch.setattr(fake.db, "get_value", fake.get_value)
    assert api.reconcile_invoice("tenant", "Company", "key") == original


def test_replay_refuses_other_source_user_and_explicitly_denied_read(source):
    fake, api = source
    fake.call(api.reserve_invoice, "tenant", "Company", "key", invoice())
    fake.call(api.create_invoice_once, "tenant", "Company", "key", invoice())
    fake.conf["scion_invoice_tenant_bindings"]["other-user"] = "tenant"
    fake.session.user = "other-user"
    with pytest.raises(PermissionError):
        api.reconcile_invoice("tenant", "Company", "key")
    fake.session.user = "source-user"
    fake.permissions.remove("read")
    with pytest.raises(PermissionError):
        api.reconcile_invoice("tenant", "Company", "key")


def test_creation_requires_a_committed_reservation(source):
    fake, api = source
    with pytest.raises(PermissionError):
        fake.call(api.create_invoice_once, "tenant", "Company", "key", invoice())
    assert not fake.claims and not fake.invoices


def test_reserved_reconciliation_is_no_effect_until_create(source):
    fake, api = source
    reservation = fake.call(api.reserve_invoice, "tenant", "Company", "key", invoice())
    assert api.reconcile_invoice("tenant", "Company", "key") == reservation
    assert not fake.invoices
