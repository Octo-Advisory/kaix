import frappe
from frontend_app.Ai_module.build_from_scratch.Extraction_for_Building_from_Scratch import entry_build_from_scratch

@frappe.whitelist(allow_guest=True)
def build_from_scratch(input):
    frappe.log_error(f"input from frontend {input}")
    k = entry_build_from_scratch(input)
    return k