#-*- coding: utf-8 -*-

import json
import requests
import datetime
import frappe
import hashlib

from base64 import b64encode, b64decode
from frappe import _
from frappe.utils import flt, cint, get_datetime, date_diff, nowdate
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


def get_print_content(print_format, doctype, docname, is_escpos=False):
	doc = frappe.get_doc(doctype, docname)
	if is_escpos:
		template = frappe.db.get_value("Print Format", print_format, "html")
		content = render_template(template, {"doc": doc})
	else:
		content = frappe.get_print(doctype. docname, print_format, doc=doc)

	if is_escpos:
		printer = IOPrinter()
		printer.receipt(content)
		raw = printer.get_content()
	else:
		raw = get_pdf(content)	
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
			action.print_format,
			kwargs.get("doctype"),
			kwargs.get("docname"),
			action.is_xml_esc_pos
		)
		gateway.PrintJob(
			printer=int(printer),
			job_type="raw" if action.is_xml_esc_pos else "pdf",
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
