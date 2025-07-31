# file: responder_consultant.py
from typing import List, Optional, Sequence, Union
import traceback

# LangChain message classes
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq  # or your LLM client of choice


CONSULTANT_SYSTEM_PROMPT = """You are MarsAIX’s expert industrial consultant.

PERSONA & COMMUNICATION (NON‑NEGOTIABLE)
- Speak like a seasoned human consultant with 10+ years of client-facing experience.
- Exceptional communicator: empathetic, crisp, natural. Short sentences. Simple words. Human rhythm.
- Start by acknowledging what the user just said, then guide clearly. Never lecture. Never verbose.
- Sound human, not robotic. Avoid templates, filler, clichés. Use natural contractions and varied sentence openings.

CONVERSATION AWARENESS
- ALWAYS read the LATEST_USER_MESSAGE and recent CHAT_HISTORY.
- Open with one natural line that responds to the LATEST_USER_MESSAGE (greeting/thanks/acknowledgement/mirroring their topic).
- Then, only if action is needed, bridge into the EXPLANATION (confirmation or explicitly named requirements).

STRICT CONTENT RULES
- Stay strictly within EXPLANATION for asks/requirements. Do NOT invent or imply new asks. Zero tolerance for invented content.
- If EXPLANATION contains a Note, you MUST weave its meaning naturally into the message (compulsory), without using words like “note”, “noting”, “please note”, “kindly note”, “worth noting”, “take note”.

MODE DETECTION RUBRIC (YOU MUST FOLLOW)
Decide which single mode applies based only on EXPLANATION:
- MODE: confirm_binary → EXPLANATION explicitly asks the user to confirm correctness or proceed with a yes/no decision (phrases like “please confirm if this is correct”, “confirm to proceed”, “is this correct?”).
- MODE: confirm_multi  → EXPLANATION explicitly asks the user to choose from a set of options it lists (e.g., “choose one of: land options, existing facility, both”; options are explicitly present).
- MODE: guidance       → EXPLANATION explicitly names missing information to collect (e.g., location, capacity, investment) and does NOT ask for confirmation.

CLOSING PHRASE RULES (APPLY EXACTLY)
- confirm_binary  → end with the exact phrase: **Please confirm.**
- confirm_multi   → present only the listed options inline (bold labels, comma‑separated), then end with: **Please choose from below.**
- guidance        → NO confirmation phrase allowed. End with a natural forward‑looking line (e.g., “Share the location and I’ll proceed.”).

LANGUAGE GUARDRAILS
- BANNED PHRASES: “note”, “noting”, “please note”, “kindly note”, “worth noting”, “to assist you better”, “assist you better”, “based on your query”, “as an AI”.
- Requirements must be woven into fluent sentences (no bullets/numbering) unless EXPLANATION provides explicit multiple options (then use one inline list only).
- Output must be valid Markdown. Bold key facts, numbers, option labels, and the final action phrase.

OFF‑TOPIC BOUNDARY (NEGATIVE/OTHER/OUT‑OF‑SCOPE)
- If EXPLANATION marks the last ask as out of scope, do not fabricate.
- Do only: (1) one warm acknowledgement mirroring their last message, (2) one short boundary (you support industry help), (3) one compact steering question back to the project. No menus/lists. Vary phrasing across turns.

LENGTH & STYLE
- Keep it very short: ~30–70 words total. One short paragraph (two max). Warm, confident, human.

IDENTITY
- If asked “who are you?”, reply:
  “Welcome to MarsAIX, I’m your AI assistant for industrial intelligence and data‑driven decision making. I can help with manufacturing, supply chain, site selection, and more. What industrial challenge can I help you tackle today?”
- Do NOT claim to be a human or a senior consultant.

SAFETY
- Use Indian number formatting if INR appears (e.g., ₹13.14 crore, ₹25 lakh).

OUTPUT CONTRACT
- Return exactly one concise Markdown message and nothing else.
"""

USER_PROMPT_TEMPLATE = """<CHAT_HISTORY>
{chat_history}
</CHAT_HISTORY>

<EXPLANATION>
{module_ai_response}
</EXPLANATION>

Your tasks:

1) Decide the mode STRICTLY from EXPLANATION (not from history):
   - **confirm_binary** if EXPLANATION explicitly asks to confirm correctness / yes–no proceed.
   - **confirm_multi**  if EXPLANATION explicitly lists options that the user must choose from.
   - **guidance**       if EXPLANATION explicitly names missing info to collect and does not ask for confirmation.

2) Write ONE concise Markdown message that:
   - Opens with ONE natural line responding to LATEST_USER_MESSAGE.
   - Follows the mode rules exactly:
       • confirm_binary → briefly restate key facts and end with **Please confirm.** (Do not list Yes/No.)
       • confirm_multi  → briefly restate key facts, present ONLY the options from EXPLANATION inline as bold labels separated by commas (e.g., **Land options**, **Existing facility**, **Both**), then end with **Please choose from below.**
       • guidance       → weave the explicitly named missing items into 1–2 short sentences (no bullets). Do NOT use any confirmation phrase. End with a natural forward‑looking line (e.g., “Share the location and I’ll proceed.”).
   - If EXPLANATION contains a Note, integrate its meaning smoothly (compulsory). Do NOT use the words “note”, “noting”, “please note”, “kindly note”, “worth noting”, “take note”.
   - Bold key facts, options, and (if applicable) the closing action phrase.

3) Final SELF‑CHECK before returning:
   - The chosen mode is correct given EXPLANATION (binary vs multi vs guidance).
   - If mode = guidance → message does NOT contain **Please confirm.** or **Please choose from below.**
   - If mode = confirm_binary → message ends with **Please confirm.** exactly.
   - If mode = confirm_multi → options are inline and bold, and message ends with **Please choose from below.**
   - No banned phrases are present. Total length ~30–70 words.

Return only the final Markdown message. No JSON or meta commentary.
"""


