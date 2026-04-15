from frontend_app.Analytics_module.Industry_form_scratch.query_to_build_industry_from_scratch import *
import frappe
import pandas as pd
from frontend_app.Management_Class.helpers.progress import insert_process,update_process
import time
import numpy as np
import traceback
from datetime import datetime
import json
from frontend_app.Management_Class.helpers.utility import randomSentences
import gc
import configparser
import os, time, json, math
from urllib.parse import quote
import requests
from shapely.geometry import shape, Point
from shapely.prepared import prep
from sklearn.neighbors import BallTree
import matplotlib.pyplot as plt
from typing import Optional, List, Dict, Any, Generator
from frontend_app.Market_Trends.getting_market_trends import retrieving_market_trends
import warnings
# configs
warnings.filterwarnings("ignore")
base_dir = os.path.expanduser("~")
config_file = os.path.join(base_dir, "frappe-bench/apps/frontend_app/frontend_app/Log_management/mars.ini")
# config_file = '/home/marsapplication/frappe-bench/apps/frontend_app/frontend_app/Log_management/mars.ini'
config = configparser.ConfigParser()
config.read(config_file)

# api_key = config['Key']['groq_key']
# location_aware_frappe_api_key = config['Frappe_api_key_and_secret_for_Location_Aware_Logic']['location_aware_frappe_api_key']
# location_aware_frappe_api_secret = config['Frappe_api_key_and_secret_for_Location_Aware_Logic']['location_aware_frappe_api_secret']
# location_aware_live_base_url = config['Frappe_api_key_and_secret_for_Location_Aware_Logic']['location_aware_live_base_url']

location_aware_frappe_api_key = config['Frappe_api_key_and_secret']['frappe_api_key']
location_aware_frappe_api_secret = config['Frappe_api_key_and_secret']['frappe_api_secret']
location_aware_live_base_url = config['Frappe_api_key_and_secret']['ritu_local_base_url']

# -------------- CONFIG (tune these) ----------------
SOFT_BOUNDARY_KM = 20
VERY_LONG_DISTANCE_KM = 100
DECENT_THRESHOLD = 3.0
EARTH_RADIUS_KM = 6371.0
USER_AGENT = "LocationRanker/1.0 (sanketmaheta99@gmail.com)"
GEOCODE_CACHE_FILE = "geocode_cache.json"

# Score tuning (you can expose these to UI)
BOOST_TIER1_IF_DECENT = 1000
BOOST_TIER2_BASE = 500
TIER2_KM_PENALTY_PER_KM = 10
TIER3_BASE = 200
TIER3_KM_PENALTY_PER_KM = 20
VERY_LONG_DISTANCE_PENALTY = -1000
OUT_OF_BOUNDS_PENALTY = -2000

# Boundary settings
RSOFT_KM           = 20.0    # soft radius
P_MAX              = 0.30    # max penalty at hard boundary (30%)

# =============================================================================
# CONSTANTS
# =============================================================================

EARTH_RADIUS_KM   = 6371.0
USER_AGENT        = "LocationRanker/1.0 (test@local.com)"
GEOCODE_CACHE_FILE = "geocode_cache_test.json"

R0_KM             = 20.0
P0                = 0.20
P_MIN             = 0.03
K_DECAY           = 0.40
MIN_MARGIN_KM_ABS = 2.0
MIN_MARGIN_FRAC   = 0.05

USER_DESCISION = "YES"

#########################################################################################################################################################################

########################  LOCATION AWARE RANKING LOGIC ##########################

def _nominatim_polygon_search(query: str) -> list:
    """
    Calls Nominatim for a query, returns polygon features only.
    """
    url     = (f"https://nominatim.openstreetmap.org/search"
               f"?format=geojson&polygon_geojson=1&q={quote(query)}")
    headers = {"User-Agent": USER_AGENT}
    try:
        r        = requests.get(url, headers=headers, timeout=30)
        raw      = r.json()
        time.sleep(1.1)   # Nominatim rate limit
        features = raw.get("features", [])
        return [
            f for f in features
            if f.get("geometry", {}).get("type") in ("Polygon", "MultiPolygon")
        ]
    except Exception as e:
        print(f"  [Nominatim ERROR] {query}: {e}")
        return []

def fetch_district_polygon(location_query: str) -> dict:
    """
    Fetches the DISTRICT level polygon (admin_level=6) for the given location.

    This single polygon is used for:
        - Centroid  → reference point for all distance calculations
        - Inside check → is this property inside the district?
        - Rsoft / Rhard are measured from this district centroid

    For "Bharuch, Gujarat, India":
        Returns Bharuch district polygon
        Centroid ≈ geographic center of Bharuch district
        Ankleshwar, Vagra, Jambusar → inside_district = True
        Vadodara, Surat             → inside_district = False

    Query strategy (tries in order, stops at first district-level match):
        1. "{place} district, {state}, India"   → most explicit
        2. "{place}, {state}, India"            → standard
        3. "{place} district, India"            → state-agnostic fallback
        4. "{place}, India"                     → last resort
    """
    place = location_query.split(",")[0].strip()
    state = location_query.split(",")[1].strip() if "," in location_query else "Gujarat"

    queries = [
        f"{place} district, {state}, India",
        f"{place}, {state}, India",
        f"{place} district, India",
        f"{place}, India",
    ]

    print(f"\n  [district polygon] Fetching district polygon for: {location_query}")

    all_features = []
    seen_ids     = set()

    for q in queries:
        features = _nominatim_polygon_search(q)
        print(f"    '{q}' → {len(features)} polygon(s)")

        for f in features:
            osm_id = (f.get("properties") or {}).get("osm_id") or id(f)
            if osm_id not in seen_ids:
                seen_ids.add(osm_id)
                all_features.append(f)

        # If any result at district level (admin_level=5 or 6) found, stop
        for f in features:
            try:
                admin = int((f.get("properties") or {}).get("admin_level", 99))
                if admin in (5, 6):
                    print(f"    District-level polygon found (admin_level={admin}), stopping search")
                    break
            except Exception:
                pass
        else:
            continue
        break

    if not all_features:
        print(f"  [district polygon] Nothing found for: {location_query}")
        return {"type": "FeatureCollection", "features": []}

    # Pick the feature closest to admin_level=6 (district)
    def score(f):
        props = f.get("properties", {}) or {}
        try:
            # Strongly prefer admin_level 6 (district) or 5 (division)
            admin       = int(props.get("admin_level", 99))
            admin_score = abs(6 - admin) * 300
        except Exception:
            admin_score = 3000
        # Tiebreaker: slightly prefer larger bbox (district > city)
        bbox = f.get("bbox", [])
        if len(bbox) == 4:
            area = (abs(float(bbox[2]) - float(bbox[0]))
                    * abs(float(bbox[3]) - float(bbox[1])))
            # Larger area = more district-like → lower penalty
            area_score = -area * 100
        else:
            area_score = 0
        return admin_score + area_score

    best       = min(all_features, key=score)
    best_props = best.get("properties", {}) or {}
    best_admin = best_props.get("admin_level", "?")
    best_name  = best_props.get("display_name", "?")[:70]

    print(f"  [district polygon] SELECTED admin_level={best_admin} → {best_name}")

    return {"type": "FeatureCollection", "features": [best]}


# This function is used for extraction valid location query from ai response
def extract_location_robust(data_dict):
    """
    More robust version with additional checks and flexibility
    """
    
    # Safely get location data
    try:
        # state_dict = data_dict.get('state', {})
        location_list = data_dict.get('Location', [])
        if not location_list or not isinstance(location_list, list):
            return "Not Available in List"
        
        location_dict = location_list[0]
        if not isinstance(location_dict, dict):
            return "Not Available in List"
        
        # Define hierarchy
        hierarchy_fields = ['Village', 'Area', 'City', 'Taluka', 'District']
        
        # Check each field in priority order
        for field in hierarchy_fields:
            field_value = location_dict.get(field)
            
            # Check if value is meaningful
            if is_meaningful_value(field_value):
                state_value = location_dict.get('State')
                
                if is_meaningful_value(state_value):
                    return f"{field_value}, {state_value}, India"
                else:
                    return str(field_value)
        
        # No meaningful values found in hierarchy
        return "Not Available in List"
        
    except (KeyError, IndexError, AttributeError, TypeError):
        return "Not Available in List"

# This function is also used as a helper function to the above function(extract_location_robust) for extraction valid location query from ai response
def is_meaningful_value(value):
    """
    Check if a value is meaningful (not None, not empty, not unavailable)
    """
    if value is None:
        return False
    
    str_value = str(value).strip().lower()
    
    # List of values that indicate "not available"
    unavailable_terms = [
        'not available in list',
        'none',
        'null',
        'na',
        'n/a',
        '',
        'undefined',
        'unknown'
    ]
    
    return str_value not in unavailable_terms and len(str_value) > 0

# ----------------- HTTP helper ----------------------
def http_get(url):
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r

# # ----------------- Boundary fetching ----------------
def fetch_raw_geojson_from_nominatim(query):
    q = quote(query)
    url = f"https://nominatim.openstreetmap.org/search?format=geojson&polygon_geojson=1&q={q}"
    r = http_get(url)
    return r.json()

def pick_best_polygon_feature(features, query_hint=None):
    """
    Prefer features by:
      1) admin_level closeness to 8 (city-level) if available,
      2) smaller bounding box area (more specific),
      3) small text bonus if query_hint appears (tie-breaker only).
    Returns a single feature.
    """
    poly = [f for f in features if f.get("geometry", {}).get("type") in ("Polygon","MultiPolygon")]
    if not poly:
        return None

    def score(f):
        props = f.get("properties", {}) or {}
        # admin_level score (prefer 8/9)
        admin = props.get("admin_level")
        try:
            admin_int = int(admin)
            admin_penalty = abs(8 - admin_int) * 100  # big influence
        except Exception:
            admin_penalty = 1000

        # bbox area fallback
        bbox = f.get("bbox")
        if bbox and len(bbox) == 4:
            minlon,minlat,maxlon,maxlat = map(float, bbox)
            area = abs(maxlon - minlon) * abs(maxlat - minlat)
            area_penalty = area * 1e6
        else:
            area_penalty = 1e6

        text_bonus = 0
        if query_hint:
            name = ((props.get("display_name") or "") + (props.get("name") or "")).lower()
            if query_hint.lower() in name:
                text_bonus = -50  # small bonus but not decisive

        return admin_penalty + area_penalty + text_bonus

    best = min(poly, key=score)
    return best

def fetch_best_boundary(query):
    """Return a FeatureCollection with exactly one chosen polygon feature (or empty)."""
    raw = fetch_raw_geojson_from_nominatim(query)
    features = raw.get("features", [])
    best = pick_best_polygon_feature(features, query_hint=query)
    if not best:
        return {"type":"FeatureCollection","features":[]}
    return {"type":"FeatureCollection", "features":[best]}

# ----------------- Build checkers & BallTree ----------------
def build_inside_checker(feature_collection):
    if not feature_collection or not feature_collection.get("features"):
        return lambda lon, lat: False
    geom = feature_collection["features"][0]["geometry"]
    polygon = prep(shape(geom))
    return lambda lon, lat: polygon.covers(Point(lon, lat))

def extract_boundary_coords(feature_collection):
    if not feature_collection or not feature_collection.get("features"):
        return np.zeros((0,2))
    geom = feature_collection["features"][0]["geometry"]
    coords = []
    if geom["type"] == "Polygon":
        for ring in geom["coordinates"]:
            for lon, lat in ring:
                coords.append([lat, lon])
    elif geom["type"] == "MultiPolygon":
        for poly in geom["coordinates"]:
            for ring in poly:
                for lon, lat in ring:
                    coords.append([lat, lon])
    return np.array(coords)

def build_balltree(boundary_coords):
    if boundary_coords.shape[0] == 0:
        return None
    return BallTree(np.radians(boundary_coords), metric='haversine')

def distance_km_to_boundary(tree, lat, lon):
    if tree is None:
        return float('inf')
    dist_rad, _ = tree.query(np.radians([[lat, lon]]), k=1)
    return dist_rad[0][0] * EARTH_RADIUS_KM

def build_border_balltree(feature_collection):
    """
    Build BallTree from ALL border ring points of the district polygon.
    Used to compute distance from any property to the nearest border point.
    """
    if not feature_collection or not feature_collection.get("features"):
        return None
    geom   = feature_collection["features"][0]["geometry"]
    coords = []
    if geom["type"] == "Polygon":
        for ring in geom["coordinates"]:
            for lon, lat in ring:
                coords.append([lat, lon])
    elif geom["type"] == "MultiPolygon":
        for poly in geom["coordinates"]:
            for ring in poly:
                for lon, lat in ring:
                    coords.append([lat, lon])
    if not coords:
        return None
    arr = np.array(coords)
    print(f"  [BallTree] Built from {len(arr)} district border points")
    return BallTree(np.radians(arr), metric='haversine')

