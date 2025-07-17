import logging
import json
import os
import asyncio
import re
from serpapi.google_search import GoogleSearch
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime, timedelta
from langchain_core.runnables import RunnableSequence
from langchain_groq import ChatGroq
from frontend_app.Market_Trends.prompts import decider_prompt
from typing import Dict
import configparser
from frontend_app.Ai_module.Query_Classification_And_Analysis import llm_70b_vers_creative, llm_70b_vers

# from langchain_openai import ChatOpenAI
config_file = '/home/mars/frappe-bench/apps/frontend_app/frontend_app/Log_management/mars.ini'
config = configparser.ConfigParser()
config.read(config_file)
api_key = config['Key']['SERPAPI_API_KEY']


# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/home/mars/frappe-bench/apps/frontend_app/frontend_app/Market_Trends/market_trends.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# File-based cache
CACHE_FILE = "/home/mars/frappe-bench/apps/frontend_app/frontend_app/Market_Trends/search_cache.json"
CACHE_EXPIRY_DAYS = 30

def load_cache() -> dict:
    """Load cache from file and prune expired entries."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            now = datetime.now()
            pruned_cache = {
                k: v for k, v in cache.items()
                if 'timestamp' in v and (now - datetime.fromisoformat(v['timestamp'])).days <= CACHE_EXPIRY_DAYS
            }
            if len(pruned_cache) < len(cache):
                logger.info("Pruned %d expired cache entries", len(cache) - len(pruned_cache))
                save_cache(pruned_cache)
            logger.info("Loaded cache, size: %d entries", len(pruned_cache))
            return pruned_cache
        except Exception as e:
            logger.error("Failed to load cache: %s", str(e))
    return {}

def save_cache(cache: dict) -> None:
    """Save cache to file."""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2)
        logger.info("Cache saved to %s, size: %d entries", CACHE_FILE, len(cache))
    except Exception as e:
        logger.error("Failed to save cache: %s", str(e))

def validate_inputs(main_industry: str, sub_sector: str, segment: str, state: str, city: str) -> None:
    """Validate input parameters."""
    logger.info("Validating inputs: %s, %s, %s, %s, %s", main_industry, sub_sector, segment, state, city)
    if not all([main_industry, sub_sector, segment, state, city]):
        logger.error("Missing input parameters")
        raise ValueError("All inputs (main_industry, sub_sector, segment, state, city) must be provided")
    for param in [main_industry, sub_sector, segment, state, city]:
        if not isinstance(param, str) or len(param.strip()) == 0:
            logger.error("Invalid input: %s must be a non-empty string", param)
            raise ValueError(f"Invalid input: {param} must be a non-empty string")

def cache_search(query: str) -> str:
    """Check file-based cache for query."""
    logger.info("Checking cache for query: %s", query)
    cache = load_cache()
    result = cache.get(query, {}).get('result')
    if result:
        logger.info("Cache hit, result length: %d characters", len(result))
    return result

def store_search(query: str, result: str) -> None:
    """Store search result in file-based cache with timestamp."""
    logger.info("Storing search result for query: %s, length: %d characters", query, len(result))
    cache = load_cache()
    cache[query] = {'result': result, 'timestamp': datetime.now().isoformat()}
    save_cache(cache)

async def async_search_web(query: str) -> str:
    """Perform async web search."""
    logger.info("Performing async web search: %s", query)
    cached_result = cache_search(query)
    if cached_result:
        logger.info("Returning cached search result")
        return cached_result
    
    if not api_key or len(api_key.strip()) == 0:
        logger.error("SERPAPI_API_KEY is missing or empty")
        raise ValueError("SERPAPI_API_KEY missing or empty in .env")

    params = {
        "q": query,
        "api_key": api_key,
        "num": 10,
    }
    try:
        search = GoogleSearch(params)
        # print(search.get_dict())
        results = search.get_dict().get("organic_results", [])
        result_str = "\n".join([f"{result.get('title', '')}: {result.get('snippet', '')}" for result in results])
        logger.info("Search successful, retrieved %d results", len(results))
        store_search(query, result_str)
        return result_str
    except Exception as e:
        logger.error("Search failed: %s", str(e))
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=10))
def safe_search_web(query: str) -> str:
    """Perform web search with retries, using async."""
    return asyncio.run(async_search_web(query))

def parse_search_results(search_results: str, city: str, state: str, sub_sector: str, segment: str) -> dict:
    """Count unique data points for each level in search results."""
    logger.info("Parsing search results for data point counts")
    counts = {"city": 0, "state": 0, "country": 0, "global": 0}
    
    # Keywords for matching
    city_synonyms = [
        city.lower(),
        city.lower().replace(" ", ""),
        "cochi" if city.lower() == "kochi" else "",
        "bengaluru" if city.lower().strip() == "bangalore" else "",
    ]
    city_synonyms = [s for s in city_synonyms if s]
    state_synonyms = [
        state.lower(),
        state.lower().replace(" ", ""),
        state.lower().replace(" ", "") + "'s",
        "tamilnadu" if state.lower() == "tamil nadu" else "",
    ]
    state_synonyms = [s for s in state_synonyms if s]
    city_pattern = re.compile(rf'({"|".join(city_synonyms)})', re.IGNORECASE)
    state_pattern = re.compile(rf'({"|".join(state_synonyms)})', re.IGNORECASE)
    india_pattern = re.compile(r'\bIndia\b|Indian|\bian\b', re.IGNORECASE)
    sector_terms = [
        sub_sector.lower(),
        segment.lower(),
        "ev",
        "electric vehicle",
        "electric vehicles",
    ]
    sector_pattern = re.compile(rf'({"|".join(map(re.escape, sector_terms))})', re.IGNORECASE)
    
    # Track unique data points
    city_points = set()
    state_points = set()
    country_points = set()
    global_points = set()
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', search_results)
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence or not sector_pattern.search(sentence):
            continue
            
        # City-level
        if city_pattern.search(sentence):
            city_points.add(sentence)
        # State-level
        elif state_pattern.search(sentence):
            state_points.add(sentence)
        # Country-level
        elif india_pattern.search(sentence):
            country_points.add(sentence)
        # Global (no specific location)
        else:
            global_points.add(sentence)
    
    counts["city"] = len(city_points)
    counts["state"] = len(state_points)
    counts["country"] = len(country_points)
    counts["global"] = len(global_points)
    
    # If no explicit location but sector-relevant, count as country (India)
    if not any([counts["city"], counts["state"], counts["country"]]) and counts["global"] > 0:
        counts["country"] = counts["global"]
        counts["global"] = 0
    
    logger.info("Data point counts: %s", counts)
    return counts

def extract_trend_allocation(output: str) -> Dict[str, int]:
    """
    Extracts trend allocation from LLM output, handling various formats.

    Ensures:
    - Parses valid JSON, code blocks, or loose text.
    - Validates sum of trends equals 5.
    - Returns default allocation if parsing fails.

    Returns:
        Dict with keys 'city', 'state', 'country', 'global', each with an integer value.
    """
    default_allocation = {"city": 0, "state": 0, "country": 0, "global": 0}

    # 1) Direct JSON Parsing
    try:
        data = json.loads(output.strip())
        if isinstance(data, dict) and all(k in data for k in ["city", "state", "country", "global"]):
            allocation = {k: int(data[k]) for k in ["city", "state", "country", "global"]}
            if sum(allocation.values()) == 5:
                return allocation
    except (json.JSONDecodeError, ValueError, TypeError, KeyError):
        pass

    # 2) Extract JSON from code blocks
    code_blocks = re.findall(r'```(?:json)?\s*(.*?)\s*```', output, flags=re.DOTALL)
    for block in code_blocks:
        try:
            data = json.loads(block.strip())
            if isinstance(data, dict) and all(k in data for k in ["city", "state", "country", "global"]):
                allocation = {k: int(data[k]) for k in ["city", "state", "country", "global"]}
                if sum(allocation.values()) == 5:
                    return allocation
        except (json.JSONDecodeError, ValueError, TypeError, KeyError):
            pass

    # 3) Regex-based extraction (full JSON structure)
    pattern_braces = re.compile(
        r'\{\s*'
        r'"city"\s*:\s*(\d+)\s*,\s*'
        r'"state"\s*:\s*(\d+)\s*,\s*'
        r'"country"\s*:\s*(\d+)\s*,\s*'
        r'"global"\s*:\s*(\d+)\s*'
        r'\s*\}',
        flags=re.DOTALL
    )
    match_braces = pattern_braces.search(output)
    if match_braces:
        allocation = {
            "city": int(match_braces.group(1)),
            "state": int(match_braces.group(2)),
            "country": int(match_braces.group(3)),
            "global": int(match_braces.group(4)),
        }
        if sum(allocation.values()) == 5:
            return allocation

    # 4) Regex-based loose extraction
    pattern_loose = re.compile(
        r'"city"\s*:\s*(\d+)|'
        r'"state"\s*:\s*(\d+)|'
        r'"country"\s*:\s*(\d+)|'
        r'"global"\s*:\s*(\d+)',
        flags=re.DOTALL
    )
    matches = pattern_loose.findall(output)
    allocation = default_allocation.copy()
    for match in matches:
        if match[0]: allocation["city"] = int(match[0])
        if match[1]: allocation["state"] = int(match[1])
        if match[2]: allocation["country"] = int(match[2])
        if match[3]: allocation["global"] = int(match[3])
    if sum(allocation.values()) == 5:
        return allocation

    logger.warning("Failed to extract valid allocation, returning default")
    return default_allocation

def decide_trend_allocation(
    search_results: str,
    main_industry: str,
    sub_sector: str,
    segment: str,
    state: str,
    city: str
) -> dict:
    """Process decider_prompt to allocate exactly 5 trends based on search result data volume."""
    logger.info("Deciding trend allocation for query")
    
    # Initialize LLM
    llm = llm_70b_vers_creative
    
    # Get LLM response
    try:
        chain = RunnableSequence(decider_prompt | llm)
        response = chain.invoke({
            "search_results": search_results,
            "main_industry": main_industry,
            "sub_sector": sub_sector,
            "segment": segment,
            "state": state,
            "city": city
        }).content
        print("="*100, "\n\n", response, "\n\n", "="*100)
        logger.debug("Raw LLM response: %s", response[:500])  # Log first 500 chars
        
        # Extract allocation
        allocation = extract_trend_allocation(response)
        if sum(allocation.values()) != 5:
            raise ValueError(f"Invalid allocation sum: {sum(allocation.values())}")
        
        logger.info("Trend allocation from LLM: %s", allocation)
        return allocation
    except Exception as e:
        logger.warning("Error in LLM allocation: %s, using fallback", str(e))
        # Fallback allocation based on data counts
        data_counts = parse_search_results(search_results, city, state, sub_sector, segment)
        allocation = {"city": 0, "state": 0, "country": 0, "global": 0}
        remaining = 5
        
        # Prioritize city
        if data_counts["city"] >= 3:
            allocation["city"] = min(3, remaining)
        elif data_counts["city"] > 0:
            allocation["city"] = 1
        remaining -= allocation["city"]
        
        # Prioritize state
        if data_counts["state"] >= 3 and remaining >= 2:
            allocation["state"] = min(3, remaining)
        elif data_counts["state"] > 0 and remaining > 0:
            allocation["state"] = min(2, remaining)
        remaining -= allocation["state"]
        
        # Country
        if data_counts["country"] >= 3 and remaining >= 2:
            allocation["country"] = min(3, remaining)
        elif data_counts["country"] > 0 and remaining > 0:
            allocation["country"] = min(2, remaining)
        remaining -= allocation["country"]
        
        # Global
        allocation["global"] = remaining
        
        logger.info("Fallback trend allocation: %s", allocation)
        return allocation