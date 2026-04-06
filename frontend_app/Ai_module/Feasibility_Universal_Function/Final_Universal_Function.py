# ── Standard library
import os
import sys
import re
import gc
import time
import json
import stat
import errno
import hashlib
import shutil
import tempfile
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Any, List, Tuple, Union
import requests
import json
from urllib.parse import urlencode, quote
import warnings
import configparser
import frappe
import base64
import gzip
import bz2
import re
import zlib
import msgpack

# ── Third-party utilities
import psutil
from dotenv import load_dotenv

# ── Chroma
import chromadb
from chromadb.config import Settings

# ── LangChain core
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate

# ── LangChain loaders
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
    CSVLoader,
    TextLoader,
    UnstructuredHTMLLoader,
    UnstructuredFileLoader,
)

# ── LangChain embeddings / vectorstores / retrievers
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers import EnsembleRetriever
import configparser
# ── LLM client (if used with MultiQuery)
from langchain_groq import ChatGroq

# PERSIST_ROOT = "D:/work_folder/mars_rag_qna/data_45/vectors"
# PERSIST_ROOT = "/home/mars/frappe-bench/apps/frontend_app/frontend_app/vectors"
base_dir = os.path.expanduser("~")
PERSIST_ROOT = os.path.join(base_dir, "frappe-bench/apps/frontend_app/frontend_app/vectors")
FEAS_DOCTYPE = "Feasibility Report"
FOLL_DOCTYPE = "Follow Up"

# per doctype storage configuration
FEASIBILITY_ALLOCATED_STORAGE = 0.6
FOLLOW_UP_ALLOCATED_STORAGE = 0.4

# storage folders name of follow up and feasibility vectors 
LABEL_FOLLOW = "Follow_Up"
LABEL_FEASIBILITY = "Feasibility_Report"

base_dir = os.path.expanduser("~")
config_file = os.path.join(base_dir, "frappe-bench/apps/frontend_app/frontend_app/Log_management/mars.ini")
config = configparser.ConfigParser()
config.read(config_file)


UNIVERSAL_DICT = {
    "Doctypes": [
        {
            "name": "Feasibility Report",
            "Vector_ID_Field": "custom_feasibility_vector_file_name",
            "Data_Source_Field": "file_path",
            "session_id_required": True
        },
        {
            "name": "Mars Configurations",
            "Storage_Field": "storage_limit",
            "Deletion_Period_Field": "time_period_for_deletion",
            "session_id_required": False
        },
        {
            "name": "File",
            "File_URL_Field": "file_url",
            "session_id_required": True
        }
    ]
}

UNIVERSAL_DICT_FOR_HELPER_DOCTYPES = {
    "Doctypes": [
        {
            "name": "Mars Configurations",
            "Storage_Field": "storage_limit",
            "Deletion_Period_Field": "time_period_for_deletion",
            "session_id_required": False
        },
        {
            "name": "File",
            "File_URL_Field": "file_url",
            "session_id_required": True
        }
    ]
}

embedding_model = HuggingFaceBgeEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
            query_instruction="Represent this sentence for searching relevant passages:"
        )

warnings.filterwarnings("ignore")
# config_file = '/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Log_management/mars.ini'
# config = configparser.ConfigParser()
# config.read(config_file)

api_key = config['Key']['groq_key'] 
frappe_api_key = config['Frappe_api_key_and_secret']['frappe_api_key']
frappe_api_secret = config['Frappe_api_key_and_secret']['frappe_api_secret']
ritu_local_base_url = config['Frappe_api_key_and_secret']['ritu_local_base_url']
live_base_url = config['Frappe_api_key_and_secret']['live_base_url']

llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.5, api_key = api_key)


# this code is to check whether the data passes to it is base64 encoded or not.
def is_base64(data: str|dict) -> bool:
    """
    Check if a string is Base64 encoded.
    
    Args:
        data: String to check
        
    Returns:
        True if data appears to be Base64 encoded, False otherwise
    """
    if isinstance(data, dict):
        frappe.log_error("is_base_64_data_a_dict", "YESSSSS")
        data = data.get("encoded_data")
    # data = data.get("encoded_data")

    if not isinstance(data, str):
        frappe.log_error("NOT A STRING", "YESSSSS")
        return False
    
    if not data:
        frappe.log_error("NO DATA AVAILABLE", "YESSSSS")
        return False
    
    # Base64 regex pattern
    base64_pattern = r'^[A-Za-z0-9+/]*={0,2}$'
    
    # Must match the pattern
    if not re.match(base64_pattern, data):
        frappe.log_error("not re.match", "YESSSSS")
        return False
    
    # Length must be divisible by 4
    if len(data) % 4 != 0:
        return False
    
    # Check for valid padding
    if '=' in data:
        # '=' can only appear at the end
        if not data.endswith('='):
            return False
        # Count '=' at the end (max 2)
        if data.count('=') > 2:
            return False
        # Check '=' are only at the end
        if not data.rstrip('=').endswith(('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
                                        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                                        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                                        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                                        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '+', '/')):
            return False
    
    # Additional check: Try to decode it (optional but more accurate)
    try:
        import base64
        # This will raise an error if it's not valid Base64
        base64.b64decode(data, validate=True)
        return True
    except:
        # If decode check fails, fall back to pattern matching
        # At this point, pattern matching already passed
        return True

# This code is to check whether the encoded data passed to us is string or not and if string then convert it in to our required format which is dict and then proceed with checking whether the passed data is base64 encoded or not.
def check_encoded_data(input_data: str) -> bool:
    """
    Handle both raw Base64 strings and JSON containing Base64
    """
    # First, try to parse as JSON
    try:
        parsed = json.loads(input_data)
        
        # Check if it has an 'encoded_data' field
        if isinstance(parsed, dict) and 'encoded_data' in parsed:
            encoded_string = parsed['encoded_data']
            return is_base64(encoded_string)
        else:
            # If it's JSON but doesn't have encoded_data, check the whole thing
            # Convert back to string and check
            return is_base64(str(input_data))
            
    except json.JSONDecodeError:
        # If it's not valid JSON, treat it as a raw string
        return is_base64(input_data)

# This code is used to decode the encoded data which is identified by the above isbase64() function   
def retrieve_and_decompress(compressed_data):
   
    data = json.loads(compressed_data)  # Read the JSON file
    # with open("log2.txt", "a", encoding="utf-8") as file:
    #     file.write(json.dumps(compressed_data) + "\n")
    # Step 2: Extract the Base64 encoded data from the specific key in the JSON
    encoded_data = data.get("encoded_data")  # Make sure the key is correct
 
    if not encoded_data:
        frappe.log_error("not encoded data", "YESS")
        print("No 'encoded_data' found in the JSON.")
        return
 
    # Step 3: Decode the Base64 encoded data
    try:
        frappe.log_error("Decode the Base64 encoded data", "YESS")
        compressed_data = base64.b64decode(encoded_data)
    except Exception as e:
        print(f"Error decoding Base64: {e}")
        frappe.log_error("Decode the Base64 encoded data(exception)", f"YESS{e}")
        return
 
    # Step 4: Decompress the decoded data (assuming gzip compression)
    try:
        frappe.log_error("Decompress the decoded data", "YESS")
        decompressed_data = gzip.decompress(compressed_data)
    except Exception as e:
        print(f"Error decompressing gzip: {e}")
        frappe.log_error("Decompress the decoded data(exception)", f"YESS{e}")
        return
 
    # Step 5: Unpack the decompressed data using msgpack
    try:
        frappe.log_error("Unpack the decompressed data using msgpack", "YESS")
        final_data = msgpack.unpackb(decompressed_data, raw=False)
        return final_data
    except Exception as e:
        print(f"Error unpacking MessagePack: {e}")
        frappe.log_error("Unpack the decompressed data using msgpack(exception)", f"YESS{e}")
        return

