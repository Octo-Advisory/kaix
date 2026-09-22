import json
import logging
import os
import re
import time
from langchain_core.runnables import RunnableSequence
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from kaix.Market_Trends.utils import validate_inputs, safe_search_web, decide_trend_allocation
from kaix.Market_Trends.prompts import summarize_prompt, format_prompt, fallback_prompt
from kaix.Ai_module.Query_Classification_And_Analysis import llm_70b_vers_creative, llm_70b_vers

# Dynamically get the user's home directory
base_dir = os.path.expanduser("~")

# Construct the full log file path
log_file = os.path.join(
    base_dir,
    "frappe-bench/apps/kaix/kaix/Market_Trends/market_trends.log"
)
# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# def get_market_trends(
#     main_industry: str,
#     sub_sector: str,
#     segment: str,
#     state: str,
#     city: str,
#     deepdown_industry_info: str,
#     deepdown_location_info: str,
#     query
# ) -> str:
def get_market_trends(query,
                      main_industry: str,
                      sub_sector: str,
                      segment: str,
                      state: str,
                      city: str,) -> str:    
    """
    Retrieve and format market trends for a specific industry and location.
    
    Args:
        main_industry: Main industry (e.g., chemical)
        sub_sector: Sub-sector (e.g., Petrochemicals)
        segment: Segment (e.g., Polymers)
        state: State or region (e.g., Kerala)
        city: City (e.g., Kochi)
    
    Returns:
        Formatted Markdown string with market trends.
    """
    # try:
    #     # Validate inputs
    #     validate_inputs(main_industry, sub_sector, segment, state, city, deepdown_industry_info, deepdown_location_info)
    #     logger.info("Starting get_market_trends for %s (%s) in %s, %s", sub_sector, segment, city, state)

    #     # Construct enhanced search query

    #     # queries without pan fields
    #     if deepdown_industry_info.lower() == "segment" and deepdown_location_info.lower() == "city": 
    #         query = f"market trends for {segment} in {sub_sector} within the {main_industry} industry in {city}, {state} for 2024-2025"
    #     elif deepdown_industry_info.lower() in ("industry","pan industry") and deepdown_location_info.lower() in ("state","pan state"):     
    #         query = f"market trends for {main_industry} industry in {state} for 2024-2025" ## asd 1
    #     elif deepdown_industry_info.lower() in ("industry","pan industry") and deepdown_location_info.lower() == "city": 
    #         query = f"market trends for {main_industry} industry in {city}, {state} for 2024-2025" ## asd3
    #     elif deepdown_industry_info.lower() in ("sub-sector","pan sub-sector") and deepdown_location_info.lower() == "city":  
    #         query = f"market trends for {sub_sector} within {main_industry} industry in {city}, {state} for 2024-2025"  ##asd 4
    #     elif deepdown_industry_info.lower() in ("sub-sector","pan sub-sector") and deepdown_location_info.lower() in ("state","pan state"):
    #         query = f"market trends for {sub_sector} within {main_industry} industry  in {state} for 2024-2025" ## asd 5
    #     elif deepdown_industry_info.lower() == "segment" and deepdown_location_info.lower() in ("state","pan state"):
    #         query = f"market trends for {segment} in {sub_sector} within the {main_industry} industry in {state} for 2024-2025" ## asd 2


        #### NOT RELEVANT ####

        # # queries with pan industry field
        # elif deepdown_industry_info.lower() == "pan industry" and deepdown_location_info.lower() in ("state","pan state"):
        #     query = f"market trends for {main_industry} industry in {state} for 2024-2025" ## asd 1
        # elif deepdown_industry_info.lower() == "pan industry" and deepdown_location_info.lower() == "city":
        #     query = f"market trends for {main_industry} industry in {city}, {state} for 2024-2025" ## asd3
        # # elif deepdown_industry_info.lower() == "pan industry" and deepdown_location_info.lower() == "pan state":
        # #     query = f"market trends for {main_industry} industry in {state} for 2024-2025"   

        # # queries with pan sub-sector field
        # elif deepdown_industry_info.lower() == "pan sub-sector" and deepdown_location_info.lower() in ("pan state","state"):
        #     query = f"market trends for {sub_sector} within {main_industry} industry  in {state} for 2024-2025" ## asd 5
        # elif deepdown_industry_info.lower() == "pan sub-sector" and deepdown_location_info.lower() == "city":
        #     query = f"market trends for {sub_sector} within {main_industry} industry in {city}, {state} for 2024-2025"  ##asd 4
        # # elif deepdown_industry_info.lower() == "pan sub-sector" and deepdown_location_info.lower() == "state":
        # #     query = f"market trends for {sub_sector} within {main_industry} industry  in {state} for 2024-2025"

        # # queries with pan state field
        # elif deepdown_industry_info.lower() == "pan state" and deepdown_location_info.lower() in ("pan industry", "industry"):
        #     query = f"market trends for {main_industry} industry in {state} for 2024-2025"  ## asd 1
        # elif deepdown_industry_info.lower() == "pan state" and deepdown_location_info.lower() in ("pan sub-sector","sub-sector"):
        #     query = f"market trends for {sub_sector} within {main_industry} industry  in {state} for 2024-2025" ## asd 5
        # elif deepdown_industry_info.lower() == "pan state" and deepdown_location_info.lower() == "segment":
        #     query = f"market trends for {segment} in {sub_sector} within the {main_industry} industry in {state} for 2024-2025" ##asd 2
    try:
        # abc = None
        # cde = abc["ABC"]
        logger.info("Checking cache for query: %s", query)

        # Initialize LLM
        llm = llm_70b_vers_creative

        # Perform web search
        search_results = safe_search_web(query)
        if not search_results:
            logger.warning("No search results found, using fallback prompt")
            time.sleep(2)  # Avoid rate limits
            chain = RunnableSequence(fallback_prompt | llm)
            output = chain.invoke(
                {
                    "main_industry": main_industry,
                    "sub_sector": sub_sector,
                    "segment": segment,
                    "state": state,
                    "city": city
                }
            ).content
            logger.info("Using fallback data scope: %s", "state" if state.lower() in output.lower() else "India")
        else:
            # Decide trend allocation
            trend_allocation = decide_trend_allocation(
                search_results=search_results,
                main_industry=main_industry,
                sub_sector=sub_sector,
                segment=segment,
                state=state,
                city=city
            )
            logger.info("Trend allocation: %s", trend_allocation)

            # Determine data scope based on allocation
            scope = "global"
            if trend_allocation["city"] > 0:
                scope = "city"
            elif trend_allocation["state"] > 0:
                scope = "state"
            elif trend_allocation["country"] > 0:
                scope = "India"
            logger.info("Detected data scope: %s for query: %s", scope, query)
            logger.info("Search results excerpt: %s", search_results[:100].replace("\n", " "))

            # Summarize trends
            time.sleep(2)  # Avoid rate limits
            summarize_chain = RunnableSequence(summarize_prompt | llm)
            trends = summarize_chain.invoke(
                {
                    "search_results": search_results,
                    "main_industry": main_industry,
                    "sub_sector": sub_sector,
                    "segment": segment,
                    "state": state,
                    "city": city,
                    "trend_allocation": json.dumps(trend_allocation)
                }
            ).content
            # Log trend types
            trend_lines = trends.split("\n")
            trend_types = []
            for line in trend_lines:
                if line.startswith("Positive:"):
                    p_line = line.split('Positive:')[1][:50].replace('\n', ' ')
                    trend_types.append(f"Positive: {p_line}")
                elif line.startswith("Negative:"):
                    n_line= line.split('Negative:')[1][:50].replace('\n', ' ')
                    trend_types.append(f"Negative: {n_line}")
            logger.info("Trend types: %s", "; ".join(trend_types) if trend_types else "No trends identified")
            if "No challenges identified" in trends:
                logger.info("No negative trends identified in summary")

            # Format output
            time.sleep(2)  # Avoid rate limits
            format_chain = RunnableSequence(format_prompt | llm)
            output = format_chain.invoke(
                {
                    "trends": trends,
                    "city": city,
                    "state": state,
                    "sub_sector": sub_sector,
                    "segment": segment,
                    "scope": scope
                }
            ).content
            
            # Log extracted entities and metrics from formatted output
            entities = [match.group(1) for match in re.finditer(r"\*\*([^\*]+)\*\*", output) if match.group(1).strip()]
            logger.info("Extracted entities and metrics: %s", ", ".join(entities) if entities else "None")
            
        # Check for empty output
        if not output.strip():
            logger.error("LLM returned empty output, using fallback")
            time.sleep(2)  # Avoid rate limits
            chain = RunnableSequence(fallback_prompt | llm)
            output = chain.invoke(
                {
                    "main_industry": main_industry,
                    "sub_sector": sub_sector,
                    "segment": segment,
                    "state": state,
                    "city": city
                }
            ).content
            logger.info("Using fallback data scope: %s", "state" if state.lower() in output.lower() else "India")
        
        logger.info("Raw LLM output length: %d characters", len(output))
        # return output
        return {"success": True, "data": output}

    
    except Exception as e:
        logger.error("Error in get_market_trends: %s", str(e))
        # return f"Error fetching market trends: {str(e)}"
        return {"success": False, "data": None,"error": f"Error fetching market trends: {str(e)}"}