import json
import frappe
import pickle

def save_chat(chat_history,chatId):
    frappe.cache.set(chatId, pickle.dumps(chat_history))

def delete_chat(key):
    frappe.cache.delete(key)

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
            return None
    else:
        return None
