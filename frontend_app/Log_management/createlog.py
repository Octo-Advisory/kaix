import frappe
from datetime import datetime
import configparser
import os
import json

# config_file = '/home/mars/frappe-bench/apps/frontend_app/frontend_app/Log_management/mars.ini'
base_dir = os.path.expanduser("~")
config_file = os.path.join(base_dir, "frappe-bench/apps/frontend_app/frontend_app/Log_management/mars.ini")
config = configparser.ConfigParser()
config.read(config_file)

@frappe.whitelist(allow_guest=True)
def log(chatId, level, key, value, file_name, module: str):
    # Define mapping of modules to their respective log tables and fields
    # frappe.log_error(f"jkdwn {config['Settings']['doc_log']}{config['Settings']['file_log'] }")
    if config['Settings']['doc_log'] == 'yes':
        log_module = {
            "ai": {"table": "Ai Log", "field": "ai_log"},
            "analytics": {"table": "Analytics Log", "field": "analytics_log"},
            "mapping": {"table": "Mapping Log", "field": "mapping_log"},
            "validation": {"table": "Validation Log", "field": "validation_log"},
        }

        if module not in log_module:
            frappe.throw(f"Invalid module: {module}")

        log_table = log_module[module]["table"]
        parent_field = log_module[module]["field"]

        # Check if a log record with the given chat_id exists
        log_doc_name = frappe.get_value("Mars Log", {"chat_id": chatId}, "name")
        
        if not log_doc_name:
            # Create a new log record if not exists
            mars_log_doc = frappe.get_doc({
                "doctype": "Mars Log",
                "chat_id": chatId,
            })
            mars_log_doc.insert()
            frappe.db.commit()
            log_doc_name = mars_log_doc.name  # Get the newly created document's name
        
        # Insert log entry into the corresponding log table dynamically
        log_entry = frappe.get_doc({
            "doctype": log_table,
            "parent": log_doc_name,
            "parentfield": parent_field,
            "parenttype": "Mars Log",
            "time_stamp": datetime.now(),
            "log_level": level,
            "key": key,
            "value": value,
            "file_name": file_name
        })
        log_entry.insert(ignore_permissions=True)  # Ensure it bypasses permission checks

        frappe.db.commit()
    if config['Settings']['file_log'] == 'yes':
            log_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                f"{key}" : value
            }
            # config_file = os.path.join(
            #     base_dir,
            #     "frappe-bench/apps/frontend_app/frontend_app/Log_management",
            #     f"{module}.txt"
            # )
            # with open(config_file, "a", encoding="utf-8") as file:
            #     file.write(json.dumps(log_entry) + "\n")
            log_dir = "/mnt/d/mars_logs"

            os.makedirs(log_dir, exist_ok=True)

            log_file = os.path.join(log_dir, f"{module}.txt")

            with open(log_file, "a", encoding="utf-8") as file:
                file.write(json.dumps(log_entry) + "\n")


@frappe.whitelist(allow_guest=True)
def update_config(doc_log,file_log):
    base_dir = os.path.expanduser("~")
    config_file = os.path.join(base_dir, "frappe-bench/apps/frontend_app/frontend_app/Log_management/mars.ini")
    # config_file = '/home/mars/frappe-bench/apps/frontend_app/frontend_app/Log_management/mars.ini'
    config = configparser.ConfigParser()

    # Ensure the directory exists
    os.makedirs(os.path.dirname(config_file), exist_ok=True)

    # Read the existing config if it exists
    if os.path.exists(config_file):
        config.read(config_file)

     # Update or add new configurations
    if 'Settings' not in config:
        config['Settings'] = {}

    config['Settings']['doc_log'] = doc_log
    config['Settings']['file_log'] = file_log

    # Save changes to the file
    with open(config_file, 'w') as configfile:
        config.write(configfile)

    return True
 