# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import frappe, unittest

class TestDocument(unittest.TestCase):
	def test_get_return_empty_list_for_table_field_if_none(self):
		d = frappe.get_doc({"doctype":"User"})
		self.assertEquals(d.get("user_roles"), [])

	def test_load(self):
		d = frappe.get_doc("DocType", "User")
		self.assertEquals(d.doctype, "DocType")
		self.assertEquals(d.name, "User")
		self.assertEquals(d.allow_rename, 1)
		self.assertTrue(isinstance(d.fields, list))
		self.assertTrue(isinstance(d.permissions, list))
		self.assertTrue(filter(lambda d: d.fieldname=="email", d.fields))

	def test_load_single(self):
		d = frappe.get_doc("Website Settings", "Website Settings")
		self.assertEquals(d.name, "Website Settings")
		self.assertEquals(d.doctype, "Website Settings")
		self.assertTrue(d.disable_signup in (0, 1))

	def test_insert(self):
		d = frappe.get_doc({
			"doctype":"Event",
			"subject":"test-doc-test-event 1",
			"starts_on": "2014-01-01",
			"event_type": "Public"
		})
		d.insert()
		self.assertTrue(d.name.startswith("EV"))
		self.assertEquals(frappe.db.get_value("Event", d.name, "subject"),
			"test-doc-test-event 1")

		# test if default values are added
		self.assertEquals(d.send_reminder, 1)
		return d

	def test_insert_with_child(self):
		d = frappe.get_doc({
			"doctype":"Event",
			"subject":"test-doc-test-event 2",
			"starts_on": "2014-01-01",
			"event_type": "Public",
			"event_individuals": [
				{
					"person": "Administrator"
				}
			]
		})
		d.insert()
		self.assertTrue(d.name.startswith("EV"))
		self.assertEquals(frappe.db.get_value("Event", d.name, "subject"),
			"test-doc-test-event 2")

		d1 = frappe.get_doc("Event", d.name)
		self.assertTrue(d1.event_individuals[0].person, "Administrator")

	def test_update(self):
		d = self.test_insert()
		d.subject = "subject changed"
		d.save()

		self.assertEquals(frappe.db.get_value(d.doctype, d.name, "subject"), "subject changed")

	def test_mandatory(self):
		frappe.delete_doc_if_exists("User", "test_mandatory@example.com")

		d = frappe.get_doc({
			"doctype": "User",
			"email": "test_mandatory@example.com",
		})
		self.assertRaises(frappe.MandatoryError, d.insert)

		d.set("first_name", "Test Mandatory")
		d.insert()
		self.assertEquals(frappe.db.get_value("User", d.name), d.name)

	def test_confict_validation(self):
		d1 = self.test_insert()
		d2 = frappe.get_doc(d1.doctype, d1.name)
		d1.save()
		self.assertRaises(frappe.TimestampMismatchError, d2.save)

	def test_confict_validation_single(self):
		d1 = frappe.get_doc("Website Settings", "Website Settings")
		d2 = frappe.get_doc("Website Settings", "Website Settings")
		d1.save()
		self.assertRaises(frappe.TimestampMismatchError, d2.save)

	def test_permission(self):
		frappe.set_user("Guest")
		d = self.assertRaises(frappe.PermissionError, self.test_insert)
		frappe.set_user("Administrator")

	def test_permission_single(self):
		frappe.set_user("Guest")
		d = frappe.get_doc("Website Settings", "Website Settigns")
		self.assertRaises(frappe.PermissionError, d.save)
		frappe.set_user("Administrator")

	def test_link_validation(self):
		frappe.delete_doc_if_exists("User", "test_link_validation@example.com")

		d = frappe.get_doc({
			"doctype": "User",
			"email": "test_link_validation@example.com",
			"first_name": "Link Validation",
			"user_roles": [
				{
					"role": "ABC"
				}
			]
		})
		self.assertRaises(frappe.LinkValidationError, d.insert)

		d.user_roles = []
		d.append("user_roles", {
			"role": "System Manager"
		})
		d.insert()

		self.assertEquals(frappe.db.get_value("User", d.name), d.name)

	def test_validate(self):
		d = self.test_insert()
		d.starts_on = "2014-01-01"
		d.ends_on = "2013-01-01"
		self.assertRaises(frappe.ValidationError, d.validate)
		self.assertRaises(frappe.ValidationError, d.run_method, "validate")
		self.assertRaises(frappe.ValidationError, d.save)

	def test_update_after_submit(self):
		d = self.test_insert()
		d.starts_on = "2014-09-09"
		self.assertRaises(frappe.UpdateAfterSubmitError, d.validate_update_after_submit)
		d.meta.get_field("starts_on").allow_on_submit = 1
		d.validate_update_after_submit()
		d.meta.get_field("starts_on").allow_on_submit = 0


