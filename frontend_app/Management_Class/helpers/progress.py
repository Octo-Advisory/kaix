# import frappe
# import logging

# # Set up logging configuration
# logging.basicConfig(level=logging.INFO)

# @frappe.whitelist()
# def insert_process(parentId, process_name, process_value, status):
#     try:
#         # Generate a unique name for the child table row
#         child_name = frappe.generate_hash("tabProgress", 10)

#         # Dynamically calculate the next idx for the child row
#         next_idx = frappe.db.sql("""
#             SELECT COALESCE(MAX(idx), 0) + 1 
#             FROM `tabProgress` 
#             WHERE parent = %s AND parentfield = %s
#         """, (parentId, 'progress'))[0][0]

#         # Insert the new row with dynamic values
#         query = f"""
#             INSERT INTO `tabProgress`
#             (name, parent, parentfield, parenttype, process_name, process_value, status, creation, modified, idx)
#             VALUES ('{child_name}', '{parentId}', 'progress', 'Session', '{process_name}', '{process_value}', '{status}', NOW(), NOW(), {next_idx})
#         """

#         # Execute the SQL query
#         frappe.db.sql(query)

#         # Commit the transaction
#         frappe.db.commit()
#          # Publish real-time event
#         # frappe.publish_realtime("progress_update", {"parentId": "nruabe8kjh" })
#         # frappe.log_error(f"Real-time event emitted: parentId=nruabe8kjh")
#         # frappe.log_error("Insert Process done")
#     except Exception as e:
#         frappe.log_error(f"Error is {e}")
#         logging.error(f"Error is {e}")


# @frappe.whitelist()
# def update_process(parentId, process_name, new_status):
#     try:
#         # Construct the SQL query to update the process value and status
#         query = f"""
#             UPDATE `tabProgress`
#             SET status = '{new_status}', modified = NOW()
#             WHERE parent = '{parentId}' AND parentfield = 'progress' AND process_name = '{process_name}'
#         """

#         # Execute the query
#         frappe.db.sql(query)

#         # Commit the transaction
#         frappe.db.commit()
#         # frappe.publish_realtime("progress_update", {"parentId": "nruabe8kjh" })
#         # frappe.log_error("Process update successful.")
#     except Exception as e:
#         frappe.log_error(f"Error updating process: {e}")
#         logging.error(f"Error updating process: {e}")
import frappe

@frappe.whitelist(allow_guest=True)
def insert_process(parentId, process_name, process_value, status):
    try:
        # Create a new child table row using Frappe ORM
        child_row = frappe.get_doc({
            "doctype": "Progress",
            "parent": parentId,
            "parentfield": "progress",
            "parenttype": "Session",
            "process_name": process_name,
            "process_value": process_value,
            "status": status
        })

        # Save the new row to the database
        child_row.insert(ignore_permissions=True)

        # frappe.publish_realtime(
        #     event="progress_update",
        #     message={"parentId": parentId, "process_name": process_name, "new_status": status},
        #     doctype="Session",
        #     user=frappe.session.user if frappe.session.user != "Guest" else "Guest" 
        # )
        # frappe.log_error(f"event is pulished with {parentId}{process_name}")
        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Error inserting process: {e}")


@frappe.whitelist(allow_guest=True)
def update_process(parentId, process_name, new_status):
    try:
        # Find the child row using Frappe ORM
        child_row = frappe.get_list(
            "Progress",
            filters={
                "parent": parentId,
                "parentfield": "progress",
                "process_name": process_name
            },
            fields=["name"],
            ignore_permissions=True
        )

        if not child_row:
            return

        # Get the specific row document
        row_doc = frappe.get_doc("Progress", child_row[0]["name"])

        # Update the status and save the document
        row_doc.status = new_status
        row_doc.save(ignore_permissions=True)

        frappe.publish_realtime(
            event="progress_update",
            message={"parentId": parentId, "process_name": process_name, "status": new_status},
            doctype="Session",
            user=frappe.session.user if frappe.session.user != "Guest" else "Guest"
        )
        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Error updating process: {e}")