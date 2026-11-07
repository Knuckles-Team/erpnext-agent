"""Typed HR operations (ERPNext setup doctypes plus the separate HR app).

Employee, Department, Designation and Holiday List ship with ERPNext; leave,
attendance, salary and payroll come from the HR app (``hrms``). Each public
method is one Frappe operation and is served as its own typed tool.
"""

from typing import Any

from erpnext_agent.api._docs import compact as _merge
from erpnext_agent.api._docs import data_of as _data
from erpnext_agent.api.api_client_resource import Api as ResourceApi
from erpnext_agent.api.api_client_resource import _doc_path
from erpnext_agent.lifecycle import DocumentState, state_of

_ATTENDANCE_TOOL = (
    "hrms.hr.doctype.employee_attendance_tool.employee_attendance_tool"
    ".mark_employee_attendance"
)
_LEAVE_BALANCE = (
    "hrms.hr.doctype.leave_application.leave_application.get_leave_balance_on"
)


class ApiHr(ResourceApi):
    # --- employee master -------------------------------------------------

    def create_employee(
        self,
        first_name: str,
        gender: str,
        date_of_birth: str,
        date_of_joining: str,
        company: str,
        last_name: str | None = None,
        department: str | None = None,
        designation: str | None = None,
        reports_to: str | None = None,
        holiday_list: str | None = None,
        employment_type: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict:
        """Hire: create an Active Employee of a company.

        POST /api/resource/Employee

        ``gender`` is a Gender record (Male, Female, Other, ...); dates are
        YYYY-MM-DD. ``extra`` carries any other Employee field.
        """
        doc = _merge(
            {
                "first_name": first_name,
                "last_name": last_name,
                "gender": gender,
                "date_of_birth": date_of_birth,
                "date_of_joining": date_of_joining,
                "company": company,
                "status": "Active",
                "department": department,
                "designation": designation,
                "reports_to": reports_to,
                "holiday_list": holiday_list,
                "employment_type": employment_type,
            },
            extra,
        )
        return self.request("POST", _doc_path("Employee"), data=doc)

    def update_employee(self, name: str, data: dict[str, Any]) -> dict:
        """Change fields of an Employee (department, designation, contact, ...).

        PUT /api/resource/Employee/<name>
        """
        return self.request("PUT", _doc_path("Employee", name), data=data)

    def get_employee(self, name: str) -> dict:
        """Read one Employee record.

        GET /api/resource/Employee/<name>
        """
        return self.request("GET", _doc_path("Employee", name))

    def list_employees(
        self,
        company: str | None = None,
        status: str | None = "Active",
        department: str | None = None,
        limit: int = 50,
    ) -> list:
        """List employees of a company, by status and department.

        GET /api/resource/Employee
        """
        filters = _merge(
            {"company": company, "status": status, "department": department}, None
        )
        return self.list_documents(
            "Employee",
            filters=filters,
            fields=[
                "name",
                "employee_name",
                "company",
                "department",
                "designation",
                "status",
                "date_of_joining",
                "relieving_date",
            ],
            limit=limit,
        )

    def relieve_employee(
        self, name: str, relieving_date: str, reason_for_leaving: str | None = None
    ) -> dict:
        """Retire or separate an employee: set the relieving date and status Left.

        PUT /api/resource/Employee/<name>

        The record and its history are kept; never delete an employee.
        """
        data = _merge(
            {
                "relieving_date": relieving_date,
                "status": "Left",
                "reason_for_leaving": reason_for_leaving,
            },
            None,
        )
        return self.request("PUT", _doc_path("Employee", name), data=data)

    # --- organisation ----------------------------------------------------

    def create_department(
        self,
        department_name: str,
        company: str,
        parent_department: str | None = None,
        is_group: bool = False,
    ) -> dict:
        """Create a Department of a company (named "<department> - <abbr>").

        POST /api/resource/Department
        """
        doc = _merge(
            {
                "department_name": department_name,
                "company": company,
                "parent_department": parent_department,
                "is_group": 1 if is_group else 0,
            },
            None,
        )
        return self.request("POST", _doc_path("Department"), data=doc)

    def list_departments(self, company: str | None = None, limit: int = 100) -> list:
        """List departments, optionally of one company.

        GET /api/resource/Department
        """
        return self.list_documents(
            "Department",
            filters={"company": company} if company else None,
            fields=["name", "department_name", "company", "parent_department"],
            limit=limit,
        )

    def create_designation(
        self, designation_name: str, description: str | None = None
    ) -> dict:
        """Create a Designation (job title), shared by every company.

        POST /api/resource/Designation
        """
        doc = _merge(
            {"designation_name": designation_name, "description": description}, None
        )
        return self.request("POST", _doc_path("Designation"), data=doc)

    def list_designations(self, limit: int = 100) -> list:
        """List designations (job titles).

        GET /api/resource/Designation
        """
        return self.list_documents(
            "Designation", fields=["name", "designation_name"], limit=limit
        )

    # --- holiday lists ---------------------------------------------------

    def create_holiday_list(
        self,
        holiday_list_name: str,
        from_date: str,
        to_date: str,
        holidays: list[dict[str, Any]] | None = None,
        weekly_off: str | None = None,
        country: str | None = None,
    ) -> dict:
        """Create a Holiday List with dated holidays, optionally adding a weekly off.

        POST /api/resource/Holiday List

        ``holidays`` rows are ``{"holiday_date": "YYYY-MM-DD", "description":
        "..."}``. With ``weekly_off`` (a weekday name such as ``Sunday``) the
        list is then filled by the server's own weekly-off generator
        (``add_holiday_list_weekly_offs``).
        """
        doc = _merge(
            {
                "holiday_list_name": holiday_list_name,
                "from_date": from_date,
                "to_date": to_date,
                "country": country,
                "holidays": holidays or [],
            },
            None,
        )
        created = self.request("POST", _doc_path("Holiday List"), data=doc)
        if not weekly_off:
            return created
        return self.add_holiday_list_weekly_offs(holiday_list_name, weekly_off)

    def add_holiday_list_weekly_offs(self, holiday_list: str, weekly_off: str) -> dict:
        """Add every <weekday> between the list's dates as a weekly-off holiday.

        POST /api/method/run_doc_method (Holiday List.get_weekly_off_dates)

        Runs the server's generator on the current document, then saves the
        rows it added. Dates already on the list are kept once.
        """
        doc = _data(self.request("GET", _doc_path("Holiday List", holiday_list)))
        doc["weekly_off"] = weekly_off
        result = self.request(
            "POST",
            "/api/method/run_doc_method",
            data={"docs": doc, "method": "get_weekly_off_dates"},
        )
        docs = result.get("docs") if isinstance(result, dict) else None
        updated = docs[0] if docs else doc
        return self.request(
            "PUT",
            _doc_path("Holiday List", holiday_list),
            data={"weekly_off": weekly_off, "holidays": updated.get("holidays", [])},
        )

    def get_holiday_list(self, name: str) -> dict:
        """Read a Holiday List with its holidays.

        GET /api/resource/Holiday List/<name>
        """
        return self.request("GET", _doc_path("Holiday List", name))

    # --- attendance ------------------------------------------------------

    def mark_attendance(
        self,
        employee: str,
        attendance_date: str,
        status: str,
        company: str | None = None,
        leave_type: str | None = None,
        shift: str | None = None,
        submit: bool = True,
    ) -> dict:
        """Mark one employee's attendance for a day and submit it.

        POST /api/resource/Attendance, then frappe.client.submit

        ``status`` is Present, Absent, On Leave, Half Day or Work From Home.
        """
        doc = _merge(
            {
                "employee": employee,
                "attendance_date": attendance_date,
                "status": status,
                "company": company,
                "leave_type": leave_type,
                "shift": shift,
            },
            None,
        )
        created = _data(self.request("POST", _doc_path("Attendance"), data=doc))
        if not submit:
            return created
        return self.request(
            "POST", "/api/method/frappe.client.submit", data={"doc": created}
        )

    def mark_bulk_attendance(
        self,
        employees: list[str],
        date: str,
        status: str,
        company: str | None = None,
        leave_type: str | None = None,
        shift: str | None = None,
    ) -> dict:
        """Mark (and submit) the same attendance status for many employees on one day.

        POST /api/method/hrms.hr.doctype.employee_attendance_tool.employee_attendance_tool.mark_employee_attendance
        """
        data = self._json_params(
            employee_list=employees,
            date=date,
            status=status,
            company=company,
            leave_type=leave_type,
            shift=shift,
        )
        return self.request("POST", f"/api/method/{_ATTENDANCE_TOOL}", data=data)

    def list_attendance(
        self,
        employee: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        company: str | None = None,
        limit: int = 100,
    ) -> list:
        """List attendance records by employee, company and date range.

        GET /api/resource/Attendance
        """
        filters: list[list[Any]] = []
        if employee:
            filters.append(["employee", "=", employee])
        if company:
            filters.append(["company", "=", company])
        if from_date:
            filters.append(["attendance_date", ">=", from_date])
        if to_date:
            filters.append(["attendance_date", "<=", to_date])
        return self.list_documents(
            "Attendance",
            filters=filters or None,
            fields=["name", "employee", "attendance_date", "status", "docstatus"],
            limit=limit,
        )

    # --- leave -----------------------------------------------------------

    def create_leave_type(
        self,
        leave_type_name: str,
        max_leaves_allowed: float | None = None,
        is_lwp: bool = False,
        include_holiday: bool = False,
        is_carry_forward: bool = False,
    ) -> dict:
        """Create a Leave Type (annual, sick, leave without pay, ...).

        POST /api/resource/Leave Type
        """
        doc = _merge(
            {
                "leave_type_name": leave_type_name,
                "max_leaves_allowed": max_leaves_allowed,
                "is_lwp": 1 if is_lwp else 0,
                "include_holiday": 1 if include_holiday else 0,
                "is_carry_forward": 1 if is_carry_forward else 0,
            },
            None,
        )
        return self.request("POST", _doc_path("Leave Type"), data=doc)

    def allocate_leave(
        self,
        employee: str,
        leave_type: str,
        from_date: str,
        to_date: str,
        new_leaves_allocated: float,
        company: str | None = None,
        submit: bool = True,
    ) -> dict:
        """Allocate leave days of a type to an employee for a period, then submit.

        POST /api/resource/Leave Allocation, then frappe.client.submit
        """
        doc = _merge(
            {
                "employee": employee,
                "leave_type": leave_type,
                "from_date": from_date,
                "to_date": to_date,
                "new_leaves_allocated": new_leaves_allocated,
                "company": company,
            },
            None,
        )
        created = _data(self.request("POST", _doc_path("Leave Allocation"), data=doc))
        if not submit:
            return created
        return self.request(
            "POST", "/api/method/frappe.client.submit", data={"doc": created}
        )

    def apply_leave(
        self,
        employee: str,
        leave_type: str,
        from_date: str,
        to_date: str,
        company: str | None = None,
        leave_approver: str | None = None,
        half_day: bool = False,
        description: str | None = None,
    ) -> dict:
        """File a Leave Application (status Open, awaiting the approver).

        POST /api/resource/Leave Application
        """
        doc = _merge(
            {
                "employee": employee,
                "leave_type": leave_type,
                "from_date": from_date,
                "to_date": to_date,
                "company": company,
                "leave_approver": leave_approver,
                "half_day": 1 if half_day else 0,
                "description": description,
                "status": "Open",
            },
            None,
        )
        return self.request("POST", _doc_path("Leave Application"), data=doc)

    def approve_leave_application(self, name: str) -> dict:
        """Approve an open Leave Application: status Approved, then submit.

        PUT /api/resource/Leave Application/<name>, then frappe.client.submit
        """
        return self._decide_leave(name, "Approved")

    def reject_leave_application(self, name: str) -> dict:
        """Reject an open Leave Application: status Rejected, then submit.

        PUT /api/resource/Leave Application/<name>, then frappe.client.submit
        """
        return self._decide_leave(name, "Rejected")

    def _decide_leave(self, name: str, status: str) -> dict:
        path = _doc_path("Leave Application", name)
        saved = _data(self.request("PUT", path, data={"status": status}))
        return self.request(
            "POST", "/api/method/frappe.client.submit", data={"doc": saved}
        )

    def get_leave_balance(self, employee: str, leave_type: str, date: str) -> dict:
        """Read an employee's remaining leave days of a type on a date.

        GET /api/method/hrms.hr.doctype.leave_application.leave_application.get_leave_balance_on
        """
        return self.request(
            "GET",
            f"/api/method/{_LEAVE_BALANCE}",
            params={"employee": employee, "leave_type": leave_type, "date": date},
        )

    # --- salary and payroll ------------------------------------------------

    def create_salary_component(
        self,
        salary_component: str,
        salary_component_abbr: str,
        component_type: str,
        description: str | None = None,
        depends_on_payment_days: bool = True,
    ) -> dict:
        """Create a Salary Component; ``component_type`` is Earning or Deduction.

        POST /api/resource/Salary Component
        """
        doc = _merge(
            {
                "salary_component": salary_component,
                "salary_component_abbr": salary_component_abbr,
                "type": component_type,
                "description": description,
                "depends_on_payment_days": 1 if depends_on_payment_days else 0,
            },
            None,
        )
        return self.request("POST", _doc_path("Salary Component"), data=doc)

    def create_salary_structure(
        self,
        name: str,
        company: str,
        currency: str,
        earnings: list[dict[str, Any]],
        deductions: list[dict[str, Any]] | None = None,
        payroll_frequency: str = "Monthly",
        submit: bool = True,
    ) -> dict:
        """Create a Salary Structure from earning and deduction rows, then submit.

        POST /api/resource/Salary Structure, then frappe.client.submit

        Rows are ``{"salary_component": ..., "amount": ...}`` or
        ``{"salary_component": ..., "amount_based_on_formula": 1, "formula":
        "base * 0.1"}``.
        """
        doc = {
            "__newname": name,
            "company": company,
            "currency": currency,
            "is_active": "Yes",
            "payroll_frequency": payroll_frequency,
            "earnings": earnings,
            "deductions": deductions or [],
        }
        created = _data(self.request("POST", _doc_path("Salary Structure"), data=doc))
        if not submit:
            return created
        return self.request(
            "POST", "/api/method/frappe.client.submit", data={"doc": created}
        )

    def assign_salary_structure(
        self,
        employee: str,
        salary_structure: str,
        from_date: str,
        base: float,
        company: str,
        currency: str,
        payroll_payable_account: str | None = None,
        income_tax_slab: str | None = None,
        submit: bool = True,
    ) -> dict:
        """Assign a Salary Structure to an employee from a date with a base pay, then submit.

        POST /api/resource/Salary Structure Assignment, then frappe.client.submit
        """
        doc = _merge(
            {
                "employee": employee,
                "salary_structure": salary_structure,
                "from_date": from_date,
                "base": base,
                "company": company,
                "currency": currency,
                "payroll_payable_account": payroll_payable_account,
                "income_tax_slab": income_tax_slab,
            },
            None,
        )
        created = _data(
            self.request("POST", _doc_path("Salary Structure Assignment"), data=doc)
        )
        if not submit:
            return created
        return self.request(
            "POST", "/api/method/frappe.client.submit", data={"doc": created}
        )

    def create_payroll_entry(
        self,
        company: str,
        posting_date: str,
        start_date: str,
        end_date: str,
        currency: str,
        payroll_payable_account: str,
        cost_center: str,
        payroll_frequency: str = "Monthly",
        exchange_rate: float = 1,
        department: str | None = None,
        payment_account: str | None = None,
    ) -> dict:
        """Create a draft Payroll Entry for a company and pay period.

        POST /api/resource/Payroll Entry
        """
        doc = _merge(
            {
                "company": company,
                "posting_date": posting_date,
                "start_date": start_date,
                "end_date": end_date,
                "currency": currency,
                "exchange_rate": exchange_rate,
                "payroll_payable_account": payroll_payable_account,
                "cost_center": cost_center,
                "payroll_frequency": payroll_frequency,
                "department": department,
                "payment_account": payment_account,
            },
            None,
        )
        return self.request("POST", _doc_path("Payroll Entry"), data=doc)

    def fill_payroll_employees(self, name: str) -> dict:
        """Fill a draft Payroll Entry with every employee its filters select, and save.

        POST /api/method/run_doc_method (Payroll Entry.fill_employee_details)
        """
        path = _doc_path("Payroll Entry", name)
        doc = _data(self.request("GET", path))
        result = self.request(
            "POST",
            "/api/method/run_doc_method",
            data={"docs": doc, "method": "fill_employee_details"},
        )
        docs = result.get("docs") if isinstance(result, dict) else None
        filled = docs[0] if docs else doc
        return self.request(
            "PUT",
            path,
            data={
                "employees": filled.get("employees", []),
                "number_of_employees": len(filled.get("employees", [])),
            },
        )

    def create_salary_slips(self, name: str) -> dict:
        """Create the draft salary slips of a Payroll Entry.

        A draft entry is submitted (submitting creates the slips); a submitted
        entry re-runs the server's slip creation for employees still missing one.

        POST /api/method/frappe.client.submit or run_doc_method create_salary_slips
        """
        doc = _data(self.request("GET", _doc_path("Payroll Entry", name)))
        if state_of(doc) is DocumentState.Draft:
            return self.request(
                "POST", "/api/method/frappe.client.submit", data={"doc": doc}
            )
        return self.run_document_method("Payroll Entry", name, "create_salary_slips")

    def submit_salary_slips(self, name: str) -> dict:
        """Submit every draft salary slip of a submitted Payroll Entry.

        POST /api/method/run_doc_method (Payroll Entry.submit_salary_slips)
        """
        return self.run_document_method("Payroll Entry", name, "submit_salary_slips")

    def list_salary_slips(
        self,
        payroll_entry: str | None = None,
        employee: str | None = None,
        limit: int = 100,
    ) -> list:
        """List salary slips by payroll entry or employee.

        GET /api/resource/Salary Slip
        """
        filters = _merge({"payroll_entry": payroll_entry, "employee": employee}, None)
        return self.list_documents(
            "Salary Slip",
            filters=filters or None,
            fields=[
                "name",
                "employee",
                "employee_name",
                "start_date",
                "end_date",
                "gross_pay",
                "total_deduction",
                "net_pay",
                "status",
                "docstatus",
            ],
            limit=limit,
        )

    def get_salary_slip(self, name: str) -> dict:
        """Read one Salary Slip with its earnings and deductions.

        GET /api/resource/Salary Slip/<name>
        """
        return self.request("GET", _doc_path("Salary Slip", name))

    # --- check-in --------------------------------------------------------

    def add_employee_checkin(
        self,
        employee: str,
        time: str,
        log_type: str | None = None,
        device_id: str | None = None,
    ) -> dict:
        """Log an employee check-in or check-out (``log_type`` IN or OUT).

        POST /api/resource/Employee Checkin

        ``time`` is "YYYY-MM-DD HH:MM:SS".
        """
        doc = _merge(
            {
                "employee": employee,
                "time": time,
                "log_type": log_type,
                "device_id": device_id,
            },
            None,
        )
        return self.request("POST", _doc_path("Employee Checkin"), data=doc)
