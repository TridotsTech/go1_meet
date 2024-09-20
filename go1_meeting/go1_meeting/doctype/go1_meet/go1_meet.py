# Copyright (c) 2024, Tridots Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate
from go1_meeting.go1_meeting.integration.validation import set_token_response
class Go1Meet(Document):
	def before_save(self):
		if not self.url:
			self.status = "Draft"
		