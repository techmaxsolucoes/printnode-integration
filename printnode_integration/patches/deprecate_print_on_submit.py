#-*- coding: utf-8 -*-

from __future__ import unicode_literals

import frappe

def execute():
    frappe.db.sql('UPDATE `tabPrint Node Action` SET `print_on` = "Submit" WHERE `print_on_submit`=1;')
    frappe.db.commit()