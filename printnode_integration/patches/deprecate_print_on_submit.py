#-*- coding: utf-8 -*-

from __future__ import unicode_literals

import frappe

def execute():
    if frappe.db.sql('''
	SELECT * FROM information_schema.COLUMNS 
	WHERE TABLE_SCHEMA=%s
		AND TABLE_NAME="tabPrint Node Action"
		AND COLUMN_NAME = "print_on_submit"''', (frappe.get_conf().db_name,)):
	    frappe.db.sql('UPDATE `tabPrint Node Action` SET `print_on` = "Submit" WHERE `print_on_submit`=1;')
	    frappe.db.commit()
