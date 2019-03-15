#-*- coding: utf-8 -*-

import json
import requests
import datetime
import frappe
import hashlib
import subprocess

from base64 import b64encode, b64decode
from frappe import _
from frappe.utils import flt, cint, get_datetime, date_diff, nowdate, now_datetime
try:
	from frappe.utils.file_manager import get_file
except ImportError:
	from frappe.core.doctype.file.file import download_file
        def get_file(file_url):
		download_file(file_url)
		file_content = frappe.response.file_content
		del frappe.local.response.file_content
		del frappe.local.response.file_name
		del frappe.local.response.type
		return [file_url, file_content]

from frappe.utils.jinja import render_template
from frappe.utils.data import scrub_urls
from frappe.utils.pdf import get_pdf
from xmlescpos.escpos import Escpos, StyleStack
from pdfkit.pdfkit import PDFKit
from six import string_types

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


class PDFKit(PDFKit):
	def to_image(self, path):
		try:
			return self.to_pdf(path)
		except UnicodeDecodeError, e:
			pass


class Configuration(object):
	pass


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
		if not kwargs.get('doctype') and action.get('print_format'):
			kwargs['doctype'] = frappe.db.get_value('Print Format', action.print_format, 'doc_type')

	if action.get("capabilities"):
		print_settings = json.loads(action.capabilities)
	else:
		print_settings = {}

	if 'collate' in print_settings:
		print_settings['collate'] = bool(print_settings['collate'])

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
			options=print_settings
		)
	else:
		print_content = b64encode(get_file(kwargs.get("filename"))[1])
		gateway.PrintJob(
			printer=int(printer),
			job_type="pdf" if kwargs.get("filename", "").lower().endswith(".pdf") else "raw",
			base64=print_content,
			options=print_settings
		)

	job = frappe.new_doc("Print Node Job").update({
		"print_node_action": action.name,
		"printer_id": action.printer,
		"print_type": "File" if action.printable_type == "Attachment" else "Print Format",
		"file_link": kwargs.get("filename"),
		"print_format": action.print_format if not action.use_standard else "Standard",
		"ref_type": kwargs.get("doctype"),
		"ref_name": kwargs.get("docname"),
		"is_xml_esc_pos": action.is_xml_esc_pos,
		"is_raw_text": action.is_raw_text,
		"print_job_name": action.action,
		"copies": print_settings.get('copies', 1),
		"job_owner": frappe.local.session.user,
		"print_timestamp": now_datetime()
	})
	job.flags.ignore_permissions = True
	job.flags.ignore_links = True
	job.flags.ignore_validate = True
	job.insert()

@frappe.whitelist()
def batch_print_via_printnode(action, docs):
	if isinstance(docs, string_types):
		docs = json.loads(docs)

	for doc in docs:
		print_via_printnode(action, **doc)

@frappe.whitelist()
def get_action_list(dt):
	return frappe.get_all('Print Node Action', 
		fields=["name", "action", "printable_type", "attachment_pattern", "depends_on", "allow_inline_batch", "batch_field", "hotkey"],
		filters={'dt': dt},
		order_by= 'idx ASC',
		limit_page_length=50
	)
