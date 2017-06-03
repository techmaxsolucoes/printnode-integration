#-*- coding: utf-8 -*-

from __future__ import unicode_literals
import json
import frappe
from . import api

def on_submit(doc, event):
	ignore_flags = False
	if isinstance(doc, basestring):
		doc = json.loads(doc, object_pairs_hook=frappe._dict)
		ignore_flags = True

	if not ignore_flags:
		if  doc.flags.on_import or doc.flags.ignore_print:
			return
	if not frappe.db.exists("Print Node Action", {"dt": doc.doctype, "print_on_submit": 1}):
		return

	for d in frappe.get_list("Print Node Action", "name", {"dt": doc.doctype, "print_on_submit": 1}):
		api.print_via_printnode(d.name, doctype=doc.doctype, docname=doc.name)
