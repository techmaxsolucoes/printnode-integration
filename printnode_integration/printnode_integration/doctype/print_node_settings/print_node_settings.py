# -*- coding: utf-8 -*-
# Copyright (c) 2015, MaxMorais and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json

from printnodeapi import Gateway
from collections import OrderedDict
from frappe.model.document import Document

capabilities = [
	"bins", "colate", "copies", "color", "dpis", "extend",
	"medias", "nup", "papers", "printrate", "support_custom_paper_size"
]

class PrintNodeSettings(Document):
	def validate(self):
		self.hardware = ""
		gw = Gateway(apikey=self.api_key)

		hardware = []

		pcs = []
		for computer in gw.computers():
			pcs.append(computer)
			hardware.append({
				"hw_type": "Computer",
				"hw_id": computer.id,
				"hw_name": computer.name,
				"description": computer.hostname,
				"status": computer.state.title()
			})

		for printer in gw.printers():
			hardware.append({
				"hw_type": "Printer",
				"hw_id": printer.id,
				"hw_name": printer.name,
				"computer": printer.computer.name,
				"description": printer.description,
				"status": printer.state.title(),
				"capabilities": json.dumps(OrderedDict(zip(capabilities, printer.capabilities))) if printer.capabilities else ""
			})

		for pc in pcs:
			for scale in gw.scales(pc.id):
				hardware.append({
					"hw_type": "Scale",
					"hw_id": scale.product_id,
					"hw_name": scale.device_name,
					"computer": pc.id
				})

		frappe.db.sql("DELETE FROM `tabPrint Node Hardware`");

		for h in hardware:
			frappe.new_doc("Print Node Hardware").update(h).insert()
			h.pop("capabilities")
		
		self.hardware = json.loads(hardware)