import frappe
import time

def test1(doc, method):
    frappe.log_error("validate", f"after_save triggered for {doc.name}")

def test2(doc, method):
    frappe.log_error("on_update", f"on_update triggered for {doc.name}")

def test3(doc, method):
    frappe.log_error("on_change", f"on_change triggered for {doc.name}")

@frappe.whitelist(allow_guest=True)
def update_me():
    try:
        doc = frappe.get_doc("Mars Config", "Deepseek")  # Fetch the document
        doc.input_token = 1900  # Update the value
        doc.save()  # Save the document (triggers on_update, on_change, validate)
        frappe.db.commit()  # Ensure changes are committed
        return 'Done'
    except Exception as e:
        frappe.log_error(f"Error in update_me: {str(e)}", "Update Function Error")
        return f"Failed: {str(e)}"