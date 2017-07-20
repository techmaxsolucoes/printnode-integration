// Copyright (c) 2016, MaxMorais and contributors
// For license information, please see license.txt

frappe.ui.form.on('Print Node Settings', {
	onload: function(frm){
		frm.set_query("dt", "actions", function(){
			return {
				filters: {
					"istable": 0,
					"issingle": 0,
					"module": ["!=", "Core"],
				}
			}
		});
		frm.set_query("print_format", "actions", function(doc, cdt, cdn){
			var d = locals[cdt][cdn];
			return {
				filters: {
					"doc_type": d.dt
				}
			}
		});
		frm.set_query("hardware", "actions", function(){
			return {
				filters: {
					"hw_type": "Printer"
				}
			}
		});
	},
	refresh: function(frm) {
		var icons = {
			"Online": '<i class="octicon octicon-issue-closed text-success"></i>',
			"Disconnected": '<i class="octicon octicon-issue text-danger"></i>',
			"Created": '<i class="octicon octicon-issue text-danger"></i>',
			"Printer": '<i class="icon icon-print"></i>',
			"Computer": '<i class="octicon octicon-device-desktop"></i>',
			"Scale": '<i class="octicon octicon-dashboard"></i>'
		}
		,template = '<table class="table table-condensed table-bordered">\
	<thead>\
		<tr class="text-center">\
		<th>&nbsp;</th>\
		<th>{{ __("Name") }}</th>\
		<th>{{ __("Computer") }}</th>\
		<th>{{ __("Device") }}</th>\
		<th>{{ __("Status") }}</th>\
		</tr>\
	</thead>\
	<tbody>\
		{% for (var i in rows) { %}\
		<tr>\
		{% var row = rows[i]; %}\
		<th class="text-right">{{ parseInt(i)+1 }}</th>\
		<td>{{ row.hw_name }}</td>\
		<td>{{ row.computer }}</td>\
		<td class="text-center">{{ icons[row.hw_type] }}</td>\
		<td class="text-center">{{ icons[row.status] }}</td>\
		</tr>\
		{% } %}\
	</tbody>\
</table>';
		frm.fields_dict.hardware_html.$wrapper.empty();
		if (frm.doc.hardware && frm.doc.hardware.length){
			$(frappe.render(template, {
				rows: JSON.parse(frm.doc.hardware),
				icons: icons
			})).appendTo(frm.fields_dict.hardware_html.$wrapper);
		}
	}
});

frappe.ui.form.on("Print Node Action", "printable_type", function(frm, cdt, cdn){
	var d = locals[cdt][cdn];
	cur_frm.set_df_property("print_format", "reqd", doc.printable_type === "Print Format", d.parentfield, cdn);
	cur_frm.set_df_property("print_format", "reqd", doc.printable_type === "Attachment", d.parentfield, cdn);
});

frappe.ui.form.on("Print Node Action", "is_xml_escpos", function(frm, cdt, cdn){
    var d = locals[cdt][cdn];
    if (d.is_raw_text && d.is_xml_escpos) frappe.model.set_value( d.doctype, d.name, 'is_raw_text', !d.is_xml_escpos );
});

frappe.ui.form.on("Print Node Action", "is_raw_text", function(frm, cdt, cdn){
    var d = locals[cdt][cdn];
    if (d.is_xml_escpos && d.is_raw_text) frappe.model.set_value( d.doctype, d.name, 'is_xml_escpos', !d.is_raw_text );
});

frappe.ui.form.on("Print Node Action", "set_print_job_options", function(frm, cdt, cdn){
	var d = locals[cdt][cdn],
	    capabilities = d.capabilities ? JSON.parse(d.capabilities) : {};
		fields = [
		{"fieldtype": "Section Break", "label": __("Print Job Options")},
		{"fieldtype": "Int", "label": ("Copies"), "fieldname": "copies", "default": capabilities.copies, "reqd": 1},
		{"fieldtype": "Select", "label": ("Rotate"), "fieldname": "rotate", "options": [
			null, "90", "180", "120" 
		], "default": capabilities.rotate},
		{"fieldtype": "Data", "label": __("Pages"), "fieldname": "pages", "description": __(
			"A set of pages to print from a PDF. A few quick examples <br>E.g. 1,3 prints pages 1 and 3. <br>-5 prints pages 1 through 5 inclusive. <br>- prints all pages. <br>Different components can be combined with a comma. <br>1,3- prints all pages except page 2."), "default": capabilities.default},
		{"fieldtype": "Column Break"},
		{"fieldtype": "Check", "label": __("Collate"), "fieldname": "collate", "default": capabilities.collate},
		{"fieldtype": "Select", "label": __("Duplex"), "fieldname": "dupplex", "options": [
			null,
			{"label": __("Long Edge"), "value": "long-edge"},
			{"label": __("Short Edge"), "value": "short-edge"}
		], "default": capabilities.dupplex}];

	frappe.prompt(
		fields,
		function(args){
			frappe.model.set_value(
				d.doctype,
				d.name,
				"capabilities",
				JSON.stringify(args)
			);
		},
		__("Print Job Capabilities for {0}", [d.printer]),
		__("Set")
	);
});
