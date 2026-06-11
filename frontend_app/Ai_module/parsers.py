"""
Ai_module/parsers.py

Single helper for converting a raw LLM string into a validated Pydantic v2
model, with one corrective retry pass and a typed failure envelope so
callers never see a half-validated payload or an unhandled exception.

Used by every per-query extraction module under Ai_module/:
    build_from_scratch, employement_query, incentive_query,
    approval_query, vendor_query, query_hints, intent_detection,
    query_refinement.

NOT used for bare-integer classification calls (approve, incentive,
vendor, employment classifiers) — those stay on re.search because they
do not return JSON objects.

Call pattern at every parse site (Day 7 wiring):

    # EXISTING LINE — unchanged
    raw = llm_client.invoke(prompt).content

    # NEW LAYER — insert after
    result = parse_llm_response(
        raw=raw,
        model_class=SomeModel,
        llm_client=llm_client,
        prompt=prompt,
    )
    if isinstance(result, SomeModel):
        # happy path — result is fully validated
        ...
    else:
        # failure envelope — result is SomeModelFailure or plain dict
        # original fallback behaviour goes here
        ...
"""

import ast
import json
import re
import sys
from typing import Any, Dict, List, Type, Union

import frappe
from pydantic import BaseModel, ValidationError

from frontend_app.Ai_module.intent_detection.schemas import IntentClassification

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Single stable title for every frappe.log_error raised from this module.
# Makes filtering the Error Log doctype in Frappe Desk trivial —
# all parser failures group under one title.
_LOG_TITLE = "parse_llm_response"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _invoke_llm(llm_client, prompt: str, json_mode: bool = False) -> str:
    """
    Normalise the LLM response to a plain string.

    The codebase uses ChatGroq clients (llm_70b_vers, llm_8b_inst,
    llm_gpt_oos_120b, llm_maverik, llm_70b_vers_creative) whose
    .invoke(prompt) returns an AIMessage with .content as the text payload.

    json_mode=True adds response_format={"type": "json_object"} to the
    call. Always set True on corrective retries so the LLM cannot respond
    with prose or fenced code blocks on the second attempt.

    Also accepts plain string returns so the function stays drop-in
    for unit test stubs.
    """
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = llm_client.invoke(prompt, **kwargs)

    if isinstance(response, str):
        return response

    # AIMessage / BaseMessage path — .content is the text payload.
    return getattr(response, "content", str(response))


