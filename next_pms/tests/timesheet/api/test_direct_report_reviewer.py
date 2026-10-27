import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import getdate, nowdate

from next_pms.resource_management.api.utils.helpers import resource_api_permissions_check
from next_pms.tests.utils import make_employee
from next_pms.timesheet.api.team import approve_or_reject_timesheet, get_team_timesheet_data, get_team_timesheet_weeks
from next_pms.timesheet.api.utils import employee_has_higher_access

MANAGER_USER = "direct.report.manager@example.com"
REPORT_USER = "direct.report.member@example.com"
STRANGER_USER = "direct.report.stranger@example.com"


class TestDirectReportReviewer(IntegrationTestCase):
    """Project Task User reviews the Team timesheet for direct reports only, and can manage allocations."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        if not frappe.db.exists("Role", "Project Task User"):
            frappe.get_doc({"doctype": "Role", "role_name": "Project Task User"}).insert(ignore_permissions=True)
        from next_pms.install import grant_project_task_user_allocation_access, setup_custom_docperms

        setup_custom_docperms()
        grant_project_task_user_allocation_access()

        for email in (MANAGER_USER, REPORT_USER, STRANGER_USER):
            if not frappe.db.exists("User", email):
                frappe.get_doc(
                    {
                        "doctype": "User",
                        "email": email,
                        "first_name": email.split("@")[0],
                        "user_type": "System User",
                        "send_welcome_email": 0,
                    }
                ).insert(ignore_permissions=True)

        cls.manager = make_employee(MANAGER_USER, leave_approver="Administrator")
        cls.report = make_employee(REPORT_USER, reports_to=cls.manager, leave_approver="Administrator")
        cls.stranger = make_employee(STRANGER_USER, leave_approver="Administrator")
        frappe.get_doc("User", MANAGER_USER).add_roles("Project Task User")
        frappe.clear_cache()

    def setUp(self):
        frappe.set_user(MANAGER_USER)

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.flags.team_review_scoped = False

    def _member_ids(self):
        result = get_team_timesheet_data(start_date=nowdate(), page_length=100)
        return {member["employee"] for member in result["members"]}

    def test_team_page_lists_only_direct_reports(self):
        members = self._member_ids()

        self.assertIn(self.report, members)
        self.assertNotIn(self.stranger, members)

    def test_requested_reports_to_cannot_widen_the_scope(self):
        result = get_team_timesheet_data(start_date=nowdate(), page_length=100, reports_to=self.stranger)

        self.assertNotIn(self.stranger, {member["employee"] for member in result["members"]})

    def test_weeks_endpoint_is_open_to_the_role(self):
        self.assertIn("weeks", get_team_timesheet_weeks(date=nowdate()))

    def test_higher_access_covers_direct_reports_only(self):
        self.assertTrue(employee_has_higher_access(self.report, ptype="read"))
        self.assertTrue(employee_has_higher_access(self.report, ptype="write"))
        self.assertFalse(employee_has_higher_access(self.stranger, ptype="read"))
        self.assertFalse(employee_has_higher_access(self.stranger, ptype="write"))

    def test_approving_a_non_report_is_refused(self):
        with self.assertRaises(frappe.PermissionError):
            approve_or_reject_timesheet(self.stranger, "Approved", dates=[str(getdate(nowdate()))])

    def test_role_can_manage_allocations(self):
        self.assertEqual(resource_api_permissions_check(), {"read": True, "write": True, "delete": True})
