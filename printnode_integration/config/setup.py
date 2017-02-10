from __future__ import unicode_literals

from frappe import _
from frappe.desk.moduleview import add_setup_action

def get_data():
	return [
		{
			"label": _("Printing"),
			"icon": "fa fa-print",
			"items": [
				{
					"type": "doctype",
					"name": "Print Node Settings",
					"description": _("Settings to setup Print Node")
				},
				{
					"type": "doctype",
					"name": "Print Node Hardware",
					"description": _("Hardwares enabled in Print Node")
				}
			]
		}
	]