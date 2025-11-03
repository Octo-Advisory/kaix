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

# ── LLM client (if used with MultiQuery)
from langchain_groq import ChatGroq

# PERSIST_ROOT = "D:/work_folder/mars_rag_qna/data_45/vectors"
PERSIST_ROOT = "/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/vectors"

FEAS_DOCTYPE = "Feasibility Report"
FOLL_DOCTYPE = "Follow Up"

# per doctype storage configuration
FEASIBILITY_ALLOCATED_STORAGE = 0.6
FOLLOW_UP_ALLOCATED_STORAGE = 0.4

# storage folders name of follow up and feasibility vectors 
LABEL_FOLLOW = "Follow_Up"
LABEL_FEASIBILITY = "Feasibility_Report"

embedding_model = HuggingFaceBgeEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
            query_instruction="Represent this sentence for searching relevant passages:"
        )

GROQ_API_KEY="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" 
API_KEY = "d3de1e0e4e25846"
API_SECRET = "51fd8e403a19045"
# BASE_URL = "https://marsaix.marsbazaar.com"
BASE_URL = "http://172.17.242.222"
# load_dotenv(dotenv_path="D:/work_folder/mars_rag_qna/.env")
# api_key = os.getenv("GROQ_API_KEY")
# api_key = os.getenv("GROQ_API_KEY")
api_key = GROQ_API_KEY
# print(api_key)
# print("Loaded API Key:", api_key is not None)  # Should print: True
# print("API KEY:", os.getenv("GROQ_API_KEY"))

llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.5, api_key = api_key)

# this code is to retrieve the values of the fields namely'storage limit' and 'time period for deletion' which are stored in 'Mars Configurations' doctype.

