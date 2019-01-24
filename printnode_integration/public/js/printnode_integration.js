frappe.provide('printnode_integration');

printnode_integration.evaluate_depends_on = function(expression, doc){
	var out = null;
	if (expression.substr(0,5) === "eval:"){
		out = new Function('doc', format('try {return {0} } catch(e){ return false; }', [
		expression.substr(5)
		]))(doc.doc);
	} else if (expression.substr(0,3) === "fn:"){
		out = cur_frm.script_manager.trigger(
		expression.substr(3),
		cur_frm.doctype,
		cur_frm.docname
		);
	} else {
		var value = doc[expression];
		if (Array.isArray(value)){
		out = !!value.length;
		} else {
		out = !!value;
		}
	}
	return out;
};

frappe.ui.form.ScriptManager = frappe.ui.form.ScriptManager.extend({
	get_handlers: function(event_name, doctype, name, callback){
		var handlers = this._super(event_name, doctype, name, callback),
			me = this;

		function print_attachment(row){
			var attachments = cur_frm.get_docinfo().attachments.filter(function(row){
				if (!row.attachment_pattern){
					return true;
				}
				return printnode_integration.evaluate_depends_on(row.attachment_pattern, {
					doc: row
				});
			}),
				options = [null];
			if (attachments && attachments.length){
				for (var i in attachments){
				options.push({
					'label': attachments[i].file_name,
					'value': attachments[i].name
				});
				}
				frappe.prompt([{
					fieldname: "attachment",
					fieldtype: "Select",
					label: __("Attachment"),
					options: options,
					reqd: options,
						"default": options[1].value
					}], function(args){
					frappe.call({
						"method": "printnode_integration.api.print_via_printnode",
						"freeze": true,
						"freeze_message": __("Sending attachment to the printer"),
						"args": {
						    "action": row.name,
							"filename": args.attachment,
							"doctype": cur_frm.doctype,
							"docname": cur_frm.docname
						}
					});
				}, __("Select an Attachment"), __("Print"))
			}
			}

		if (event_name === "refresh" && cur_frm){
			(handlers.new_style || handlers).push(
				function(){
					frappe.call({
						"method": "printnode_integration.api.get_action_list",
						"args": {
							"dt": cur_frm.doctype,
							"is_batch": 0
						},
						"callback": function(res){
							if (res && res.message && res.message.length){
								res.message.forEach(function(row){
									if ((row.depends_on && row.depends_on.length) && !printnode_integration.evaluate_depends_on(row.depends_on, {"doc": cur_frm.doc})){
										return;
									}
									function handler(){
										if (row.printable_type == "Print Format"){
											if (!row.allow_inline_batch){
												frappe.call({
													"method": "printnode_integration.api.print_via_printnode",
													"freeze": true,
													"freeze_message": __("Sending document to the printer"),
													"args": {
														"action": row.name,
														"doctype": cur_frm.doctype,
														"docname": cur_frm.docname
													}

												});
											} else {
												if (row.batch_field.indexOf('.') >= 0){
													var table_field = row.batch_field.split(".")[0];
													var reference_list = cur_frm.doc[table_field];
												} else {
													var reference_list = [cur_frm.doc];
												}
												var inline_field = row.batch_field.split(".");
												inline_field = inline_field.pop();
												debugger;
												frappe.call({
													'method': 'printnode_integration.api.batch_print_via_printnode',
													'freeze': true,
													'freeze_message': __('Sending documents to the printer'),
													'args': {
														'action': row.name,
														'docs': reference_list.map((d) => { return {'docname': d[inline_field]}; })
													}
												});
											}
										} else {
											print_attachment(row);
										}
									};
									let btn = cur_frm.add_custom_button(row.action, handler, __('Print Node Integration'));
									if (row.hotkey && row.hotkey.length){
										frappe.ui.keys.on(row.hotkey, function(){
											handler();
										});
									}
								});
							}
						}
					});
				}
			);
		}
		return handlers;
	}
});


frappe.views.ListView = class ListView extends frappe.views.ListView {
	make_bulk_printing() {
		super.make_bulk_printing();
		var me = this,
			print_settings = frappe.model.get_doc(':Print Settings', 'Print Settings'),
			allow_print_for_draft = cint(print_settings.allow_print_for_draft),
			is_submittable = frappe.model.is_submittable(me.doctype),
			allow_print_for_cancelled = cint(print_settings.allow_print_for_cancelled),
			actions = [null];

		// get all actions
		frappe.call({
			'method': 'printnode_integration.api.get_action_list',
			'args': {
				'dt': me.doctype
			},
			'callback': function(res){
				if (res && res.message){
					res.message.forEach(function(action){
						action.push({'label': action.action, 'value': action.name});
					});
				}
			}
		});

		// bulk printing
		me.page.add_menu_item(__('Print via Print Node'), function(){
			var items = me.get_checked_items(),
				valid_docs = items.filter(function(doc){
					return !is_submittable || doc.docstatus === 1 || 
						(allow_print_for_cancelled && doc.docstatus == 2) ||
						(allow_print_for_draft && doc.docstatu == 0) ||
						frappe.user_roles.includes('Administrator');
				}).map(function(doc){
					return {'doctype': me.doctype, 'docname': doc.name}
				}),
				invalid_docs = items.filter(function(doc){
					return !valid_docs.includes({'doctype': me.doctype, 'docname': doc.name});
				});

				if (invalid_docs.length >= 1){
					frappe.msgprint(__('You selected Draft of Cancelled documents'));
					return;
				}

				if (valid_docs.length >= 1){
					var dialog = new frappe.ui.Dialog({
						title: __("Print Documents via Print Node"),
						fields: [
							{'fieldtype': 'Select', 'label': __('Action'), 'fieldname': 'action', 'reqd': 1, 'options': actions},
						]
					});

					dialog.set_primary_action(__('Print via Print Node'), function(){
						var args = dialog.get_values();
						if (!args) return;
						dialog.hide();
						frappe.call({
							'method': 'printnode_integration.api.batch_print_via_printnode',
							'args': {
								'action': args.action,
								'docs': valid_docs
							},
							'freeze': true,
							'freeze_message': format(__('Sending {0} documents to the printer'), [valid_docs.length]),
						});
					});
				}
		}, true);
	}
}