def dist_to_border_km(border_tree, lat, lon):
    """Distance in km from (lat, lon) to nearest district border point."""
    if border_tree is None:
        return float('inf')
    dist_rad, _ = border_tree.query(np.radians([[lat, lon]]), k=1)
    return dist_rad[0][0] * EARTH_RADIUS_KM

def haversine_km(lat1, lon1, lat2, lon2):
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1); dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi/2)**2
         + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2)
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))

def compute_expansion_fraction(rsoft):
    return P_MIN + (P0 - P_MIN) * math.exp(-K_DECAY * ((rsoft / R0_KM) - 1.0))

def compute_rhard(rsoft):
    p = compute_expansion_fraction(rsoft)
    rhard = rsoft * (1.0 + p)
    return max(rhard, rsoft + max(MIN_MARGIN_KM_ABS, MIN_MARGIN_FRAC * rsoft))

# ---------------- Geocoding w/ cache -----------------
def load_geocode_cache():
    if os.path.exists(GEOCODE_CACHE_FILE):
        try:
            with open(GEOCODE_CACHE_FILE,'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_geocode_cache(cache):
    with open(GEOCODE_CACHE_FILE,'w') as f:
        json.dump(cache, f, indent=2)

######################################################################################################

# original option
def geocode_area(area_name, state="Gujarat", country="India", cache=None):
    if cache is None:
        cache = load_geocode_cache()
    key = f"{area_name},{state},{country}".lower()
    if key in cache:
        return cache[key]
    full = quote(f"{area_name}, {state}, {country}")
    url = f"https://nominatim.openstreetmap.org/search?format=json&limit=1&q={full}"
    try:
        r = http_get(url)
        data = r.json()
        time.sleep(1.0)
        if data:
            lat = float(data[0]['lat']); lon = float(data[0]['lon'])
            cache[key] = [lat, lon]
            save_geocode_cache(cache)
            return [lat, lon]
        cache[key] = None
        save_geocode_cache(cache)
        return None
    except Exception as e:
        print("Geocode error:", e)
        return None
    


######################################################################################################

# --------------- Classification & scoring ----------------
def classify_property(lat, lon, is_inside_city, is_inside_state, city_tree):
    if is_inside_city(lon, lat):
        return 1, 0.0
    d_km = distance_km_to_boundary(city_tree, lat, lon)
    if d_km <= SOFT_BOUNDARY_KM and is_inside_state(lon, lat):
        return 2, d_km
    if is_inside_state(lon, lat):
        return 3, d_km
    return 4, d_km

def compute_final_score(quality, tier, distance_km, has_decent_tier1):
    if tier == 1:
        return quality + (BOOST_TIER1_IF_DECENT if has_decent_tier1 else -500)
    if tier == 2:
        return quality + (BOOST_TIER2_BASE - TIER2_KM_PENALTY_PER_KM * distance_km)
    if tier == 3:
        if distance_km > VERY_LONG_DISTANCE_KM:
            return quality + VERY_LONG_DISTANCE_PENALTY
        return quality + (TIER3_BASE - TIER3_KM_PENALTY_PER_KM * distance_km)
    return quality + OUT_OF_BOUNDS_PENALTY

# --------------- Decent-enough logic (improved) --------------
def decide_has_decent_tier1(df, tier1_df, absolute_threshold=DECENT_THRESHOLD, relative_fraction=0.7, min_count=1):
    if len(tier1_df) == 0:
        return False
    max_global = df['Aggregate Property Performance Score (APPS)'].max()
    absolute_ok = (tier1_df['Aggregate Property Performance Score (APPS)'] >= absolute_threshold).any()
    relative_ok = (tier1_df['Aggregate Property Performance Score (APPS)'] >= (relative_fraction * max_global)).any()
    count_ok = (tier1_df['Aggregate Property Performance Score (APPS)'] >= absolute_threshold).sum() >= min_count
    return absolute_ok or relative_ok or count_ok

# --------------- Search expansion hook (placeholder) ----------------
def expand_search_within_hard_boundary(hard_boundary_geojson, needed_count=10):
    """
    Placeholder: integrate with your property store.
    Given a hard boundary (geojson polygon), query your DB / spatial index
    for more candidate properties inside the polygon and return them as a DataFrame.
    This function must be implemented by your backend:
      - Example: SELECT * FROM properties WHERE ST_Within(geom, hard_boundary) LIMIT 1000
    For now, raise NotImplementedError to avoid silent failure.
    """
    raise NotImplementedError("Integrate this function with your property database to expand candidate set.")

def compute_penalty(d_from_border, rsoft, rhard):
    """
    d_from_border = distance from property to nearest district border point.
    Inside district properties are handled separately (penalty = 0 always).
    """
    if d_from_border <= rsoft:
        return 0.0
    if d_from_border <= rhard:
        band = rhard - rsoft
        return min(P_MAX * (d_from_border - rsoft) / band, P_MAX) if band > 0 else P_MAX
    return 1.0

def compute_final_score(base, penalty):
    return base * (1.0 - penalty)

def normalize_0_10(values):
    mn, mx = min(values), max(values)
    if mn == mx:
        return [5.0] * len(values)
    return [(v - mn) / (mx - mn) * 10.0 for v in values]

# --------------- Explainability helper ----------------
def explain_property(row):
    expl = {
        "Property_ID": row['Property_ID'],
        "tier": row['tier'],
        "distance_km": row['distance_from_city_km'],
        "quality": row['Aggregate Property Performance Score (APPS)'],
        "final_score": row['final_score'],
    }
    # Add how score components contributed
    tier = row['tier']; d = row['distance_from_city_km']; q = row['Aggregate Property Performance Score (APPS)']
    if tier == 1:
        expl['location_boost'] = (BOOST_TIER1_IF_DECENT if row.get('has_decent_tier1') else -500)
    elif tier == 2:
        expl['location_boost'] = (BOOST_TIER2_BASE - TIER2_KM_PENALTY_PER_KM * d)
    elif tier == 3:
        if d > VERY_LONG_DISTANCE_KM:
            expl['location_boost'] = VERY_LONG_DISTANCE_PENALTY
        else:
            expl['location_boost'] = (TIER3_BASE - TIER3_KM_PENALTY_PER_KM * d)
    else:
        expl['location_boost'] = OUT_OF_BOUNDS_PENALTY
    return expl

# --------------- Experimental: alternate scoring functions ------------
def alt_score_logistic(quality, tier, distance_km, has_decent_tier1):
    """
    Example of a softer scoring scheme (useful from location_example.ipynb).
    Use this as an experiment without changing the main scoring contract.
    """
    # quality scaled
    q = quality
    if tier == 1:
        boost = BOOST_TIER1_IF_DECENT if has_decent_tier1 else -500
        return q + boost
    if tier == 2:
        # logistic decay with distance
        decay = 1 / (1 + math.exp((distance_km - SOFT_BOUNDARY_KM/2)/5))
        return q + BOOST_TIER2_BASE * decay
    if tier == 3:
        decay = max(0, 1 - distance_km/VERY_LONG_DISTANCE_KM)
        return q + TIER3_BASE * decay
    return q + OUT_OF_BOUNDS_PENALTY

def resolve_coordinates(df, cache):
    print("\n[STEP 2] Resolving coordinates...")
    df = df.copy()
    df['area_name'] = df['Property_ID'].apply(
        lambda x: (x.split('--')[1] if '--' in x else x).split('-')[0])
    lats, lons = [], []
    for _, row in df.iterrows():
        lat = lon = None
        if row.get('lat_long'):
            try:
                parts = [float(x.strip()) for x in str(row['lat_long']).split(',')]
                if len(parts) >= 2:
                    lat, lon = parts[0], parts[1]
                    print(f"  {row['Property_ID']} -> Frappe: {lat}, {lon}")
            except Exception:
                pass
        if lat is None:
            q      = f"{row.get('area_name','')}, {row.get('state','Gujarat')}, India"
            coords = geocode_place(q, cache)
            if coords:
                lat, lon = coords[0], coords[1]
                print(f"  {row['Property_ID']} -> Geocoded: {lat}, {lon}")
            else:
                print(f"  {row['Property_ID']} -> FAILED")
        lats.append(lat); lons.append(lon)
    df['latitude']  = lats
    df['longitude'] = lons
    before = len(df)
    df = df.dropna(subset=['latitude', 'longitude']).reset_index(drop=True)
    print(f"  {len(df)}/{before} properties resolved")
    df['latitude']  = df['latitude'].astype(float)
    df['longitude'] = df['longitude'].astype(float)
    return df


def fetch_frappe_doc_universal(
    doctype: str,
    identifier: str,
    *,
    fields: list[str] | None = None,
    timeout: int = 30,
    debug: bool = False,
):

    # base_url = ritu_local_base_url
    base_url = location_aware_live_base_url

    headers = {
        "Authorization": f"token {location_aware_frappe_api_key}:{location_aware_frappe_api_secret}",
        "Content-Type": "application/json",
        "Expect": "",
    }

    doctype_path = quote(doctype, safe="")
    name_path = quote(identifier, safe="")

    # ---------- Step 1: try by primary key ----------
    url = f"{base_url.rstrip('/')}/api/resource/{doctype_path}/{name_path}"
    params = {}

    if fields:
        params["fields"] = json.dumps(fields)

    r = requests.get(url, headers=headers, params=params, timeout=timeout)
    data = r.json()

    if debug:
        print("[TRY name]", r.url)

    # ---------- success case ----------
    if isinstance(data, dict) and "exc_type" not in data:
        return data

    # ---------- Step 2: fallback to filter lookup ----------
    # Works for File and other non-standard doctypes
    fallback_params = {
        "filters": json.dumps({"file_name": identifier})
    }

    if fields:
        fallback_params["fields"] = json.dumps(fields)

    fallback_url = f"{base_url.rstrip('/')}/api/resource/{doctype_path}"

    r2 = requests.get(
        fallback_url,
        headers=headers,
        params=fallback_params,
        timeout=timeout
    )

    fallback_data = r2.json()

    if debug:
        print("[FALLBACK filter]", r2.url)

    return fallback_data

def fetch_all_frappe_records(
    doctype: str,
    *,
    filters: Dict[str, Any] | None = None,
    fields: List[str] | None = None,
    order_by: str | None = None,
    limit_page_length: int = 1000,
    timeout: int = 30,
    debug: bool = False,
    verify_ssl: bool = False,
    max_records: int = 0,  # 0 means no limit
    include_deleted: bool = False,
) -> List[Dict[str, Any]]:
    """
    Fetch ALL records from a Frappe doctype with pagination support.
    
    Args:
        doctype: Name of the doctype to fetch
        filters: Dictionary of filters (e.g., {"status": "Active"})
        fields: List of field names to fetch
        order_by: Field to order by (e.g., "creation desc")
        limit_page_length: Records per page (max 1000 for Frappe API)
        timeout: Request timeout in seconds
        debug: Print debug information
        verify_ssl: Verify SSL certificates
        max_records: Maximum number of records to fetch (0 = no limit)
        include_deleted: Include deleted records
    
    Returns:
        List of all records from the doctype
    """
    
    base_url = location_aware_live_base_url
    headers = {
        "Authorization": f"token {location_aware_frappe_api_key}:{location_aware_frappe_api_secret}",
        "Content-Type": "application/json",
        "Expect": "",
    }
    
    doctype_path = quote(doctype, safe="")
    url = f"{base_url.rstrip('/')}/api/resource/{doctype_path}"
    
    all_records = []
    start = 0
    total_fetched = 0
    page = 0
    
    while True:
        page += 1
        params = {
            "limit_start": start,
            "limit_page_length": limit_page_length,
        }
        
        if filters:
            params["filters"] = json.dumps(filters)
        
        if fields:
            params["fields"] = json.dumps(fields)
        
        if order_by:
            params["order_by"] = order_by
        
        if include_deleted:
            params["include_deleted"] = "1"
        
        if debug:
            print(f"[PAGE {page}] Fetching {limit_page_length} records starting from {start}")
        
        try:
            r = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout,
                verify=verify_ssl,
            )
            
            r.raise_for_status()
            data = r.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching records: {e}")
            if debug:
                print(f"URL: {url}")
                print(f"Params: {params}")
            break
        
        # Handle different response formats
        if isinstance(data, dict):
            if "data" in data:
                page_records = data["data"]
            elif "exc_type" in data:
                print(f"API Error: {data.get('exc', 'Unknown error')}")
                break
            else:
                page_records = []
        else:
            page_records = data
        
        if not page_records:
            if debug:
                print(f"[PAGE {page}] No more records found")
            break
        
        records_count = len(page_records)
        all_records.extend(page_records)
        total_fetched += records_count
        
        if debug:
            print(f"[PAGE {page}] Fetched {records_count} records (Total: {total_fetched})")
        
        # Check if we've reached the maximum requested records
        if max_records > 0 and total_fetched >= max_records:
            if total_fetched > max_records:
                all_records = all_records[:max_records]
            if debug:
                print(f"Reached maximum limit of {max_records} records")
            break
        
        # If we got fewer records than requested, we've reached the end
        if records_count < limit_page_length:
            if debug:
                print(f"Reached end of records (got {records_count} < {limit_page_length})")
            break
        
        # Prepare for next page
        start += limit_page_length
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.1)
    
    if debug:
        print(f"Total records fetched: {len(all_records)}")
    
    return all_records