def _resolve_failure_envelope(
    model_class: Type[BaseModel],
    error: Exception,
    raw_output: str,
) -> Union[BaseModel, Dict[str, Any]]:
    """
    Build the typed failure envelope.

    Convention followed throughout the Day 6 schemas: every happy-path
    model Foo has a sibling FooFailure in the same schemas.py file with
    two required fields — error: str and raw_output: str — plus all
    happy-path fields as Optional with None defaults.

    When the sibling class is found and is itself a BaseModel subclass,
    we instantiate it so callers get a consistent .model_dump() contract
    whether the result is a success or a failure.

    If the sibling class does not exist or cannot be instantiated, we
    degrade to a plain dict with the same two keys. Never None, never
    a raised exception.
    """
    failure_name = f"{model_class.__name__}Failure"
    module = sys.modules.get(model_class.__module__)
    failure_cls = getattr(module, failure_name, None) if module else None

    if isinstance(failure_cls, type) and issubclass(failure_cls, BaseModel):
        try:
            return failure_cls(error=str(error), raw_output=raw_output)
        except ValidationError:
            # Sibling class exists but its schema does not match.
            # Fall through to the plain dict rather than raising —
            # rule 6 forbids leaking exceptions to the caller.
            pass

    return {"error": str(error), "raw_output": raw_output}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_llm_response(
    raw: str,
    model_class: Type[BaseModel],
    llm_client,
    prompt: str,
) -> BaseModel:
    """
    Parse `raw` (a JSON string from an LLM) into a validated instance of
    `model_class`, retrying exactly once with a corrective prompt on failure.

    Parameters
    ----------
    raw : str
        The original LLM completion. Expected to be a JSON object that
        matches model_class's schema. The LLM may emit stray prose,
        fenced code blocks, or schema violations — all handled here.

    model_class : Type[BaseModel]
        A Pydantic v2 model class from one of the Day 6 schemas.py files.
        Validated with model_class(**parsed) — the v2 idiom.

    llm_client :
        The same ChatGroq client used for the original call.
        Pass the same instance so the retry runs against the same model.
        e.g. llm_70b_vers, llm_8b_inst, llm_gpt_oos_120b, llm_maverik.

    prompt : str
        The original prompt that produced `raw`. Included verbatim in the
        corrective retry so the LLM keeps full task context, not just
        the validation error.

    Returns
    -------
    BaseModel
        Happy path  : a validated model_class instance.
        Failure path: a sibling {model_class.__name__}Failure envelope
                      if defined, otherwise a plain dict with
                      'error' and 'raw_output' keys.

    Guarantees
    ----------
    - Never returns a fake-success instance.
    - Never raises to the caller — all exceptions are caught internally.
    - Logs every unrecovered failure via frappe.log_error(str(error),
      _LOG_TITLE). No print(), no custom logger.
    - Retries exactly once — caps latency and token spend.
    """

    # ------------------------------------------------------------------
    # Attempt 1 — parse raw as-is
    # ------------------------------------------------------------------
    # JSONDecodeError and ValidationError are both treated as recoverable.
    # Both flow into the same corrective retry because the fix is the
    # same in both cases: ask the LLM to return well-formed JSON again.
    first_error: Exception
    try:
        parsed = json.loads(raw)
        return model_class(**parsed)
    except (ValidationError, json.JSONDecodeError) as exc:
        first_error = exc

    # ------------------------------------------------------------------
    # Build the corrective retry prompt
    # ------------------------------------------------------------------
    # Includes the original prompt (task context), the raw output
    # (what the LLM actually said), and the validation error (what was
    # wrong) — all verbatim. The explicit "ONLY valid JSON" instruction
    # addresses the most common failure mode: LLM adding prose or fences.
    corrective_prompt = (
        f"{prompt}\n\n"
        "---\n"
        "Your previous response could not be parsed.\n\n"
        f"Previous raw output:\n{raw}\n\n"
        f"Validation error:\n{first_error}\n\n"
        "Return ONLY valid JSON that conforms to the expected schema. "
        "Do not include any prose, markdown fences, or commentary."
    )

    # ------------------------------------------------------------------
    # Attempt 2 — single corrective retry
    # ------------------------------------------------------------------
    # json_mode=True forces response_format={"type":"json_object"} on
    # the retry call so the LLM cannot produce prose on the second pass.
    # Any failure — transport error, JSONDecodeError, ValidationError —
    # flows into the log + envelope branch. Retries are capped at one.
    retry_raw = raw  # fallback so envelope still has something if the LLM call itself blows up
    try:
        retry_raw = _invoke_llm(llm_client, corrective_prompt, json_mode=True)
        parsed_retry = json.loads(retry_raw)
        return model_class(**parsed_retry)
    except Exception as exc:  # noqa: BLE001 — total catch required, no exception escapes
        frappe.log_error(str(exc), _LOG_TITLE)
        return _resolve_failure_envelope(model_class, exc, retry_raw)

def extract_json_object(text: str) -> str:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model output")
    return match.group(0)

def safe_parse_output(output_str: str) -> list:
    """
    P1-5 legacy fallback. The canonical parse boundary for
    classify_query_multilabel is parse_llm_response(IntentClassification)
    at the chain.invoke() site. This helper survives for callers that
    still hand it a raw LLM string with no LLM context for a corrective
    retry.

    Strategy:
      1) json.loads             — supports {"categories":[...]} and bare [...]
      2) ast.literal_eval       — tolerates Python-literal lists
      3) bracket scan           — first [...] block
      4) IntentClassification   — pydantic validation as the shape gate
      5) substring scan         — last-resort match against the 9 known names
      6) []                     — final fallback (kept for back-compat)
    """
    MAIN_CATEGORIES = {
        "Query to build industry from Scratch",
        "Query to search Vendors",
        "Query to search Incentives",
        "Query to Get Approvals",
        "Query to Get Employee Search"
    }

    FALLBACK_CATEGORIES = {
        "Negatively Intended Query",
        "Other industry-related queries",
        "Valueless queries",
        "Follow-up Query"
    }
    output_str = output_str.strip()

    def _validate(candidate_list):
        # Funnel every candidate through IntentClassification so unknown
        # categories, mixed types, and empty lists fail at the boundary
        # rather than silently propagating downstream.
        try:
            validated = IntentClassification(categories=candidate_list)
            return list(validated.categories)
        except Exception:
            return None

    # Case 1: strict JSON
    try:
        parsed = json.loads(output_str)
        if isinstance(parsed, dict) and "categories" in parsed:
            ok = _validate(parsed["categories"])
            if ok is not None:
                return ok
        elif isinstance(parsed, list):
            ok = _validate(parsed)
            if ok is not None:
                return ok
        elif isinstance(parsed, str):
            ok = _validate([parsed.strip('"')])
            if ok is not None:
                return ok
    except json.JSONDecodeError:
        pass

    # Case 2: Python literal list
    try:
        parsed = ast.literal_eval(output_str)
        if isinstance(parsed, list):
            ok = _validate([str(cat) for cat in parsed])
            if ok is not None:
                return ok
    except (ValueError, SyntaxError):
        pass

    # Case 3: scan for a [...] block
    bracket_match = re.search(r"\[.*?\]", output_str)
    if bracket_match:
        try:
            parsed = ast.literal_eval(bracket_match.group(0))
            if isinstance(parsed, list):
                ok = _validate([str(cat) for cat in parsed])
                if ok is not None:
                    return ok
        except (ValueError, SyntaxError):
            pass

    # Case 4: substring scan against the 9 known names
    for known_cat in MAIN_CATEGORIES.union(FALLBACK_CATEGORIES):
        if known_cat in output_str:
            ok = _validate([known_cat])
            if ok is not None:
                return ok

    return []

