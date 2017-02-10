frappe.ui.form.ScriptManager = frappe.ui.form.ScriptManager.extend({
	get_handlers: function(event_name, doctype, name, callback){
		var handlers = this._super(event_name, doctype, name, callback),
			me = this;
		
		function evaluate_depends_on(expression, doc){
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

		function print_attachment(row){
			var attachments = cur_frm.get_docinfo().attachments.filter(function(row){
				if (!row.attachment_pattern){
					return true;
				}
				return evaluate_depends_on(row.attachment_pattern, {
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
						"args": {
						"action": row.name,
						"filename": args.attachment
						}
					});
				}, __("Select an Attachment"), __("Print"))
			}
			}

		if (event_name === "refresh" && cur_frm){
			handlers.push(
				function(){
					frappe.call({
						"method": "frappe.client.get_list",
						"args": {
							"doctype": "Print Node Action",
							"filters": {
								"dt": cur_frm.doctype,
							},
							"fields": ["name", "action", "printable_type", "attachment_pattern", "depends_on"],
							"order_by": "idx ASC"
						},
						"callback": function(res){
							if (res && res.message && res.message.length){
								var row;
								for (var i in res.message){
									row = res.message[i];
									debugger;
									if ((row.depends_on && row.depends_on.length) && !evaluate_depends_on(row.depends_on, {"doc": cur_frm.doc})){
										continue;
									}
									cur_frm.add_custom_button(row.action, function(){
										if (row.printable_type == "Print Format"){
											frappe.call({
												"method": "printnode_integration.api.print_via_printnode",
												"args": {
													"action": row.action,
													"doctype": cur_frm.doctype,
													"docname": cur_frm.docname
												}
											});
										} else {
											print_attachment(row);
										}
									}, __('Print Node Integration'))
								}
							}
						}
					});
				}
			);
		}
		return handlers;
	}
});
