import pandas as pd
from bs4 import BeautifulSoup
import re
import frappe
from langchain.prompts import PromptTemplate

from kaix.Ai_module.Query_Classification_And_Analysis  import llm_70b_vers, llm_gpt_oos_120b


def clean_html_description_robust(html_text: str) -> str:
    soup = BeautifulSoup(html_text, "html.parser")
    output_lines = []
    for elem in soup.recursiveChildGenerator():
        if elem.name == "p":
            output_lines.append(elem.get_text(" ", strip=True))
        elif elem.name == "br":
            output_lines.append("\n")
        elif elem.name in ["ul", "ol"]:
            items = [f"- {li.get_text(strip=True)}" for li in elem.find_all("li")]
            output_lines.extend(items)
        elif elem.name == "table":
            rows = []
            for tr in elem.find_all("tr"):
                cells = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
                rows.append(" | ".join(cells))
            if rows:
                output_lines.append("\n".join(rows))
        elif elem.name in ["h1", "h2", "h3", "h4"]:
            header_text = elem.get_text(" ", strip=True)
            output_lines.append(f"\n{header_text.upper()}\n")
    final_text = "\n\n".join(line for line in output_lines if line.strip())
    return final_text.strip()

def normalize_incentive_fields(data: dict) -> dict:
    """
    Cleans the incentive data by converting empty or invalid string values to 'None',
    and ensures scale_of_business is normalized as a list of clean values or [None].

    Args:
        data (dict): The original incentive data.

    Returns:
        dict: Cleaned and normalized data.
    """
    def is_invalid(value):
        if value is None:
            return True
        if isinstance(value, str):
            stripped = value.strip()
            return stripped in ("", "\u00a0", "{}", "null", "None", "NULL")
        return False

    cleaned = {}

    for key, val in data.items():
        if key == "scale_of_business":
            # Normalize to list of clean values
            if is_invalid(val):
                cleaned[key] = [None]
            elif isinstance(val, str):
                items = [s.strip() for s in val.split(",") if not is_invalid(s)]
                cleaned[key] = items if items else [None]
            elif isinstance(val, list):
                items = [s.strip() for s in val if not is_invalid(s)]
                cleaned[key] = items if items else [None]
            else:
                cleaned[key] = [None]
        elif key == "description":
            cleaned[key] = "None" if is_invalid(val) else clean_html_description_robust(val)
        else:
            cleaned[key] = "None" if is_invalid(val) else val

    return cleaned