def fetch_frappe_doc_universal(
    doctype: str,
    identifier: str,
    *,
    fields: list[str] | None = None,
    timeout: int = 30,
    debug: bool = False,
):

    base_url = ritu_local_base_url

    headers = {
        "Authorization": f"token {frappe_api_key}:{frappe_api_secret}",
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


# THIS FUNCTION IS FOR HELPER DOCTYPES ONLY AND NOT FOR THE MAIN DOCTYPES.
def wrapper_for_frappe_function_for_fetching_fields(doctype_name: str, doc_session_id:str = None, fields = ["*"]):

    # doctype_name(input parameter) = the actual name of the doctype from which fields are to be fetched
    # doc_session_id(input parameter) = the session id present in the respective doctype.But if no value is provided in this input parameter then we will insert the value of the doctype_name input parameter as a default value in this but in no way we will leave this input parameter empty.

    # for value in UNIVERSAL_DICT.get("Doctypes", []):
    for value in UNIVERSAL_DICT_FOR_HELPER_DOCTYPES.get("Doctypes", []):
        # print(value)
        if value["name"] == doctype_name:
            print(doctype_name)
            if value["session_id_required"]:
                if not doc_session_id:
                    with open("/home/marsaiae/frappe-bench/apps/usaix/usaix/Ai_module/Feasibility_Universal_Function/testlog.txt", "a") as file:
                        file.write(f"\nSTATUS👌:- /n{"Particular session id is required for the respective doctype."}")
                    return "Particular session id is required for the respective helper doctype without which we cannot go ahead."
            
                # data = frappe_function_for_fetching_fields_from_doctype(doctype = doctype_name, doc_id = doc_session_id)
                data = fetch_frappe_doc_universal(doctype = doctype_name, identifier = doc_session_id, fields = fields)
                with open("/home/marsaiae/frappe-bench/apps/usaix/usaix/Ai_module/Feasibility_Universal_Function/testlog.txt", "a") as file:
                    file.write(f"\nSTATUS👌:- /n{data}") 
                return data
            
            elif not value["session_id_required"]:
                print("ok😍")
                doc_session_id = doctype_name
                print(doc_session_id)
                print(type(doc_session_id))
                # data = frappe_function_for_fetching_fields_from_doctype(doctype = doctype_name, doc_id = doc_session_id)
                data = fetch_frappe_doc_universal(doctype = doctype_name, identifier = doc_session_id, fields = fields)
                with open("/home/marsaiae/frappe-bench/apps/usaix/usaix/Ai_module/Feasibility_Universal_Function/testlog.txt", "a") as file:
                    file.write(f"\nSTATUS👌:- /n{data}")
                return data

    with open("/home/marsaiae/frappe-bench/apps/usaix/usaix/Ai_module/Feasibility_Universal_Function/testlog.txt", "a") as file:
        file.write(f"\nSTATUS👌:- /n{"The doctype mentioned does not exist in the Universal dict in which we store the doctypes which requires the usage of vector stores"}")
    return "The doctype mentioned does not exist in the Universal helper doctype dict in which we store the doctypes that acts as a helper to the main doctypes."

def detect_data_source(data):
    frappe.log_error("data_for_detection", f"{data}")
    frappe.log_error("data_for_detection_again", f"{type(data)}")
    # json.loads(data)
    # detecting whether the data is base64 encoded or not
    detect_base64_data = check_encoded_data(data)
    frappe.log_error("is_it_base_64", f"{detect_base64_data}")
    if detect_base64_data:
        frappe.log_error("is_it_base_64", f"{detect_base64_data}")
        return "base64_encoded_data"

    # 1. JSON onject(dict or list)
    if isinstance(data, (dict, list)):
        return "JSON_object"

    # 2. JSON string
    if isinstance(data, str):
        # check if it's a valid JSON content
        try:
            frappe.log_error("json_string_2", f"{json.loads(data)}")
            json.loads(data)
            frappe.log_error("json_string", f"{json.loads(data)}")
            return "json_string"
        except:
            pass

        # check if it's a filename (file path exists or looks like one)
        if os.path.isfile(data):
            return "file_path"
        
        # check for filename pattern even if it does'nt exist yet(it means even if it is not a filepath and rather a filename then check it)
        if any(data.endswith(ext) for ext in [
            ".pdf", ".txt", ".json", ".csv", ".docx", 
            ".xlsx", ".png", ".jpg", ".jpeg"
        ]):

            return "file_name_like"

        return "string"
        # data_type = type(data)
        # frappe.log_error("data_type", f"{data_type}")
        # return data_type

    # 3. PIL images object
    if isinstance(data, Image.Image):
        return "PIL image"

    # 4. Image bytes
    if isinstance(data, (bytes, bytearray)):
        try:
            Image.open(BytesIO(data))
            return "Image Bytes"
        except:
            return "raw bytes"

    return "Unknown"

# this code is to retrieve the values of the fields namely'storage limit' and 'time period for deletion' which are stored in 'Mars Configurations' doctype.
def fetch_doc_fields_by_name(
    doctype: str,
    doc_name: str,                 # for Single doctypes, this is the same as doctype
    *,
    fields: list[str] | None = None,  # e.g. ["*"] or ["doc_log", "file_log", ...]
    timeout: int = 30,
    debug: bool = False,
):
 
    # base_url = live_base_url
    base_url = ritu_local_base_url

    if not (base_url and frappe_api_key and frappe_api_secret):
        raise ValueError("Missing BASE_URL / API_KEY / API_SECRET")

    headers = {
        "Authorization": f"token {frappe_api_key}:{frappe_api_secret}",
        "Content-Type": "application/json",
        "Expect": "",
    }

    doctype_path  = quote(doctype, safe="")
    name_path     = quote(doc_name, safe="")
    url = f"{base_url.rstrip('/')}/api/resource/{doctype_path}/{name_path}"

    params = {}
    if fields:
        params["fields"] = json.dumps(fields)

    r = requests.get(url, headers=headers, params=params, timeout=timeout)
 
    return r.json()["data"]     # <-- a dict of fieldname -> value

def fetch_single_doc_by_name(
    doctype: str,
    doc_name: str,
    *,
    api_key: str | None = None,
    api_secret: str | None = None,
    base_url: str | None = None,
    fields: list[str] | None = None,   # e.g. ["*"] or ["name", "owner", ...]
    timeout: int = 30,
    debug: bool = False,
    ):
    
    """
    Fetch a single Frappe/ERPNext document by name from a given DocType.

    - Uses token auth: 'token <api_key>:<api_secret>'
    - URL-encodes the DocType (handles spaces)
    - Accepts optional 'fields' (["*"] for all fields)
    - Falls back to env vars if args are None:
        API_KEY, API_SECRET, BASE_URL
    - Returns parsed JSON (dict). Raises requests.HTTPError on non-2xx.
    """

    # base_url = live_base_url
    base_url = ritu_local_base_url

    if not base_url:
        raise ValueError("Missing base_url (pass base_url=... or set BASE_URL env var)")
    if not frappe_api_key or not frappe_api_secret:
        raise ValueError("Missing API credentials (API_KEY/API_SECRET)")

    # ---- headers ----
    headers = {
        "Authorization": f"token {frappe_api_key}:{frappe_api_secret}",
        "Content-Type": "application/json",
        "Expect": "",
    }

    # ---- request URL (doctype in path must be encoded) ----
    doctype_path = quote(doctype, safe="")
    url = f"{base_url.rstrip('/')}/api/resource/{doctype_path}"

    # ---- query params: filter by exact name ----
    if doctype == "File":
        params = {
            # "filters": json.dumps({"name": doc_name})
            "filters": json.dumps({"file_name": doc_name})
        }
    if doctype == "Feasibility Report":
        params = {
            "filters": json.dumps({"name": doc_name})
            # "filters": json.dumps({"file_name": doc_name})
        }
        
    if fields:
        params["fields"] = json.dumps(fields)

    # ---- make request ----
    r = requests.get(url, headers=headers, params=params, timeout=timeout)

   
    data = r.json()
   

    return data

def make_headers():
 
    return {"Authorization": f"token {frappe_api_key}:{frappe_api_secret}", "Expect": ""}

def fetch_pdf_to_temp(file_url: str, is_private: bool | None = None) -> str:

    # base_url = live_base_url
    base_url = ritu_local_base_url

    path = file_url if file_url.startswith("/") else f"/{file_url}"
    if is_private is None:
        is_private = path.startswith("/private/")

    if file_url.startswith("http://") or file_url.startswith("https://"):
        url = file_url
    elif is_private:
        url = f"{base_url}/api/method/frappe.utils.file_manager.download_file?{urlencode({'file_url': path})}"
    else:
        url = f"{base_url}{path}"

    r = requests.get(url, headers=make_headers(), timeout=60, stream=True)

    ct = r.headers.get("Content-Type","").lower()
    if "pdf" not in ct and not file_url.lower().endswith(".pdf"):
        # still allow if private API returns application/octet-stream
        sample = next(r.iter_content(1024), b"")
        if not sample.startswith(b"%PDF-"):
            raise RuntimeError(f"Expected PDF, got Content-Type={ct} (first bytes not %PDF-)")
    r.raise_for_status()

    fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    with os.fdopen(fd, "wb") as f:
        for chunk in r.iter_content(1024 * 64):
            if chunk: f.write(chunk)
    return tmp_path

# def getting_pdf_from_file_url_in_feasibility_session_id(data: json):
#     pdf_path = data["data"][0]["file_path"]

#     m = re.search(r'[^/\\]+$', pdf_path)
#     filename = m.group(0) if m else None
#     # print(filename)  # samplesecured_256bitaes_pdf.pdf

#     # calling the fetch_single_doc_by_name() again to access the contents of the pdf from the "file list" doctype in order to create a new vector file form it.
#     file_data = fetch_single_doc_by_name(
#     "File", # 
#     # "Report-05-08-25 -2010",
#     filename,
#     api_key=frappe_api_key,
#     api_secret=frappe_api_secret,
#     base_url=ritu_local_base_url,
#     fields=["*"],   # or omit to use server defaults
#     debug=True
#     ) 

#     if file_data["data"]:
#         if_is_file_data = file_data["data"][0]["file_url"]
#         if not if_is_file_data:
#             # print("No such file exists.Upload the PDF again to continue")
#             return "No such file exists.Upload the PDF again to continue"
#         if if_is_file_data:
#             tmp_pdf = fetch_pdf_to_temp(if_is_file_data)
#             # sanity check
#             if not os.path.exists(tmp_pdf) or os.path.getsize(tmp_pdf) < 1024:
#                 return "Downloaded file is missing/too small to be a valid PDF.", "fail-file-download-too-small"

#             with open(tmp_pdf, "rb") as fh:
#                 head = fh.read(5)
#             if head != b"%PDF-":
#                 return "Downloaded file is not a PDF (likely an HTML redirect/login page).", "fail-not-a-pdf"

#             return tmp_pdf
#     if not file_data["data"]:
#         # print("No such file exists.Upload the PDF again to continue")
#         return "No such file exists.Upload the PDF again to continue"
#     # if_is_file_data = file_data["data"][0]["file_url"]
#     # if not if_is_file_data:
#     #     print("No such file exists.Upload the PDF again to continue")
#     #     return "No such file exists.Upload the PDF again to continue"
#     # if if_is_file_data:
#     #     tmp_pdf = fetch_pdf_to_temp(if_is_file_data)
#     #     return tmp_pdf

def getting_pdf_from_file_url_in_feasibility_session_id(
    main_doctype_data: dict|str,
    main_doctype_field: str,
    helper_doctype_name: str,
    helper_doctype_field: str,
    ):
    # What is main_doctype_data = the amin doctype is the doctype where vector is used like feasibility report doctype and the helper doctype is the doctype which acts as a helper to the main doctype like the file doctype here.
    # pdf_path = data["data"][0]["file_path"]
    pdf_path = main_doctype_data["data"][main_doctype_field]

    m = re.search(r'[^/\\]+$', pdf_path)
    filename = m.group(0) if m else None
    # print(filename)  # samplesecured_256bitaes_pdf.pdf

    # calling the fetch_single_doc_by_name() again to access the contents of the pdf from the "file list" doctype in order to create a new vector file form it.
    # file_data = fetch_single_doc_by_name(
    file_data = wrapper_for_frappe_function_for_fetching_fields(
    # "File",  
    doctype_name = helper_doctype_name, # 
    # "Report-05-08-25 -2010",
    doc_session_id = filename,

    # fields=["*"],   # or omit to use server defaults
    # debug=True
    ) 

    with open("/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Ai_module/Feasibility_Universal_Function/testlog.txt", "a") as file:
        file.write(f"\nSTATUS👌:- /n{file_data}")
    print(file_data)

    if_is_file_data = None

    if isinstance(file_data, dict):
        if file_data["data"]:
            # if_is_file_data = file_data["data"][0]["file_url"]
            # if_is_file_data = file_data["data"][helper_doctype_field]
            try:
                for item in file_data["data"]:
                    if_is_file_data = item[helper_doctype_field]
            except:
                return "some error occured while fetching required fields from the 'file' doctype."
            if not if_is_file_data:
                # print("No such file exists.Upload the PDF again to continue")
                return "No such file exists.Upload the PDF again to continue"
            if if_is_file_data:
                tmp_pdf = fetch_pdf_to_temp(if_is_file_data)
                # sanity check
                if not os.path.exists(tmp_pdf) or os.path.getsize(tmp_pdf) < 1024:
                    return "Downloaded file is missing/too small to be a valid PDF:- fail-file-download-too-small"

                with open(tmp_pdf, "rb") as fh:
                    head = fh.read(5)
                if head != b"%PDF-":
                    return "Downloaded file is not a PDF (likely an HTML redirect/login page):- fail-not-a-pdf"

                return tmp_pdf
        if not file_data["data"]:
            # print("No such file exists.Upload the PDF again to continue")
            return "No such file exists.Upload the PDF again to continue"
    
    else:
        return file_data

# def checking_whether_vector_file_exists_or_not_and_ifnot_then_creating_new_vector_file(
#         doctype:str, 
#         doc_name:str,
#         folder_name:str):
    
#     data = fetch_single_doc_by_name(
#     doctype,
#     doc_name,
#     api_key=frappe_api_key,
#     api_secret=frappe_api_secret,
#     base_url=ritu_local_base_url,
#     fields=["*"],   # or omit to use server defaults
#     debug=True
#     ) # returns a json

#     # print("data", data)

#     # print("data(fetch_doc_by_name)",data)
    
#     if doctype == "Feasibility Report":
#         is_vector_exists = data["data"][0]["custom_feasibility_vector_file_name"]
#         # print(is_vector_exists)
#         if not is_vector_exists:
            
#             creating_vectors = getting_pdf_from_file_url_in_feasibility_session_id(data=data)

#             if creating_vectors == "No such file exists.Upload the PDF again to continue":
#                 return creating_vectors, "fail-not is_vector_exists-also_PDF_not_exists"
#             else:
#                 return creating_vectors, "success-not is_vector_exists-but_PDF_exists"

#         elif is_vector_exists:
#             # parent = Path(fr"D:\work_folder\mars_rag_qna\data_45\vectors\{doctype}")
#             # parent = Path(fr"{PERSIST_ROOT}\{doctype}")
#             parent = Path(fr"{PERSIST_ROOT}/{folder_name}")
#             # parent = os.path.join(PERSIST_ROOT, folder_name)
#             os.makedirs(parent, exist_ok=True)
#             folders = sorted([p for p in parent.iterdir() if p.is_dir()],
#                             key=lambda p: p.stat().st_ctime)  # creation time on Windows

#             iter_folders = []

#             for p in folders:
#                 iter_folders.append(p.name)

#             # print("ITER_FOLDERS",iter_folders)

#             for item in iter_folders:
#                 # print("ITEM",item)
#                 # print("VECTOR",is_vector_exists)
#                 if item == is_vector_exists:
#                     # print("VECTOR MATCH",is_vector_exists)
#                     return is_vector_exists, "success-is_vector_exists"
        
#             creating_vectors = getting_pdf_from_file_url_in_feasibility_session_id(data=data)
#             if creating_vectors == "No such file exists.Upload the PDF again to continue":
#                 return creating_vectors, "fail-no_PDF_exists"
#             else:
#                 # print("VECTOR MATCH",is_vector_exists)
#                 return creating_vectors, "success-is_PDF_exists"
#                 # return "vector folder does not exist in the local storage", "fail-is_vector_exists"
                    
                
#     else: # for follow up #
#         # print("The support for follow up is not integrated yet")
#         return "The support for follow up is not integrated yet"

def checking_whether_vector_file_exists_or_not_and_ifnot_then_creating_new_vector_file(
        doctype:str, # it means the name of the doctype
        doc_name:str, # it means the session id of the doctype
        folder_name:str,
        vector_id_field: str,
        data_source_field: str):
    
    # data = fetch_single_doc_by_name(
    # doctype,
    # doc_name,

    # fields=["*"],   # or omit to use server defaults
    # debug=True
    # ) # returns a json

    # data = wrapper_for_frappe_function_for_fetching_fields(
    #     doctype_name = doctype,
    #     doc_session_id = doc_name,
    # )    

    data = fetch_frappe_doc_universal(
        doctype = doctype,
        identifier = doc_name
    )

    frappe.log_error("Check", f"{data}")

    with open("/home/marsaiae/frappe-bench/apps/usaix/usaix/Ai_module/Feasibility_Universal_Function/testlog.txt", "a") as file:
        file.write(f"\nSTATUS👌:- /n{data}")

    if not isinstance(data, dict):
        return data, "fail-not is_vector_exists-also_PDF_not_exists"

    vector_id_field_for_respective_doctype = None
    data_source_fields_for_respective_doctype = None
    name_for_helper_doctype = None
    field_for_helper_doctype = None

    # These fields are present only for those doctypes in the universal dict for which session id is required.
    # for value in UNIVERSAL_DICT["Doctypes"]:
    #     if value["name"] == doctype and value["session_id_required"]:
    #         if vector_id_field and data_source_field:
    #             vector_id_field_for_respective_doctype = vector_id_field
    #             data_source_fields_for_respective_doctype = data_source_field
    #         else:
    #             vector_id_field_for_respective_doctype = value["Vector_ID_Field"]
    #             data_source_fields_for_respective_doctype = value["Data_Source_Field"]

    # for value in UNIVERSAL_DICT.get("Doctypes", []):
    #     if (
    #         value.get("name") == doctype
    #         and value.get("session_id_required") is True
    #         and vector_id_field
    #         and data_source_field
    #     ):
    #         vector_id_field_for_respective_doctype = vector_id_field
    #         data_source_fields_for_respective_doctype = data_source_field
    #     else:
    #         vector_id_field_for_respective_doctype = value["Vector_ID_Field"]
    #         data_source_fields_for_respective_doctype = value["Data_Source_Field"]

    # for value in UNIVERSAL_DICT.get("Doctypes", []):
        # if value.get("name") == doctype and value.get("session_id_required"):
        #     vector_id_field_for_respective_doctype = (
        #         vector_id_field or value["Vector_ID_Field"]
        #     )
        #     data_source_fields_for_respective_doctype = (
        #         data_source_field or value["Data_Source_Field"]
        #     )
        #     break
        # else:
        #     raise ValueError(f"Doctype '{doctype}' not found or not session-based")

    # found = False
    # for value in UNIVERSAL_DICT.get("Doctypes", []):
    #     if value.get("name") == doctype and value.get("session_id_required"):
    #         vector_id_field_for_respective_doctype = vector_id_field or value["Vector_ID_Field"]
    #         data_source_fields_for_respective_doctype = data_source_field or value["Data_Source_Field"]
    #         found = True
    #         break

    # if not found:
    #     raise ValueError(f"Doctype '{doctype}' not found or not session-based")

    vector_id_field_for_respective_doctype = vector_id_field 
    data_source_fields_for_respective_doctype = data_source_field 

    for value in UNIVERSAL_DICT_FOR_HELPER_DOCTYPES.get("Doctypes", []):
        if value["name"] == "File":
            name_for_helper_doctype = "File"
            field_for_helper_doctype = value["File_URL_Field"]

    fail_statements = [
    "No such file exists.Upload the PDF again to continue",
    "some error occured while fetching required fields from the 'file' doctype.",
    "Downloaded file is missing/too small to be a valid PDF:- fail-file-download-too-small",
    "Downloaded file is not a PDF (likely an HTML redirect/login page):- fail-not-a-pdf",
    "Particular session id is required for the respective helper doctype without which we cannot go ahead.",
    "The doctype mentioned does not exist in the Universal helper doctype dict in which we store the doctypes that acts as a helper to the main doctypes.",
    ]

    # checking_data_source = detect_data_source(data)
    # doc_data = safe_get_data(data)

    # if not isinstance(doc_data, dict):
    #     return "Invalid Response from feasibility Report Doctype"
    source_value = data["data"][data_source_fields_for_respective_doctype]  
    frappe.log_error("source_value", f"{source_value}")  
    # source_value = doc_data.get(data_source_fields_for_respective_doctype)
    checking_data_source = detect_data_source(source_value)
    frappe.log_error("another check", f"{type(checking_data_source)}")
    frappe.log_error("checking_data_source", f"{checking_data_source}")

    try:
        # is_vector_exists = data["data"][0]["custom_feasibility_vector_file_name"]
        is_vector_exists = data["data"][vector_id_field_for_respective_doctype]
    except KeyError:
        is_vector_exists = None
    
    '''This block of code(ie:- if block) supports the data source which is either the file path or file name ie. basically just the path or name and not the actual content
    which is why a helper doctype namely "file" doctype is needed to fetch the actual content from either the file path or file name.'''
    if checking_data_source == "file_path" or checking_data_source == "file_name_like":
    # if doctype == "Feasibility Report":
        
        # try:
        #     # is_vector_exists = data["data"][0]["custom_feasibility_vector_file_name"]
        #     is_vector_exists = data["data"][vector_id_field_for_respective_doctype]
        # except KeyError:
        #     is_vector_exists = None
        # print(is_vector_exists)
        if not is_vector_exists:

            # for value in UNIVERSAL_DICT_FOR_HELPER_DOCTYPES.get("Doctypes", []):
            #     if value["name"] == "File":
            #         name_for_helper_doctype = "File"
            #         field_for_helper_doctype = value["File_URL_Field"]
            
            # creating_vectors = getting_pdf_from_file_url_in_feasibility_session_id(data=data)
            creating_vectors = getting_pdf_from_file_url_in_feasibility_session_id(
                                                                                    main_doctype_data=data, 
                                                                                    main_doctype_field=data_source_fields_for_respective_doctype,
                                                                                    helper_doctype_name=name_for_helper_doctype,
                                                                                    helper_doctype_field=field_for_helper_doctype)

            # fail_statements = [
            #     "No such file exists.Upload the PDF again to continue",
            #     "some error occured while fetching required fields from the 'file' doctype.",
            #     "Downloaded file is missing/too small to be a valid PDF:- fail-file-download-too-small",
            #     "Downloaded file is not a PDF (likely an HTML redirect/login page):- fail-not-a-pdf",
            #     "Particular session id is required for the respective helper doctype without which we cannot go ahead.",
            #     "The doctype mentioned does not exist in the Universal helper doctype dict in which we store the doctypes that acts as a helper to the main doctypes.",
            #     ]

            for value in fail_statements:
                if creating_vectors == value:
                    return creating_vectors, "fail-not is_vector_exists-also_PDF_not_exists"
                else:
                    return creating_vectors, "success-not is_vector_exists-but_PDF_exists"
            # if creating_vectors == "No such file exists.Upload the PDF again to continue":
            #     return creating_vectors, "fail-not is_vector_exists-also_PDF_not_exists"
            # elif creating_vectors == "some error occured while fetching required fields from the 'file' doctype.":
            #     return creating_vectors, "fail-not is_vector_exists-also_PDF_not_exists"
            # else:
            #     return creating_vectors, "success-not is_vector_exists-but_PDF_exists"

        elif is_vector_exists:
            # parent = Path(fr"D:\work_folder\mars_rag_qna\data_45\vectors\{doctype}")
            # parent = Path(fr"{PERSIST_ROOT}\{doctype}")
            parent = Path(fr"{PERSIST_ROOT}/{folder_name}")
            # parent = os.path.join(PERSIST_ROOT, folder_name)
            os.makedirs(parent, exist_ok=True)
            folders = sorted([p for p in parent.iterdir() if p.is_dir()],
                            key=lambda p: p.stat().st_ctime)  # creation time on Windows

            iter_folders = []

            for p in folders:
                iter_folders.append(p.name)

            # print("ITER_FOLDERS",iter_folders)

            for item in iter_folders:
                # print("ITEM",item)
                # print("VECTOR",is_vector_exists)
                if item == is_vector_exists:
                    # print("VECTOR MATCH",is_vector_exists)
                    return is_vector_exists, "success-is_vector_exists"
              
            creating_vectors = getting_pdf_from_file_url_in_feasibility_session_id(
                                                                                    main_doctype_data=data, 
                                                                                    main_doctype_field=data_source_fields_for_respective_doctype,
                                                                                    helper_doctype_name=name_for_helper_doctype,
                                                                                    helper_doctype_field=field_for_helper_doctype)

            for value in fail_statements:
                if creating_vectors == value:
                    return creating_vectors, "fail-no_PDF_exists"
                else:
                    return creating_vectors, "success-is_PDF_exists"
            # if creating_vectors == "No such file exists.Upload the PDF again to continue":
            #     return creating_vectors, "fail-no_PDF_exists"
            # else:
            #     # print("VECTOR MATCH",is_vector_exists)
            #     return creating_vectors, "success-is_PDF_exists"
                # return "vector folder does not exist in the local storage", "fail-is_vector_exists"
    
    elif checking_data_source == "JSON_object" or checking_data_source == "json_string" or checking_data_source == "base64_encoded_data":
        # if not is_vector_exists:
        #     try:
        #         # is_vector_exists = data["data"][0]["custom_feasibility_vector_file_name"]
        #         is_json_exists = data["data"][data_source_fields_for_respective_doctype]
        #         frappe.log_error("is_json_exists", f"{is_json_exists}")
        #     except KeyError:
        #         is_json_exists = None

        #     if not is_json_exists:
        #         frappe.log_error("is_json_exists", f"fail-not is_vector_exists-also_JSON_not_exists")
        #         return is_json_exists, "fail-not is_vector_exists-also_JSON_not_exists"
        #     elif is_json_exists:
        #         frappe.log_error("is_json_exists", "success-not is_vector_exists-but_JSON_exists")
        #         return is_json_exists, "success-not is_vector_exists-but_JSON_exists"


        # elif is_vector_exists:
        if is_vector_exists:
                        # parent = Path(fr"D:\work_folder\mars_rag_qna\data_45\vectors\{doctype}")
            # parent = Path(fr"{PERSIST_ROOT}\{doctype}")
            parent = Path(fr"{PERSIST_ROOT}/{folder_name}")
            # parent = os.path.join(PERSIST_ROOT, folder_name)
            os.makedirs(parent, exist_ok=True)
            folders = sorted([p for p in parent.iterdir() if p.is_dir()],
                            key=lambda p: p.stat().st_ctime)  # creation time on Windows

            iter_folders = []

            for p in folders:
                iter_folders.append(p.name)

            # print("ITER_FOLDERS",iter_folders)

            for item in iter_folders:
                # print("ITEM",item)
                # print("VECTOR",is_vector_exists)
                if item == is_vector_exists:
                    # print("VECTOR MATCH",is_vector_exists)
                    return is_vector_exists, "success-is_vector_exists"

        try:
            # is_vector_exists = data["data"][0]["custom_feasibility_vector_file_name"]
            is_json_exists = data["data"][data_source_fields_for_respective_doctype]
            frappe.log_error("is_json_exists", f"{is_json_exists}")
        except KeyError:
            is_json_exists = None

        if not is_json_exists:
            frappe.log_error("is_json_exists", f"fail-not is_vector_exists-also_JSON_not_exists")
            return is_json_exists, "fail-not is_vector_exists-also_JSON_not_exists"
        elif is_json_exists:
            frappe.log_error("is_json_exists", "success-not is_vector_exists-but_JSON_exists")
            if checking_data_source == "base64_encoded_data":
                is_json_exists = retrieve_and_decompress(is_json_exists)
                frappe.log_error("base64_decode_data", f"{is_json_exists}")
            return is_json_exists, "success-not is_vector_exists-but_JSON_exists"

    else:
        return "Either the support for the data source passed is not available or something went wrong.", "fail-not is_vector_exists-also_JSON_not_exists"

    
### 2nd version of updated working code ###   #### WE WILL GO WITH THESE  ####
def ingest_and_persist_with_budget_2(
    source,
    *,
    # persist_root: str,                # parent folder where per-doc vector stores live
    embedding_model,                  # LangChain embeddings (e.g., HuggingFaceBgeEmbeddings)
    # allocated_budget: int,            # total allowed bytes under per-doctype subfolder
    Total_allocated_budget: int|str = None,
    # chunking knobs
    parent_chunk_size: int = 2000,
    parent_chunk_overlap: int = 600,
    child_chunk_size: int = 500,
    child_chunk_overlap: int = 200,
    doctype_name: str = None,
    field_name: str = None,
    follow_up_storage_limit: int = None,
    feasibility_storage_limit: int = None,
):
    """
    1) Load PDF/JSON (or inline JSON), chunk (parent->child), compute stable_doc_id
    2) Build Chroma in TEMP (chromadb.PersistentClient), precompute embeddings
    3) Budget check against persist_root/vectors/<doctype>/ (replacement-aware)
    4) If OK, move temp store to persist_root/vectors/<doctype>/<fileStem>__<stable_doc_id>; else skip
    Returns dict with status, sizes, paths, and child_docs.
    """
    # ---------------------- Imports ----------------------
    import os, json, mimetypes, hashlib, re, shutil, tempfile, time, gc, stat, sys, errno
    from typing import Any, List, Tuple, Union
    from pathlib import Path
    from datetime import datetime
    import psutil
    from langchain.schema import Document
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import (
        PyPDFLoader, Docx2txtLoader, UnstructuredExcelLoader,
        UnstructuredPowerPointLoader, CSVLoader, TextLoader,
        UnstructuredHTMLLoader, UnstructuredFileLoader
    )
    import chromadb
    from chromadb.config import Settings

    # ---------------------- Helpers ----------------------
    SIZE_RE = re.compile(r'(?i)\b(\d+)\s*([KMG])(?:I)?B\b')

    def extract_size(s: str):
        m = SIZE_RE.search(s) if isinstance(s, str) else None
        if not m:
            return None
        value = int(m.group(1))
        unit = m.group(2).upper() + "B"
        return value, unit

    def _hash(s: str, n: int = 16) -> str:
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:n]

    def _safe_stem(filename: str) -> str:
        stem = os.path.splitext(os.path.basename(filename))[0]
        return re.sub(r"[^A-Za-z0-9._-]+", "_", stem)

    def _get_dir_size_bytes(path: str) -> int:
        if not os.path.exists(path):
            return 0
        total = 0
        for root, _, files in os.walk(path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
        return total

    def _humanize_bytes(n: int) -> str:
        for unit in ["B","KB","MB","GB","TB","PB"]:
            if n < 1024:
                return f"{n:.2f} {unit}"
            n /= 1024
        return f"{n:.2f} EB"

    def to_bytes(value, unit=None, binary=True):
        unit = unit.strip().upper()
        if binary:
            powers = {"B":0, "K":1, "KB":1, "KIB":1, "M":2, "MB":2, "MIB":2, "G":3, "GB":3, "GIB":3, "T":4, "TB":4, "TIB":4}
            base = 1024
        else:
            powers = {"B":0, "KB":1, "MB":2, "GB":3, "TB":4}
            base = 1000
        p = powers[unit]
        return int(value * (base ** p))

    def _safe_rmtree(path: str, retries: int = 10, delay: float = 0.25):
        last = None
        for _ in range(retries):
            try:
                if os.path.exists(path):
                    shutil.rmtree(path)
                return True
            except Exception as e:
                last = e
                time.sleep(delay)
        try:
            shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass
        return last is None

    def _list_oldest_dirs(root: Path, exclude_name: str) -> list[Path]:
        items = [p for p in root.iterdir() if p.is_dir() and p.name != exclude_name]
        return sorted(items, key=lambda p: p.stat().st_ctime)

    def delete_function(dir_path:str):
        if os.path.isdir(dir_path):
            is_exist = "Directory exists"
        else:
            return "The directory you are trying to delete does not exist"

        target = os.path.normcase(os.path.normpath(dir_path))
        holders = []
        for proc in psutil.process_iter(["pid","name"]):
            try:
                for f in proc.open_files():
                    p = os.path.normcase(os.path.normpath(f.path))
                    if p.startswith(target):
                        holders.append((proc.info["pid"], proc.info["name"], f.path))
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

        for pid, name, path in holders:
            try:
                psutil.Process(pid).terminate()
            except Exception:
                pass
        time.sleep(1.0)
        for pid, name, path in holders:
            try:
                p = psutil.Process(pid)
                if p.is_running():
                    p.kill()
            except Exception:
                pass

        def _force_writable(func, path, exc_info):
            exc = exc_info[1]
            if isinstance(exc, FileNotFoundError):
                return
            if isinstance(exc, OSError) and getattr(exc, "errno", None) == errno.ENOENT:
                return
            if isinstance(exc, PermissionError):
                try:
                    os.chmod(path, stat.S_IWRITE)
                except Exception:
                    pass
                try:
                    func(path); return
                except FileNotFoundError:
                    return
            raise exc

        def delete_folder_robust(dir_path, retries=8, delay=0.5):
            if not dir_path:
                raise ValueError("dir_path is empty")
            dir_path = os.path.normpath(dir_path)
            if not os.path.exists(dir_path):
                return True
            if sys.platform.startswith("win") and not dir_path.startswith("\\\\?\\"):
                dir_path = "\\\\?\\" + dir_path
            last = None
            for _ in range(retries):
                try:
                    shutil.rmtree(dir_path, onerror=_force_writable)
                    return True
                except FileNotFoundError:
                    return True
                except OSError as e:
                    if getattr(e, "errno", None) == errno.ENOENT:
                        return True
                    last = e; time.sleep(delay)
                except Exception as e:
                    last = e; time.sleep(delay)
            if not os.path.exists(dir_path):
                return True
            raise last if last else RuntimeError("Failed to delete and unknown error state.")

        return "Successfully deleted the directory" if delete_folder_robust(dir_path) else "Failed to delete the directory"

    def _flatten_json_lines(obj: Any, parent: str = "") -> List[str]:
        lines = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                key = f"{parent}.{k}" if parent else str(k)
                lines.extend(_flatten_json_lines(v, key))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                key = f"{parent}[{i}]" if parent else f"[{i}]"
                lines.extend(_flatten_json_lines(v, key))
        else:
            lines.append(f"{parent}: {obj}")
        return lines

    def _json_to_documents(data: Any, source_meta: str, max_chars_per_doc: int = 2000) -> List[Document]:
        docs: List[Document] = []
        if isinstance(data, list) and all(isinstance(x, (dict, list)) for x in data):
            for idx, item in enumerate(data):
                lines = _flatten_json_lines(item)
                text = "\n".join(lines) if lines else json.dumps(item, ensure_ascii=False, indent=2)
                start = 0
                while start < len(text):
                    chunk = text[start:start + max_chars_per_doc]
                    docs.append(Document(page_content=chunk, metadata={"source": source_meta, "type": "json", "record_index": idx}))
                    start += max_chars_per_doc
        else:
            lines = _flatten_json_lines(data)
            text = "\n".join(lines) if lines else json.dumps(data, ensure_ascii=False, indent=2)
            start = 0; part = 0
            while start < len(text):
                chunk = text[start:start + max_chars_per_doc]
                docs.append(Document(page_content=chunk, metadata={"source": source_meta, "type": "json", "part": part}))
                start += max_chars_per_doc; part += 1
        return docs

    def _normalize_json_payload(obj: Any) -> Any:
        """
        Normalize common wrapper formats:
        - {"data": ...} -> ...
        - {"message": {"data": ...}} -> ...
        - list/dict as-is
        """
        if isinstance(obj, dict):
            # most common wrappers in APIs
            if "data" in obj and isinstance(obj["data"], (dict, list)):
                return obj["data"]
            if "message" in obj and isinstance(obj["message"], dict) and "data" in obj["message"]:
                return obj["message"]["data"]
        return obj


    def _try_parse_inline_json(src: Any) -> Tuple[bool, Any]:
        """
        Try to parse inline JSON from:
        - dict/list (already JSON)
        - str (JSON string)
        - bytes/bytearray (utf-8 JSON)
        Returns: (is_json, parsed_obj)
        """
        if isinstance(src, (dict, list)):
            return True, _normalize_json_payload(src)

        if isinstance(src, (bytes, bytearray)):
            try:
                s = bytes(src).decode("utf-8").strip()
            except Exception:
                return False, None
            if s.startswith("{") or s.startswith("["):
                try:
                    return True, _normalize_json_payload(json.loads(s))
                except Exception:
                    return False, None
            return False, None

        if isinstance(src, str):
            s = src.strip()
            if s.startswith("{") or s.startswith("["):
                try:
                    return True, _normalize_json_payload(json.loads(s))
                except Exception:
                    return False, None

        return False, None

    # def _load_document(src: Union[str, dict, list]) -> Tuple[Union[List[Document], str], str, str]:
    #     try:
    #         if isinstance(src, (dict, list)):
    #             return _json_to_documents(src, source_meta="inline_json"), "successful loading", "inline_json.json"
    #         if isinstance(src, str):
    #             s = src.strip()
    #             if s.startswith("{") or s.startswith("["):
    #                 try:
    #                     data = json.loads(s)
    #                     return _json_to_documents(data, source_meta="inline_json_string"), "successful loading", "inline_json.json"
    #                 except Exception:
    #                     pass
    #         if not isinstance(src, str):
    #             return "Invalid source type. Provide a file path, JSON dict/list, or JSON string.", "error loading document", "unknown.json"

    #         file_path = src
    #         mime_type, _ = mimetypes.guess_type(file_path)
    #         file_ext = os.path.splitext(file_path)[1].lower()

    #         if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
    #             return [], "error loading document", os.path.basename(file_path)

    #         if mime_type == "application/json" or file_ext == ".json":
    #             with open(file_path, "r", encoding="utf-8") as f:
    #                 data = json.load(f)
    #             return _json_to_documents(data, source_meta=file_path), "successful loading", os.path.basename(file_path)

    #         if mime_type == "application/pdf" or file_ext == ".pdf":
    #             return PyPDFLoader(file_path).load(), "successful loading", os.path.basename(file_path)
    #         elif (mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or file_ext == ".docx"):
    #             return Docx2txtLoader(file_path).load(), "successful loading", os.path.basename(file_path)
    #         elif (mime_type in ("application/vnd.ms-excel","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet") or file_ext in (".xls", ".xlsx")):
    #             return UnstructuredExcelLoader(file_path).load(), "successful loading", os.path.basename(file_path)
    #         elif mime_type == "text/plain" or file_ext == ".txt":
    #             return TextLoader(file_path).load(), "successful loading", os.path.basename(file_path)
    #         else:
    #             return UnstructuredFileLoader(file_path, mode="elements").load(), "successful loading", os.path.basename(file_path)

    #     except Exception as e:
    #         return f"Error loading {src}: {str(e)}", "error loading document", "unknown.json"

    def _load_document(src: Any) -> Tuple[Union[List[Document], str], str, str]:
        """
        Supports:
        - Inline JSON: dict/list, JSON string, JSON bytes
        - File paths: pdf/docx/xlsx/txt/json file
        """
        try:
            # ---------- A) Inline JSON content ----------
            is_json, parsed = _try_parse_inline_json(src)
            if is_json:
                # Use a stable pseudo filename for inline JSON
                return _json_to_documents(parsed, source_meta="inline_json"), "successful loading", "inline_json.json"

            # ---------- B) File path mode ----------
            if not isinstance(src, str):
                return (
                    "Invalid source type. Provide a file path OR inline JSON (dict/list/JSON string/JSON bytes).",
                    "error loading document",
                    "unknown",
                )

            file_path = src.strip()
            mime_type, _ = mimetypes.guess_type(file_path)
            file_ext = os.path.splitext(file_path)[1].lower()

            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                return [], "error loading document", os.path.basename(file_path)

            if mime_type == "application/json" or file_ext == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data = _normalize_json_payload(data)
                return _json_to_documents(data, source_meta=file_path), "successful loading", os.path.basename(file_path)

            if mime_type == "application/pdf" or file_ext == ".pdf":
                return PyPDFLoader(file_path).load(), "successful loading", os.path.basename(file_path)
            elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or file_ext == ".docx":
                return Docx2txtLoader(file_path).load(), "successful loading", os.path.basename(file_path)
            elif mime_type in (
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ) or file_ext in (".xls", ".xlsx"):
                return UnstructuredExcelLoader(file_path).load(), "successful loading", os.path.basename(file_path)
            elif mime_type == "text/plain" or file_ext == ".txt":
                return TextLoader(file_path).load(), "successful loading", os.path.basename(file_path)
            else:
                return UnstructuredFileLoader(file_path, mode="elements").load(), "successful loading", os.path.basename(file_path)

        except Exception as e:
            return f"Error loading {type(src)}: {str(e)}", "error loading document", "unknown"



    # ---------------------- 1) Load ----------------------
    docs, status, uploaded_filename = _load_document(source)
    if not isinstance(docs, list) or len(docs) == 0:
        return {"ok": False, "status": status, "message": "No documents loaded or parsing failed."}

    # ---------------------- 2) Chunk (hierarchical) ----------------------
    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=parent_chunk_size, chunk_overlap=parent_chunk_overlap, length_function=len
    )
    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=child_chunk_size, chunk_overlap=child_chunk_overlap, length_function=len
    )
    parent_docs = parent_splitter.split_documents(docs)
    child_docs = child_splitter.split_documents(parent_docs)
    
    # ---------------------- 3) Stable IDs ----------------------
    if isinstance(source, str) and isinstance(docs, list) and len(docs) > 0 and os.path.exists(source):
        source_label = os.path.abspath(source)
    else:
        preview = "\n".join(d.page_content for d in child_docs[:3])[:2000]
        source_label = f"inline_json::{_hash(preview or 'empty')}"

    joined = "\n\n".join(d.page_content for d in child_docs)
    stable_doc_id = f"doc_{_hash(joined or source_label)}"
    short_doc_id = stable_doc_id.replace("doc_", "")[:16]

    for i, d in enumerate(child_docs):
        d.metadata["chunk_id"] = f"{i:05d}_{_hash(d.page_content)}"
        d.metadata["source"] = source_label
        # d.metadata["stable_doc_id"] = stable_doc_id
        d.metadata["stable_doc_id"] = short_doc_id
        d.metadata["doc_id"] = f"doc_{i}"
        d.metadata["parent_id"] = f"parent_{i//4}"
        d.metadata["chunk_level"] = "child" if len(d.page_content) < 1000 else "parent"

    # ---------------------- 4) Build vectors in TEMP (chromadb) ----------------------
    texts     = [d.page_content for d in child_docs]
    metadatas = [d.metadata     for d in child_docs]
    ids       = [f"{d.metadata.get('doc_id','doc')}__{d.metadata['chunk_id']}" for d in child_docs]

    if not texts:
        return {"ok": False, "status": "no_chunks",
                "message": "Text chunks are empty; not adding to Chroma."}

    # safe_name = _safe_stem(uploaded_filename or "inline_json")
    # collection_name = f"{safe_name}__{stable_doc_id}"

    MAX_COLLECTION_LEN = 63

    safe_name = _safe_stem(uploaded_filename or "inline_json")

    # hard-trim filename part
    safe_name = safe_name[:30]

    # shorten hash
    # short_doc_id = stable_doc_id.replace("doc_", "")[:16]

    collection_name = f"{safe_name}_{short_doc_id}"

    # final safety clamp
    collection_name = collection_name[:MAX_COLLECTION_LEN].strip("_-")

    # --- Folder structure: <persist_root>/vectors/<Feasibility Report|Follow Up>/<collection_name> ---

    # vectors_root      = os.path.join(persist_root, "vectors")   # main root
    # vectors_root      = PERSIST_ROOT   # main root
    # os.makedirs(vectors_root, exist_ok=True)
    os.makedirs(PERSIST_ROOT, exist_ok=True)

    # doctype_norm = (doctype_name or label_feasibility).strip().lower()
    # if doctype_norm in ("follow up", "follow_up", "followup"):
    #     target_root = os.path.join(vectors_root, label_follow)
    # else:
    #     # default to Feasibility Report
    #     target_root = os.path.join(vectors_root, label_feasibility)

    if doctype_name == FEAS_DOCTYPE:
        # target_root = os.path.join(vectors_root, label_feasibility)
        # target_root = os.path.join(PERSIST_ROOT, LABEL_FEASIBILITY)
        target_root = os.path.join(PERSIST_ROOT, doctype_name)
        # allocated_budget_bytes_per_doctype = Total_allocated_budget_bytes
        storage_config = FEASIBILITY_ALLOCATED_STORAGE
    elif doctype_name == FOLL_DOCTYPE:
        # target_root = os.path.join(vectors_root, label_follow)
        # target_root = os.path.join(PERSIST_ROOT, LABEL_FOLLOW)
        target_root = os.path.join(PERSIST_ROOT, doctype_name)
        # allocated_budget_bytes_per_doctype = Total_allocated_budget_bytes
        storage_config = FOLLOW_UP_ALLOCATED_STORAGE

    target_root = os.path.join(PERSIST_ROOT, doctype_name)

    final_dir = os.path.join(target_root, collection_name)
    os.makedirs(target_root, exist_ok=True)

    tmpdir = tempfile.mkdtemp()
    temp_client = None
    temp_col = None
    try:
        temp_client = chromadb.PersistentClient(path=tmpdir, settings=Settings(anonymized_telemetry=False))
        temp_col = temp_client.get_or_create_collection(name=collection_name)

        # Precompute embeddings once with the LangChain model
        embs = embedding_model.embed_documents(texts)
        temp_col.add(ids=ids, documents=texts, metadatas=metadatas, embeddings=embs)

        new_size = _get_dir_size_bytes(tmpdir)

        # ---------------------- 5) Replacement-aware budget gate (per-doctype subfolder) ----------------------
        current_usage = _get_dir_size_bytes(target_root)
        existing_size = _get_dir_size_bytes(final_dir)  # 0 if not present
        projected_total = current_usage - existing_size + new_size

        # ---------------- TOTAL BYTE SIZE OF THE PERSIST ROOT --------------------------
        preparing_persist_root = fr"{PERSIST_ROOT}"
        total_byte_size_of_persist_root = _get_dir_size_bytes(preparing_persist_root)

        #------ projected total of whole persists root including the new vector file stored in temp file to get the possible storage limit --------------
        projected_total_of_persist_root_including_new_vector_file_created = total_byte_size_of_persist_root + new_size

        parent = Path(target_root)
        final_name = Path(final_dir).name  # don't delete this one
        failed_cleanup = False

        ## getting the storage limit from mars configurations doctype
        for value in UNIVERSAL_DICT_FOR_HELPER_DOCTYPES.get("Doctypes", []):
            if value["name"] == "Mars Configurations": 
                fields = [value["Storage_Field"], value["Deletion_Period_Field"]]
                configuration_doctype = value["name"]
                # fields = ["storage_limit","time_period_for_deletion"]
                data = wrapper_for_frappe_function_for_fetching_fields(doctype_name = configuration_doctype)

                with open("/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Ai_module/Feasibility_Universal_Function/testlog.txt", "a") as file:
                    file.write(f"\nSTATUS👌:- /n{data}")

        if not isinstance(data, dict):
            Total_allocated_budget = STORAGE_LIMIT
            # Total_allocated_budget = data["data"]["storage_limit"]
            with open("/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Ai_module/Feasibility_Universal_Function/testlog.txt", "a") as file:
                file.write(f"\nSTATUS👌:- /n{Total_allocated_budget}")
        elif isinstance(data, dict):
            # Total_allocated_budget = STORAGE_LIMIT
            Total_allocated_budget = data["data"]["storage_limit"]

        ## getting the storage limit from mars configurations doctype
        # fields = ["storage_limit","time_period_for_deletion"]
        # data = fetch_doc_fields_by_name("Mars Configurations", "Mars Configurations", fields=fields)
        # print("storage limit", data["storage_limit"])
        # print(type(data["storage_limit"]))
        # print("time period for deletion", data["time_period_for_deletion"])
        # -> {'doc_log': 1, 'file_log': 1, 'retention_days': 1, 'storage_limit': 4, 'time_period_for_deletion': 0, 'groq_key': '...'}

        # Total_allocated_budget = data["storage_limit"]

        # parse human budget if passed as string like "6gb", else assume bytes||
        # if isinstance(allocated_budget, str):
        if isinstance(Total_allocated_budget, str):
            val_unit = extract_size(Total_allocated_budget)
            if not val_unit:
                raise ValueError(f"allocated_budget='{Total_allocated_budget}' not parseable (e.g., '6GB', '500 MB').")
            value, unit = val_unit
            Total_allocated_budget_bytes = to_bytes(value=value, unit=unit)
            # allocated_budget_bytes = to_bytes(value=value, unit=unit)
        else:
            Total_allocated_budget_bytes = int(Total_allocated_budget)
            # allocated_budget_bytes = int(allocated_budget)

        # deriving budget bytes allocated per doctype vectors:-
        # allocated_budget_bytes_per_doctype = Total_allocated_budget_bytes * storage_config
        allocated_budget_bytes_per_doctype = Total_allocated_budget_bytes 

        # Keep freeing space until within budget or nothing left to delete
        # while projected_total > allocated_budget_bytes:
        while projected_total > allocated_budget_bytes_per_doctype:
        # while projected_total_of_persist_root_including_new_vector_file_created > allocated_budget_bytes_per_doctype:
            candidates = _list_oldest_dirs(parent, exclude_name=final_name)
            if not candidates:
                # print("[Budget] No more folders to delete; still over budget.")
                failed_cleanup = True
                break

            oldest = candidates[0]
            dt = datetime.fromtimestamp(oldest.stat().st_ctime)
            # print(f"[Budget] Deleting oldest: {dt} - {oldest.name}")

            result = delete_function(str(oldest))
            if result != "Successfully deleted the directory":
                # print(f"[Budget] Could not delete '{oldest}'; aborting cleanup.")
                failed_cleanup = True
                break

            # Recompute usage after deletion
            current_usage = _get_dir_size_bytes(target_root)
            existing_size = _get_dir_size_bytes(final_dir)
            projected_total = current_usage - existing_size + new_size

            # print(f"[Budget] After deleting '{oldest.name}': "
                #   f"current={_humanize_bytes(current_usage)}, "
                #   f"projected_total={_humanize_bytes(projected_total)}, "
                # #   f"budget={_humanize_bytes(allocated_budget_bytes)}")
                # #   f"budget={_humanize_bytes(Total_allocated_budget_bytes)}")
                #   f"budget={_humanize_bytes(allocated_budget_bytes_per_doctype)}")

        if failed_cleanup or projected_total > allocated_budget_bytes_per_doctype:
        # if failed_cleanup or projected_total_of_persist_root_including_new_vector_file_created > allocated_budget_bytes_per_doctype:
            del temp_col; del temp_client; gc.collect(); time.sleep(0.2)
            return {
                "ok": False,
                "status": "budget_exceeded",
                "message": (
                    f"Adding '{collection_name}' would exceed budget: "
                    f"current={_humanize_bytes(current_usage)}, "
                    f"existing_dir={_humanize_bytes(existing_size)}, "
                    f"new={_humanize_bytes(new_size)}, "
                    f"projected_total={_humanize_bytes(projected_total)}, "
                    # f"projected_total_of_persist_root_including_new_vector_file={_humanize_bytes(projected_total_of_persist_root_including_new_vector_file_created)}, "
                    # f"budget={_humanize_bytes(allocated_budget_bytes)}"
                    f"budget={_humanize_bytes(allocated_budget_bytes_per_doctype)}"
                ),
                "uploaded_filename": uploaded_filename,
                "collection_name": collection_name,
                "stable_doc_id": stable_doc_id,
                "persist_root": PERSIST_ROOT,
                "target_root": target_root,
                "final_dir": final_dir,
                "num_chunks": len(child_docs),
                "sizes": {
                    "new_bytes": new_size,
                    "current_usage_bytes": current_usage,
                    "existing_bytes": existing_size,
                    "projected_total_bytes": projected_total,
                    # "budget_bytes": allocated_budget_bytes,
                    "budget_bytes": Total_allocated_budget_bytes,
                },
                # "child_docs": child_docs,
            }

        # ---------------------- 6) Within budget → persist to final_dir ----------------------
        del temp_col; del temp_client; gc.collect(); time.sleep(0.2)

        if os.path.exists(final_dir):
            _safe_rmtree(final_dir)
        shutil.copytree(tmpdir, final_dir)

        return {
            "ok": True,
            "status": "persisted",
            "message": (
                f"Persisted '{collection_name}' at {final_dir}. "
                f"Size={_humanize_bytes(new_size)} | "
                # f"Projected total={_humanize_bytes(projected_total)} / {_humanize_bytes(allocated_budget_bytes)}"
                f"Projected total={_humanize_bytes(projected_total)} / {_humanize_bytes(allocated_budget_bytes_per_doctype)}"
            ),
            "uploaded_filename": uploaded_filename,
            "collection_name": collection_name,
            "stable_doc_id": stable_doc_id,
            "persist_root": PERSIST_ROOT,
            "target_root": target_root,
            "final_dir": final_dir,
            "num_chunks": len(child_docs),
            "sizes": {
                "new_bytes": new_size,
                "projected_total_bytes": projected_total,
                # "budget_bytes": allocated_budget_bytes,
                "budget_bytes": Total_allocated_budget_bytes,
            },
            # "child_docs": child_docs,
        }

    finally:
        _safe_rmtree(tmpdir)


