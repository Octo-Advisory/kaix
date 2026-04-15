import frappe
import os
import traceback
from frontend_app.Ai_module.Feasibility_study.feasibility_study import query_classification
from frappe.utils import now_datetime
import time

def resolve_full_file_path(relative_path):
    """Convert /files/xyz.pdf to actual filesystem path"""
    if relative_path.startswith("/files/"):
        relative_path = relative_path.replace("/files/", "")
    full_path = os.path.join(frappe.utils.get_site_path(), "public", "files", relative_path)
    
    if not os.path.exists(full_path):
        frappe.log_error(f"Resolved path {full_path} does not exist", "File Path Error")
        raise FileNotFoundError(f"File not found at path: {full_path}")
    
    return full_path

@frappe.whitelist()
def feasibility_method_call(file_path): 
    user = frappe.session.user
    frappe.log_error("user",user)
    full_path = resolve_full_file_path(file_path)
    frappe.log_error("full_path",full_path)
    doc = frappe.get_doc({
        "doctype": "Feasibility Report",
        "user": user,
        "status": "Processing",
        "file_path" : full_path,
        "timestamp": now_datetime()
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    frappe.log_error("doc is",doc)
    frappe.enqueue(
        run_feasibility_analysis,
        queue='long',
        timeout=900,
        file_path=full_path,
        result_docname=doc.name,
        user=user
    )

    return {"status": "queued", "message": "Analysis started."}

# def run_feasibility_analysis(file_path, result_docname, user):
#     try:
#         frappe.log_error("come here with",file_path)
#         from frontend_app.Ai_module.Feasibility_study.feasibility_study import query_classification
#         result = query_classification(file_path)
#         doc = frappe.get_doc("Feasibility Report", result_docname)
#         doc.status = "Complete"
#         doc.result_data = frappe.as_json(result)
#         if result.get("feasibility_title"):
#             doc.feasibility_title = result["feasibility_title"]
#         doc.save(ignore_permissions=True)
#         frappe.db.commit()
#         frappe.publish_realtime(
#             event="feasibility_analysis_done",
#             message={"status": "done","docname" : doc.name},
#             user=user,
#         )

#     except Exception as e:
#         frappe.log_error("Feasibility Job Error",frappe.get_traceback())
#         doc = frappe.get_doc("Feasibility Report", result_docname)
#         doc.status = "Fail"
#         doc.feasibility_title = "Processing Error" #added By Jenith on 6/8/25
#         doc.result_data = frappe.as_json({"error": str(e)})
#         doc.save(ignore_permissions=True)
#         frappe.db.commit()
#         frappe.publish_realtime(
#             event="feasibility_analysis_done",
#             message={"status": "error", "message": str(e)},
#             user=user
#         )

def run_feasibility_analysis(file_path, result_docname, user):
    try:
        frappe.log_error("come here with", file_path)

        from frontend_app.Ai_module.Feasibility_study.feasibility_study import query_classification
        result = query_classification(file_path=file_path, feasibility_id=result_docname, vector_id_field="custom_feasibility_vector_file_name", data_source_field="file_path")

        with open("/home/mars/frappe-bench/apps/frontend_app/frontend_app/Ai_module/Feasibility_study/testlog.txt", "a") as file:
            file.write(f"\nresult:- \n{result}")

        # -----------------------------------------
        # ALWAYS RELOAD FIRST
        # -----------------------------------------
        doc = frappe.get_doc("Feasibility Report", result_docname)
        doc.reload()

        # -----------------------------------------
        # MODIFY AFTER RELOAD
        # -----------------------------------------
        doc.status = "Complete"
        doc.result_data = frappe.as_json(result)

        if result.get("feasibility_title"):
            doc.feasibility_title = result["feasibility_title"]

        with open("/home/mars/frappe-bench/apps/frontend_app/frontend_app/Ai_module/Feasibility_study/testlog.txt", "a") as file:
            file.write(f"\nstatus:- {doc.status}\nresult_data:- {doc.result_data}")

        # -----------------------------------------
        # BYPASS TIMESTAMP CHECK
        # -----------------------------------------
        doc.flags.ignore_version = True
        doc.save(ignore_permissions=True)

        frappe.publish_realtime(
            event="feasibility_analysis_done",
            message={"status": "done", "docname": doc.name},
            user=user,
        )

    except Exception as e:
        frappe.log_error("Feasibility Job Error", frappe.get_traceback())

        # Reload before modifying in exception
        doc = frappe.get_doc("Feasibility Report", result_docname)
        doc.reload()

        doc.status = "Fail"
        doc.feasibility_title = "Processing Error"
        doc.result_data = frappe.as_json({"error": str(e)})

        doc.flags.ignore_version = True
        doc.save(ignore_permissions=True)

        frappe.publish_realtime(
            event="feasibility_analysis_done",
            message={"status": "error", "message": str(e)},
            user=user,
        )

# @frappe.whitelist()
# def get_latest_feasibility_result():
#     user = frappe.session.user
#     result = frappe.get_all(
#         "Feasibility Result",
#         filters={"user": user},
#         fields=["name", "status", "result_json", "viewed"],
#         order_by="timestamp desc",
#         limit=1
#     )
#     if result:
#         return {"exists": True, **result[0]}
#     return {"exists": False}