def fetch_property_data(property_ids):
    print("\n[STEP 1] Fetching from Frappe DB...")
    area_records = fetch_all_frappe_records(
        doctype="Area", fields=["district", "state"],
        order_by="creation desc", limit_page_length=500, verify_ssl=False)
    print(f"  Got {len(area_records)} Area records")

    district_to_state = {}
    for rec in area_records:
        d, s = rec.get("district"), rec.get("state")
        if d and s and d not in district_to_state:
            district_to_state[d] = s

    rows = []
    for prop_id in property_ids:
        print(f"  Fetching: {prop_id}")
        try:
            doc      = fetch_frappe_doc_universal("Survey No", prop_id)
            data     = doc.get("data", {})
            district = data.get("district")
            lat_long = data.get("latitude_longitude")
            state    = district_to_state.get(district, "Gujarat")
            rows.append({"Property_ID": prop_id, "district": district,
                         "state": state, "lat_long": lat_long})
            print(f"    district={district}  state={state}  lat_long={lat_long}")
        except Exception as e:
            print(f"    ERROR: {e}")
            rows.append({"Property_ID": prop_id, "district": None,
                         "state": "Gujarat", "lat_long": None})
    print(pd.DataFrame(rows))
    return pd.DataFrame(rows)

def getting_appropriate_state_for_each_property(property_dataframe):

    # this functions gets the state for each property of the df(which we are getting as an input) and also latitude, longitude if available.
    # example:- for 1078--Kalavad-Jamnagar, state is gujarat.

    all_records_doctype_details = fetch_all_frappe_records(
        doctype="Area",
        fields=["district", "state"],
        order_by="creation desc",
        limit_page_length=500,
        debug=True,
        verify_ssl=False,
    )

    frappe.log_error("all_records_doctype_details",f"{all_records_doctype_details}")

    property_name_list = property_dataframe["Property_ID"].tolist()
    frappe.log_error("property_name_list",f"{property_name_list}")

    property_names_with_their_states = {}
    
    for property in property_name_list:
        respective_doctype_record_details = fetch_frappe_doc_universal(doctype = "Survey No", identifier=property)
        district_value = respective_doctype_record_details["data"]["district"]
        frappe.log_error("district_value",f"{district_value}")
        try:
            lat_long = respective_doctype_record_details["data"]["latitude_longitude"]
        except:
            lat_long = None

        state_value = []
        seen_states = set()  # Track already seen states

        for record in all_records_doctype_details:
            if record["district"] == district_value:
                state = record["state"]
                if state not in seen_states:
                    seen_states.add(state)
                    state_value.append(state)
                    property_names_with_their_states[property] = {"state": state, "lat_long": lat_long}
                    # print(state)  # Print only unique state

    return property_names_with_their_states

# this function will normalize final scores to a 0-10 scale.
def normalize_scores_to_range(df, score_column='final_score', new_column='normalized_score', target_min=0, target_max=10):
    """
    Normalizes scores to a specified range (default 0-10) using min-max scaling.
    
    Formula: normalized = (score - min) / (max - min) * (target_max - target_min) + target_min
    
    Handles edge case where all scores are identical (returns target_midpoint).
    """
    scores = df[score_column].astype(float)
    
    min_score = scores.min()
    max_score = scores.max()
    
    # Edge case: all scores identical
    if min_score == max_score:
        df[new_column] = (target_min + target_max) / 2
        return df
    
    # Min-max normalization
    normalized = (scores - min_score) / (max_score - min_score) * (target_max - target_min) + target_min
    
    df[new_column] = normalized
    
    print(f"\n=== Score Normalization ===")
    print(f"Original range: [{min_score:.2f}, {max_score:.2f}]")
    print(f"Normalized range: [{normalized.min():.2f}, {normalized.max():.2f}]")
    
    return df

# Alternative: Sigmoid-based normalization (preserves ranking better for extreme values)
def normalize_scores_sigmoid(df, score_column='final_score', new_column='normalized_score', target_min=0, target_max=10):
    """
    Uses sigmoid function to normalize, which handles extreme outliers better.
    Maps any range to 0-1, then scales to target range.
    """
    import math
    
    scores = df[score_column].astype(float)
    
    # Standardize to z-scores first
    mean_score = scores.mean()
    std_score = scores.std() or 1  # avoid division by zero
    
    z_scores = (scores - mean_score) / std_score
    
    # Sigmoid: 1 / (1 + exp(-z))
    sigmoid_scores = 1 / (1 + z_scores.apply(lambda z: math.exp(-z)))
    
    # Scale to target range
    normalized = sigmoid_scores * (target_max - target_min) + target_min
    
    df[new_column] = normalized
    
    print(f"\n=== Sigmoid Normalization ===")
    print(f"Original range: [{scores.min():.2f}, {scores.max():.2f}]")
    print(f"Normalized range: [{normalized.min():.2f}, {normalized.max():.2f}]")
    
    return df

# ----------------- Full pipeline runner (integrates everything) ----------------
def run_location_postprocessor(df_properties, user_location_query, state=None,
                               scoring_fn=compute_final_score, expand_if_poor=True,
                               min_local_candidates=1):
    """
    df_properties must contain:
      - property_id
      - property_suitability_score
      - latitude (optional, if missing geocode will be used)
      - longitude (optional)
      - area_name (optional)
    """
    df = df_properties.copy()
    frappe.log_error("df",f"{df}")

    # function to get each property's state and lat_long
    state_and_lat_long = getting_appropriate_state_for_each_property(df_properties)
    frappe.log_error("state_and_lat_long",f"{state_and_lat_long}")

    # 1) enrich coordinates (geocode area_name when lat/lon missing)
    cache = load_geocode_cache()
    if ('latitude' not in df.columns) or ('longitude' not in df.columns) or df[['latitude','longitude']].isnull().any().any():
        # try geocoding by area_name if exists
        if 'area_name' not in df.columns:
            df['area_name'] = df['Property_ID'].apply(lambda x: (x.split('--')[1] if '--' in x else x).split('-')[0])
        coords_map = {}
        unique_areas = df['area_name'].unique().tolist()
        print("unique_areas", unique_areas)
        # for a in unique_areas:
        for property in state_and_lat_long:
            # if a in coords_map:
            if property in coords_map:
                continue
            # for property in state_and_lat_long:
            # if a in property:
            if state_and_lat_long[property]["lat_long"]:
                #   Split by comma and convert to floats
                coords_list = [float(x.strip()) for x in state_and_lat_long[property]["lat_long"].split(',')]  
                res = coords_list
                print("from available coordinates")
            elif not state_and_lat_long[property]["lat_long"]:
                appropriate_state = state_and_lat_long[property]["state"]
                if '--' in property:
                    area_name = property.split('--')[1].split('-')[0]
                res = geocode_area(area_name, state=appropriate_state, country="India", cache=cache)  # adapt state/country if you have better context
                print("generated_coordinates")
            print(property, res)
            print(type(res))
            # coords_map[a] = res or (None, None)
            coords_map[property] = res or (None, None)
        # df['latitude'] = df['area_name'].map(lambda x: coords_map.get(x, (None,None))[0])
        # df['longitude'] = df['area_name'].map(lambda x: coords_map.get(x, (None,None))[1])
        df['latitude'] = df['Property_ID'].map(lambda x: coords_map.get(x, (None,None))[0])
        df['longitude'] = df['Property_ID'].map(lambda x: coords_map.get(x, (None,None))[1])
        df = df.dropna(subset=['latitude','longitude']).reset_index(drop=True)
        if len(df) == 0:
            raise Exception("No geocoded properties available. Provide real coordinates or fix geocoding.")
        
        df['latitude'] = df['latitude'].astype(float)
        df['longitude'] = df['longitude'].astype(float)

        frappe.log_error("df",f"{df}")

    # 2) fetch boundaries: city then automatic hard boundary derivation
    city_boundary = fetch_best_boundary(user_location_query)
    if not city_boundary.get('features'):
        print("Warning: no city boundary found.")
    # derive hard boundary (state or fallback country) by inspecting city feature props
    state_boundary = None
    try:
        city_feat = city_boundary['features'][0]
        city_props = city_feat.get('properties', {}) or {}
        address = city_props.get('address') or {}
        state_name = address.get('state') or state
        country_name = address.get('country') or "India"
        if state_name:
            state_boundary = fetch_best_boundary(f"{state_name}, {country_name}")
        else:
            # fallback to country polygon
            state_boundary = fetch_best_boundary(country_name)
    except Exception:
        # fallback safe behavior
        state_boundary = fetch_best_boundary("India")

    frappe.log_error("state_boundary",f"{state_boundary}")

    # 3) build checkers & index
    is_inside_city = build_inside_checker(city_boundary)
    is_inside_state = build_inside_checker(state_boundary)
    city_coords = extract_boundary_coords(city_boundary)
    city_tree = build_balltree(city_coords)

    # 4) classify and compute distances
    tiers = []
    dists = []
    for idx, row in df.iterrows():
        lat = float(row['latitude']); lon = float(row['longitude'])
        tier, dist_km = classify_property(lat, lon, is_inside_city, is_inside_state, city_tree)
        tiers.append(tier); dists.append(dist_km)
    df['tier'] = tiers
    df['distance_from_city_km'] = dists
    frappe.log_error("classify and compute distances",f"{df}")

    # 5) decide decency
    tier1_df = df[df['tier'] == 1]
    has_decent_tier1 = decide_has_decent_tier1(df, tier1_df)
    df['has_decent_tier1'] = has_decent_tier1

    # If local properties are poor and expansion is enabled -> attempt to expand
    if expand_if_poor:
        local_count = len(df[df['tier'].isin([1,2])])
        if (not has_decent_tier1) and (local_count < min_local_candidates):
            print("Local candidates poor — attempting search expansion inside hard boundary.")
            try:
                extra_df = expand_search_within_hard_boundary(state_boundary, needed_count=100)
                # merge: append extra candidates that are not already present
                # expected extra_df columns: property_id, property_suitability_score, latitude, longitude
                if extra_df is not None and not extra_df.empty:
                    # drop duplicates by property_id if present
                    combined = pd.concat([df, extra_df], ignore_index=True).drop_duplicates(subset=['Property_ID'])
                    df = combined.reset_index(drop=True)
                    # re-run classification quickly (for demo simplicity we call recursively but avoid infinite loop)
                    return run_location_postprocessor(df, user_location_query, state_hint=state_hint,
                                                      scoring_fn=scoring_fn, expand_if_poor=False,
                                                      min_local_candidates=min_local_candidates)
            except NotImplementedError:
                print("Search expansion hook not implemented. Skipping expansion.")
            except Exception as e:
                print("Expansion failed:", e)

    # 6) compute final score and rank
    df['final_score'] = df.apply(lambda r: scoring_fn(r['Aggregate Property Performance Score (APPS)'], r['tier'], r['distance_from_city_km'], has_decent_tier1), axis=1)
    # ========== NEW: Normalize scores to 0-10 ==========
    # df = normalize_scores_to_range(df, score_column='final_score', 
    #                                new_column='normalized_score', 
    #                                target_min=0, target_max=10)
    df = normalize_scores_sigmoid(df, score_column='final_score', 
                                   new_column='normalized_score', 
                                   target_min=0, target_max=10)

    # Sort by normalized score (preserves same order since it's monotonic)
    df_sorted = df.sort_values('final_score', ascending=False).reset_index(drop=True)
    df_sorted['new_rank'] = df_sorted.index + 1
    frappe.log_error("compute final score and rank",f"{df}")

    # 7) Add per-row explainability (update to include normalized score)
    # df_sorted['explain'] = df_sorted.apply(lambda r: explain_property(r), axis=1)
    df_sorted['explain'] = df_sorted.apply(lambda r: {
        **explain_property(r),
        'normalized_score': round(r.get('normalized_score', r['final_score']), 2)
    }, axis=1)
    frappe.log_error("Add per-row explainability (update to include normalized score)",f"{df}")

    # Ensure latitude & longitude are included in final output
    final_columns = [
        'new_rank',
        'Property_ID',
        'area_name' if 'area_name' in df_sorted.columns else None,
        'latitude',
        'longitude',
        'tier',
        'distance_from_city_km',
        'Aggregate Property Performance Score (APPS)',
        'final_score',
        'normalized_score',      # NEW: 0-10 scale
        'explain'
    ]

    # Drop None columns safely
    final_columns = [c for c in final_columns if c in df_sorted.columns]

    return df_sorted[final_columns]

# def run_location_postprocessor(
#     df_properties,
#     user_location_query,
#     scoring_fn=compute_final_score,
#     expand_if_poor=True,
#     min_local_candidates=1
# ):
#     """
#     Location-aware post-processing ranking function.

#     df_properties must contain:
#       - property_id
#       - property_suitability_score
#       - latitude (optional)
#       - longitude (optional)

