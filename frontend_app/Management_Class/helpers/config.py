import os
import frappe
import configparser

config_file = '/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Log_management/mars.ini'
config = configparser.ConfigParser()
config.read(config_file)

@frappe.whitelist(allow_guest=True)
def update_config(doc):
    config_file = '/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Log_management/mars.ini'
    config = configparser.ConfigParser()

    # Ensure the directory exists
    os.makedirs(os.path.dirname(config_file), exist_ok=True)

    # Read the existing config if it exists
    if os.path.exists(config_file):
        config.read(config_file)

     # Update or add new configurations
    if 'Settings' not in config:
        config['Settings'] = {}
    
    doc_log = doc.doc_log
    file_log = doc.file_log
    key = doc.groq_key

    config['Settings']['doc_log'] = doc_log
    config['Settings']['file_log'] = file_log
    config['Key']['groq_key'] = key

    # Save changes to the file
    with open(config_file, 'w') as configfile:
        config.write(configfile)

    return True