# def yet_to_decide(allocated_budget, doctype, doc_name, folder_name):
def ensure_vector_store(doctype, doc_name, folder_name, vector_id_field, data_source_field):

    temporary, progress = checking_whether_vector_file_exists_or_not_and_ifnot_then_creating_new_vector_file(doctype=doctype, doc_name=doc_name, folder_name=folder_name, vector_id_field=vector_id_field, data_source_field=data_source_field)
    # print("TEMPORARY", temporary)
    with open("/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Ai_module/Feasibility_Universal_Function/testlog.txt", "a") as file:
        file.write(f"/nSTATUS👌:- /n{progress}")
    # print("PROGRESS", progress)

    if progress == "fail-no_PDF_exists":
        return temporary, "DO NOT PROCEED"
    elif progress == "fail-not is_vector_exists-also_PDF_not_exists" or progress == "fail-not is_vector_exists-also_JSON_not_exists":
        return temporary, "DO NOT PROCEED"
    elif progress == "success-not is_vector_exists-but_PDF_exists" or progress == "success-not is_vector_exists-but_JSON_exists":
        # qwerty = ingest_and_persist_with_budget(
        qwerty = ingest_and_persist_with_budget_2(
            # source = "Wood Saw Mill and Seasoning Plant Rs. 86.64 million Dec-2022.pdf",
            # source = "Survey, Pre-engineering Feasibility Study (1).pdf",
            # source = "textile_processing_unit_feasibility.pdf",
            # source = "Manufacturing Unit for Steel Wire Spring Rs. 52.75 million Nov-2021.pdf",
            # source = "Manufacturing of Aluminum Food Packaging Containers Rs. 12.93 million Aug-2022.pdf",
            # source = incentive,
            # source = tmp_pdf,
            source = temporary,
            # persist_root = PERSIST_ROOT,
            embedding_model = embedding_model,
            # allocated_budget = allocated_budget,
            # Total_allocated_budget= allocated_budget,
            # doctype_name="Feasibility Report"
            doctype_name=doctype
        )
        frappe.log_error("okay", f"{qwerty}")

        return qwerty, "CONDITIONAL PROCEED"
    
    elif progress == "success-is_vector_exists":
        qwerty = {
            "ok": True,
            "collection_name": temporary,
            "persist_root": PERSIST_ROOT,
            "final_dir": os.path.join(PERSIST_ROOT, LABEL_FEASIBILITY, temporary),
        }
        return qwerty, "PROCEED"


    elif progress == "success-is_PDF_exists":
        qwerty = ingest_and_persist_with_budget_2(
            # source = "Wood Saw Mill and Seasoning Plant Rs. 86.64 million Dec-2022.pdf",
            # source = "Survey, Pre-engineering Feasibility Study (1).pdf",
            # source = "textile_processing_unit_feasibility.pdf",
            # source = "Manufacturing Unit for Steel Wire Spring Rs. 52.75 million Nov-2021.pdf",
            # source = "Manufacturing of Aluminum Food Packaging Containers Rs. 12.93 million Aug-2022.pdf",
            # source = incentive,
            # source = tmp_pdf,
            source = temporary,
            # persist_root = PERSIST_ROOT,         
            # persist_root = "D:/work_folder/vector_directories",
            embedding_model = embedding_model,
            # allocated_budget = allocated_budget,
            # Total_allocated_budget= allocated_budget,
            # doctype_name="Feasibility Report"
            doctype_name=doctype
        )
        return qwerty, "CONDITIONAL PROCEED"
    
