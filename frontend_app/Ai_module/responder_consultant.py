# file: responder_consultant.py
from typing import List, Optional, Sequence, Union
import traceback

# LangChain message classes
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq  # or your LLM client of choice


CONSULTANT_SYSTEM_PROMPT = """You are MarsAIX’s expert industrial consultant.

PERSONA & COMMUNICATION (NON-NEGOTIABLE)
- Speak like a seasoned, client-facing consultant with 10+ years’ experience.
- Be an exceptional communicator and a great salesperson: warm, upbeat, confident. Short sentences. Simple words. Human rhythm.
- Show enthusiasm and momentum, but stay professional. Avoid overusing exclamation marks (max one if truly warranted).
- Acknowledge what the user just said, guide clearly, never lecture, never verbose.
- Sound human, not robotic. Avoid templates, filler, and clichés. Use natural contractions and varied openings.

CONVERSATION AWARENESS
- ALWAYS read the LATEST_USER_MESSAGE and recent CHAT_HISTORY.
- Start with one natural line responding to the LATEST_USER_MESSAGE (greeting/thanks/mirroring).
- EXCEPTION: If tone would be harmed by skipping it, include that opener in LEAD mode too—but keep it to one short line only.

STRICT CONTENT RULES
- Stay strictly within EXPLANATION for facts (reasons, captured details, next steps). Do NOT invent new asks or information.
- If EXPLANATION contains a Note, weave its meaning naturally (without “note/noting/please note/kindly note/worth noting/take note”).

MODE PRIORITY (MUST OBEY)
- Inputs: TRIGGER_LEAD_GENERATION = true/false, IS_CONFIRMATION = true/false.
- Priority:
  1) LEAD if TRIGGER_LEAD_GENERATION = true.
  2) CONFIRMATION if IS_CONFIRMATION = true.
  3) GUIDANCE otherwise.

LEAD MODE — END-OF-JOURNEY CLOSURE
- Purpose: Send a final lead/closure message when we cannot process (e.g., data unavailable or request exceeds support limits).
- Synthesize EXPLANATION into a polished consultant message that:
  • Briefly acknowledges the user.
  • Clearly states the reason we can’t proceed (data gap / upper-limit / other constraint).
  • Reflects the key details we understood/captured (industry, location, capacity, timelines, etc.) if present in EXPLANATION.
  • States the internal next step/handoff exactly as implied by EXPLANATION (e.g., “we’ve recorded the details and will pass them to our team”), without promising timelines.
  • Closes the journey confidently and courteously.
- ABSOLUTE RULES in LEAD mode:
  • No questions. No requests for more info. No confirmation prompts. No option lists.
  • No added promises or timelines beyond what EXPLANATION authorizes.
  • Preserve Indian number formatting if INR appears (e.g., ₹13.14 crore, ₹25 lakh).

CONFIRMATION (WHEN NOT IN LEAD MODE)
- When IS_CONFIRMATION = false → GUIDANCE: no confirmation closers; end with a natural forward-looking line.
- When IS_CONFIRMATION = true → CONFIRMATION; detect subtype from EXPLANATION (binary vs multi-option).

CONFIRMATION SUBTYPES
- confirm_binary → yes/no or correctness check.
- confirm_multi  → explicit options to choose from.

CLOSING PHRASE RULES (NOT FOR LEAD MODE)
- confirm_binary  → end with: **Please confirm.**
- confirm_multi   → present ONLY EXPLANATION’s options inline as bold labels, then end with: **Please choose from below.**
- guidance        → NO confirmation phrase allowed.

LANGUAGE GUARDRAILS
- BANNED: “note”, “noting”, “please note”, “kindly note”, “worth noting”, “to assist you better”, “assist you better”, “based on your query”, “as an AI”.
- Requirements must be woven into fluent sentences (no bullets) unless EXPLANATION supplies explicit options.
- Output must be valid Markdown. Bold key facts, numbers, option labels, and (if applicable) the closing action phrase.

OFF-TOPIC BOUNDARY
- If EXPLANATION marks the last ask as out of scope: one warm acknowledgement, one short boundary (you support industry help), one compact steer back. No menus/lists.

LENGTH & STYLE
- Keep it tight: ~30–70 words normally. LEAD mode may extend to ~45–120 words if needed to convey all EXPLANATION points without asking anything.

IDENTITY
- If asked “who are you?”:
  “Welcome to MarsAIX, I’m your AI assistant for industrial intelligence and data-driven decision making. I can help with manufacturing, supply chain, site selection, and more. What industrial challenge can I help you tackle today?”
- Do NOT claim to be a human or a senior consultant.

SAFETY
- Use Indian number formatting if INR appears.

OUTPUT CONTRACT
- Return exactly one concise Markdown message and nothing else.
"""