#     Returns:
#       Ranked DataFrame with lat/lon, tier, distance, final_score, explainability.
#     """

#     df = df_properties.copy()
#     cache = load_geocode_cache()

#     # ------------------------------------------------------------------
#     # STEP 1: Resolve user location boundary (City → State → Country)
#     # ------------------------------------------------------------------
#     city_boundary = fetch_best_boundary(user_location_query)
#     if not city_boundary.get("features"):
#         raise Exception("Unable to resolve city boundary from user location")

#     city_feat = city_boundary["features"][0]
#     city_props = city_feat.get("properties", {}) or {}
#     address = city_props.get("address", {}) or {}

#     state_name = address.get("state")
#     country_name = address.get("country", "India")

#     # Hard boundary = state if available, else country
#     if state_name:
#         hard_boundary = fetch_best_boundary(f"{state_name}, {country_name}")
#     else:
#         hard_boundary = fetch_best_boundary(country_name)

#     # ------------------------------------------------------------------
#     # STEP 2: Build spatial utilities
#     # ------------------------------------------------------------------
#     is_inside_city = build_inside_checker(city_boundary)
#     is_inside_state = build_inside_checker(hard_boundary)

#     city_coords = extract_boundary_coords(city_boundary)
#     city_tree = build_balltree(city_coords)

#     # User location centroid (for geocode validation)
#     city_geom = shape(city_feat["geometry"])
#     city_centroid = (city_geom.centroid.y, city_geom.centroid.x)  # (lat, lon)

#     # ------------------------------------------------------------------
#     # STEP 3: Ensure latitude / longitude for all properties
#     # ------------------------------------------------------------------
#     if "latitude" not in df.columns or "longitude" not in df.columns:
#         df["latitude"] = None
#         df["longitude"] = None

#     # Extract area name and contextual hint from property_id
#     df[["area_name", "area_hint"]] = df["property_id"].apply(
#         lambda pid: pd.Series(extract_area_and_hint(pid))
#     )

#     # Geocode missing coordinates
#     coords_map = {}
#     resolved_state_map = {}

#     for _, row in df.iterrows():
#         area = row["area_name"]
#         hint = row["area_hint"]

#         if pd.notna(row["latitude"]) and pd.notna(row["longitude"]):
#             continue

#         if area in coords_map:
#             continue

#         lat, lon, resolved_state = geocode_with_fallback(
#             area_name=area,
#             state_hint=hint or state_name,
#             country_hint=country_name,
#             cache=cache,
#             user_location_centroid=city_centroid
#         )

#         coords_map[area] = (lat, lon)
#         resolved_state_map[area] = resolved_state

#     # Map back coordinates
#     df["latitude"] = df["area_name"].map(lambda a: coords_map.get(a, (None, None))[0])
#     df["longitude"] = df["area_name"].map(lambda a: coords_map.get(a, (None, None))[1])

#     df = df.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)
#     df["latitude"] = df["latitude"].astype(float)
#     df["longitude"] = df["longitude"].astype(float)

#     if len(df) == 0:
#         raise Exception("No properties could be geocoded")

#     # ------------------------------------------------------------------
#     # STEP 4: Tier classification (Z1–Z4)
#     # ------------------------------------------------------------------
#     tiers = []
#     distances = []

#     for _, row in df.iterrows():
#         lat, lon = row["latitude"], row["longitude"]
#         tier, dist_km = classify_property(
#             lat, lon, is_inside_city, is_inside_state, city_tree
#         )
#         tiers.append(tier)
#         distances.append(dist_km)

#     df["tier"] = tiers
#     df["distance_from_city_km"] = distances

#     # ------------------------------------------------------------------
#     # STEP 5: Decent-enough gate (core document logic)
#     # ------------------------------------------------------------------
#     tier1_df = df[df["tier"] == 1]
#     has_decent_tier1 = decide_has_decent_tier1(df, tier1_df)
#     df["has_decent_tier1"] = has_decent_tier1

#     # ------------------------------------------------------------------
#     # STEP 6: Optional expansion (CASE B)
#     # ------------------------------------------------------------------
#     if expand_if_poor:
#         local_count = len(df[df["tier"].isin([1, 2])])
#         if not has_decent_tier1 and local_count < min_local_candidates:
#             try:
#                 extra_df = expand_search_within_hard_boundary(
#                     hard_boundary, needed_count=100
#                 )
#                 if extra_df is not None and not extra_df.empty:
#                     merged = (
#                         pd.concat([df, extra_df], ignore_index=True)
#                         .drop_duplicates(subset=["property_id"])
#                         .reset_index(drop=True)
#                     )
#                     return run_location_postprocessor(
#                         merged,
#                         user_location_query,
#                         scoring_fn=scoring_fn,
#                         expand_if_poor=False,
#                         min_local_candidates=min_local_candidates
#                     )
#             except NotImplementedError:
#                 pass

#     # ------------------------------------------------------------------
#     # STEP 7: Final scoring & ranking
#     # ------------------------------------------------------------------
#     df["final_score"] = df.apply(
#         lambda r: scoring_fn(
#             r["property_suitability_score"],
#             r["tier"],
#             r["distance_from_city_km"],
#             has_decent_tier1
#         ),
#         axis=1
#     )

#     df_sorted = df.sort_values("final_score", ascending=False).reset_index(drop=True)
#     df_sorted["new_rank"] = df_sorted.index + 1

#     # Explainability
#     df_sorted["explain"] = df_sorted.apply(explain_property, axis=1)

#     # ------------------------------------------------------------------
#     # STEP 8: Final output (explicit, auditable)
#     # ------------------------------------------------------------------
#     return df_sorted[
#         [
#             "new_rank",
#             "property_id",
#             "area_name",
#             "latitude",
#             "longitude",
#             "tier",
#             "distance_from_city_km",
#             "property_suitability_score",
#             "final_score",
#             "explain",
#         ]
#     ]



# -------------------- Example test run --------------------
# if __name__ == "__main__":
    # small sample like your earlier test
    # sample = pd.DataFrame({
    #     'property_id': ['2318--Vagra-Bharuch','4640--Ankleshwar-Bharuch','4707--Bharuch-Bharuch','6144--Ankleshwar-Bharuch'],
    #     'property_suitability_score': [2.144654,4.672502,3.292534,4.722931],
    #     # If you have exact coords include them; else the pipeline will geocode using area_name fallback
    #     # 'latitude':[21.8447606,21.6293206,21.7080427,21.6293206],
    #     # 'longitude':[72.8448749,72.9945103,72.9956936,72.9945103]
    # })
  

#########################################################################################################################################################################

