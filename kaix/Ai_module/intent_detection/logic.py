import json
import re
import frappe
from typing import Any
from langchain.prompts import PromptTemplate
from kaix.Ai_module.intent_detection.prompts import MODULE_SWITCH_PROMPT, INDUSTRY_SCOPE_GUARD_PROMPT

def update_user_intension(user_intension,chatId):
    query = "UPDATE `tabSession` SET user_intension = %s WHERE name = %s"
    frappe.db.sql(query, (user_intension, chatId))
    frappe.db.commit() 

def detect_module_switch_intent(
    user_query: str,
    current_modules: list,
    llm: Any,
    chat_history: list,
) -> dict:
    """
    Detects whether the user is attempting to switch from the current module(s) to a different one,
    based on recent conversation history and the latest user query.

    Parameters:
    -----------
    user_query : str
        The latest message from the user.

    current_modules : list
        A list of currently active modules. Example:
        ["Query to search Incentives"], or
        ["Query to search Incentives", "Query to Get Approvals"]
    
    chat_history : list
    A list of Message objects (HumanMessage or AIMessage), from which last few turns will be extracted.

    llm : Any
        The language model to be used (e.g., LLMChain, LangChain-compatible model).

    Returns:
    --------
    dict
        A JSON object with the key "switch_module" and a boolean value:
        {
            "switch_module": true or false
        }

    Notes:
    ------
    - This function does not classify the destination module; it only detects if the user
      wants to exit the current modules based on a shift in intent.
    """

    Chat_history_normal = "\n".join(chat_history)

    prompt_template = MODULE_SWITCH_PROMPT

    prompt = PromptTemplate(
        input_variables=["current_modules", "chat_history", "user_query"],
        template=prompt_template
    )

    chain = prompt | llm
    result = chain.invoke({
        "current_modules": str(current_modules),
        "chat_history": Chat_history_normal,
        "user_query": user_query
    })

    response = result.content.strip().lower()
    with open("testlog.txt", "a") as file:
        file.write(f"\n%%%%%%%% I am inside the module change dection: {response} ====> {result}")
    switch_flag = response == "true"

    return {
        "switch_module": switch_flag
    }

def check_industry_scope_with_feasibility(
    latest_query: str,
    feasibility_structured_summary: dict,
    llm,
    chat_history: list[str] | None = None,
):
    """
    Runs *before* any other routing. Uses an LLM to decide if the latest query
    belongs to the same MAIN INDUSTRY as the feasibility context.

    Returns a minimal dict:
      {
        "redirect": bool,          # True => UI should redirect to new chat
        "reason": str,             # one of: "industry_changed", "small_talk", "within_industry", "insufficient_signal", "vendors_cross_industry_ok", "raw_material_unrelated"
        "confidence": float        # 0.0 - 1.0
      }

    Behavior highlights:
    - If SMALL-TALK/GREETING or query lacks industry/product context => allow flow (redirect=False).
    - If feasibility JSON is missing main_industry/sub-sector/product (any or all):
        - Try to infer MAIN INDUSTRY from whatever is present (product or sub-sector).
        - If inference is uncertain => allow flow (no redirect).
    - If user clearly switches MAIN INDUSTRY => redirect=True (reason="industry_changed").
    - Vendor/raw-material/equipment queries: allow flow even if cross-industry is plausible,
      unless the raw material is *clearly* 100% unrelated to the feasibility main industry
      (then redirect=True, reason="raw_material_unrelated").
    """
    

    # Prepare feasibility context safely (at least one of "product", "sub-sector", "main_industry" may exist)
    fea = feasibility_structured_summary.get('structured_summary', {})
    fco_min = {
        "main_industry": fea.get("main_industry"),          # may be None
        "sub_sector": fea.get("sub-sector"),                # may be None
        "product": fea.get("product"),                      # may be None
        # Optional extras that can help the model reason (don’t *depend* on them)
        "location": fea.get("Location"),
        "final_product_capacity": fea.get("final_product_capacity"),
        "supplies": fea.get("supplies"),
        "equipments": fea.get("equipments"),
    }

    # Compact history (optional)
    history_text = "\n".join(chat_history or [])

    system_prompt = INDUSTRY_SCOPE_GUARD_PROMPT
    
    user_payload = {
        "latest_query": latest_query,
        "feasibility_context": fco_min,
        "chat_history_excerpt": history_text[-4000:] if history_text else ""  # keep prompt tight
    }

    # Call LLM
    resp = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
    ])

    text = resp.content if hasattr(resp, "content") else str(resp)

    # Try to parse strict JSON
    try:
        gate = json.loads(text)
    except Exception:
        # Lenient fallback: attempt to extract JSON object
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                gate = json.loads(m.group(0))
            except Exception:
                gate = {"redirect": False, "reason": "insufficient_signal", "confidence": 0.25}
        else:
            gate = {"redirect": False, "reason": "insufficient_signal", "confidence": 0.25}

    # Normalize + conservative exposure of industry strings
    redirect = bool(gate.get("redirect", False))
    reason = str(gate.get("reason", "insufficient_signal"))
    confidence = float(gate.get("confidence", 0.0))
    expected_industry = gate.get("expected_industry")
    detected_industry = gate.get("detected_industry")

    if confidence < 0.60:
        expected_industry = None
        detected_industry = None

    # --- Compose confirmation message & options (only when redirecting) ---
    if redirect:
        exp = expected_industry or "the industry in your feasibility study"
        det = detected_industry or "a different industry"
        confirmation_message_static = (
            "This chat thread is specifically connected to the industry given in your feasibility study "
            f"(**{exp}**). Your latest query appears to be about **{det}**. "
            "For a better experience, we recommend starting a new chat with your latest query. "
            "If you press **Yes**, we'll redirect you to a new chat thread; if you press **No**, you can "
            f"continue here regarding **{exp}**. Please choose from the options below."
        )
        confirmation_message_options = [
            {"label": "Yes, start new chat", "value": "RedirectToNewChat"},
            {"label": "No, stay here", "value": "StayInCurrentChat"}
        ]
        is_confirmation = True
        ai_response = confirmation_message_static
        options = confirmation_message_options
        fallback =  f"Okay — we’ll continue in this chat for **{exp}** (the industry from your feasibility study) and proceed with your latest query here."
    else:
        # Let normal flow decide message & UI; keep clean
        ai_response = None
        is_confirmation = None
        options = None
        fallback = None

    # --- Final response JSON (compatible + extended) ---
    response = {
        "Ai_response": ai_response,
        "Is_confirmation": is_confirmation,
        "options": options, 
        "Trigger_Lead_Generation": False,

        # existing routing/telemetry flags
        "RedirectRequired": redirect,
        "RedirectReason": reason,
        "on_stay_fallback_message": fallback,
        "Confidence": confidence,
        "UserQuery": latest_query,
        "ExpectedIndustry": expected_industry,
        "DetectedIndustry": detected_industry,
        "UsedFeasibilityDefaults": []
    }
    return response