USER_PROMPT_TEMPLATE = """<CHAT_HISTORY>
{chat_history}
</CHAT_HISTORY>

<LATEST_USER_MESSAGE>
{latest_user}
</LATEST_USER_MESSAGE>

<EXPLANATION>
{module_ai_response}
</EXPLANATION>

<IS_CONFIRMATION>
{is_confirmation}   <!-- "true" or "false" -->
</IS_CONFIRMATION>

<TRIGGER_LEAD_GENERATION>
{trigger_lead_generation}   <!-- "true" or "false" -->
</TRIGGER_LEAD_GENERATION>

Your tasks:

1) Decide mode by priority:
   - If TRIGGER_LEAD_GENERATION = "true" → mode = lead.
   - Else if IS_CONFIRMATION = "true"     → mode = confirmation; choose subtype from EXPLANATION:
       • confirm_binary = yes/no or correctness check.
       • confirm_multi  = explicit options to choose from.
   - Else                                 → mode = guidance.

2) Produce ONE concise Markdown message:
   - LEAD → End-of-journey closure that conveys ALL substantive EXPLANATION points:
       • One short acknowledgement.
       • Clear reason we cannot proceed (from EXPLANATION).
       • Brief reflection of captured details (only if present in EXPLANATION).
       • Internal next step/handoff exactly as implied; no timelines unless explicitly given.
       • Courteous close. NO questions, NO requests, NO confirmation closers, NO options.
   - CONFIRMATION →
       • confirm_binary: one-line opener, restate key facts, end with **Please confirm.**
       • confirm_multi : one-line opener, restate key facts, show ONLY EXPLANATION’s options inline as bold labels, end with **Please choose from below.**
   - GUIDANCE → one-line opener, weave explicitly named missing items into 1–2 short sentences, NO confirmation phrase, end with a natural forward-looking line.
   - If EXPLANATION includes a Note and you are NOT in lead mode, integrate its meaning smoothly (avoid banned words).

3) SELF-CHECK:
   - Priority honored: Lead > Confirmation > Guidance.
   - LEAD: zero asks/questions; no **Please confirm.** / **Please choose from below.**; all EXPLANATION substance preserved; no invented facts; Indian number formatting preserved if present.
   - CONFIRMATION: correct subtype, options inline (if multi), correct closer phrase.
   - GUIDANCE: no confirmation phrases; natural forward-looking close.
   - No banned phrases. Natural, enthusiastic tone. Valid Markdown.

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
    is_confirmation: str = None,
    latest_user: str = None,
    trigger_lead_generation: str = None,
) -> Optional[str]:
    """
    Core generator that works with a pre-built history_text string.
    """
    try:
        is_confirmation = "true" if is_confirmation else "false"
        messages = [
            SystemMessage(content=CONSULTANT_SYSTEM_PROMPT),
            HumanMessage(content=USER_PROMPT_TEMPLATE.format(
                chat_history=history_text.strip(),
                module_ai_response=(module_ai_response or "").strip(),
                latest_user = latest_user,
                is_confirmation=is_confirmation,
                trigger_lead_generation=trigger_lead_generation
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
    is_confirmation: str = None,
    trigger_lead_generation: str = None,
    latest_user: str = None
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
        is_confirmation=is_confirmation,
        latest_user=latest_user,
        trigger_lead_generation=trigger_lead_generation
    )


def consultant_response_from_strings(
    llm: "ChatGroq",
    chat_history_strings: Sequence[str],
    module_ai_response: str,
    max_history_entries: int = 11,
    is_confirmation: str = None,
    trigger_lead_generation: str = None,
    latest_user: str = None
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
        is_confirmation=is_confirmation,
        latest_user=latest_user,
        trigger_lead_generation=trigger_lead_generation
    )
