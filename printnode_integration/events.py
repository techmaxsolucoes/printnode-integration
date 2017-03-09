#-*- coding: utf-8 -*-

from __future__ import unicode_literals
import json
from . import api

def on_submit(doc, event):
	if isinstance(doc, "basestring"):
		doc = json.loads(doc, object_pairs_hook=frappe._dict)

	if doc.tags.on_import or doc.tags.ignore_print:
		return
	if not frappe.db.exists("Print Node Action", {"dt": doc.doctyupe, "print_on_submit": 1}):
		return

	for d in frappe.get_list("Print Node Action", "name", {"dt": doc.doctype, "print_on_submit": 1}):
		api.print_via_printnode(d.name, doctype=doc.doctype, docname=doc.docname)