# def yet_to_decide_2(allocated_budget, doctype, doc_name):
@frappe.whitelist()
def ensure_vector_and_update_record(doctype, doc_name, vector_id_field, data_source_field):

    frappe.log_error("Check", f"{doctype} {doc_name} {vector_id_field} {data_source_field}")
    #getting in which folder vector is to be stored
    if doctype == FEAS_DOCTYPE:
        folder_name = doctype
    elif doctype == FOLL_DOCTYPE:
        folder_name = doctype
    folder_name = doctype

    # base_url = live_base_url
    base_url = ritu_local_base_url

    def make_headers():
        return {
            "Authorization": f"token {frappe_api_key}:{frappe_api_secret}",
            "Content-Type": "application/json",
            "Expect": "",
        }
 
    def dbg(label, r):
        pass
 
    def update_record(doctype, docname, updated_data, timeout=30):
        # Prepare the API endpoint URL
        url = f"{base_url}/api/resource/{doctype}/{docname}"
        # Make the PUT request to update the record
        r = requests.put(url, headers=make_headers(), data=json.dumps(updated_data), timeout=timeout)
        frappe.db.commit()
        try:
            r.raise_for_status()  # Raise an exception for HTTP errors

        except requests.HTTPError:
            dbg("resource update error", r)

            raise
 
       # Return the response

        return r.json()


    # mko, is_proceed = yet_to_decide(allocated_budget=allocated_budget, doctype = doctype, doc_name = doc_name, folder_name = folder_name)
    mko, is_proceed = ensure_vector_store(doctype = doctype, doc_name = doc_name, folder_name = folder_name, vector_id_field=vector_id_field, data_source_field=data_source_field)

    if is_proceed.lower() == "proceed":
        return mko, True
    elif is_proceed.lower() == "do not proceed":
        # print("cannot go ahead with QnA")
        return mko, False
    else:
        if mko["ok"] == False:
            # print("failed to create vector file")
            return mko, False
        elif mko["ok"] == True:
            # print("vector created and updated in the database")
            vector_file_name = mko["collection_name"]

            # Define the updated data for the document
            updated_data = {
                "custom_feasibility_vector_file_name": vector_file_name,  # Example field to update
                # Add other fields to update here
            }
        
            # Call the function to update the record
            updated_response = update_record(doctype, doc_name, updated_data)
        
            # Print the response (which should include the updated document data)
            # print(json.dumps(updated_response, indent=2))

        with open("/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Ai_module/Feasibility_Universal_Function/testlog.txt", "a") as file:
            file.write(f"\nSTATUS👌:- /n{mko}")

            return mko, True

if __name__ == "__main__":
    mko_2, status = ensure_vector_and_update_record(
                            # allocated_budget="4mb", 
                            doctype = FEAS_DOCTYPE, 
                            # doc_name = "Report-05-08-25 -2009",)
                            # doc_name = "Report-28-10-25 -2427",)
                            # doc_name = "Report-05-08-25 -2012",)
                            # doc_name = "Report-15-10-25 -2426",)
                            # doc_name = "Report-06-10-25 -2424",)
                            # doc_name = "Report-14-08-25 -2053",)
                            # doc_name = "Report-14-10-25 -2425",)
                            # doc_name = "Report-13-08-25 -2046",)
                            # doc_name = "Report-05-08-25 -2009",)
                            # doc_name = "Report-03-10-25 -2116",)
                            # doc_name="Report-14-08-25 -2050")
                            # doc_name="Report-03-11-25 -2174")
                            doc_name="Report-28-10-25 -2427")

    with open("testlog.txt", "a") as file:
        file.write(f"\nJSON👌:- \n{mko_2}")
