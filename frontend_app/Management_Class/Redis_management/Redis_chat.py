# import json
# import frappe
# import pickle

# def save_chat(chat_history,chatId):
#     frappe.cache.set(chatId, pickle.dumps(chat_history),ex=1200)

# def delete_chat(key):
#     frappe.cache.delete(key)

# def get_chat(key):
#     # Fetch the cached value
#     cached_value = frappe.cache.get(key)

#     if cached_value:
#         # Deserialize the cached value
#         try:
#             original_value = pickle.loads(cached_value)
#             return original_value
#         except Exception as e:
#             # Handle potential deserialization errors
#             return None
#     else:
#         return None
   
# def save_state(state,stateId):
#     frappe.cache.set(stateId,json.dumps(state),ex=1200)

# def delete_state(key):
#     frappe.log_error(f"come here with key {key}")
#     frappe.cache.delete(key)
#     return key

# def get_state(key):
#     # Fetch the cached value
#     cached_value = frappe.cache.get(key)
#     if cached_value:
#         return json.loads(cached_value.decode("utf-8"))  # Decode bytes and parse JSON
#     return None

import json
import frappe


# Extract the actual Session ID from the key
def _extract_session_id(key, marker):
    parts = key.split(marker)
    if len(parts) != 2:
        raise ValueError(f"Invalid key format: {key}")
    return parts[1]

# Save chat to Session Original Method
# def save_chat(chat_history, key):
#     from langchain.schema import BaseMessage
#     try:
#         session_id = _extract_session_id(key, "chat_")

#         # Convert only necessary fields
#         chat_json = json.dumps([
#             {"type": msg.type, "content": msg.content}
#             for msg in chat_history if isinstance(msg, BaseMessage)
#         ])

#         with open("log3.txt", "a") as file:
#             file.write(f"\n Details from redis chat {chat_history, key , session_id, chat_json}")
#         frappe.db.set_value("Session", session_id, "chat_json", chat_json)
#         frappe.db.commit()
#     except Exception as e:
#         frappe.log_error(f"Error saving chat for {key}: {e}")

# Save Chat to Session 
def save_chat(chat_history, key):
    import json
    from langchain.schema import BaseMessage

    try:
        frappe.log_error("CHAT_HISTORY_0",f"{chat_history}")
        session_id = _extract_session_id(key, "chat_")

        final_msgs = []
        
        # Find the index of the last human message
        last_human_index = None
        for i in range(len(chat_history) - 1, -1, -1):
            if isinstance(chat_history[i], BaseMessage) and chat_history[i].type == "human":
                last_human_index = i
                break
        
        for idx, msg in enumerate(chat_history):
            if isinstance(msg, BaseMessage):
                msg_dict = {
                    "type": msg.type,
                    "content": msg.content,
                    **(msg.additional_kwargs or {})
                }

                if idx == last_human_index:
                    msg_dict["method_called"] = 0

                final_msgs.append(msg_dict)

        # with open("log3.txt", "a") as file:
        #     file.write(f"\n📨 Final Save New for {session_id}: {json.dumps(final_msgs)}")


        frappe.db.set_value("Session", session_id, "chat_json", json.dumps(final_msgs))
        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"❌ Error saving chat for {key}: {e}")
 
# The below is the original old methoid 
# def get_chat(key):
#     try:
#         from langchain.schema import HumanMessage, AIMessage
#         session_id = _extract_session_id(key, "chat_")
#         raw = frappe.db.get_value("Session", session_id, "chat_json")
#         if not raw:
#             return []

#         msg_map = {"human": HumanMessage, "ai": AIMessage}
#         messages = json.loads(raw)
#         # Debug log
#         with open("log3.txt", "a") as file:
#             file.write(f"\n📨 {session_id } Messages: {json.dumps(raw)}")
#         return [msg_map[m["type"]](content=m["content"]) for m in messages if m["type"] in msg_map]
#     except Exception as e:
#         frappe.log_error(f"Error getting chat for {key}: {str(e)}")
#         return []