@frappe.whitelist()
def industry_from_scratch(aiResponse,chatId,selectedOption):
    frappe.log_error("aiResponse",f"{aiResponse}")

    try:
        analyse_query = randomSentences('industry', 'Analyzing Your Query')
        fetch_data = randomSentences('industry', 'Fetching Data')
        analyse_data = randomSentences('industry', 'Analyzing Data')
        prepare_result = randomSentences('industry', 'Preparing Results')

        insert_process(chatId,"Analyzing Your Query",analyse_query,"Pending")
        update_process(chatId,"Analyzing Your Query","Processing",0)
        insert_process(chatId,"Fetching Data",fetch_data,"Pending")
        insert_process(chatId,"Analyzing Data",analyse_data,"Pending")   
        insert_process(chatId,"Preparing Result",prepare_result,"Pending")
        time.sleep(3)
        update_process(chatId,"Analyzing Your Query","Complete",1)
        update_process(chatId,"Fetching Data","Processing",0)
        time.sleep(4)
        found_property = True
        found_employment = True
        found_incentive = True
        found_approval = True
        # found_vendor = True

        state_ai_response = aiResponse['state']
        frappe.log_error("state_ai_response",f"{state_ai_response}")
        
        # main_industry = aiResponse.get("Main-Industry")
        # sub_sector = aiResponse.get("Sub-Sector")
        # segment = aiResponse.get("Segment")
        # capacity = aiResponse.get("Capacity")
        # keyword_given_by_user = aiResponse.get("KEYWORDS")
        main_industry = state_ai_response.get("Main-Industry")
        sub_sector = state_ai_response.get("Sub-Sector")
        segment = state_ai_response.get("Segment")
        capacity = state_ai_response.get("Capacity")
        keyword_given_by_user = state_ai_response.get("KEYWORDS")
        log_to_file("keyword_given_by_user",keyword_given_by_user)
        update_process(chatId,"Fetching Data","Complete",1)

        update_process(chatId,"Analyzing Data","Processing",0)
        industry = get_industry(main_industry)
        sub_sector,zone_id = get_subsector(sub_sector)
        segment = get_segment(segment)
        with open("log2.txt", "a") as file:
            file.write(f"\n Industry, Sub-sector, Segment:::>>>:::>>>:::>>> {industry},{sub_sector}, {segment}, Zone: {zone_id}")
        # min_land ,max_land = get_land_requirements(industry,sub_sector,segment,capacity)
        result = integrate_land_calculation(capacity,industry,sub_sector,segment)
        required_exact_land_by_user, required_LowerMargin_land_for_user, required_UpperMargin_land_for_user = result["Land_size"], result["Lower_limit_land_size"], result["Upper_limit_land_size"]
        area_list = get_list_of_area_id(zone_id)
        frappe.log_error("area_list",f"{area_list}")
        with open("log2.txt", "a") as file:
            file.write(f"\n Unique list of areas cities state:::>>>:::>>>:::>>> {area_list}, {zone_id}")
        city_list = get_list_of_city_list(area_list)
        state_list = get_state_list(city_list)
        with open("log2.txt", "a") as file:
            file.write(f"\n Unique list of areas cities state:::>>>:::>>>:::>>> {area_list},{city_list}, {state_list}")

        ######################### getting property list based on user descision ###########################
        # # if USER_DESCISION == "NO":
        # if aiResponse['Is_confirmation'] == True:
        #     frappe.log_error("USER_DESCISION",f"{USER_DESCISION}")
        #     property_employment_df,property_list = get_property_and_employement(zone_id,area_list,required_LowerMargin_land_for_user,required_UpperMargin_land_for_user,found_property,found_employment,selectedOption = selectedOption)
        # # elif USER_DESCISION == "YES":
        # elif aiResponse['Is_confirmation'] == False:
        #     frappe.log_error("USER_DESCISION",f"{USER_DESCISION}")
        #     property_employment_df,property_list = get_property_and_employement(zone_id,area_list,required_LowerMargin_land_for_user,required_UpperMargin_land_for_user,found_property,found_employment,selectedOption = selectedOption, location='Gujarat')
        #     # Check if first attempt returned valid data
        #     if property_employment_df is None or (hasattr(property_employment_df, 'empty') and property_employment_df.empty):
        #         frappe.log_error("First attempt returned no data", f"property_employment_df: {property_employment_df}")
        
        #         # Second attempt without location
        #         property_employment_df, property_list = get_property_and_employement(
        #             zone_id, 
        #             area_list, 
        #             required_LowerMargin_land_for_user, 
        #             required_UpperMargin_land_for_user, 
        #             found_property, 
        #             found_employment, 
        #             selectedOption=selectedOption
        #         )
        # if USER_DESCISION == "NO":
        for option in aiResponse['options']:
            if option['value'] == aiResponse['User Intention']:
                USER_DESCISION = option['label']
                frappe.log_error("USER_DESCISION",f"{USER_DESCISION}")

        # getting the location_scope:- it means whether user wants to stay in district or he wants to extend the district boundary or whether he wants to expand all over the state
        LOCATION_SCOPE = state_ai_response['Location_Scope']
        frappe.log_error("LOCATION_SCOPE",f"{LOCATION_SCOPE}")

        if USER_DESCISION == "Yes, this is correct" or USER_DESCISION == "Explore Land for New Unit" or USER_DESCISION == "View All Setup Options" or USER_DESCISION == "Explore Existing Facilities":
            frappe.log_error("USER_DESCISION_0",f"{USER_DESCISION}")
            if LOCATION_SCOPE == 'full_state':
                for item in state_ai_response["Location"]:
                    if item['State'] != 'None':
                        specific_location = item['State']
                        frappe.log_error("specific_location",f"{specific_location}")
                property_employment_df,property_list = get_property_and_employement(zone_id,area_list,required_LowerMargin_land_for_user,required_UpperMargin_land_for_user,found_property,found_employment,selectedOption = selectedOption, location=specific_location)

            elif LOCATION_SCOPE == "district_only":
                for item in state_ai_response["Location"]:
                    if item['District'] != 'None':
                        specific_location = item['District']
                        frappe.log_error("specific_location",f"{specific_location}")
                property_employment_df,property_list = get_property_and_employement(zone_id,area_list,required_LowerMargin_land_for_user,required_UpperMargin_land_for_user,found_property,found_employment,selectedOption = selectedOption, location=specific_location)

            elif LOCATION_SCOPE == "district_nearby":
                for item in state_ai_response["Location"]:
                    if item['District'] != 'None':
                        specific_location = item['District']
                        frappe.log_error("specific_location",f"{specific_location}")
                property_employment_df,property_list = get_property_and_employement(zone_id,area_list,required_LowerMargin_land_for_user,required_UpperMargin_land_for_user,found_property,found_employment,selectedOption = selectedOption, location=specific_location)

        ### WE HAVE USED 'PASS' IN THIS ELIF CONDITION AS MOST PROBABLY IF USER DESCISSION IS NO OR REFINE REQUIREMENTS THEN IT WOULD NOT COME TO ANALYTICS ENGINE, SO THAT'S WHY.
        elif USER_DESCISION == "No, this is not correct" or USER_DESCISION == "Refine Requirements":
            pass

        ### CHECKING WHETHER THE PROPERTY LIST IS EMPTY OR NOT IN ORDER TO SEE THAT WHETHER THE LOCAITON ENTERED BY USER THOUGH AVAILABLE IN DB BUT IF NO PROPERTIES AVAILABLE FOR THAT LOCATION THEN THE FALLBACK SHOULD TRIGGER ie. ALL OVER GUJARAT PROPERTIES WILL BE SHOWN TO USER.
        # Check if first attempt returned valid data
        if property_employment_df is None or (hasattr(property_employment_df, 'empty') and property_employment_df.empty):
            frappe.log_error("First attempt returned no data", f"property_employment_df: {property_employment_df}")

            LOCATION_SCOPE = None
    
            # Second attempt without location
            property_employment_df, property_list = get_property_and_employement(
                zone_id, 
                area_list, 
                required_LowerMargin_land_for_user, 
                required_UpperMargin_land_for_user, 
                found_property, 
                found_employment, 
                selectedOption=selectedOption,
                location = None
            )

            frappe.log_error("2nd_attempt_property_employment_df" ,f"{property_employment_df}")

        ####################################################################################################

        frappe.log_error("property_list",f"{property_list}")
        frappe.log_error("property_employment_df_dict",f"{property_employment_df.to_json()}")
        frappe.log_error("property_employment_df",f"{property_employment_df}")
        with open("log2.txt", "a") as file:
            file.write(f"\n PROPERTY DATAAA:::>>>:::>>>:::>>> {property_employment_df.to_string(index=False)}")
        r_insights = {}
        for state in state_list:
            _, r_insights_dict = retrieving_market_trends(industry, industry, industry, state, state, "pan_industry", "pan_state") 
            filtered_data = {
                "market_trends": r_insights_dict.get("market_trends", None),
                "local_laws": r_insights_dict.get("local_laws", None),
                "taxes": r_insights_dict.get("taxes", None)
            }
            r_insights[state] = filtered_data

        with open("log2.txt", "a") as file:
            file.write(f"\n Regulatory Insights Data Final version ][[][][][]] {r_insights}")
        # Convert dictionary to DataFrame for merging
        market_info_df = pd.DataFrame.from_dict(r_insights, orient='index').reset_index()
        market_info_df.rename(columns={'index': 'state'}, inplace=True)
        # Merge on the 'state' column
        property_employment_df = property_employment_df.merge(market_info_df, on='state', how='left')
        # frappe.log_error("property_employment_df",f"{property_employment_df.to}")
        columns_to_drop = [
            'distance_from_nearest_railway_station',
            'distance_from_nearest_seaport', 'distance_from_power_source',
            'latitude_longitude', 'road_connectivity',
            'distance_from_nearest_airport', 'employment_area_id',
            'employmenttype_id', 'availability'
        ]
        propert_keyword_df =  property_employment_df.drop(columns=columns_to_drop)

        frappe.log_error("propert_keyword_df",f"{propert_keyword_df}")
        propert_keyword_df["tree_cutting_involved"] = propert_keyword_df["tree_cutting_involved"].apply(lambda x: "Tree Cutting" if x == "Yes" else "None")
        propert_keyword_df["road_cutting_involved"] = propert_keyword_df["road_cutting_involved"].apply(lambda x: "Road Cutting" if x == "Yes" else "None")
        propert_keyword_df["pole_shifting"] = propert_keyword_df["pole_shifting"].apply(lambda x: "Pole Shifting" if x == "Yes" else "None")
        propert_keyword_df["business_location_type"] = propert_keyword_df["business_location_type"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)
        propert_keyword_df["land_type"] = propert_keyword_df["land_type"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)
        propert_keyword_df["vicinity_of"] = propert_keyword_df["vicinity_of"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)
        propert_keyword_df["Cross_the_following"] = propert_keyword_df["Cross_the_following"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)

        propert_keyword_df = propert_keyword_df.rename(columns= {'property_id':'ID'})

        propert_keyword_df.drop_duplicates(subset=["ID"], inplace=True)
        frappe.log_error("propert_keyword_df",f"{propert_keyword_df.to_json()}")

        ##########################################################################
        ########## NEW LOGIC FOR PROPERTY RANKING(NEW LOGIC) #############################

        # if USER_DESCISION == "NO":
        if LOCATION_SCOPE == "district_nearby":

            # step-1:- calculating hard boundary as per exponential decay logic
            hard_boundary_calculation = compute_rhard(RSOFT_KM)  # when default soft_boundary_km is used.
            # hard_boundary_calculation = 50  # when default soft_boundary_km is used.
            p_exp     = compute_expansion_fraction(RSOFT_KM)
            frappe.log_error("hard_boundary_calculation",f"{hard_boundary_calculation}")

            # step-2:- getting the properties and their repsective latitude and longitude from the property_keyword_df json and forming a dataframe from it. 21.606572933000024,73.01477826199968
            property_id_list = []
            for property_id in propert_keyword_df["ID"]:
                property_id_list.append(property_id)
            
            frappe.log_error("property_id_list",f"{property_id_list}")

            property_df_with_lat_long = fetch_property_data(property_id_list)
            frappe.log_error("property_df_with_lat_long",f"{property_df_with_lat_long}")

            # step-3:- filtering the properties recieved from propert_keyword_df json based on the filter-1:- user mentioned location and filter-2:- soft and hard boundary km.
            df = property_df_with_lat_long.copy()

            # location_query_result = extract_location_robust(aiResponse) # example:- "bharuch, gujarat, india" or "Not available in list."
            location_query_result = extract_location_robust(state_ai_response) # example:- "bharuch, gujarat, india" or "Not available in list."
            frappe.log_error("location_query_result",f"{location_query_result}")

            district_polygon = fetch_district_polygon(location_query_result) # getting boundary coordinates for the user mentioned location.
            frappe.log_error("district_polygon",f"{district_polygon}")

            border_tree = build_border_balltree(district_polygon) # building a border tree

            is_inside = build_inside_checker(district_polygon) # building a checker that checks based on lat and long of the properties that whether these properties are inside the user mentioned location or not.
            frappe.log_error("is_inside",f"{is_inside}")

            # Classify each property
            zones, border_dists, inside_flags = [], [], []
            for _, row in df.iterrows():
                frappe.log_error("lat_long_0",f"{df.to_json()}")
                lat_long_str = row['lat_long']
                frappe.log_error("lat_long_1",f"{lat_long_str}")
                lat_str, lon_str = lat_long_str.split(',')
                latitude = float(lat_str.strip())
                longitude = float(lon_str.strip())
                frappe.log_error("lat_long",f"{latitude}, {longitude}")
                inside = is_inside(longitude, latitude)
                frappe.log_error("inside",f"{inside}")
                d_bdr  = round(dist_to_border_km(border_tree, latitude, longitude), 2)
                frappe.log_error("d_bdr",f"{d_bdr}")
                inside_flags.append(inside)
                border_dists.append(d_bdr)

                if inside:
                    zones.append("Zone1_inside_district")
                elif d_bdr <= RSOFT_KM:
                    zones.append("Zone2_soft_buffer")
                elif d_bdr <= hard_boundary_calculation:
                    zones.append("Zone3_hard_buffer")
                else:
                    zones.append("EXCLUDED")

            frappe.log_error("zones",f"{zones}")
            frappe.log_error("border_dists",f"{border_dists}")
            frappe.log_error("inside_flags",f"{inside_flags}")

            # step-4:- determining which properties are inside the hard boundary and which are outside based on the distance in km calculated of the properties.
            df['inside_district']    = inside_flags
            df['dist_to_border']     = border_dists
            df['zone']               = zones

            # GEO FILTER — before scoring
            print("  GEO FILTER (before scoring):")
            passed   = df[df['zone'] != "EXCLUDED"].copy().reset_index(drop=True)
            frappe.log_error("passed",f"{passed}")

            # hard_boundary_properties = df[df['zone'] == "Zone3_hard_buffer"].copy().reset_index(drop=True)
            # frappe.log_error("hard_boundary_properties",f"{hard_boundary_properties}")

            passed_properties_list = passed['Property_ID'].tolist()
            frappe.log_error("passed_properties_list",f"{passed_properties_list}")
            excluded = df[df['zone'] == "EXCLUDED"].copy().reset_index(drop=True)
            frappe.log_error("excluded",f"{excluded}")
            frappe.log_error("df",f"{df}")

            property_employment_df = property_employment_df[property_employment_df["property_id"].isin(passed_properties_list)].reset_index(drop=True)
            propert_keyword_df = propert_keyword_df[propert_keyword_df["ID"].isin(passed_properties_list)].reset_index(drop=True)
            property_list = passed_properties_list  # update property_list as well

            frappe.log_error("filtered_property_employment_df", f"{property_employment_df.to_json()}")
            frappe.log_error("filtered_propert_keyword_df", f"{propert_keyword_df.to_json()}")

            zone_mapping = passed[["Property_ID", "zone"]].drop_duplicates()
            frappe.log_error("zone_mapping", f"{zone_mapping}")

        ##########################################################################

        # Incentive_only_df = get_incentive(sub_sector,main_industry,area_list,city_list,state_list)
        property_incentive_mapped_df,found_incentive = get_property_incentive_mapped(industry,sub_sector,area_list,city_list,state_list,property_list,found_incentive)
        # property_incentive_mapped_df,found_incentive = get_property_incentive_mapped(industry,sub_sector,area_list,city_list,state_list,passed_properties_list,found_incentive)
        frappe.log_error("area_list",f"{area_list}")
        frappe.log_error("city_list",f"{city_list}")
        frappe.log_error("state_list",f"{state_list}")
        frappe.log_error("property_list",f"{property_list}")

        frappe.log_error("property_incentive_mapped_df",f"{property_incentive_mapped_df.to_json()}")
        frappe.log_error("found_incentive",f"{found_incentive}")
        Solution_screen_incentive_lookup_df = process_incentive_df_to_send_solution_screen(property_incentive_mapped_df)
        frappe.log_error("Solution_screen_incentive_lookup_df",f"{Solution_screen_incentive_lookup_df.to_json()}")
        frappe.log_error("property_employment_df",f"{property_employment_df.to_json()}")

        df_for_property_wise_individual_score, df_for_property_wise_emp_score = transform_dataframes(property_employment_df)
        frappe.log_error("df_for_property_wise_individual_score",f"{df_for_property_wise_individual_score.to_json()}")
        df_with_property_wise_individual_score = calculate_property_suitability(df_for_property_wise_individual_score,required_LowerMargin_land_for_user,required_UpperMargin_land_for_user)
        frappe.log_error("final_property_ranking_for_decision_000",f"{df_with_property_wise_individual_score["property_id"]}")
        frappe.log_error("final_property_ranking_for_decision_111",f"{df_with_property_wise_individual_score["property_suitability_score"]}")
        frappe.log_error("final_property_ranking_for_decision_222",f"{df_with_property_wise_individual_score["property_suitability_score"].tolist()}")
        # with open("/home/mars/frappe-bench/apps/frontend_app/frontend_app/Management_Class/Analytics_management/log2.txt", "w") as file:
        #     file.write("calculate_property_suitability", df_with_property_wise_individual_score)
        df_with_property_wise_individual_score.sort_values(by=["property_suitability_score"], ascending=False)
        frappe.log_error("df_with_property_wise_individual_score",f"{df_with_property_wise_individual_score}")
        final_property_ranking_for_decision = pd.DataFrame({"Property_ID": list(property_employment_df["property_id"].unique())})
        # frappe.log_error("final_property_ranking_for_decision_for_employment", final_property_ranking_for_decision)
        cols = ["property_id", "Network Connectivity", "taxes", "local_laws", "market_trends"]

        right = (
            property_employment_df[cols]
            .drop_duplicates(subset=["property_id"])  # <-- key change
        )

        final_property_ranking_for_decision = (
            pd.merge(
                final_property_ranking_for_decision,
                right,
                left_on="Property_ID",
                right_on="property_id",
                how="left",
            )
            .drop(columns=["property_id"])
        )

        # with open("/home/mars/frappe-bench/sites/log2.txt", "w") as file:
        #     file.write(f"\n DF WITH SCORES AND MARKET TRENDsssssssssssssssssssssssssssssssS {final_property_ranking_for_decision}")
        frappe.log_error("final_property_ranking_for_decision",f"{final_property_ranking_for_decision}")
        final_property_ranking_for_decision = pd.merge(final_property_ranking_for_decision, df_with_property_wise_individual_score[["property_id","property_suitability_score"]], left_on="Property_ID", right_on="property_id", how='left').drop(columns=["property_id"])
        
        df_with_property_wise_emp_score = calculate_employment_availability_score(df_for_property_wise_emp_score,sub_sector)
        df_with_property_wise_emp_score.sort_values(by=["employment_availability_score"], ascending=False)
        Solution_screen_employment_lookup_df = df_for_property_wise_emp_score[["property_id","Semi-skilled", "Skilled", "Unskilled", "Skill_Type"]]


        final_property_ranking_for_decision = pd.merge(final_property_ranking_for_decision, df_with_property_wise_emp_score[["property_id","employment_availability_score"]], 
         left_on="Property_ID", right_on="property_id", how='left').drop(columns=["property_id"])
        df_with_property_wise_incentive_score = get_property_wise_incentive_score(property_incentive_mapped_df,property_employment_df,found_incentive)
        
        # Step 1: Identify Uncommon Property IDs
        uncommon_property_ids = list(set(final_property_ranking_for_decision["Property_ID"]) ^ set(df_with_property_wise_incentive_score["Property ID"]))
    
        uncommon_property_ids_for_sol_incentive = list(set(Solution_screen_incentive_lookup_df["property_id"]) ^ set(df_with_property_wise_incentive_score["Property ID"]))

        # Step 2: Filter out uncommon properties from final_property_ranking_for_decision
        final_property_ranking_for_decision = final_property_ranking_for_decision[
            ~final_property_ranking_for_decision["Property_ID"].isin(uncommon_property_ids)
        ]

        Solution_screen_incentive_lookup_df = Solution_screen_incentive_lookup_df[
            ~Solution_screen_incentive_lookup_df["property_id"].isin(uncommon_property_ids_for_sol_incentive)
        ]

        final_property_ranking_for_decision = pd.merge(final_property_ranking_for_decision, df_with_property_wise_incentive_score[["Property ID","Scaled Final Score"]], 
         left_on="Property_ID", right_on="Property ID", how='left').drop(columns=["Property ID"])
        final_property_ranking_for_decision.rename(columns={'Scaled Final Score': 'Property_wise_incentive_score'}, inplace=True)

        property_approval_mapped_df,found_approval = get_property_approval_mapped(main_industry,sub_sector,area_list,city_list,state_list,property_list,found_approval)
        Solution_screen_approval_lookup_df = process_approval_df_to_send_solution_screen(property_approval_mapped_df)
        df_with_property_wise_approval_score = get_property_wise_approval_score(found_approval,property_approval_mapped_df,property_employment_df)

       
       # Step 1: Identify Uncommon Property IDs
        uncommon_property_ids = list(set(final_property_ranking_for_decision["Property_ID"]) ^ set(df_with_property_wise_approval_score["Property ID"]))

        # Step 2: Filter out uncommon properties from final_property_ranking_for_decision
        final_property_ranking_for_decision = final_property_ranking_for_decision[
            ~final_property_ranking_for_decision["Property_ID"].isin(uncommon_property_ids)
        ]

        # Step 1: Identify Uncommon Property IDs
        uncommon_property_ids_for_sol_approval = list(set(Solution_screen_approval_lookup_df["property_id"]) ^ set(df_with_property_wise_approval_score["Property ID"]))

        # Step 2: Filter out uncommon properties from Solution_screen_approval_lookup_df
        Solution_screen_approval_lookup_df = Solution_screen_approval_lookup_df[
            ~Solution_screen_approval_lookup_df["property_id"].isin(uncommon_property_ids_for_sol_approval)
        ]

        Solution_screen_approval_lookup_df = pd.merge(Solution_screen_approval_lookup_df, df_with_property_wise_approval_score[["Property ID", "Efficient Approval Time","Online Percentage","Pre-Requisite","Pre-Establishment","Pre-Operation","Others","Mode_Pre-Requisite","Mode_Pre-Establishment","Mode_Pre-Operation","Mode_Others"]], left_on="property_id", right_on="Property ID").drop(columns=["Property ID"])

        final_property_ranking_for_decision = pd.merge(final_property_ranking_for_decision, df_with_property_wise_approval_score[["Property ID","Final Score"]], 
         left_on="Property_ID", right_on="Property ID", how='left').drop(columns=["Property ID"])
        final_property_ranking_for_decision.rename(columns={'Final Score': 'Property_wise_approval_score'}, inplace=True)

        supply_rules_df = get_supply_rule(main_industry,sub_sector,segment,capacity)
        with open("log2.txt", "a") as file:
            file.write(f"\n Checking Supplies DF  {supply_rules_df}")
        vendor_df = get_vendor_df(supply_rules_df)
        with open("log2.txt", "a") as file:
            file.write(f"\n Checking Vendor DF  {vendor_df}")


        property_latlong_df = property_employment_df[["property_id", "latitude_longitude"]].drop_duplicates()
        test_return = get_supply_scores(property_latlong_df,supply_rules_df,vendor_df,prefered_range=(0,250), tolerable_range=(251,500))
        # if len(test_return) == 2:
        #     property_mapped_supply_individual_score, property_mapped_supply_alternate_sug= test_return[0], test_return[1]
        # else:
        #     property_mapped_supply_individual_score, property_mapped_supply_alternate_sug = test_return, None

        property_mapped_supply_individual_score, property_mapped_supply_alternate_sug, property_wise_all_vendor_df= test_return[0], test_return[1], test_return[2]
        
        df_with_property_wise_vendor_score = calculate_final_supply_mapped_property_scores_with_condition(property_mapped_supply_individual_score, property_latlong_df)

        Solution_screen_essential_supply_vendor_lookup_df, Solution_screen_non_essential_supply_vendor_lookup_df = process_supply_vendor_df_to_send_solution_screen(property_mapped_supply_individual_score)
        Solution_screen_essential_supply_all_vendor_lookup_df, Solution_screen_non_essential_supply_all_vendor_lookup_df = process_supply_vendor_df_to_send_solution_screen(property_wise_all_vendor_df, all_vendor=True)
        # Step 1: Identify Uncommon Property IDs
        uncommon_property_ids = list(set(final_property_ranking_for_decision["Property_ID"]) ^ set(df_with_property_wise_vendor_score["property_id"]))
        # if (not Solution_screen_essential_supply_vendor_lookup_df.empty) and (not Solution_screen_non_essential_supply_vendor_lookup_df.empty):
        #     uncommon_property_ids_accross_essential_supply = list(set(Solution_screen_essential_supply_vendor_lookup_df["property_id"]) ^ set(df_with_property_wise_vendor_score["property_id"]))
        #     uncommon_property_ids_accross_non_essential_supply = list(set(Solution_screen_non_essential_supply_vendor_lookup_df["property_id"]) ^ set(df_with_property_wise_vendor_score["property_id"]))
        #             # Step 2: Filter out uncommon properties from final_property_ranking_for_decision
        #     Solution_screen_essential_supply_vendor_lookup_df = Solution_screen_essential_supply_vendor_lookup_df[
        #         ~Solution_screen_essential_supply_vendor_lookup_df["property_id"].isin(uncommon_property_ids_accross_essential_supply)
        #     ]
        #     # Step 2: Filter out uncommon properties from final_property_ranking_for_decision
        #     Solution_screen_non_essential_supply_vendor_lookup_df = Solution_screen_non_essential_supply_vendor_lookup_df[
        #         ~Solution_screen_non_essential_supply_vendor_lookup_df["property_id"].isin(uncommon_property_ids_accross_non_essential_supply)
        #     ]
        # else:
        #     Solution_screen_essential_supply_vendor_lookup_df = pd.DataFrame({
        #         "property_id": list(final_property_ranking_for_decision["Property_ID"].unique()),
        #         "No_of_vendors_found": [0,]*len(final_property_ranking_for_decision)
        #     })
        #     Solution_screen_non_essential_supply_vendor_lookup_df = pd.DataFrame({
        #         "property_id": list(final_property_ranking_for_decision["Property_ID"].unique()),
        #         "No_of_vendors_found": [0,]*len(final_property_ranking_for_decision)
        #     })

        # Step 0: Get the reference property IDs
        reference_property_ids = set(df_with_property_wise_vendor_score["property_id"])
        final_property_ids = list(final_property_ranking_for_decision["Property_ID"].unique())

        # Case 1: Both DataFrames are non-empty
        if (not Solution_screen_essential_supply_vendor_lookup_df.empty) and (not Solution_screen_non_essential_supply_vendor_lookup_df.empty):
            
            uncommon_essential = list(set(Solution_screen_essential_supply_vendor_lookup_df["property_id"]) ^ reference_property_ids)
            uncommon_non_essential = list(set(Solution_screen_non_essential_supply_vendor_lookup_df["property_id"]) ^ reference_property_ids)
            
            Solution_screen_essential_supply_vendor_lookup_df = Solution_screen_essential_supply_vendor_lookup_df[
                ~Solution_screen_essential_supply_vendor_lookup_df["property_id"].isin(uncommon_essential)
            ]
            Solution_screen_non_essential_supply_vendor_lookup_df = Solution_screen_non_essential_supply_vendor_lookup_df[
                ~Solution_screen_non_essential_supply_vendor_lookup_df["property_id"].isin(uncommon_non_essential)
            ]

        # Case 2: Essential is empty, Non-essential is not
        elif Solution_screen_essential_supply_vendor_lookup_df.empty and not Solution_screen_non_essential_supply_vendor_lookup_df.empty:
            
            uncommon_non_essential = list(set(Solution_screen_non_essential_supply_vendor_lookup_df["property_id"]) ^ reference_property_ids)
            Solution_screen_non_essential_supply_vendor_lookup_df = Solution_screen_non_essential_supply_vendor_lookup_df[
                ~Solution_screen_non_essential_supply_vendor_lookup_df["property_id"].isin(uncommon_non_essential)
            ]
            
            Solution_screen_essential_supply_vendor_lookup_df = pd.DataFrame({
                "property_id": final_property_ids,
                "No_of_vendors_found": [0] * len(final_property_ids)
            })

        # Case 3: Non-essential is empty, Essential is not
        elif not Solution_screen_essential_supply_vendor_lookup_df.empty and Solution_screen_non_essential_supply_vendor_lookup_df.empty:
            
            uncommon_essential = list(set(Solution_screen_essential_supply_vendor_lookup_df["property_id"]) ^ reference_property_ids)
            Solution_screen_essential_supply_vendor_lookup_df = Solution_screen_essential_supply_vendor_lookup_df[
                ~Solution_screen_essential_supply_vendor_lookup_df["property_id"].isin(uncommon_essential)
            ]
            
            Solution_screen_non_essential_supply_vendor_lookup_df = pd.DataFrame({
                "property_id": final_property_ids,
                "No_of_vendors_found": [0] * len(final_property_ids)
            })

        # Case 4: Both are empty
        else:
            Solution_screen_essential_supply_vendor_lookup_df = pd.DataFrame({
                "property_id": final_property_ids,
                "No_of_vendors_found": [0] * len(final_property_ids)
            })
            Solution_screen_non_essential_supply_vendor_lookup_df = pd.DataFrame({
                "property_id": final_property_ids,
                "No_of_vendors_found": [0] * len(final_property_ids)
            })

        # Step 2: Filter out uncommon properties from final_property_ranking_for_decision
        final_property_ranking_for_decision = final_property_ranking_for_decision[
            ~final_property_ranking_for_decision["Property_ID"].isin(uncommon_property_ids)
        ]

        # Step 2: Filter out uncommon properties from final_property_ranking_for_decision
        final_property_ranking_for_decision = final_property_ranking_for_decision[
            ~final_property_ranking_for_decision["Property_ID"].isin(uncommon_property_ids)
        ]

        # Step 3: Perform Merging
        final_property_ranking_for_decision = pd.merge(
            final_property_ranking_for_decision,
            df_with_property_wise_vendor_score[["property_id", "final_score"]],
            left_on="Property_ID", right_on="property_id", 
            how='left'
        ).drop(columns=["property_id"])

        # Step 4: Rename Columns
        final_property_ranking_for_decision.rename(columns={
            "final_score": "Property-Wise Vendor Score (PWVS)", 
            "employment_availability_score": "Property-Wise Employment Score (PWES)",
            "Property_wise_incentive_score": "Property-Wise Incentive Score (PWIS)",
            "Property_wise_approval_score": "Property-Wise Approval Score (PWAS)",
            "property_suitability_score": "Property-Wise Suitability Score (PWSS)"
        }, inplace=True)
        
        preference = {
            "Property-Wise Vendor Score (PWVS)":5,
            "Property-Wise Employment Score (PWES)":4,
            "Property-Wise Suitability Score (PWSS)":3,
            "Property-Wise Incentive Score (PWIS)":2,
            "Property-Wise Approval Score (PWAS)":2,
        }
        final_property_ranking_for_decision["Aggregate Property Performance Score (APPS)"] = (preference["Property-Wise Vendor Score (PWVS)"] / sum(preference.values())*final_property_ranking_for_decision["Property-Wise Vendor Score (PWVS)"]) + (preference["Property-Wise Employment Score (PWES)"] / sum(preference.values())*final_property_ranking_for_decision["Property-Wise Employment Score (PWES)"]) + (preference["Property-Wise Suitability Score (PWSS)"] / sum(preference.values())*final_property_ranking_for_decision["Property-Wise Suitability Score (PWSS)"]) + (preference["Property-Wise Approval Score (PWAS)"] / sum(preference.values())*final_property_ranking_for_decision["Property-Wise Approval Score (PWAS)"]) + (preference["Property-Wise Incentive Score (PWIS)"] / sum(preference.values())*final_property_ranking_for_decision["Property-Wise Incentive Score (PWIS)"])

        ########################################################################################################################################################
        ################### penalty calculation for proeprties outside soft boundary but within hard boundary as per the new logic(NEW LOGIC) ##############################

        # if USER_DESCISION == "NO":
        if LOCATION_SCOPE == "district_nearby":
            frappe.log_error("final_property_ranking_for_decision_before",f"{final_property_ranking_for_decision}")
            penalty_multiplier = 1 - p_exp  # p_exp already computed earlier

            # Step 1: Merge zone info
            final_property_ranking_for_decision = pd.merge(
                final_property_ranking_for_decision,
                zone_mapping,
                on="Property_ID",
                how="left"
            )

            # Step 2: Apply penalty on APPS
            final_property_ranking_for_decision["Aggregate Property Performance Score (APPS)"] = final_property_ranking_for_decision.apply(
                lambda row: row["Aggregate Property Performance Score (APPS)"] * penalty_multiplier
                if row["zone"] == "Zone3_hard_buffer" 
                else row["Aggregate Property Performance Score (APPS)"],
                axis=1
            )

        #######################################################################################################################################


        final_property_ranking_for_decision = final_property_ranking_for_decision.sort_values(by=["Aggregate Property Performance Score (APPS)"], ascending=False)
        frappe.log_error("final_property_ranking_for_decision_after",f"{final_property_ranking_for_decision}")
        frappe.log_error("final_property_ranking_for_decision_12345",f"{final_property_ranking_for_decision.to_json()}")
 

        #########################################################################################################################################################################
         
        ################### EXECUTION OF LOCATION AWARE RANKING LOGIC(OLD LOGIC) #########################

        # property_id_list = final_property_ranking_for_decision["Property_ID"].tolist()
        # property_id_dict = final_property_ranking_for_decision["Property_ID"]
        # # property_id_list = property_id_dict.tolist()
        # frappe.log_error("property_id_list",f"{property_id_list}")
        # frappe.log_error("property_id_dict",f"{property_id_dict}")
        # aggregate_score_list = final_property_ranking_for_decision["Aggregate Property Performance Score (APPS)"].tolist()
        # frappe.log_error("aggregate_score_list",f"{aggregate_score_list}")

        # df_formation = pd.DataFrame({
        #                 'Property_ID': property_id_list,
        #                 'Aggregate Property Performance Score (APPS)': aggregate_score_list
        #                 })
        # frappe.log_error("df_formation",f"{df_formation}")

        # location_query_result = extract_location_robust(aiResponse) # example:- "bharuch, gujarat, india" or "Not available in list."

        # if location_query_result == "Not Available in List":
        #     frappe.log_error("Not Available in List",f"{location_query_result}")
        #     location_aware_property_ranking = "Not Available in List"
        #     frappe.log_error("location_aware_property_ranking",f"{location_aware_property_ranking}")
        #     # return location_aware_property_ranking
        # elif location_query_result != "Not Available in List":
        #     frappe.log_error("Available in List",f"{location_query_result}")
        #     # run the pipeline
        #     result = run_location_postprocessor(df_formation, location_query_result)
        #     original_format_columns = ["Property_ID", "normalized_score"]
        #     location_aware_property_ranking = result[original_format_columns]
        #     frappe.log_error("location_aware_property_ranking",f"{location_aware_property_ranking}")

        #     # Convert DICT_1 to dataframe
        #     dict_df = pd.DataFrame(list(property_id_dict.items()), columns=['dict_key', 'Property_ID'])

        #     # Merge with original dataframe
        #     merged_df = pd.merge(dict_df, location_aware_property_ranking, on='Property_ID', how='left')

        #     # Convert to dictionary
        #     result_dict = dict(zip(merged_df['dict_key'], merged_df['normalized_score']))
        #     final_property_ranking_for_decision["Reranked_Aggregate_Property_Performance_Score_(RAPPS)"] = result_dict

        #     frappe.log_error("result_dict",f"{result_dict}")
        #     frappe.log_error("ULTIMATE",f"{final_property_ranking_for_decision.to_json()}")

        #########################################################################################################################################################################

        # Sorting all dataframes based on scores_df order
        Solution_screen_employment_lookup_df = sort_by_scores(Solution_screen_employment_lookup_df, final_property_ranking_for_decision)
        Solution_screen_incentive_lookup_df = sort_by_scores(Solution_screen_incentive_lookup_df, final_property_ranking_for_decision)
        Solution_screen_approval_lookup_df = sort_by_scores(Solution_screen_approval_lookup_df, final_property_ranking_for_decision)
        Solution_screen_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_essential_supply_vendor_lookup_df, final_property_ranking_for_decision)
        Solution_screen_essential_supply_all_vendor_lookup_df = sort_by_scores(Solution_screen_essential_supply_all_vendor_lookup_df, final_property_ranking_for_decision)
        Solution_screen_non_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_vendor_lookup_df, final_property_ranking_for_decision)
        Solution_screen_non_essential_supply_all_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_all_vendor_lookup_df, final_property_ranking_for_decision)
        if not keyword_given_by_user:
            frappe.log_error("keyword_given_by_user",f"{final_property_ranking_for_decision}")
            Final_analytics_results_query_to_build_industry_from_scratch = {
                # "Filtered_final_property_ranking_for_decision" : None,
                # "Filtererd_Solution_screen_employment_lookup_df" : None,
                # "Filtererd_Solution_screen_incentive_lookup_df" : None,
                # "Filtererd_Solution_screen_approval_lookup_df" : None,
                # "Filtererd_Solution_screen_essential_supply_vendor_lookup_df" : None,
                # "Filtererd_Solution_screen_non_essential_supply_vendor_lookup_df" : None,

                # "Unfiltered_final_property_ranking_for_decision" : final_property_ranking_for_decision.to_json() if not final_property_ranking_for_decision.empty else None,
                # "Unfiltered_Solution_screen_employment_lookup_df" : Solution_screen_employment_lookup_df.to_json() if not  Solution_screen_employment_lookup_df.empty else None,
                # "Unfiltered_Solution_screen_incentive_lookup_df" : Solution_screen_incentive_lookup_df.to_json() if not Solution_screen_incentive_lookup_df.empty else None ,
                # "Unfiltered_Solution_screen_approval_lookup_df" : Solution_screen_approval_lookup_df.to_json() if not Solution_screen_approval_lookup_df.empty else None,
                # "Unfiltered_Solution_screen_essential_supply_vendor_lookup_df" : Solution_screen_essential_supply_vendor_lookup_df.to_json() if not Solution_screen_essential_supply_vendor_lookup_df.empty else None,
                # "Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df" : Solution_screen_non_essential_supply_vendor_lookup_df.to_json() if not Solution_screen_non_essential_supply_vendor_lookup_df.empty else None,


                "final_scoring_df": final_property_ranking_for_decision.to_json() if not final_property_ranking_for_decision.empty else None,
                "Employment_lookup_df": Solution_screen_employment_lookup_df.to_json() if not Solution_screen_employment_lookup_df.empty else None,
                "Solution_lookup_df": Solution_screen_incentive_lookup_df.to_json() if not Solution_screen_incentive_lookup_df.empty else None,
                "Approval_lookup_df": Solution_screen_approval_lookup_df.to_json() if not Solution_screen_approval_lookup_df.empty else None,
                "Essential_supply_vendor_lookup_df": Solution_screen_essential_supply_vendor_lookup_df.to_json() if not Solution_screen_essential_supply_vendor_lookup_df.empty else None,
                "Essential_supply_all_vendor_lookup_df": Solution_screen_essential_supply_all_vendor_lookup_df.to_json() if not Solution_screen_essential_supply_all_vendor_lookup_df.empty else None,
                "Non_essential_supply_vendor_lookup_df": Solution_screen_non_essential_supply_vendor_lookup_df.to_json() if not Solution_screen_non_essential_supply_vendor_lookup_df.empty else None,
                "Non_essential_supply_all_vendor_lookup_df": Solution_screen_non_essential_supply_all_vendor_lookup_df.to_json() if not Solution_screen_non_essential_supply_all_vendor_lookup_df.empty else None
            }
        else:
            frappe.log_error("keyword_given_by_user_0",f"{final_property_ranking_for_decision}")
            keyword_result = filter_df_by_keywords(keyword_given_by_user, propert_keyword_df)
            filtered_keyword_df, unfiltered_keyword_df = keyword_result[0], keyword_result[1]
            if len(filtered_keyword_df) != 0:

                Filtered_final_property_ranking_for_decision = pd.merge(final_property_ranking_for_decision, filtered_keyword_df, left_on="Property_ID", right_on="ID").drop("ID", axis=1).sort_values(by=["aggregated_score"], ascending=False)
                frappe.log_error("Filtered_final_property_ranking_for_decision",f"{Filtered_final_property_ranking_for_decision}")
                frappe.log_error("Filtered_final_property_ranking_for_decision_json",f"{Filtered_final_property_ranking_for_decision.to_json()}")

                Unfiltered_final_property_ranking_for_decision = pd.merge(final_property_ranking_for_decision, unfiltered_keyword_df, left_on="Property_ID", right_on="ID").drop("ID", axis=1).sort_values(by=["Aggregate Property Performance Score (APPS)"], ascending=False)
                # Unfiltered_final_property_ranking_for_decision = pd.merge(final_property_ranking_for_decision, unfiltered_keyword_df, left_on="Property_ID", right_on="ID").drop("ID", axis=1).sort_values(by=["Reranked_Aggregate_Property_Performance_Score_(RAPPS)"], ascending=False)
                final_property_ranking_for_decision = pd.concat([Filtered_final_property_ranking_for_decision,Unfiltered_final_property_ranking_for_decision], axis = 0, ignore_index=True)
                final_property_ranking_for_decision["aggregated_score"] = (0.3 * final_property_ranking_for_decision["aggregated_score"]) + (0.7 * final_property_ranking_for_decision["Aggregate Property Performance Score (APPS)"])
                # final_property_ranking_for_decision["aggregated_score"] = (0.3 * final_property_ranking_for_decision["aggregated_score"]) + (0.7 * final_property_ranking_for_decision["Reranked_Aggregate_Property_Performance_Score_(RAPPS)"])
                final_property_ranking_for_decision = final_property_ranking_for_decision.sort_values(by=["aggregated_score"], ascending=False) 
                
                Filtererd_Solution_screen_employment_lookup_df = sort_by_scores(Solution_screen_employment_lookup_df, Filtered_final_property_ranking_for_decision, for_final_return=True)
                Filtererd_Solution_screen_incentive_lookup_df = sort_by_scores(Solution_screen_incentive_lookup_df, Filtered_final_property_ranking_for_decision, for_final_return=True)
                Filtererd_Solution_screen_approval_lookup_df = sort_by_scores(Solution_screen_approval_lookup_df, Filtered_final_property_ranking_for_decision, for_final_return=True)
                Filtererd_Solution_screen_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_essential_supply_vendor_lookup_df, Filtered_final_property_ranking_for_decision, for_final_return=True)
                Filtererd_Solution_screen_essential_supply_all_vendor_lookup_df = sort_by_scores(Solution_screen_essential_supply_all_vendor_lookup_df, Filtered_final_property_ranking_for_decision, for_final_return=True)
                Filtererd_Solution_screen_non_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_vendor_lookup_df, Filtered_final_property_ranking_for_decision, for_final_return=True)
                Filtererd_Solution_screen_non_essential_supply_all_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_all_vendor_lookup_df, Filtered_final_property_ranking_for_decision, for_final_return=True)
                
                Unfiltered_Solution_screen_employment_lookup_df = sort_by_scores(Solution_screen_employment_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_incentive_lookup_df = sort_by_scores(Solution_screen_incentive_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_approval_lookup_df = sort_by_scores(Solution_screen_approval_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_essential_supply_vendor_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_essential_supply_all_vendor_lookup_df = sort_by_scores(Solution_screen_essential_supply_all_vendor_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_vendor_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_non_essential_supply_all_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_all_vendor_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                
                Solution_screen_employment_lookup_df = pd.concat([Filtererd_Solution_screen_employment_lookup_df,Unfiltered_Solution_screen_employment_lookup_df], axis = 0, ignore_index=True)
                Solution_screen_incentive_lookup_df = pd.concat([Filtererd_Solution_screen_incentive_lookup_df,Unfiltered_Solution_screen_incentive_lookup_df], axis = 0, ignore_index=True)
                Solution_screen_approval_lookup_df = pd.concat([Filtererd_Solution_screen_approval_lookup_df,Unfiltered_Solution_screen_approval_lookup_df], axis = 0, ignore_index=True)
                Solution_screen_essential_supply_vendor_lookup_df = pd.concat([Filtererd_Solution_screen_essential_supply_vendor_lookup_df,Unfiltered_Solution_screen_essential_supply_vendor_lookup_df], axis = 0, ignore_index=True)
                Solution_screen_essential_supply_all_vendor_lookup_df = pd.concat([Filtererd_Solution_screen_essential_supply_all_vendor_lookup_df,Unfiltered_Solution_screen_essential_supply_all_vendor_lookup_df], axis = 0, ignore_index=True)
                Solution_screen_non_essential_supply_vendor_lookup_df = pd.concat([Filtererd_Solution_screen_non_essential_supply_vendor_lookup_df,Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df], axis = 0, ignore_index=True)
                Solution_screen_non_essential_supply_all_vendor_lookup_df = pd.concat([Filtererd_Solution_screen_non_essential_supply_all_vendor_lookup_df,Unfiltered_Solution_screen_non_essential_supply_all_vendor_lookup_df], axis = 0, ignore_index=True)
                
                Solution_screen_employment_lookup_df = sort_by_scores(Solution_screen_employment_lookup_df, final_property_ranking_for_decision, for_final_return=True)
                Solution_screen_incentive_lookup_df = sort_by_scores(Solution_screen_incentive_lookup_df, final_property_ranking_for_decision, for_final_return=True)
                Solution_screen_approval_lookup_df = sort_by_scores(Solution_screen_approval_lookup_df, final_property_ranking_for_decision, for_final_return=True)
                Solution_screen_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_essential_supply_vendor_lookup_df, final_property_ranking_for_decision, for_final_return=True)
                Solution_screen_essential_supply_all_vendor_lookup_df = sort_by_scores(Solution_screen_essential_supply_all_vendor_lookup_df, final_property_ranking_for_decision, for_final_return=True)
                Solution_screen_non_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_vendor_lookup_df, final_property_ranking_for_decision, for_final_return=True)
                Solution_screen_non_essential_supply_all_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_all_vendor_lookup_df, final_property_ranking_for_decision, for_final_return=True)
                # print(type(Filtererd_Solution_screen_employment_lookup_df))
                Final_analytics_results_query_to_build_industry_from_scratch = {

                    # "Filtered_final_property_ranking_for_decision" : Filtered_final_property_ranking_for_decision.to_json() if not Filtered_final_property_ranking_for_decision.empty else None,
                    # "Filtererd_Solution_screen_employment_lookup_df" : Filtererd_Solution_screen_employment_lookup_df.to_json() if not Filtererd_Solution_screen_employment_lookup_df.empty else None,
                    # "Filtererd_Solution_screen_incentive_lookup_df" : Filtererd_Solution_screen_incentive_lookup_df.to_json() if not Filtererd_Solution_screen_incentive_lookup_df.empty else None,
                    # "Filtererd_Solution_screen_approval_lookup_df" : Filtererd_Solution_screen_approval_lookup_df.to_json() if not Filtererd_Solution_screen_approval_lookup_df.empty else None,
                    # "Filtererd_Solution_screen_essential_supply_vendor_lookup_df" : Filtererd_Solution_screen_essential_supply_vendor_lookup_df.to_json() if not Filtererd_Solution_screen_essential_supply_vendor_lookup_df.empty else None,
                    # "Filtererd_Solution_screen_non_essential_supply_vendor_lookup_df" : Filtererd_Solution_screen_non_essential_supply_vendor_lookup_df.to_json() if not Filtererd_Solution_screen_non_essential_supply_vendor_lookup_df.empty else None,

                    # "Unfiltered_final_property_ranking_for_decision" : Unfiltered_final_property_ranking_for_decision.to_json() if not Unfiltered_final_property_ranking_for_decision.empty else None,
                    # "Unfiltered_Solution_screen_employment_lookup_df" : Unfiltered_Solution_screen_employment_lookup_df.to_json() if not Unfiltered_Solution_screen_employment_lookup_df.empty else None,
                    # "Unfiltered_Solution_screen_incentive_lookup_df" : Unfiltered_Solution_screen_incentive_lookup_df.to_json() if not Unfiltered_Solution_screen_incentive_lookup_df.empty else None,
                    # "Unfiltered_Solution_screen_approval_lookup_df" : Unfiltered_Solution_screen_approval_lookup_df.to_json() if not Unfiltered_Solution_screen_approval_lookup_df.empty else None,
                    # "Unfiltered_Solution_screen_essential_supply_vendor_lookup_df" : Unfiltered_Solution_screen_essential_supply_vendor_lookup_df.to_json() if not Unfiltered_Solution_screen_essential_supply_vendor_lookup_df.empty else None,
                    # "Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df" : Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df.to_json() if not Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df.empty else None

                    "final_scoring_df": final_property_ranking_for_decision.to_json() if not final_property_ranking_for_decision.empty else None,
                    "Employment_lookup_df": Solution_screen_employment_lookup_df.to_json() if not Solution_screen_employment_lookup_df.empty else None,
                    "Solution_lookup_df": Solution_screen_incentive_lookup_df.to_json() if not Solution_screen_incentive_lookup_df.empty else None,
                    "Approval_lookup_df": Solution_screen_approval_lookup_df.to_json() if not Solution_screen_approval_lookup_df.empty else None,
                    "Essential_supply_vendor_lookup_df": Solution_screen_essential_supply_vendor_lookup_df.to_json() if not Solution_screen_essential_supply_vendor_lookup_df.empty else None,
                    "Essential_supply_all_vendor_lookup_df": Solution_screen_essential_supply_all_vendor_lookup_df.to_json() if not Solution_screen_essential_supply_all_vendor_lookup_df.empty else None,
                    "Non_essential_supply_vendor_lookup_df": Solution_screen_non_essential_supply_vendor_lookup_df.to_json() if not Solution_screen_non_essential_supply_vendor_lookup_df.empty else None,
                    "Non_essential_supply_all_vendor_lookup_df": Solution_screen_non_essential_supply_all_vendor_lookup_df.to_json() if not Solution_screen_non_essential_supply_all_vendor_lookup_df.empty else None
                }
            else:
                frappe.log_error("keyword_given_by_user_2",f"{final_property_ranking_for_decision}")
                Unfiltered_final_property_ranking_for_decision = pd.merge(final_property_ranking_for_decision, unfiltered_keyword_df, left_on="Property_ID", right_on="ID").drop("ID", axis=1).sort_values(by=["aggregated_score"], ascending=False)
                Unfiltered_final_property_ranking_for_decision["aggregated_score"] = (0.3 * Unfiltered_final_property_ranking_for_decision["aggregated_score"]) + (0.7 * Unfiltered_final_property_ranking_for_decision["Aggregate Property Performance Score (APPS)"])
                # Unfiltered_final_property_ranking_for_decision["aggregated_score"] = (0.3 * Unfiltered_final_property_ranking_for_decision["aggregated_score"]) + (0.7 * Unfiltered_final_property_ranking_for_decision["Reranked_Aggregate_Property_Performance_Score_(RAPPS)"])
                Unfiltered_final_property_ranking_for_decision = Unfiltered_final_property_ranking_for_decision.sort_values(by=["aggregated_score"], ascending=False)
                Unfiltered_Solution_screen_employment_lookup_df = sort_by_scores(Solution_screen_employment_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_incentive_lookup_df = sort_by_scores(Solution_screen_incentive_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_approval_lookup_df = sort_by_scores(Solution_screen_approval_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_essential_supply_vendor_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_essential_supply_all_vendor_lookup_df = sort_by_scores(Solution_screen_essential_supply_all_vendor_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_vendor_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_non_essential_supply_all_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_all_vendor_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                
                final_property_ranking_for_decision = Unfiltered_final_property_ranking_for_decision
                frappe.log_error("final_property_ranking_for_decision_333",f"{final_property_ranking_for_decision}")

                Solution_screen_employment_lookup_df = Unfiltered_Solution_screen_employment_lookup_df
                Solution_screen_incentive_lookup_df = Unfiltered_Solution_screen_incentive_lookup_df
                Solution_screen_approval_lookup_df = Unfiltered_Solution_screen_approval_lookup_df
                Solution_screen_essential_supply_vendor_lookup_df = Unfiltered_Solution_screen_essential_supply_vendor_lookup_df
                Solution_screen_essential_supply_all_vendor_lookup_df = Unfiltered_Solution_screen_essential_supply_all_vendor_lookup_df
                Solution_screen_non_essential_supply_vendor_lookup_df = Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df
                Solution_screen_non_essential_supply_all_vendor_lookup_df = Unfiltered_Solution_screen_non_essential_supply_all_vendor_lookup_df
                Final_analytics_results_query_to_build_industry_from_scratch ={
                # "Filtered_final_property_ranking_for_decision" : None,
                # "Filtererd_Solution_screen_employment_lookup_df" : None,
                # "Filtererd_Solution_screen_incentive_lookup_df" : None,
                # "Filtererd_Solution_screen_approval_lookup_df" : None,
                # "Filtererd_Solution_screen_essential_supply_vendor_lookup_df" : None,
                # "Filtererd_Solution_screen_non_essential_supply_vendor_lookup_df" : None,

                # "Unfiltered_final_property_ranking_for_decision" : Unfiltered_final_property_ranking_for_decision.to_json() if not Unfiltered_final_property_ranking_for_decision.empty else None,
                # "Unfiltered_Solution_screen_employment_lookup_df" : Unfiltered_Solution_screen_employment_lookup_df.to_json() if not Unfiltered_Solution_screen_employment_lookup_df.empty else None,
                # "Unfiltered_Solution_screen_incentive_lookup_df" : Unfiltered_Solution_screen_incentive_lookup_df.to_json() if not Unfiltered_Solution_screen_incentive_lookup_df.empty else None,
                # "Unfiltered_Solution_screen_approval_lookup_df" : Unfiltered_Solution_screen_approval_lookup_df.to_json() if not Unfiltered_Solution_screen_approval_lookup_df.empty else None,
                # "Unfiltered_Solution_screen_essential_supply_vendor_lookup_df" : Unfiltered_Solution_screen_essential_supply_vendor_lookup_df.to_json() if not Unfiltered_Solution_screen_essential_supply_vendor_lookup_df.empty else None,
                # "Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df" : Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df.to_json() if not Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df.empty else None

                "final_scoring_df": final_property_ranking_for_decision.to_json() if not final_property_ranking_for_decision.empty else None,
                "Employment_lookup_df": Solution_screen_employment_lookup_df.to_json() if not Solution_screen_employment_lookup_df.empty else None,
                "Solution_lookup_df": Solution_screen_incentive_lookup_df.to_json() if not Solution_screen_incentive_lookup_df.empty else None,
                "Approval_lookup_df": Solution_screen_approval_lookup_df.to_json() if not Solution_screen_approval_lookup_df.empty else None,
                "Essential_supply_vendor_lookup_df": Solution_screen_essential_supply_vendor_lookup_df.to_json() if not Solution_screen_essential_supply_vendor_lookup_df.empty else None,
                "Essential_supply_all_vendor_lookup_df": Solution_screen_essential_supply_all_vendor_lookup_df.to_json() if not Solution_screen_essential_supply_all_vendor_lookup_df.empty else None,
                "Non_essential_supply_vendor_lookup_df": Solution_screen_non_essential_supply_vendor_lookup_df.to_json() if not Solution_screen_non_essential_supply_vendor_lookup_df.empty else None,
                "Non_essential_supply_all_vendor_lookup_df": Solution_screen_non_essential_supply_all_vendor_lookup_df.to_json() if not Solution_screen_non_essential_supply_all_vendor_lookup_df.empty else None

                }

        response = {
                "Analytics_response": Final_analytics_results_query_to_build_industry_from_scratch,
                "Is_Error" : False
            }
        log_to_file("response",response)
        update_process(chatId,"Analyzing Data","Complete",1)
        update_process(chatId,"Preparing Result","Processing",0)
        time.sleep(5)
        update_process(chatId,"Preparing Result","Complete",1)
        del aiResponse
        del Final_analytics_results_query_to_build_industry_from_scratch
        
        locals().clear()
        gc.collect()
        
        return response
        
    
    except Exception as e:
        update_process(chatId,"Analyzing Data","Fail",0)
        error_details = traceback.format_exc()
        
        log_to_file("main error",str(error_details))
        response = {
                "Analytics_response": f"Error From Analytics :- {e}",
                "Is_Error" : True
            }
        return response
    
def log_to_file(key,value):
    """
    Logs key-value data to a file with a timestamp.
    
    :param filename: Name of the log file.
    :param data: Key-value pairs to log.
    """
    log_entry = {
        "t": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        f"{key}" : value
    }
    
    with open("log2.txt", "a", encoding="utf-8") as file:
        file.write(json.dumps(log_entry) + "\n")