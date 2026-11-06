"""Typed HR operations: each maps to its documented Frappe REST call."""

import json
from unittest.mock import patch

import pytest

from erpnext_agent.api_client import Api

SUBMIT = ("POST", "/api/method/frappe.client.submit")


def _client() -> Api:
    return Api(base_url="http://localhost")


def _calls(req) -> list[tuple]:
    return [c.args for c in req.call_args_list]


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R008")
def test_employee_master_hire_update_list_and_relieve():
    client = _client()
    with patch.object(client, "request", return_value={"data": []}) as req:
        client.create_employee(
            "Ada", "Female", "1990-01-01", "2026-01-05", "C", department="Ops - C"
        )
        args, kwargs = req.call_args
        assert args == ("POST", "/api/resource/Employee")
        assert kwargs["data"] == {
            "first_name": "Ada",
            "gender": "Female",
            "date_of_birth": "1990-01-01",
            "date_of_joining": "2026-01-05",
            "company": "C",
            "status": "Active",
            "department": "Ops - C",
        }
        client.update_employee("HR-EMP-1", {"designation": "Engineer"})
        req.assert_called_with(
            "PUT",
            "/api/resource/Employee/HR-EMP-1",
            data={"designation": "Engineer"},
        )
        client.get_employee("HR-EMP-1")
        req.assert_called_with("GET", "/api/resource/Employee/HR-EMP-1")
        client.list_employees(company="C")
        args, kwargs = req.call_args
        assert args == ("GET", "/api/resource/Employee")
        assert json.loads(kwargs["params"]["filters"]) == {
            "company": "C",
            "status": "Active",
        }
        client.relieve_employee("HR-EMP-1", "2026-06-30", "Moved on")
        req.assert_called_with(
            "PUT",
            "/api/resource/Employee/HR-EMP-1",
            data={
                "relieving_date": "2026-06-30",
                "status": "Left",
                "reason_for_leaving": "Moved on",
            },
        )


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R008")
def test_department_designation_and_holiday_list():
    client = _client()
    with patch.object(client, "request", return_value={"data": []}) as req:
        client.create_department("Ops", "C")
        req.assert_called_with(
            "POST",
            "/api/resource/Department",
            data={"department_name": "Ops", "company": "C", "is_group": 0},
        )
        client.list_departments("C")
        assert req.call_args.args == ("GET", "/api/resource/Department")
        client.create_designation("Engineer")
        req.assert_called_with(
            "POST",
            "/api/resource/Designation",
            data={"designation_name": "Engineer"},
        )
        client.list_designations()
        assert req.call_args.args == ("GET", "/api/resource/Designation")
        client.get_holiday_list("H")
        req.assert_called_with("GET", "/api/resource/Holiday%20List/H")
    holiday = {"name": "H", "from_date": "2026-01-01", "to_date": "2026-01-31"}
    with patch.object(
        client,
        "request",
        side_effect=[
            {"data": holiday},
            {"data": holiday},
            {"docs": [{**holiday, "holidays": [{"holiday_date": "2026-01-04"}]}]},
            {"data": holiday},
        ],
    ) as req:
        client.create_holiday_list("H", "2026-01-01", "2026-01-31", weekly_off="Sunday")
    calls = _calls(req)
    assert calls[0] == ("POST", "/api/resource/Holiday%20List")
    assert calls[2] == ("POST", "/api/method/run_doc_method")
    run = req.call_args_list[2].kwargs["data"]
    assert run["method"] == "get_weekly_off_dates"
    assert run["docs"]["weekly_off"] == "Sunday"
    assert req.call_args_list[3].kwargs["data"] == {
        "weekly_off": "Sunday",
        "holidays": [{"holiday_date": "2026-01-04"}],
    }


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R008")
def test_attendance_mark_bulk_and_list():
    client = _client()
    draft = {"name": "HR-ATT-1", "docstatus": 0}
    with patch.object(
        client, "request", side_effect=[{"data": draft}, {"message": {}}]
    ) as req:
        client.mark_attendance("E1", "2026-01-05", "Present", company="C")
    assert _calls(req) == [("POST", "/api/resource/Attendance"), SUBMIT]
    assert req.call_args_list[1].kwargs == {"data": {"doc": draft}}
    with patch.object(client, "request") as req:
        client.mark_bulk_attendance(["E1", "E2"], "2026-01-06", "Absent")
        args, kwargs = req.call_args
        assert args == (
            "POST",
            "/api/method/hrms.hr.doctype.employee_attendance_tool"
            ".employee_attendance_tool.mark_employee_attendance",
        )
        assert kwargs["data"] == {
            "employee_list": '["E1", "E2"]',
            "date": "2026-01-06",
            "status": "Absent",
        }
        client.list_attendance("E1", "2026-01-01", "2026-01-31")
        assert json.loads(req.call_args.kwargs["params"]["filters"]) == [
            ["employee", "=", "E1"],
            ["attendance_date", ">=", "2026-01-01"],
            ["attendance_date", "<=", "2026-01-31"],
        ]


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R008")
def test_leave_type_allocation_application_and_decision():
    client = _client()
    with patch.object(client, "request") as req:
        client.create_leave_type("zz Annual", max_leaves_allowed=20)
        req.assert_called_with(
            "POST",
            "/api/resource/Leave%20Type",
            data={
                "leave_type_name": "zz Annual",
                "max_leaves_allowed": 20,
                "is_lwp": 0,
                "include_holiday": 0,
                "is_carry_forward": 0,
            },
        )
        client.apply_leave("E1", "zz Annual", "2026-02-02", "2026-02-03")
        args, kwargs = req.call_args
        assert args == ("POST", "/api/resource/Leave%20Application")
        assert kwargs["data"]["status"] == "Open"
        client.get_leave_balance("E1", "zz Annual", "2026-02-01")
        req.assert_called_with(
            "GET",
            "/api/method/hrms.hr.doctype.leave_application.leave_application"
            ".get_leave_balance_on",
            params={"employee": "E1", "leave_type": "zz Annual", "date": "2026-02-01"},
        )
    alloc = {"name": "HR-LAL-1"}
    with patch.object(client, "request", side_effect=[{"data": alloc}, {}]) as req:
        client.allocate_leave("E1", "zz Annual", "2026-01-01", "2026-12-31", 20)
    assert _calls(req) == [("POST", "/api/resource/Leave%20Allocation"), SUBMIT]
    assert req.call_args_list[0].kwargs["data"]["new_leaves_allocated"] == 20
    for decide, status in (
        (client.approve_leave_application, "Approved"),
        (client.reject_leave_application, "Rejected"),
    ):
        saved = {"name": "HR-LAP-1", "status": status}
        with patch.object(client, "request", side_effect=[{"data": saved}, {}]) as req:
            decide("HR-LAP-1")
        assert _calls(req) == [
            ("PUT", "/api/resource/Leave%20Application/HR-LAP-1"),
            SUBMIT,
        ]
        assert req.call_args_list[0].kwargs == {"data": {"status": status}}
        assert req.call_args_list[1].kwargs == {"data": {"doc": saved}}


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R008")
def test_salary_component_structure_and_assignment():
    client = _client()
    with patch.object(client, "request") as req:
        client.create_salary_component("zz Basic", "ZB", "Earning")
        req.assert_called_with(
            "POST",
            "/api/resource/Salary%20Component",
            data={
                "salary_component": "zz Basic",
                "salary_component_abbr": "ZB",
                "type": "Earning",
                "depends_on_payment_days": 1,
            },
        )
    with patch.object(
        client, "request", side_effect=[{"data": {"name": "S"}}, {}]
    ) as req:
        client.create_salary_structure(
            "S", "C", "USD", [{"salary_component": "zz Basic", "amount": 100}]
        )
    assert _calls(req) == [("POST", "/api/resource/Salary%20Structure"), SUBMIT]
    sent = req.call_args_list[0].kwargs["data"]
    assert sent["__newname"] == "S" and sent["is_active"] == "Yes"
    with patch.object(
        client, "request", side_effect=[{"data": {"name": "A"}}, {}]
    ) as req:
        client.assign_salary_structure("E1", "S", "2026-01-01", 1000, "C", "USD")
    assert _calls(req) == [
        ("POST", "/api/resource/Salary%20Structure%20Assignment"),
        SUBMIT,
    ]
    assert req.call_args_list[0].kwargs["data"]["base"] == 1000


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R008")
def test_payroll_entry_fill_create_and_submit_slips():
    client = _client()
    with patch.object(client, "request") as req:
        client.create_payroll_entry(
            "C",
            "2026-01-31",
            "2026-01-01",
            "2026-01-31",
            "USD",
            "Payroll Payable - C",
            "Main - C",
        )
        args, kwargs = req.call_args
        assert args == ("POST", "/api/resource/Payroll%20Entry")
        assert kwargs["data"]["exchange_rate"] == 1
        assert kwargs["data"]["payroll_frequency"] == "Monthly"
    entry = {"name": "HR-PRUN-1", "docstatus": 0}
    rows = [{"employee": "E1"}, {"employee": "E2"}]
    with patch.object(
        client,
        "request",
        side_effect=[{"data": entry}, {"docs": [{**entry, "employees": rows}]}, {}],
    ) as req:
        client.fill_payroll_employees("HR-PRUN-1")
    assert _calls(req) == [
        ("GET", "/api/resource/Payroll%20Entry/HR-PRUN-1"),
        ("POST", "/api/method/run_doc_method"),
        ("PUT", "/api/resource/Payroll%20Entry/HR-PRUN-1"),
    ]
    assert req.call_args_list[1].kwargs["data"]["method"] == "fill_employee_details"
    assert req.call_args_list[2].kwargs["data"] == {
        "employees": rows,
        "number_of_employees": 2,
    }
    with patch.object(client, "request", side_effect=[{"data": entry}, {}]) as req:
        client.create_salary_slips("HR-PRUN-1")
    assert _calls(req)[1] == SUBMIT
    submitted = {**entry, "docstatus": 1}
    with patch.object(client, "request", side_effect=[{"data": submitted}, {}]) as req:
        client.create_salary_slips("HR-PRUN-1")
    assert _calls(req)[1] == ("POST", "/api/method/run_doc_method")
    assert req.call_args_list[1].kwargs["data"]["method"] == "create_salary_slips"
    with patch.object(client, "request") as req:
        client.submit_salary_slips("HR-PRUN-1")
        assert req.call_args.kwargs["data"]["method"] == "submit_salary_slips"
        assert req.call_args.kwargs["data"]["dn"] == "HR-PRUN-1"
        client.list_salary_slips(payroll_entry="HR-PRUN-1")
        assert json.loads(req.call_args.kwargs["params"]["filters"]) == {
            "payroll_entry": "HR-PRUN-1"
        }
        client.get_salary_slip("Sal Slip/E1/00001")
        req.assert_called_with(
            "GET", "/api/resource/Salary%20Slip/Sal%20Slip%2FE1%2F00001"
        )


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R008")
def test_employee_checkin():
    client = _client()
    with patch.object(client, "request") as req:
        client.add_employee_checkin("E1", "2026-01-05 09:00:00", log_type="IN")
        req.assert_called_with(
            "POST",
            "/api/resource/Employee%20Checkin",
            data={"employee": "E1", "time": "2026-01-05 09:00:00", "log_type": "IN"},
        )