def get_chat(key):
                                                                                                                                                                                   
    try:
        from langchain.schema import HumanMessage, AIMessage
        session_id = _extract_session_id(key, "chat_")
        raw = frappe.db.get_value("Session", session_id, "chat_json")
        # with open("log3.txt", "a") as file:
        #     file.write(f"\n📨 Final Save New for NEWWWWWW {raw}")
        if not raw:
            return []

        msg_map = {"human": HumanMessage, "ai": AIMessage}
        messages = json.loads(raw)
        frappe.log_error("MESSAGES",f"{messages}")

        # with open("log3.txt", "a") as file:
        #     file.write(f"\n📨OK OK  {session_id} New Messages (raw): {raw}")

        return [
            msg_map[m["type"]](
                content=m["content"],
                additional_kwargs={k: v for k, v in m.items() if k not in ["type", "content"]}
            )
            for m in messages if m["type"] in msg_map
        ]  # to be reviewed 🙌

    except Exception as e:
        frappe.log_error(f"Error getting chat for {key}: {str(e)}")
        return []

# Get chat from Session
# def get_chat(key):
#     try:
#         session_id = _extract_session_id(key, "chat_")
#         chat_json = frappe.db.get_value("Session", session_id, "chat_json")
#         return json.loads(chat_json) if chat_json else []
#     except Exception as e:
#         frappe.log_error(f"Error getting chat for key {key}: {str(e)}")
#         return []

# Delete chat in Session
def delete_chat(key):
    try:
        session_id = _extract_session_id(key, "chat_")
        frappe.db.set_value("Session", session_id, "chat_json", "")
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Error deleting chat for key {key}: {str(e)}")

# Save state to Session
# def save_state(state, key):
#     try:
#         session_id = _extract_session_id(key, "_state_")
#         state_json = json.dumps(state)
#         frappe.db.set_value("Session", session_id, "state_json", state_json)
#         frappe.db.commit()
#     except Exception as e:
#         frappe.log_error(f"Error saving state for key {key}: {str(e)}")

# Get state from Session
# def get_state(key):
#     try:
#         session_id = _extract_session_id(key, "_state_")
#         state_json = frappe.db.get_value("Session", session_id, "state_json")
#         return json.loads(state_json) if state_json else None
#     except Exception as e:
#         frappe.log_error(f"Error getting state for key {key}: {str(e)}")
#         return None

# # Delete state in Session
# def delete_state(key):
#     try:
#         session_id = _extract_session_id(key, "_state_")
#         frappe.db.set_value("Session", session_id, "state_json", "")
#         frappe.db.commit()
#         return key
#     except Exception as e:
#         frappe.log_error(f"Error deleting state for key {key}: {str(e)}")
#         return None
    
def _get_session_state_record(session_id, key):
    # Try to find existing child row
    children = frappe.get_all(
        "Session State",
        filters={"parent": session_id, "key": key},
        fields=["name"]
    )
    return children[0]["name"] if children else None


def save_state(state, key):
    try:
        session_id = _extract_session_id(key, "_state_")
        state_json = json.dumps(state)

        record_name = _get_session_state_record(session_id, key)

        if record_name:
            frappe.db.set_value("Session State", record_name, "state_json", state_json)
        else:
            frappe.get_doc({
                "doctype": "Session State",
                "parent": session_id,
                "parenttype": "Session",
                "parentfield": "session_states",  # this should match your child table fieldname in the parent Session Doctype
                "key": key,
                "state_json": state_json
            }).insert()

        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Error saving state for key {key}: {str(e)}")

def get_state(key):
    try:
        session_id = _extract_session_id(key, "_state_")
        result = frappe.get_value(
            "Session State",
            {"parent": session_id, "key": key},
            "state_json"
        )
        return json.loads(result) if result else None
    except Exception as e:
        frappe.log_error(f"Error getting state for key {key}: {str(e)}")
        return None

def delete_state(key):
    try:
        session_id = _extract_session_id(key, "_state_")

        name = _get_session_state_record(session_id, key)
        if name:
            frappe.delete_doc("Session State", name)
            frappe.db.commit()
            return key
        return None
    except Exception as e:
        frappe.log_error(f"Error deleting state for key {key}: {str(e)}")
        return None

