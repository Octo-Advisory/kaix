import json
import frappe
import pickle

def save_chat(chat_history):
    # redis_conn = frappe.cache().client
    frappe.cache.set("chat_history", pickle.dumps(chat_history))

def delete_chat(key):
    frappe.cache.delete("chat_history")

def get_chat(key):
    # Fetch the cached value
    cached_value = frappe.cache.get(key)

    if cached_value:
        # Deserialize the cached value
        try:
            original_value = pickle.loads(cached_value)
            return original_value
        except Exception as e:
            # Handle potential deserialization errors
            frappe.log_error(f"Error deserializing cached value for key {key}: {e}")
            return None
    else:
        return None