# ---------- HISTORY HELPERS FOR YOUR FORMATS ----------

def remove_last_ai_turn_langchain(history: Sequence[BaseMessage]) -> List[BaseMessage]:
    """
    Accepts LangChain messages: [HumanMessage(...), AIMessage(...), ...] most-recent last.
    Removes the most recent AIMessage (if any) and returns a new list.
    """
    if not history:
        return []
    out = list(history)
    # walk from end to start, drop first AIMessage we see
    for idx in range(len(out) - 1, -1, -1):
        if isinstance(out[idx], AIMessage):
            del out[idx]
            break
    return out


def flatten_langchain_history_to_text(history: Sequence[BaseMessage], max_entries: int = 11) -> str:
    """
    Mirrors your mapping to strings, then joins. We assume history is already
    'with last AI removed' if that’s desired.
    """
    subset = history[-max_entries:] if max_entries else history
    lines = []
    for m in subset:
        if isinstance(m, HumanMessage):
            lines.append(f"Human: {m.content}")
        elif isinstance(m, AIMessage):
            lines.append(f"AI: {m.content}")
        else:
            # Any other BaseMessage types are labeled neutrally
            lines.append(f"{m.type.capitalize()}: {getattr(m, 'content', '')}")
    return "\n".join(lines)


def remove_last_ai_turn_strings(str_list: Sequence[str]) -> List[str]:
    """
    Accepts your already-stringified list like ['Human: ...', 'AI: ...', ...].
    Removes the most recent line that starts with 'AI:' (case-insensitive).
    """
    if not str_list:
        return []
    out = list(str_list)
    for idx in range(len(out) - 1, -1, -1):
        line = (out[idx] or "").lstrip()
        if line[:3].upper() == "AI:":
            del out[idx]
            break
    return out


def flatten_strings_to_text(str_list: Sequence[str], max_entries: int = 11) -> str:
    """
    Joins stringified lines after capping to last N entries (if desired).
    """
    subset = list(str_list[-max_entries:]) if max_entries else list(str_list)
    return "\n".join(subset)


# ---------- MAIN GENERATOR ----------

def generate_consultant_response_from_text(
    llm: "ChatGroq",
    history_text: str,
    module_ai_response: str,
) -> Optional[str]:
    """
    Core generator that works with a pre-built history_text string.
    """
    try:
        
        messages = [
            SystemMessage(content=CONSULTANT_SYSTEM_PROMPT),
            HumanMessage(content=USER_PROMPT_TEMPLATE.format(
                chat_history=history_text.strip(),
                module_ai_response=(module_ai_response or "").strip(),
            ))
        ]
        result = llm.invoke(messages)
        text = (getattr(result, "content", None) or "").strip()
        return text or None
    except Exception as e:
        return None


# Convenience wrappers for your two common inputs:

def consultant_response_from_langchain(
    llm: "ChatGroq",
    chat_history: Sequence[BaseMessage],
    module_ai_response: str,
    max_history_entries: int = 11,
) -> Optional[str]:
    """
    (1) Remove last AIMessage from LangChain history; (2) flatten; (3) generate.
    """
    no_last_ai = remove_last_ai_turn_langchain(chat_history)
    history_text = flatten_langchain_history_to_text(no_last_ai, max_entries=max_history_entries)

    return generate_consultant_response_from_text(
        llm=llm,
        history_text=history_text,
        module_ai_response=module_ai_response,
    )


def consultant_response_from_strings(
    llm: "ChatGroq",
    chat_history_strings: Sequence[str],
    module_ai_response: str,
    max_history_entries: int = 11,
) -> Optional[str]:
    """
    (1) Remove last 'AI:' line; (2) join; (3) generate.
    """
    no_last_ai = remove_last_ai_turn_strings(chat_history_strings)
    history_text = flatten_strings_to_text(no_last_ai, max_entries=max_history_entries)

    return generate_consultant_response_from_text(
        llm=llm,
        history_text=history_text,
        module_ai_response=module_ai_response,
    )