@frappe.whitelist()
def generate_incentive_summary_markdown(incentive_data: dict) -> dict:
    """
    Generates markdown-formatted financial benefit summaries for each applicable business scale
    using a three-step LLM pipeline:
      1. LLM 1: Structured computation (JSON)
      2. LLM 2: Summary generation and validation
      3. LLM 3: Final markdown formatting with emphasis and layout

    Args:
        incentive_data (dict): {
            "incentive_name",
            "incentive_type",
            "quantum_of_assistance",
            "description",
            "scale_of_business": str | list | None
        }
        content_llm: LLM for computation logic (LLM 1)
        summary_llm: LLM for generating verified plain-text summary (LLM 2)
        formatting_llm: LLM for formatting summary to markdown (LLM 3)

    Returns:
        dict: {
            "raw_prompt": input sent to LLM 1,
            "initial_response": {scale: json_output_from_llm1},
            "verified_summary": {scale: plain_text_output_from_llm2},
            "final_markdown": {scale: markdown_output_from_llm3}
        }
    """
    with open("log2.txt", "a") as file:
        file.write(f"\nMethod Called for contextual {incentive_data}")
    incentive_data = normalize_incentive_fields(incentive_data)
    scale_list = incentive_data["scale_of_business"]
   

    raw_responses = {}
    verified_summaries = {}
    final_markdowns = {}
    raw_prompt_reference = None

    # Step 1 prompt (Structured Calculator - LLM 1)
    generation_prompt_1 = PromptTemplate.from_template("""
 You are a financial calculation engine and policy logic interpreter.

Your task is to read the provided incentive details and generate a structured JSON containing all possible benefit components of the incentive. For each component, identify the benefit type, applicable cost category, investment estimate (based on business scale), and perform accurate numeric calculations.

Do not generate summaries or natural language text. Output only a clean JSON object containing the breakdowns.

---

INPUT DATA:

Incentive Name: {incentive_name}  
Incentive Type: {incentive_type}  
Quantum of Assistance: {quantum_of_assistance}  
Description: {description}  
Scale of Business: {scale_of_business}

Note:
- Industry, product, and capacity are not provided.
- You must infer sector context (if any) using only the incentive name, type, description, and quantum of assistance.
- If the scheme is pan-industry, avoid assigning to any specific sector.

If scale of business is missing:
- Use the language, tone, and assistance quantum to infer a reasonable investment level.

You must always include all distinct benefit structures mentioned — such as Horizontal and Vertical paths — and compute each as a separate object.

Never hallucinate investment values using arbitrary unit logic like “$300 per kg” unless that unit-based logic is explicitly present in the scheme.

Always perform arithmetic in raw form (without commas), and then format the result using standard international comma notation (e.g., $1,000,000).

---

INSTRUCTIONS:

1. Identify all distinct benefit components mentioned in the description or quantum of assistance (e.g., horizontal vs. vertical).
                                                       
2. For each component, determine:
   - Support type: "Absolute", "Proportional", or "Proportional with Cap"
   - Supported cost category (e.g., buildings, plant, BUA, utilities, interest)
   - Applicable cap amount if any
   - Required assumptions (e.g., BUA area or cost)
   - For each benefit path, explicitly extract or infer whether a cap is applicable.
      - If the cap is mentioned, include its value under "benefit_cap"
      - If no cap is mentioned in the input text, explicitly write: "No cap mentioned"
   - If no numerical values (percentage, per-unit rates, investment categories, or caps) are explicitly mentioned in the description or quantum of assistance, you may generate a sample illustrative calculation — but you must:
      - Clearly mark it as an approximation
      - Use realistic and moderate values consistent with the scale of business
      - Mention in the calculation_step: "This is an approximate illustration based on typical investment patterns. Not derived from explicit scheme values."
      - Never fabricate per-unit logic like $/kg, $/sq.ft., etc., unless the input explicitly mentions it

3. Estimate investment based on scale of business:
   - Micro: < $50,000 in assets (typically ≤10 employees)
   - Small: $50,000–$250,000 in assets (11–50 employees)
   - Medium: $250,000–$500,000 in assets (51–100 employees)
   - Large: > $500,000 in assets (>100 employees)
   - If scale is not given, use logical inference from the scheme text
4. Perform raw arithmetic first, then format numbers using standard international comma style.
5. Never let benefit exceed investment. Net cost must always be greater than zero.
                                                       
Ensure:
- Benefit is never more than investment
- Net cost is always positive (never $0)
- All numbers ≥ $100,000 are formatted with standard international commas
- Values should be rounded to 2 decimal places where applicable

---

NUMBER FORMATTING AND INTERPRETATION RULES

All figures ≥ $100,000 must be formatted using standard international numbering conventions (thousands separators every 3 digits).

Follow these steps:

1. Perform raw arithmetic first — do not use $ or commas while calculating.
   - Example: 43800000 × 3 = 131400000

2. Format using standard international comma grouping (groups of 3 digits from the right):
   - $100,000
   - $1,000,000
   - $2,500,000
   - $13,140,000

3. Count digits from right:
   - Group every 3 digits with a comma (e.g., 000 in 100,000; 1,000,000)

4. Interpret properly:
   - $2,500,000 means two million five hundred thousand dollars
   - $25,000,000 means twenty-five million dollars
                                                       
5. DECIMAL SAFETY RULE:
   - Always **truncate decimals** before formatting any number using standard comma rules.
   - For example, if the value is `3800000.0`, treat it as `3800000`.
   - Never count decimal digits when inserting commas.
   - Apply rounding **only for large summarized values (e.g., $ millions)**, not raw formatted numbers.

Round large summarized values to 2 decimal places.

Never:
- Misplace digits or commas
- Show benefit greater than investment
- Output net cost as $0

---

OUTPUT FORMAT:

A JSON object containing the following:

{{
  "incentive_name": "...",
  "scale_of_business": "...",
  "benefit_paths": [
    {{
      "name": "Horizontal Support for Infrastructure",
      "support_type": "Proportional with Cap",
      "supported_cost": "Building and infrastructure (excluding land)",
      "investment_raw": 40000000,
      "benefit_percent": 25,
      "benefit_cap": 250000000,
      "benefit_raw": 10000000,
      "net_cost_raw": 30000000,
      "formatted": {{
        "investment": "$40,000,000",
        "benefit": "$10,000,000",
        "net_cost": "$30,000,000"
      }},
      "calculation_step": "25% of $40,000,000 = $10,000,000 (capped at $250,000,000)"
    }},
    {{
      "name": "Vertical Support on Built-up Area",
      "support_type": "Absolute",
      "supported_cost": "Built-up area (BUA)",
      "benefit_cap": 250000000,
      "built_up_area_sqft": 10000,
      "rate_per_sqft": 300,
      "investment_raw": 5000000,
      "benefit_raw": 3000000,
      "net_cost_raw": 2000000,
      "formatted": {{
        "investment": "$5,000,000",
        "benefit": "$3,000,000",
        "net_cost": "$2,000,000"
      }},
      "calculation_step": "$300 × 10,000 sq.ft. = $3,000,000"
    }}
  ]
}}

Do not write any explanatory text. Only return the JSON object as shown. Ensure all calculations are precise and internally consistent.
    """)

    # Step 2 prompt (Summary Generator & Validator - LLM 2)
    generation_prompt_2 = PromptTemplate.from_template("""
You are a financial summarizer and validation agent.

You will receive structured JSON data from a calculation engine along with full incentive metadata. Your job is to:

1. Validate that all calculations are accurate.
   - Recompute all values to ensure arithmetic is correct.
   - Ensure benefit does not exceed investment.
   - Ensure caps (if applicable) are enforced properly.
   - Re-check that the investment used in benefit calculation matches the reported investment value.
   - Do not allow mismatch between assumed investment in the header and actual values used in calculation breakdown.
2. Check if cap is mentioned for each benefit path. If not, verify using the input text (name, type, description, quantum of assistance). If it is evident from the description or known scheme rules, include it—even if LLM 1 omitted it.
3. Format all amounts using standard international comma rules and USD currency notation.
4. Generate a professional financial benefit summary in paragraph form.

---

REFERENCE DETAILS:

Incentive Name: {incentive_name}  
Incentive Type: {incentive_type}  
Quantum of Assistance: {quantum_of_assistance}  
Description: {description}  
Scale of Business: {scale_of_business}

---

STRUCTURE TO FOLLOW:

1. Title  
   - Include the incentive name and scale of business

2. Core Benefit Overview  
   - Describe each benefit path and what it supports

3. Illustrative Financial Details  
   - One paragraph per benefit path explaining:
     - Total investment assumed
     - How benefit was calculated
     - Net cost
     - Calculation breakdown in formatted currency
     - Ensure all values are already correct and validated in this output.
     - Do not reference any previous mistakes or corrections. Never include phrases like “the above is incorrect”, “upon reviewing”, or “the correct value is…”.
     - If the benefit is based on assumptions due to missing explicit inputs, retain the disclaimer already provided by LLM 1. Do not add clarification or re-validate it.

4. Key Financial Insights  
   - Mention benefit caps (if applicable), scale-based investment logic, and estimated offsets

5. Eligibility Criteria:
   - Only include this section if there is a clearly stated eligibility condition in the description or quantum of assistance.
   - If no eligibility information is present in the input, omit this section entirely.
   - Do not write placeholders like “Not explicitly provided”.


6. Conclusion  
   - State how useful the incentive is for the given scale

Ensure the final output follows this structure:
1. Title
2. Core Benefit Overview
3. Illustrative Financial Details
4. Key Financial Insights
5. Eligibility Criteria
6. Conclusion

Each financial example must match the structure of investment → benefit → net cost, with clearly formatted figures in standard international style. If the scheme includes multiple benefit components (e.g., horizontal and vertical), summarize each in separate paragraphs.

Avoid using any numeric per-unit logic (e.g., $300/kg or $500/sq.ft.) unless explicitly mentioned in the incentive description. Do not invent unit rates.

---

FORMATTING RULES:

- Do not use markdown, bullet points, emojis, or placeholder text.
- Format all numbers ≥ $100,000 using standard international style commas (e.g., $2,500,000, $25,000,000).
- Round large values to 2 decimal places when summarizing (e.g., $ millions).
- Avoid repeating raw numbers unless necessary.
- Do not invent or modify computed figures.
- Round off large summarized values to 2 decimal places
- Never explain estimates using artificial unit rates unless provided
- Ensure net cost is always greater than zero
- Do not include commentary, self-correction, or phrases like “upon reviewing the calculation...” or “therefore the correct value is...”. All values must be correct in the first instance, with no clarification or explanation needed.
- If LLM 1 provides approximate examples with disclaimers (e.g., "illustration based on typical investment patterns"), retain them as-is. Do not rephrase or over-justify these in the summary.
- Never include commentary or self-correction logic such as “this appears to be wrong” or “the correct result should be…”. All outputs must be framed as correct in the first place.
- Decimal Truncation: Before applying comma formatting, always convert all monetary values to integers. Never format values like 3800000.0 as $3,800,00.0. Correct approach is $3,800,000.
- Only apply rounding to large summarized values, and **truncate decimals for all raw dollar values**.
- Net cost must be calculated as: net_cost = investment - benefit
  - Never show net cost as $0 unless the benefit fully offsets the total investment (which is rare).
  - For interest subsidies or partial grants, ensure the net cost reflects the uncovered portion of investment, not zero.
  - Double-check that investment and benefit amounts are consistent across all calculations.
                                               
---

HOW TO FORMAT AND INTERPRET NUMBERS IN STANDARD INTERNATIONAL STYLE

Ensure every figure ≥ $100,000 is formatted correctly using standard international commas.

Follow these rules:

1. Use comma system:
   - $100,000
   - $1,000,000
   - $2,500,000
   - $13,140,000

2. Comma logic:
   - Last 3 digits = first group
   - Remaining digits = grouped by 2s

3. Interpret carefully:
   - $2,500,000 means two million five hundred thousand dollars
   - $25,000,000 means twenty-five million dollars

Round large figures (millions) to 2 decimal places and do not misplace commas or misread values.

---

STRUCTURED JSON (FROM LLM 1):

{structured_json_output}

---

OUTPUT:

Return a clean, paragraph-form financial summary using the structure above. Ensure all numeric and logical validations are complete before generating the summary.
    """)

    # Step 3 prompt (Markdown Formatter + Math Validator)
    formatting_prompt = PromptTemplate.from_template("""
You are a professional financial formatter and math validator.

Your task is to take the raw incentive summary below and return a polished markdown version with:
- Proper **headings** using ## and ### where appropriate
- Proper **bullet points** and **numbered lists** where logical
- Important **figures** ($ amounts, percentages, dates) and **key terms** in **bold**
- Maintain accurate **standard international number system formatting**:
  - Always truncate decimal parts **before** inserting commas. Never include decimals when formatting.
  - For example, format `3800000.0` as **$3,800,000**, not $3,800,00.0.
- No emojis
- No markdown tables
- No hallucinated changes — always use the content provided

Additionally, you must verify all mathematical operations shown in the content (e.g., "$300 × 10,000 = $3,000,000"):
- If the result is wrong, silently correct it and update the value in-place. Do not mention that a correction was made.
- If the benefit exceeds the investment (e.g., net cost becomes $0 or negative), recalculate with a higher realistic investment
- If the math seems ambiguous or impossible to verify, do NOT change it — keep the original as-is
- Net cost must be calculated as: net_cost = investment - benefit
  - Never show net cost as $0 unless the benefit fully offsets the total investment (which is rare).
  - For interest subsidies or partial grants, ensure the net cost reflects the uncovered portion of investment, not zero.
  - Double-check that investment and benefit amounts are consistent across all calculations.
- Do not include any self-correction phrases like “however, this seems wrong” or “the corrected version is…”.
- The final markdown must appear clean and confident. Only the corrected version should appear — the incorrect version must be removed entirely.
- Ensure that formatting logic always uses the **integer part** of any number before applying comma formatting. Never apply comma rules to decimal values like `3800000.0` — treat as `3800000`.

Input:
{raw_text}

Output:
Markdown formatted and verified content only.
    """)

    for scale in scale_list:
        scale = scale.capitalize() if scale else scale
        llm_input = {
            "incentive_name": incentive_data.get("incentive_name", ""),
            "incentive_type": incentive_data.get("incentive_type", ""),
            "quantum_of_assistance": incentive_data.get("quantum_of_assistance", ""),
            "description": incentive_data.get("description", ""),
            "scale_of_business": scale or "Not specified"
        }

        # Step 1: Structured Computation from LLM 1
        chain_step1 = generation_prompt_1 | llm_gpt_oos_120b
        response_step1 = chain_step1.invoke(llm_input)
        llm1_json = response_step1.content.strip()
        key = scale if scale else "Default"
        raw_responses[key] = llm1_json

        # Step 2: Plain Text Summary from LLM 2
        chain_step2 = generation_prompt_2 | llm_gpt_oos_120b
        response_step2 = chain_step2.invoke({
            "incentive_name": llm_input["incentive_name"],
            "incentive_type": llm_input["incentive_type"],
            "quantum_of_assistance": llm_input["quantum_of_assistance"],
            "description": llm_input["description"],
            "scale_of_business": llm_input["scale_of_business"],
            "structured_json_output": llm1_json
        })

        summary_text = response_step2.content.strip()
        summary_text = re.sub(r"<think>.*?</think>", "", summary_text, flags=re.DOTALL).strip()
        verified_summaries[key] = summary_text

        # Step 3: Markdown Formatting from LLM 3
        chain_step3 = formatting_prompt | llm_70b_vers
        formatted = chain_step3.invoke({"raw_text": summary_text})
        final_markdowns[key] = formatted.content.strip()

        # Store initial prompt reference
        if raw_prompt_reference is None:
            raw_prompt_reference = generation_prompt_1.format(**llm_input)
    
    import json

    data = {
        "final_markdown": final_markdowns
    }

    # Convert to valid JSON string
    json_string = json.dumps(data, ensure_ascii=False)

    # Now save `json_string` to DB

    return json_string


