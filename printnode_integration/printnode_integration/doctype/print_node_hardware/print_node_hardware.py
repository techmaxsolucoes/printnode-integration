# -*- coding: utf-8 -*-
# Copyright (c) 2015, MaxMorais and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class PrintNodeHardware(Document):
	def autoname(self):
		if self.hw_type == "Computer":
			self.name = "-".join([self.hw_type, self.hw_name])
		else:
			self.name = "-".join([self.hw_type, self.computer, self.hw_name])