def fetch_doc_fields_by_name(
    doctype: str,
    doc_name: str,                 # for Single doctypes, this is the same as doctype
    *,
    fields: list[str] | None = None,  # e.g. ["*"] or ["doc_log", "file_log", ...]
    timeout: int = 30,
    debug: bool = False,
):
    # load_dotenv("D:/work_folder/mars_rag_qna/.env")
    # base_url   = os.getenv("BASE_URL")
    # base_url = "https://marsaix.marsbazaar.com"
    base_url = "http://172.17.242.222"
    # api_key    = os.getenv("API_KEY")
    api_key = "d3de1e0e4e25846"
    # api_secret = os.getenv("API_SECRET")
    api_secret = "51fd8e403a19045"
    if not (base_url and api_key and api_secret):
        raise ValueError("Missing BASE_URL / API_KEY / API_SECRET")

    headers = {
        "Authorization": f"token {api_key}:{api_secret}",
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
    # if debug:
        # print(f"[GET] {r.status_code} {r.url}")
        # print(r.text[:800])
    # r.raise_for_status() 
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

    # load_dotenv(dotenv_path="D:/work_folder/mars_rag_qna/.env")

    # ---- fallbacks to environment ----
    # base_url = "https://marsaix.marsbazaar.com"
    base_url = "http://172.17.242.222"
    # api_key    = os.getenv("API_KEY")
    api_key = "d3de1e0e4e25846"
    # api_secret = os.getenv("API_SECRET")
    api_secret = "51fd8e403a19045"

    if not base_url:
        raise ValueError("Missing base_url (pass base_url=... or set BASE_URL env var)")
    if not api_key or not api_secret:
        raise ValueError("Missing API credentials (API_KEY/API_SECRET)")

    # ---- headers ----
    headers = {
        "Authorization": f"token {api_key}:{api_secret}",
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

    # if debug:
        # print(f"[GET] {r.status_code} {r.url}")
        # Print first 800 chars for safety
        # print(r.text[:800])

    # raise for HTTP errors (will include body in debug above)
    r.raise_for_status()

    # ---- parse and return ----
    data = r.json()
    # if debug:
        # print(json.dumps(data, indent=2))

    return data

def make_headers():
    load_dotenv(dotenv_path="D:/work_folder/mars_rag_qna/.env")

    # ---- fallbacks to environment ----
    api_key    = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    return {"Authorization": f"token {api_key}:{api_secret}", "Expect": ""}

def fetch_pdf_to_temp(file_url: str, is_private: bool | None = None) -> str:
    # normalize
    # load_dotenv(dotenv_path="D:/work_folder/mars_rag_qna/.env")
    # base_url = "https://marsaix.marsbazaar.com"
    base_url = "http://172.17.242.222"
    # api_key    = os.getenv("API_KEY")
    api_key = "d3de1e0e4e25846"
    # api_secret = os.getenv("API_SECRET")
    api_secret = "51fd8e403a19045"

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

def getting_pdf_from_file_url_in_feasibility_session_id(data: json):
    pdf_path = data["data"][0]["file_path"]

    m = re.search(r'[^/\\]+$', pdf_path)
    filename = m.group(0) if m else None
    # print(filename)  # samplesecured_256bitaes_pdf.pdf

    # calling the fetch_single_doc_by_name() again to access the contents of the pdf from the "file list" doctype in order to create a new vector file form it.
    file_data = fetch_single_doc_by_name(
    "File", # 
    # "Report-05-08-25 -2010",
    filename,
    # api_key="d3de1e0e4e25846",
    # api_secret="51fd8e403a19045",
    # base_url="https://marsaix.marsbazaar.com",
    fields=["*"],   # or omit to use server defaults
    debug=True
    ) # returns a json
    # print("file_date(getting_pdf_from_file_url_in_feasibility_session_id)", file_data)

    if file_data["data"]:
        if_is_file_data = file_data["data"][0]["file_url"]
        if not if_is_file_data:
            # print("No such file exists.Upload the PDF again to continue")
            return "No such file exists.Upload the PDF again to continue"
        if if_is_file_data:
            tmp_pdf = fetch_pdf_to_temp(if_is_file_data)
            # sanity check
            if not os.path.exists(tmp_pdf) or os.path.getsize(tmp_pdf) < 1024:
                return "Downloaded file is missing/too small to be a valid PDF.", "fail-file-download-too-small"

            with open(tmp_pdf, "rb") as fh:
                head = fh.read(5)
            if head != b"%PDF-":
                return "Downloaded file is not a PDF (likely an HTML redirect/login page).", "fail-not-a-pdf"

            return tmp_pdf
    if not file_data["data"]:
        # print("No such file exists.Upload the PDF again to continue")
        return "No such file exists.Upload the PDF again to continue"
    # if_is_file_data = file_data["data"][0]["file_url"]
    # if not if_is_file_data:
    #     print("No such file exists.Upload the PDF again to continue")
    #     return "No such file exists.Upload the PDF again to continue"
    # if if_is_file_data:
    #     tmp_pdf = fetch_pdf_to_temp(if_is_file_data)
    #     return tmp_pdf


def checking_whether_vector_file_exists_or_not_and_ifnot_then_creating_new_vector_file(
        doctype:str, 
        doc_name:str,
        folder_name:str):
    
    data = fetch_single_doc_by_name(
    doctype,
    doc_name,
    # api_key="d3de1e0e4e25846",
    # api_secret="51fd8e403a19045",
    # base_url="https://marsaix.marsbazaar.com",
    fields=["*"],   # or omit to use server defaults
    debug=True
    ) # returns a json

    # print("data(fetch_doc_by_name)",data)
    
    if doctype == "Feasibility Report":
        is_vector_exists = data["data"][0]["custom_feasibility_vector_file_name"]
        # print(is_vector_exists)
        if not is_vector_exists:
            # pdf_path = data["data"][0]["file_path"]

            # m = re.search(r'[^/\\]+$', pdf_path)
            # filename = m.group(0) if m else None
            # print(filename)  # samplesecured_256bitaes_pdf.pdf

            # # calling the fetch_single_doc_by_name() again to access the contents of the pdf from the "file list" doctype in order to create a new vector file form it.
            # file_data = fetch_single_doc_by_name(
            # "File", # 
            # # "Report-05-08-25 -2010",
            # filename,
            # # api_key="d3de1e0e4e25846",
            # # api_secret="51fd8e403a19045",
            # # base_url="https://marsaix.marsbazaar.com",
            # fields=["*"],   # or omit to use server defaults
            # debug=True
            # ) # returns a json

            # if_is_file_data = file_data["data"][0]["file_url"]
            # if not if_is_file_data:
            #     print("No such file exists.Upload the PDF again to continue")
            #     return "No such file exists.Upload the PDF again to continue", "fail-not is_vector_exists"
            # if if_is_file_data:
            #     tmp_pdf = fetch_pdf_to_temp(if_is_file_data)
            #     return tmp_pdf, "success-not is_vector_exists"
            
            creating_vectors = getting_pdf_from_file_url_in_feasibility_session_id(data=data)

            if creating_vectors == "No such file exists.Upload the PDF again to continue":
                return creating_vectors, "fail-not is_vector_exists-also_PDF_not_exists"
            else:
                return creating_vectors, "success-not is_vector_exists-but_PDF_exists"

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
                # else:
                #     creating_vectors = getting_pdf_from_file_url_in_feasibility_session_id(data=data)
                #     if creating_vectors == "No such file exists.Upload the PDF again to continue":
                #         return creating_vectors, "fail-no_PDF_exists"
                #     else:
                #         print("VECTOR MATCH",is_vector_exists)
                #         return creating_vectors, "success-is_PDF_exists"
            creating_vectors = getting_pdf_from_file_url_in_feasibility_session_id(data=data)
            if creating_vectors == "No such file exists.Upload the PDF again to continue":
                return creating_vectors, "fail-no_PDF_exists"
            else:
                # print("VECTOR MATCH",is_vector_exists)
                return creating_vectors, "success-is_PDF_exists"
                # return "vector folder does not exist in the local storage", "fail-is_vector_exists"
                    
                
    else: # for follow up #
        # print("The support for follow up is not integrated yet")
        return "The support for follow up is not integrated yet"
    
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

    def _load_document(src: Union[str, dict, list]) -> Tuple[Union[List[Document], str], str, str]:
        try:
            if isinstance(src, (dict, list)):
                return _json_to_documents(src, source_meta="inline_json"), "successful loading", "inline_json.json"
            if isinstance(src, str):
                s = src.strip()
                if s.startswith("{") or s.startswith("["):
                    try:
                        data = json.loads(s)
                        return _json_to_documents(data, source_meta="inline_json_string"), "successful loading", "inline_json.json"
                    except Exception:
                        pass
            if not isinstance(src, str):
                return "Invalid source type. Provide a file path, JSON dict/list, or JSON string.", "error loading document", "unknown.json"

            file_path = src
            mime_type, _ = mimetypes.guess_type(file_path)
            file_ext = os.path.splitext(file_path)[1].lower()

            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                return [], "error loading document", os.path.basename(file_path)

            if mime_type == "application/json" or file_ext == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return _json_to_documents(data, source_meta=file_path), "successful loading", os.path.basename(file_path)

            if mime_type == "application/pdf" or file_ext == ".pdf":
                return PyPDFLoader(file_path).load(), "successful loading", os.path.basename(file_path)
            elif (mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or file_ext == ".docx"):
                return Docx2txtLoader(file_path).load(), "successful loading", os.path.basename(file_path)
            elif (mime_type in ("application/vnd.ms-excel","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet") or file_ext in (".xls", ".xlsx")):
                return UnstructuredExcelLoader(file_path).load(), "successful loading", os.path.basename(file_path)
            elif mime_type == "text/plain" or file_ext == ".txt":
                return TextLoader(file_path).load(), "successful loading", os.path.basename(file_path)
            else:
                return UnstructuredFileLoader(file_path, mode="elements").load(), "successful loading", os.path.basename(file_path)

        except Exception as e:
            return f"Error loading {src}: {str(e)}", "error loading document", "unknown.json"

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

    for i, d in enumerate(child_docs):
        d.metadata["chunk_id"] = f"{i:05d}_{_hash(d.page_content)}"
        d.metadata["source"] = source_label
        d.metadata["stable_doc_id"] = stable_doc_id
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

    safe_name = _safe_stem(uploaded_filename or "inline_json")
    collection_name = f"{safe_name}__{stable_doc_id}"

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
        target_root = os.path.join(PERSIST_ROOT, LABEL_FEASIBILITY)
        # allocated_budget_bytes_per_doctype = Total_allocated_budget_bytes
        storage_config = FEASIBILITY_ALLOCATED_STORAGE
    elif doctype_name == FOLL_DOCTYPE:
        # target_root = os.path.join(vectors_root, label_follow)
        target_root = os.path.join(PERSIST_ROOT, LABEL_FOLLOW)
        # allocated_budget_bytes_per_doctype = Total_allocated_budget_bytes
        storage_config = FOLLOW_UP_ALLOCATED_STORAGE

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

        parent = Path(target_root)
        final_name = Path(final_dir).name  # don't delete this one
        failed_cleanup = False

        ## getting the storage limit from mars configurations doctype
        fields = ["storage_limit","time_period_for_deletion"]
        data = fetch_doc_fields_by_name("Mars Configurations", "Mars Configurations", fields=fields)
        # print("storage limit", data["storage_limit"])
        # print(type(data["storage_limit"]))
        # print("time period for deletion", data["time_period_for_deletion"])
        # -> {'doc_log': 1, 'file_log': 1, 'retention_days': 1, 'storage_limit': 4, 'time_period_for_deletion': 0, 'groq_key': '...'}

        Total_allocated_budget = data["storage_limit"]

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
        allocated_budget_bytes_per_doctype = Total_allocated_budget_bytes * storage_config

        # Keep freeing space until within budget or nothing left to delete
        # while projected_total > allocated_budget_bytes:
        while projected_total > allocated_budget_bytes_per_doctype:
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
def ensure_vector_store(doctype, doc_name, folder_name):

    temporary, progress = checking_whether_vector_file_exists_or_not_and_ifnot_then_creating_new_vector_file(doctype=doctype, doc_name=doc_name, folder_name=folder_name)
    # print("TEMPORARY", temporary)
    with open("testlog.txt", "a") as file:
        file.write(f"/nSTATUS👌:- /n{progress}")
    # print("PROGRESS", progress)

    if progress == "fail-no_PDF_exists":
        return temporary, "DO NOT PROCEED"
    elif progress == "fail-not is_vector_exists-also_PDF_not_exists":
        return temporary, "DO NOT PROCEED"
    elif progress == "success-not is_vector_exists-but_PDF_exists":
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
def ensure_vector_and_update_record(doctype, doc_name):

    #getting in which folder vector is to be stored
    if doctype == FEAS_DOCTYPE:
        folder_name = LABEL_FEASIBILITY
    elif doctype == FOLL_DOCTYPE:
        folder_name = LABEL_FOLLOW

    # load_dotenv(dotenv_path="D:/work_folder/mars_rag_qna/.env")

    # base_url = "https://marsaix.marsbazaar.com"
    base_url = "http://172.17.242.222"
    # api_key    = os.getenv("API_KEY")
    api_key = "d3de1e0e4e25846"
    # api_secret = os.getenv("API_SECRET")
    api_secret = "51fd8e403a19045"

    def make_headers():
        return {
            "Authorization": f"token {api_key}:{api_secret}",
            "Content-Type": "application/json",
            "Expect": "",
        }
 
    # def dbg(label, r):
        # print(f"[{label}] {r.status_code} {r.url}")
        # print(r.text[:800])
 
    def update_record(doctype, docname, updated_data, timeout=30):
        # Prepare the API endpoint URL
        url = f"{base_url}/api/resource/{doctype}/{docname}"
        # Make the PUT request to update the record
        r = requests.put(url, headers=make_headers(), data=json.dumps(updated_data), timeout=timeout)
        try:
            r.raise_for_status()  # Raise an exception for HTTP errors

        except requests.HTTPError:
            dbg("resource update error", r)

            raise
 
       # Return the response

        return r.json()


    # mko, is_proceed = yet_to_decide(allocated_budget=allocated_budget, doctype = doctype, doc_name = doc_name, folder_name = folder_name)
    mko, is_proceed = ensure_vector_store(doctype = doctype, doc_name = doc_name, folder_name = folder_name)

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
                            doc_name="Report-14-08-25 -2050")

    # print("JSON👌",mko_2)
    with open("testlog.txt", "a") as file:
        file.write(f"\nJSON👌:- \n{mko_2}")
    # tmp438ieonb__doc_1703688dc9a5de44
                            # /home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/vectors/Feasibility_Report/tmpj9xp08lg__doc_b9948d88c025ce62/77ece48b-33e4-414c-8f0c-11b26d31e159

                            # {'ok': True, 'uploaded_filename': 'tmplwf12vs2__doc_1703688dc9a5de44', 'collection_name': 'tmplwf12vs2__doc_1703688dc9a5de44', 'persist_root': '/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/vectors', 'vectors_root': '/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/vectors', 'final_dir': PosixPath('/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/vectors/tmplwf12vs2__doc_1703688dc9a5de44')}
    # tmpjb9yw2bs__doc_9734791eb66b1f3b