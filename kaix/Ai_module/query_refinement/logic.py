import frappe
from langchain.prompts import PromptTemplate

from kaix.Ai_module.parsers import parse_llm_response
from kaix.Ai_module.query_refinement.schemas import RefinedQuery
from kaix.Ai_module.query_refinement.prompts import retriever_prompt_template

def refine_query_with_history(
    history, 
    latest_query, 
    llm,
    context_freshness_config=None,
    feasibility_json: dict | None = None,   # NEW (structured_summary object or whole feasibility payload)
    feasibility_mode: bool = False  
):
    """                      
    Refines user query using chat history with intelligent context handling.
    
    Parameters:
    -----------
    history : list
        List of previous conversation turns (alternating User/AI messages)
    latest_query : str
        The user's latest input query
    llm : LLM instance
        Language model instance (e.g., ChatOpenAI)
    context_freshness_config : dict, optional
        Configuration for context freshness windows. Default values if not provided:
        {
            'fresh_turns': 2,      # 0-2 turns ago = FRESH
            'recent_turns': 4,     # 3-4 turns ago = RECENT
            'aging_turns': 7,      # 5-7 turns ago = AGING
            'stale_turns': 8       # 8+ turns ago = STALE
        }
    
    Returns:
    --------
    str
        The refined standalone query
    
    Examples:
    ---------
    # Use default freshness windows
    refined = refine_query_with_history(history, query, llm)
    
    # Use custom freshness windows (more aggressive context retention)
    config = {
        'fresh_turns': 3,
        'recent_turns': 6,
        'aging_turns': 10,
        'stale_turns': 12
    }
    refined = refine_query_with_history(history, query, llm, config)
    
    # Use custom freshness windows (more conservative context retention)
    config = {
        'fresh_turns': 1,
        'recent_turns': 2,
        'aging_turns': 4,
        'stale_turns': 5
    }
    refined = refine_query_with_history(history, query, llm, config)
    """
    
    # Set default freshness configuration if not provided
    if context_freshness_config is None:
        context_freshness_config = {
            'fresh_turns': 2,
            'recent_turns': 4,
            'aging_turns': 7,
            'stale_turns': 8
        }
    
    # Extract configuration values
    fresh_turns = context_freshness_config.get('fresh_turns', 2)
    recent_turns_lower = fresh_turns+1
    recent_turns = context_freshness_config.get('recent_turns', 4)
    aging_turns_lower = recent_turns+1
    aging_turns = context_freshness_config.get('aging_turns', 7)
    stale_turns = context_freshness_config.get('stale_turns', 8)
    
    # Validate configuration (ensure logical ordering)
    if not (0 < fresh_turns < recent_turns < aging_turns < stale_turns):
        raise ValueError(
            f"Context freshness configuration must follow: "
            f"0 < fresh_turns < recent_turns < aging_turns < stale_turns. "
            f"Got: fresh={fresh_turns}, recent={recent_turns}, "
            f"aging={aging_turns}, stale={stale_turns}"
        )

    prompt = PromptTemplate(
        input_variables=["fresh_turns", "recent_turns_lower", "recent_turns", "aging_turns_lower", "aging_turns", "stale_turns", "history", "latest_query"],
        template=retriever_prompt_template
    )
    # print(prompt)


    chain = prompt | llm

    invoke_payload = {
        "fresh_turns": fresh_turns,
        "recent_turns_lower": recent_turns_lower,
        "recent_turns": recent_turns,
        "aging_turns_lower": aging_turns_lower,
        "aging_turns": aging_turns,
        "stale_turns": stale_turns,
        "history": "\n".join(history),
        "latest_query": latest_query,
        "feasibility_mode": feasibility_mode,
        "feasibility_json_str": feasibility_json,
    }
    refined_query = chain.invoke(invoke_payload)
    with open("testlog.txt", "a") as file:
        file.write(f"\n &&&&&&&&&&&&&&&&&&&&&&&& Prompt:\n{refined_query}")

    # Uncomment if you have this function
    # update_llm_token(refined_query)

    raw_output = getattr(refined_query, "content", str(refined_query)).strip()

    # P1-5: validate the raw LLM output through RefinedQuery.
    # parse_llm_response does json.loads -> RefinedQuery, then exactly one
    # corrective retry (json_mode=True) on failure, then a
    # RefinedQueryFailure envelope. The legacy regex extraction is no
    # longer the parse boundary.
    filled_prompt = prompt.format(**invoke_payload)
    result = parse_llm_response(
        raw=raw_output,
        model_class=RefinedQuery,
        llm_client=llm,
        prompt=filled_prompt,
    )
    if isinstance(result, RefinedQuery):
        return result.refined_query

    # Unrecoverable even after one retry. parse_llm_response already
    # logged the failure; degrade to returning the raw text rather than
    # silently mis-extracting via regex as the old path did.
    frappe.log_error(
        f"refine_query_with_history envelope: {result}",
        "refine_query_with_history",
    )
    return raw_output
