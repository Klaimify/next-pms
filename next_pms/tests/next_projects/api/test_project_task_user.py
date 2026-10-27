import frappe
from erpnext import get_default_company
from frappe.tests import IntegrationTestCase

from next_pms.install import PROJECT_COST_FIELDS
from next_pms.next_projects.api.project import (
    FINANCIAL_LIST_KEYS,
    get_project_sidebar,
    get_project_tracking,
    get_projects_view,
)
from next_pms.utils.permissions import can_view_financials

TASK_USER = "project.taskuser@example.com"
MANAGER_USER = "project.taskmanager@example.com"
PROJECT_NAME = "Project Task User Fixture"


class TestProjectTaskUser(IntegrationTestCase):
    """The Project Task User role opens the project pages but never receives financial data."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        for role in ("Project Task User", "Projects Manager"):
            if not frappe.db.exists("Role", role):
                frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)
        from next_pms.install import restrict_project_cost_fields, setup_custom_docperms

        setup_custom_docperms()
        restrict_project_cost_fields()

        cls.task_user = cls.make_user(TASK_USER, "Project Task User")
        cls.manager_user = cls.make_user(MANAGER_USER, "Projects Manager")
        cls.project = cls.make_project()
        for fieldname in PROJECT_COST_FIELDS:
            frappe.db.set_value("Project", cls.project, fieldname, 1000)
        for user in (cls.task_user, cls.manager_user):
            frappe.share.add("Project", cls.project, user, read=1, write=1, flags={"ignore_share_permission": True})
        frappe.clear_cache()

    @classmethod
    def tearDownClass(cls):
        frappe.set_user("Administrator")
        super().tearDownClass()

    @classmethod
    def make_user(cls, email, role):
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
        frappe.get_doc("User", email).add_roles(role)
        return email

    @classmethod
    def make_project(cls):
        existing = frappe.db.get_value("Project", {"project_name": PROJECT_NAME})
        if existing:
            return existing
        return (
            frappe.get_doc(
                {
                    "doctype": "Project",
                    "project_name": PROJECT_NAME,
                    "company": get_default_company(),
                    "custom_billing_type": "Non-Billable",
                }
            )
            .insert(ignore_permissions=True, ignore_mandatory=True)
            .name
        )

    def tearDown(self):
        frappe.set_user("Administrator")

    def test_financial_access_follows_the_role(self):
        self.assertFalse(can_view_financials(self.task_user))
        self.assertTrue(can_view_financials(self.manager_user))

    def test_project_doc_hides_cost_fields_from_task_user(self):
        frappe.set_user(self.task_user)
        doc = frappe.client.get("Project", self.project)

        for fieldname in PROJECT_COST_FIELDS:
            self.assertFalse(doc.get(fieldname), fieldname)

    def test_project_doc_keeps_cost_fields_for_manager(self):
        frappe.set_user(self.manager_user)
        doc = frappe.client.get("Project", self.project)

        for fieldname in PROJECT_COST_FIELDS:
            self.assertEqual(doc.get(fieldname), 1000, fieldname)

    def test_list_view_has_no_financial_keys(self):
        frappe.set_user(self.task_user)
        result = get_projects_view(view="list", search=PROJECT_NAME)

        self.assertTrue(result["data"])
        for project in result["data"]:
            for key in FINANCIAL_LIST_KEYS:
                self.assertNotIn(key, project)

    def test_kanban_view_has_no_billing_type(self):
        frappe.set_user(self.task_user)
        result = get_projects_view(view="kanban", search=PROJECT_NAME)

        cards = [card for group in result["data"].values() for card in group]
        self.assertTrue(cards)
        for card in cards:
            self.assertNotIn("billing_type", card)

    def test_computed_sort_falls_back_for_task_user(self):
        frappe.set_user(self.task_user)
        result = get_projects_view(view="list", search=PROJECT_NAME, order_by="total_budget desc")

        self.assertTrue(result["data"])

    def test_list_view_keeps_financial_keys_for_manager(self):
        frappe.set_user(self.manager_user)
        result = get_projects_view(view="list", search=PROJECT_NAME)

        self.assertTrue(result["data"])
        for key in FINANCIAL_LIST_KEYS:
            self.assertIn(key, result["data"][0])

    def test_sidebar_has_no_financials_for_task_user(self):
        frappe.set_user(self.task_user)
        sidebar = get_project_sidebar(self.project)

        self.assertNotIn("burn", sidebar)
        self.assertNotIn("billing_team", sidebar)
        for member in sidebar["members"]:
            self.assertNotIn("hourly_rate", member)

    def test_sidebar_has_financials_for_manager(self):
        frappe.set_user(self.manager_user)
        sidebar = get_project_sidebar(self.project)

        self.assertIn("burn", sidebar)
        self.assertIn("billing_team", sidebar)

    def test_tracking_is_rejected_for_task_user(self):
        frappe.set_user(self.task_user)

        with self.assertRaises(frappe.PermissionError):
            get_project_tracking(self.project)
