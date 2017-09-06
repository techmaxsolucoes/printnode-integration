#-*- coding: utf-8 -*-

from __future__ import unicode_literals
import json
import frappe
from . import api

def on_insert( doc, handler=None ):
    ignore_flags = False
	if isinstance(doc, basestring):
    		doc = json.loads(doc, object_pairs_hook=frappe._dict)
			ignore_flags = True
	
	if not ignore_flags:
    	if doc.flags.on_import or doc.flags.ignore_print:
    		return
	
	if not frappe.db.exists("Print Node Action", {"dt": doc.doctype, "print_on": "Insert"}):
    		return

	for d in frappe.db.exists("Print Node Action", {"dt": doc.doctype, "print_on": "Insert"}):
    	api.print_via_printnode(d.name, doctype=doc.doctype, docname=doc.name)


def on_update( doc, handler=None ):
    ignore_flags = False
	if isinstance( doc, basestring ):
    	doc = json.loads( doc, object_pairs_hook=frappe._dict )
		ignore_flags = True
	
	if not ignore_flags:
    	if doc.flags.on_import or doc.flags.ignore_print:
    		return

	if not frappe.db.exists("Print Node Action", {"dt": doc.doctype, "print_on": "Update"}):
    	return

	for d in frappe.get_list("Print Node Action", ["name", "ensure_single_print"], {"dt": doc.doctype, "print_on": "Update"}):
    	if d.ensure_single_print and frappe.db.exists("Print Job", d.name):
    		continue
		api.print_via_printnode(d.name, doctype=doc.doctype, docname=doc.name)

def on_submit(doc, handler=None):
	ignore_flags = False
	if isinstance(doc, basestring):
		doc = json.loads(doc, object_pairs_hook=frappe._dict)
		ignore_flags = True

	if not ignore_flags:
		if  doc.flags.on_import or doc.flags.ignore_print:
			return
	
	if not frappe.db.exists("Print Node Action", {"dt": doc.doctype, "print_on": "Submit"}):
		return

	for d in frappe.get_list("Print Node Action", "name", {"dt": doc.doctype, "print_on": "Submit"}):
		api.print_via_printnode(d.name, doctype=doc.doctype, docname=doc.name)