def extract_json_from_llm_response(raw_output: str, json_key: str) -> Dict[str, Union[List[str], None]]:
    """
    Extracts a JSON object containing the specified key from an LLM response.

    Supports:
    - Direct JSON responses.
    - JSON blocks enclosed in triple backticks.
    - Loosely structured JSON in plain text.

    Handles cases where:
    - The key's value is explicitly `null` or `None`.
    - The key contains a list of values.
    
    Parameters:
    -----------
    raw_output : str
        The raw text output from the LLM.

    json_key : str
        The expected key in the JSON response (e.g., "KEYWORDS").

    Returns:
    --------
    Dict[str, Union[List[str], None]]:
        A dictionary with the extracted values, ensuring a structured JSON output.
    """

    # --- Case 1: Direct JSON Parsing ---
    try:
        data_entire = json.loads(raw_output.strip())
        if isinstance(data_entire, dict) and json_key in data_entire:
            extracted_value = data_entire.get(json_key, None)
            return {json_key: extracted_value if isinstance(extracted_value, list) else None}
    except (json.JSONDecodeError, ValueError, TypeError):
        pass  # JSON parsing failed

    # --- Case 2: Extract JSON inside triple backticks ---
    code_blocks = re.findall(r'```(?:[a-zA-Z0-9_-]+)?(.*?)```', raw_output, flags=re.DOTALL)
    for block in code_blocks:
        try:
            block_data = json.loads(block.strip())
            if isinstance(block_data, dict) and json_key in block_data:
                extracted_value = block_data.get(json_key, None)
                return {json_key: extracted_value if isinstance(extracted_value, list) else None}
        except (json.JSONDecodeError, ValueError, TypeError):
            pass  # JSON parsing failed

    # --- Case 3: Regex-based Extraction ---
    
    #    a) Pattern with curly braces (full JSON structure)
    pattern_braces = re.compile(r'\{\s*"' + json_key + r'"\s*:\s*(\[[^]]*\]|null|None)\s*\}', flags=re.DOTALL)
    match_braces = pattern_braces.search(raw_output)
    if match_braces:
        keyword_list = match_braces.group(1).strip()

        # If the extracted value is explicitly "null" or "None", return None
        if keyword_list.lower() in ["null", "none"]:
            return {json_key: None}

        extracted_values = [kw.strip('" ') for kw in keyword_list.strip("[]").split(',') if kw.strip('" ')]
        return {json_key: extracted_values if extracted_values else None}

    #    b) Loose JSON structure extraction (if above didn't work)
    pattern_no_braces = re.compile(r'"' + json_key + r'"\s*:\s*(\[[^]]*\]|null|None)', flags=re.DOTALL)
    match_no_braces = pattern_no_braces.search(raw_output)
    if match_no_braces:
        keyword_list = match_no_braces.group(1).strip()

        if keyword_list.lower() in ["null", "none"]:
            return {json_key: None}

        extracted_values = [kw.strip('" ') for kw in keyword_list.strip("[]").split(',') if kw.strip('" ')]
        return {json_key: extracted_values if extracted_values else None}

    # -- If nothing worked, return a default response --
    return {json_key: None}

@frappe.whitelist()
def convert_string_json(input):
    try:
        # Try strict JSON parse first
        return json.loads(input)
    except json.JSONDecodeError:
        try:
            # Fallback: parse Python literal dict
            parsed = ast.literal_eval(input)
            # Convert to JSON-compatible dict string and then parse it to validate
            return json.loads(json.dumps(parsed))
        except (ValueError, SyntaxError) as e:
            return {"error": f"Invalid input: {str(e)}"}