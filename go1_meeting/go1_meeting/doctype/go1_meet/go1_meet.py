# Copyright (c) 2024, Tridots Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate

class Go1Meet(Document):
	def validate(self):
		if self.platform == "WhereBy":
			frappe.log_error("date type",type(self.start_date))
			if getdate(self.end_date) <= getdate(self.start_date):
				frappe.throw("End Date should be greater than start Date")
