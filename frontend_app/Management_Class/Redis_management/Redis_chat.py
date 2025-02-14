import json
import frappe
import pickle

def save_chat(chat_history,chatId):
    frappe.cache.set(chatId, pickle.dumps(chat_history),ex=600)

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
    
def save_state(state,stateId):
    frappe.cache.set(stateId,json.dumps(state),ex=600)

def delete_state(key):
    frappe.log_error(f"come here with key {key}")
    frappe.cache.delete(key)
    return key

def get_state(key):
    # Fetch the cached value
    cached_value = frappe.cache.get(key)
    if cached_value:
        return json.loads(cached_value.decode("utf-8"))  # Decode bytes and parse JSON
    return None