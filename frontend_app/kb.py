import frappe

@frappe.whitelist(allow_guest=True)
def krunal(a, b):
    try:
        sum = int(a) * int(b)
        return {"message": sum}
    except Exception as e:
        return {"message": e}
