#-*- coding: utf-8 -*-

from __future__ import unicode_literals
import json
import frappe
from frappe.utils.background_jobs import enqueue
from . import api

def print_via_printnode( doctype, docname, docevent):
	if frappe.flags.in_import or frappe.flags.in_patch:
		return
	if not frappe.db.exists(doctype, docname):
		enqueue('printnode_integration.events.print_via_printnode', enqueue_after_commit=False, doctype=doctype, docname=docname, docevent=docevent)

	doc = frappe.get_doc(doctype, docname)
	ignore_flags = True
	
	if not ignore_flags:
		if doc.flags.on_import or doc.flags.ignore_print:
			return

	if not frappe.db.exists("Print Node Action", {"dt": doc.doctype, "print_on": docevent}):
		return

	for d in frappe.get_list("Print Node Action", ["name", "ensure_single_print", "allow_inline_batch", "batch_field"], {"dt": doc.doctype, "print_on": docevent}):
		if docevent == "Update" and d.ensure_single_print and frappe.db.exists("Print Job", d.name):
			continue
		if not d.allow_inline_batch:
			api.print_via_printnode(d.name, doctype=doc.doctype, docname=doc.name)
		else:
			if '.' in d.batch_field:
				table_field = d.batch_field.split('.')[0]
				reference_list = doc.get(table_field)
			else:
				reference_list = [doc]
			inline_field = d.batch_field.split('.')[-1]
			api.batch_print_via_printnode(d.name, map(lambda d: frappe._dict(docname=d.get(inline_field)), reference_list))

def after_insert( doc, handler=None ):
	enqueue('printnode_integration.events.print_via_printnode', enqueue_after_commit=True, doctype=doc.doctype, docname=doc.name, docevent='Insert', now=True)

def on_update( doc, handler=None ):
	enqueue('printnode_integration.events.print_via_printnode', enqueue_after_commit=True, doctype=doc.doctype, docname=doc.name, docevent='Update', now=True)
	
def on_submit(doc, handler=None):
	print((doc.doctype, doc.name, 'Submit'))
	enqueue('printnode_integration.events.print_via_printnode', enqueue_after_commit=True, doctype=doc.doctype, docname=doc.name, docevent='Submit', now=True)

def on_trash(doc, handler=None):
	settings = frappe.get_doc('Print Node Settings', 'Print Node Settings')
	if not settings.api_key or settings.allow_deletion_for_printed_documents:
		for print_job in frappe.get_all('Print Node Job', fields=['name'], 
			filters={'ref_type': doc.doctype, 'ref_name': doc.name}):
			frappe.delete_doc('Print Node Job', print_job.name, ignore_permissions=True)
