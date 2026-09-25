from urllib.parse import quote
import requests

frappe_api_key = "d3de1e0e4e25846"
frappe_api_secret = "a17a89fc01bd744"
# ; ritu_local_base_url = http://172.17.242.222
ritu_local_base_url = "http://172.22.232.42"
# live_base_url = https://marsaix.marsbazaar.com

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

qwerty = fetch_frappe_doc_universal(doctype = "Survey No", identifier='8353--Siem Reap-Siem Reap')
print(qwerty) 