# -*- coding: utf-8 -*-
# Copyright (c) 2015, MaxMorais and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class PrintNodeHardware(Document):
	def autoname(self):
		self.name = "-".join([self.hw_type, str(self.hw_id)])