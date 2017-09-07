#-*- coding: utf-8 -*-

import json
import requests
import datetime
import frappe
import hashlib

from base64 import b64encode, b64decode
from frappe import _
from frappe.utils import flt, cint, get_datetime, date_diff, nowdate, now_datetime
from frappe.utils.file_manager import get_file
from frappe.utils.jinja import render_template
from frappe.utils.data import scrub_urls
from frappe.utils.pdf import get_pdf
from xmlescpos.escpos import Escpos, StyleStack

try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO

try:
	from printnodeapi.Gateway import Gateway
except ImportError:
	from printnodeapi.gateway import Gateway

class IOPrinter(Escpos):
	def __init__(self):
		self.slip_sheet_mode = False
		self.io = StringIO()
		self.stylestack = StyleStack()

	def _raw(self, msg):
		self.io.write(msg)

	def get_content(self):
		return self.io.getvalue()


def get_print_content(print_format, doctype, docname, is_escpos=False, is_raw=False):
	if is_escpos or is_raw:
		doc = frappe.get_doc(doctype, docname)
		template = frappe.db.get_value("Print Format", print_format, "html")
		content = render_template(template, {"doc": doc})
		if is_escpos:
			content.replace("<br>", "<br/>")
	else:
		content = frappe.get_print(doctype, docname, print_format)

	if is_escpos:
		printer = IOPrinter()
		printer.receipt(content)
		raw = printer.get_content()
	elif is_raw:
		raw = content
	else:
		raw = get_pdf(content)	

	#frappe.msgprint("<pre>%s</pre>" %raw)
	
	return b64encode(raw)

@frappe.whitelist()
def print_via_printnode(action, **kwargs):
	settings = frappe.get_doc("Print Node Settings", "Print Node Settings")
	if not settings.api_key:
		frappe.throw(
			_("Your Print Node API Key is not configured in Print Node Settings")
		)
	if not frappe.db.exists("Print Node Action", action):
		frappe.throw(
			_("Unable to find an action in Print settings to execute this print")
		)
	else:
		action = frappe.get_doc("Print Node Action", action)

	if action.get("capabilities"):
		print_settings = json.loads(action.capabilities)
	else:
		print_settings = {}

	printer = frappe.db.get_value("Print Node Hardware", action.printer, "hw_id")

	gateway = Gateway(apikey=settings.api_key)

	if action.printable_type == "Print Format":
		print_content = get_print_content(
			action.print_format if not action.use_standard else "Standard",
			kwargs.get("doctype"),
			kwargs.get("docname"),
			action.is_xml_esc_pos,
			action.is_raw_text
		)
		raw = action.is_xml_esc_pos or action.is_raw_text
		gateway.PrintJob(
			printer=int(printer),
			job_type="raw" if raw else "pdf",
			title=action.action,
			base64=print_content,
			**print_settings
		)

	else:
		print_content = b64encode(get_file(kwargs.get("filename", ""))[1])
		gateway.PrintJob(
			printer=int(printer),
			job_type="pdf" if kwargs.get("filename", "").lower().endswith(".pdf") else "raw",
			base64=print_content,
			**print_settings
		)

	job = frappe.new_doc("Print Node Job").update({
		"print_node_action": action.name,
		"printer_id": action.printer,
		"print_type": action.printable_type,
		"file_link": kwargs.get("filename"),
		"print_format": action.print_format if not actions.is_standard else "Standard",
		"ref_type": kwargs.get("doctype"),
		"ref_name": kwargs.get("docname"),
		"is_xml_esc_pos": action.is_xml_esc_pos,
		"is_raw_text": action.is_raw_text,
		"print_job_name": action.action,
		"copies": 1,
		"job_owner": frappe.local.session.user,
		"print_timestamp": now_datetime()
	})
	job.flags.ignore_permissions = True
	job.flags.ignore_links = True
	job.flags.ignore_validate = True
	job.insert()
