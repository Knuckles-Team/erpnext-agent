"""The Frappe document lifecycle as one explicit state machine.

Frappe persists the lifecycle as the integer ``docstatus`` (0, 1, 2) on the
server. This module maps that integer once, at the edge, to
:class:`DocumentState` and owns the only table of legal moves. ``transition``
is the single function that decides legality; it performs no I/O, so a refusal
always happens before any write request leaves the client.

Submit and cancel post to and reverse the ledger, so they are irreversible
enough that the refusal must act before the call, not after a server error.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

MACHINE = "DocumentLifecycle"


class DocumentState(StrEnum):
    Draft = "Draft"
    Submitted = "Submitted"
    Cancelled = "Cancelled"


class DocumentEvent(StrEnum):
    Save = "Save"
    Submit = "Submit"
    Cancel = "Cancel"
    Amend = "Amend"


class RefusalReason(StrEnum):
    NotDraft = "NotDraft"
    NotSubmittable = "NotSubmittable"
    NotSubmitted = "NotSubmitted"
    HasSubmittedLinks = "HasSubmittedLinks"
    StaleDocument = "StaleDocument"
    NotCancelled = "NotCancelled"
    # The server returned a docstatus outside 0, 1, 2 (not one of the six
    # row codes; see the report in the delivery notes).
    UnknownDocstatus = "UnknownDocstatus"


class IllegalTransition(Exception):
    """A move the machine does not allow; raised before any API call."""

    machine = MACHINE

    def __init__(
        self,
        state: DocumentState | None,
        event: DocumentEvent,
        reason: RefusalReason,
        doctype: str | None = None,
        name: str | None = None,
        detail: str = "",
    ):
        self.state = state
        self.event = event
        self.reason = reason
        self.doctype = doctype
        self.name = name
        self.detail = detail
        self.code = "STATE_TRANSITION_REFUSED"
        who = f"{doctype} {name}".strip() if doctype or name else "document"
        super().__init__(
            f"{self.code}: {MACHINE} refuses {event.value} of {who} in state "
            f"{state.value if state else 'unknown'} ({reason.value})"
            + (f": {detail}" if detail else "")
        )


# The closed table of legal moves. No second table exists.
TRANSITIONS: dict[tuple[DocumentState, DocumentEvent], DocumentState] = {
    (DocumentState.Draft, DocumentEvent.Save): DocumentState.Draft,
    (DocumentState.Draft, DocumentEvent.Submit): DocumentState.Submitted,
    (DocumentState.Submitted, DocumentEvent.Cancel): DocumentState.Cancelled,
    (DocumentState.Cancelled, DocumentEvent.Amend): DocumentState.Draft,
}

# Refusal reason when the (state, event) pair is not in the table.
_WRONG_STATE: dict[DocumentEvent, RefusalReason] = {
    DocumentEvent.Save: RefusalReason.NotDraft,
    DocumentEvent.Submit: RefusalReason.NotDraft,
    DocumentEvent.Cancel: RefusalReason.NotSubmitted,
    DocumentEvent.Amend: RefusalReason.NotCancelled,
}

_BY_DOCSTATUS = {
    0: DocumentState.Draft,
    1: DocumentState.Submitted,
    2: DocumentState.Cancelled,
}


@dataclass(frozen=True)
class Guards:
    """Facts read from the server that the guards of a move depend on."""

    doctype: str | None = None
    name: str | None = None
    is_submittable: bool = True
    submitted_links: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    expected_modified: str | None = None
    server_modified: str | None = None


def state_of(doc: Mapping[str, Any] | int | None) -> DocumentState:
    """Map the integer ``docstatus`` (0, 1, 2) to a state, once, at the edge."""
    raw = doc.get("docstatus", 0) if isinstance(doc, Mapping) else doc
    try:
        value = int(raw) if raw is not None else 0
    except (TypeError, ValueError):
        value = -1
    if isinstance(raw, bool) or value not in _BY_DOCSTATUS:
        name = doc.get("name") if isinstance(doc, Mapping) else None
        doctype = doc.get("doctype") if isinstance(doc, Mapping) else None
        raise IllegalTransition(
            None,
            DocumentEvent.Save,
            RefusalReason.UnknownDocstatus,
            doctype,
            name,
            f"docstatus {raw!r} is not 0, 1 or 2",
        )
    return _BY_DOCSTATUS[value]


def transition(
    state: DocumentState, event: DocumentEvent, guards: Guards | None = None
) -> DocumentState:
    """Return the next state or raise :class:`IllegalTransition`.

    The single place that decides whether a move is legal.
    """
    g = guards or Guards()

    def refuse(reason: RefusalReason, detail: str = "") -> IllegalTransition:
        return IllegalTransition(state, event, reason, g.doctype, g.name, detail)

    target = TRANSITIONS.get((state, event))
    if target is None:
        raise refuse(_WRONG_STATE[event])
    if event is DocumentEvent.Submit and not g.is_submittable:
        raise refuse(
            RefusalReason.NotSubmittable, f"{g.doctype} is not a submittable doctype"
        )
    if event is DocumentEvent.Cancel:
        if (
            g.expected_modified is not None
            and g.server_modified is not None
            and str(g.expected_modified) != str(g.server_modified)
        ):
            raise refuse(
                RefusalReason.StaleDocument,
                f"modified {g.expected_modified} differs from server {g.server_modified}",
            )
        if g.submitted_links:
            listed = ", ".join(
                f"{d.get('doctype')} {d.get('name')}" for d in g.submitted_links
            )
            raise refuse(
                RefusalReason.HasSubmittedLinks, f"submitted linked documents: {listed}"
            )
    return target
