import os
import frappe
from datetime import datetime
import random #added by jenith on 22-5-25
import subprocess
import sys
import json
import time
import gc
import re
import ast
import spacy
# from frontend_app.Ai_module.Query_Classification_And_Analysis import llm_70b_vers_creative

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import configparser
from math import radians, sin, cos, sqrt, atan2
from geopy.distance import geodesic

# from langchain_openai import ChatOpenAI
base_dir = os.path.expanduser("~")
config_file = os.path.join(base_dir, "frappe-bench/apps/frontend_app/frontend_app/Log_management/mars.ini")
config = configparser.ConfigParser()
config.read(config_file)
groq_api_key = config['Key']['groq_key']

# Initialize LLM    
llm_70b_vers_creative = ChatGroq(groq_api_key=groq_api_key, model_name="llama-3.3-70b-versatile", temperature=0.7)
llm_4_maverick = ChatGroq(groq_api_key=groq_api_key, model_name="meta-llama/llama-4-maverick-17b-128e-instruct", temperature=0.7) #Added by jenith for Query Hints Ai Responses



@frappe.whitelist(allow_guest=True)
def delete_user(user_id):
    try:
        frappe.delete_doc('User', user_id, ignore_permissions=True)
        return {'status': 'success', 'message': 'User deleted'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
    

@frappe.whitelist()
def get_docs_with_children(doctype, names):
    """
    Universal API to fetch multiple documents with their child tables.

    Args:
        doctype (str): Parent doctype name (e.g., "Vendor")
        names (list): List of document names

    Returns:
        List of dicts representing each document, including child tables
    """
    try:
        results = []
        names = json.loads(names)
        for name in names:
            doc = frappe.get_doc(doctype, name)
            results.append(doc)

        return results

    except Exception as e:
        frappe.throw(f"Error fetching {doctype} data: {str(e)}")

@frappe.whitelist()
def get_cities():
    res = frappe.db.get_list('City',fields=['city_name'], limit=10000)
    return res
 
@frappe.whitelist()
def checkApiThreshold(apiName):
    if apiName == "" or apiName == " " or apiName == None:
        return False
     
    # apiName = "Goolge Geocoding Api"
    config_data = frappe.db.get_list('Mars Config', filters=[['title', '=', apiName]], fields=['*'])

    # Get today's date in YYYY-MM-DD format
    today_date = datetime.today().strftime('%Y-%m-%d')

    if len(config_data)>0:
        item = config_data[0]
        #save daily threshold value
        dailyMinLimit = item.daily_min_count
        dailyMaxLimit = item.daily_max_count
        
        #save monthly threshold value
        monthlyMinLimit = item.monthly_min_count
        monthlyMaxLimit = item.monthly_max_count

        #get daily limit data
        daily_limit_data = frappe.db.get_list('Api Daily Limit', filters=[['api_id', '=', item.name],['date', '=', today_date]], fields=['*'])
        
        #check if record exist if no then insert a new record
        if len(daily_limit_data)<=0:

            doc = frappe.get_doc({
                'doctype': 'Api Daily Limit', 
                'api_id':item.name,
                "date": today_date,
                "count": 1
            })
            doc.insert()
            frappe.db.commit()
        
        
        else:
            daily_limit_data_item = daily_limit_data[0]
            #get current daily count value
            current_daily_count = daily_limit_data_item.count
            current_daily_count = current_daily_count + 1
            
            #check if current daily is equal to min limit if yes then send notificantion.
            if current_daily_count == dailyMinLimit:
                frappe.log_error(f"send email daily limit exceed")
                print("send email daily limit exceed ")
                
            #check if current daily is equal to max limit if yes then send notificantion and stop execution    
            if current_daily_count > dailyMaxLimit:
                return False
            
            #if max limit is not surpassed then save current daily count
            doc = frappe.get_doc('Api Daily Limit', daily_limit_data_item.name)
            doc.count = current_daily_count
            doc.save()
            frappe.db.commit()
        
        monthly_limit_data = frappe.db.get_list('Api Monthly Limit', filters=[['api_id', '=', item.name],['date', '=', today_date]], fields=['*'])
        
        #check if record exist if no then insert a new record
        if len(monthly_limit_data)<=0:
            doc = frappe.get_doc({
                'doctype': 'Api Monthly Limit', 
                'api_id':item.name,
                "date": today_date,
                "count": 1
            })
            doc.insert()
            frappe.db.commit()
        else:
            monthly_limit_data_item = monthly_limit_data[0]
            #get current daily count value
            current_monthly_count = monthly_limit_data_item.count
            current_monthly_count = current_monthly_count + 1
            
            #check if current daily is equal to min limit if yes then send notificantion.
            if current_monthly_count == monthlyMinLimit:
                frappe.log_error(f"send email daily limit exceed")
                print("send email daily limit exceed ")
                
            #check if current daily is equal to max limit if yes then send notificantion and stop execution    
            if current_monthly_count > monthlyMaxLimit:
                return False
            
            #if max limit is not surpassed then save current daily count
            doc = frappe.get_doc('Api Monthly Limit', monthly_limit_data_item.name)
            doc.count = current_monthly_count
            doc.save()
            frappe.db.commit()
        return True
    else:
        return False
    
def update_llm_token(result,llm='Llama'):
    input_token = result.usage_metadata["input_tokens"]
    output_token = result.usage_metadata["output_tokens"]
    total_token = result.usage_metadata["total_tokens"]
    doc = frappe.get_doc("Mars Config", llm)  # Fetch the document
    doc.input_token = doc.input_token + input_token  # Update the value
    doc.output_token = doc.output_token + output_token  # Update the value
    doc.total_token = doc.total_token + total_token  # Update the value
    doc.save()  # Save the document (triggers on_update, on_change, validate)
    frappe.db.commit()  # Ensure changes are committed

#added by jenith 
def randomSentences(module_name,process_name):
    
    analyse_query_approval = ['Evaluating your approval request details', 'Starting with a detailed review of your submission', 'Assessing the intent and scope of your request', 'Review initiated — checking key input parameters', 'Initiating approval review process']
    fetching_approval = ['Collecting necessary data for verification', 'Fetching all associated documents and records','Pulling historical and contextual data','Fetching relevant entries from approval database','Accessing support documents and entries']
    analyzing_approval = ['Analyzing data against approval rules and policies', 'Running compliance and eligibility checks','Evaluating conditions and approval thresholds','Applying business rules and logic for assessment','Performing eligibility and impact analysis']
    preparing_approval = ['Finalizing decision and preparing response','Compiling and delivering the approval outcome', 'Generating decision summary and next steps','Approval result is being finalized and logged','Approval decision being drafted for action']
    
    analyse_query_incentives = ["Checking your selected region and industry","Looking into your chosen location","Scanning the area you selected","Reviewing incentive availability in your region","Exploring incentive programs in your area"]
    fetching_incentives = ["Finding available incentives in that area","Finding industry-specific incentives","Searching for active government schemes","Filtering results for your business sector","Cross-checking with your industry category"]
    analyzing_incentives = ["Going through rules and eligibility","Verifying the latest eligibility criteria","Matching them with your industry type","Validating based on your inputs","Making sense of policies and amounts"]
    preparing_incentives = ["Getting the best options for you","Bringing up matching results for you","Preparing your incentive summary","Showing what incentives you can claim","Compiling what you're eligible for"]

    analyse_query_vendors = ["Checking your selected industry and location","Understanding your vendor requirements","Identifying key vendor categories","Reviewing your specified criteria","Starting the vendor search process"]
    fetching_vendors = ["Finding vendors in the specified region","Gathering vendor profiles and ratings","Searching for vendors matching your industry","Filtering vendors by services and location","Collecting vendor data from multiple sources"]
    analyzing_vendors = ["Evaluating vendor reliability and reviews","Verifying vendor credentials and compliance","Comparing vendors based on user needs","Checking availability and service terms","Assessing vendor performance and feedback"]
    preparing_vendors = ["Compiling the best vendor options for you","Preparing vendor shortlist and recommendations","Finalizing vendor details for your review","Presenting vendor matches with full profiles","Getting your vendor results ready to explore"]


    analyse_query_industry = ["Analyzing your industry and preferred location","Understanding your setup goals and requirements","Exploring regions suitable for your industry type","Reviewing location intent and business objectives","Starting your site discovery process"]
    fetching_industry = [ "Gathering property options aligned with your needs", "Finding potential sites based on setup suitability", "Shortlisting regions with promising business potential", "Exploring land parcels across your selected areas", "Scanning zones with high industrial compatibility"]
    analyzing_industry = ["Evaluating site feasibility for your business","Analyzing incentives, connectivity, and surroundings", "Assessing setup readiness across locations","Reviewing supporting infrastructure and vendor access", "Scoring properties based on multiple growth factors"]
    preparing_industry = ["Preparing best-matched property suggestions","Compiling location insights for informed decision-making", "Finalizing property profiles tailored to your setup", "Creating your personalized site recommendation list", "Getting your ideal business locations ready to view"]

    sentence_map = {
        'Analyzing Your Query': {
            'approval': analyse_query_approval,
            'incentives': analyse_query_incentives,
            'vendors': analyse_query_vendors,
            'industry': analyse_query_industry
        },
        'Fetching Data': {
            'approval': fetching_approval,
            'incentives': fetching_incentives,
            'vendors': fetching_vendors,
            'industry': fetching_industry
        },
        'Analyzing Data': {
            'approval': analyzing_approval,
            'incentives': analyzing_incentives,
            'vendors': analyzing_vendors,
            'industry': analyzing_industry
        },
        'Preparing Results': {
            'approval': preparing_approval,
            'incentives': preparing_incentives,
            'vendors': preparing_vendors,
            'industry': preparing_industry
        }
    }

    # Random sentence from the correct list
    selected_list = sentence_map[process_name][module_name]
    return random.choice(selected_list)
 
@frappe.whitelist(allow_guest=True)
def generate_chat_title(user_query):
   
    system_prompt = """
    You are an expert at generating ultra-concise, meaningful chat titles. Follow these steps for every query:

    1. ANALYZE the user query by extracting:
    - Primary Topic: [Single noun/phrase capturing main subject]
    - Key Action: [Verb + target if applicable]
    - Context: [Optional specifier like language/domain]

    2. GENERATE a title by combining these elements in to 5 to 6 words following these rules:
    - Format: Title Case, no punctuation
    - Omit filler words (e.g., "how to", "help with")
    - Prioritize specificity over generality
    - No ending punctuation
    - *Uniqueness*: Never repeat any word in the title

    3. OUTPUT ONLY THE TITLE with no additional text.

    Example Analysis:
    User Query: "Troubleshooting Django database connection timeouts"
    - Primary Topic: Django database connections
    - Key Action: Troubleshooting timeouts
    - Context: (implied in topic)
    Title: "Django Database Timeout Troubleshooting"

    User Query: "show me some vendors for pharmaceutical industry in bharuch city of gujarat state"
    - Primary Topic: Pharmaceutical vendors
    - Key Action: Show/list (implied)
    - Context: Bharuch city, Gujarat
    Title: "Pharmaceutical Vendors In Bharuch Gujarat"

    User Query: "i want to build cement industry from scratch,so i want area in which i can build the industry, vendors from which i can procure raw materials for the industry,employment availability in the area of the industry, approval and incentives for the city and area in which industry to be developed"
    - Primary Topic:  Cement industry setup
    - Key Action: : Build from scratch
    - Context: Location selection, vendors, employment, approvals, incentives
    Title: "Cement Industry Setup Guide Location Vendors Approvals"

    User Query: "i want to see the employment availability in anand city of gujarat state"
    - Primary Topic: employment availability
    - Key Action: Show/list (implied)
    - Context: anand city, gujarat state
    Title: "Employment Availability in Anand Gujarat"

    User Query: "what are the incentives available for the devloping textile industry in anand city of gujarat state and also tell me the approvals needed to set up this industry in the anand city of gujarat state"
    - Primary Topic: Textile industry
    - Key Action:  Incentives & approvals
    - Context: Anand city, Gujarat state
    Title: "Textile Industry Incentives Approvals Anand Gujarat"

    WARNING:- The output should be meaningful and relate to the original query. Also do not include anything else in the output apart from the actual output.

    Now process this query:
    """

    try:
        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", f"User Query: \"{user_query}\"\n\nPerform analysis and generate title as shown in the example.")
        ])
        
        # Create the chain
        chain = prompt | llm_70b_vers_creative
        
        # Invoke the chain
        response = chain.invoke({})
        
        # Extract and validate title
        raw_title = response.content
        title = raw_title.strip('"').strip("'").split("\n")[0].strip()
        
        # Ensure 5-6 words
        words = title.split()
        if len(words) > 6:
            title = " ".join(words[:6])
        elif len(words) < 5 and len(words) > 0:
            title = " ".join(words + [""]*(5-len(words)))
        
        return title
    
    except Exception as e:
        print(f"Error generating title: {e}")
        # Fallback to first 6 meaningful words
        return " ".join([w for w in user_query.split() if w.lower() not in ["how", "what", "the"]][:6])


@frappe.whitelist(allow_guest=True)
def generate_query_hints(query_list, input_industry_name):

   # this function generates queries based on chat_history provided to it and then classifies them in to their repsective module names

    prompt_template =  """
   You are an intelligent assistant that helps users explore and plan key aspects of setting up an industry in India.

   Your task is to:
   1. Generate 6 compact and properly framed follow-up questions based on the user's chat history  
   2. Classify each question into the correct industrial planning module

   ---

   [User Query Sessions]:
   You will be given a list of 5 session-wise query lists:
   • Session 1 – Least recent (oldest)
   • Session 5 – Most recent (latest)

   Format:
   Session 1: [ ... list of 5–10 queries ... ]  
   Session 2: [ ... ]  
   Session 3: [ ... ]  
   Session 4: [ ... ]  
   Session 5: [ ... ]  
   {chat_history}

   [Fallback Industry Name]:
   Used only when **all five sessions are empty**  
   {industry_name}

   ---

   OBJECTIVE

   Help the user explore realistic, decision-relevant aspects of setting up an industry such as:
   • Land availability  
   • Vendor access  
   • Workforce presence  
   • Government incentives  
   • Regulatory approvals  

   ---

   PHASE 1: QUERY GENERATION STRATEGY

   1. *RELEVANCE CHECK FIRST (MANDATORY):*
      • Carefully evaluate each query across all five sessions.
      • Only include queries relevant to the platform’s supported scope:
      – Land availability, Vendor proximity, Workforce access, Government incentives, Regulatory approvals

   2. *WEIGHTED RELEVANCE STRATEGY:*
      • Prioritize more recent sessions — Session 5 has the highest influence, Session 1 the least.
      • However, do not ignore earlier sessions entirely — bring in industry-location combinations from older sessions if not already reflected.

   3. *OUTPUT DIVERSITY REQUIREMENT:*
      • Ensure generated queries span multiple modules and industries.
      • Do not concentrate all queries on a single module or industry unless that pattern is clearly reflected in the input.

   4. *LOCATION RESTRICTION ENFORCEMENT (MANDATORY):*
      • Only use **those city names explicitly mentioned in the chat history** as valid locations for output queries.
      • Do **not** introduce new cities, even common ones like Ahmedabad, Surat, Bharuch, Rajkot, etc., unless they appear in the user’s prior queries.
      • This applies to both normal generation and fallback.

   5. *FALLBACK MODE (STRICT TRIGGER):*
      • If all five sessions are empty, switch to fallback generation using the provided `industry_name`.
      • In fallback mode:
      – Use realistic city names from Gujarat (Ahmedabad, Surat, Vadodara, Rajkot, Bharuch)
      – Generate 6 queries
      – Each query must include:
         ▸ The fallback `industry_name`
         ▸ A specific Gujarat city from the list above
         ▸ Exactly one supported module
      – Avoid vague phrases like “nearby” or “suitable area”

   6. *KEYWORD AWARENESS (WHEN APPLICABLE):*
      • If relevant queries include:
      – Product capacity (e.g., “100000 tablets”)
      – Specific raw materials or product names
      – Named schemes or policy references
      → Include and reflect these meaningfully in generated queries.

   7. *STRICT GOOD QUERY STRUCTURE RULE (MANDATORY):*
      • Every generated query must **strictly** follow the structure and style of the examples in the "GOOD QUERY STRUCTURE EXAMPLES" section below.
      • The query must:
         – Start with a natural question form (e.g., "What is...", "Tell me...", "I want to...", "What are...")
         – Explicitly include both the industry and the location
         – Contain exactly one supported topic (land, vendor, labor, incentives, or approvals)
         – Be grammatically correct, concise, and free of vague location phrases
      • **Do not** produce fragment-style queries or deviate from the example structure.

   ---

   FORMATTING RULES FOR GENERATED QUERIES

   • Each query must be 10–15 words or fewer  
   • Be compact, clear, and grammatically well-formed  
   • Each query must include both an industry and a location  
   • Allowed topics: land, vendor, labor, incentives, or approvals only  

   DO NOT generate queries that involve:
   • Price or cost (e.g., land cost, labor cost)  
   • Land allocation process or policy  
   • Raw material quality checks  
   • Specific skill levels (e.g., "engineers", "MBAs")  
   • Vague location phrases like "nearby", "in suitable areas"

   ---

   MODULE DEFINITIONS FOR CLASSIFICATION

   Each generated query must be classified into **exactly one** of the following five modules:

   1. **Build from Scratch**  
      • About starting a new industry unit  
      • Keywords: build, start, location, setup, timeline, capacity  

   2. **Employment**  
      • About workforce or labor availability  
      • Keywords: labor, employment, workforce, workers  

   3. **Vendor Search**  
      • About supplier or equipment sourcing  
      • Keywords: vendor, supplier, equipment, raw material  

   4. **Incentives**  
      • About government support or subsidies  
      • Keywords: incentive, scheme, subsidy, grant, support  

   5. **Approval**  
      • About regulatory requirements or licenses  
      • Keywords: approval, permission, license, clearance  

   ---

   MODULE KEYWORDS (reference only – do not rely solely on these):

   • **Build from Scratch**: build, location, start  
   • **Incentives**: incentive, benefit, subsidy, grant  
   • **Approval**: approval, permission, license, clearance  
   • **Employment**: labor, employment, workforce  
   • **Vendor Search**: vendor, supplier, equipment, raw materials  

   ---

   INTERNAL PROJECT AND MODULE SCOPE (REFERENCE ONLY)

   — Project Capabilities:
   • Suggest land *availability* based on location and industry  
   • Recommend suppliers (raw materials, equipment) by proximity  
   • Provide labor availability by general skill type  
   • Identify necessary government approvals  
   • Suggest applicable government incentives  

   — Module Focus:
   • **Build from Scratch** – holistic setup (land, labor, vendor, approvals, incentives)  
   • **Employment** – availability of workers by skill and geography  
   • **Vendor Search** – proximity and relevance of raw material suppliers  
   • **Incentives** – government schemes based on location and industry  
   • **Approval** – regulatory requirements and permits required for setup  

   — GOOD QUERY STRUCTURE EXAMPLES (STRICTLY FOLLOW THIS FORMAT):
   • What is the vendor availability for cement industry in Vadodara, Gujarat?  
   • Tell me all the incentives available for pharmaceutical industry in Surat city?  
   • What are the employment options around the Anand city?  
   • I want to build a toy factory with 100000 toys capacity  
   • What are the approvals required for building electrochemical storage unit in Bharuch?

   ---

   FINAL OUTPUT FORMAT

   Return only a valid Python list of dictionaries:
   [
      {{"query": "<generated_question_1>", "module": "<classified_module>"}},
      {{"query": "<generated_question_2>", "module": "<classified_module>"}},
      ...
   ]
   """

    formatted_prompt = prompt_template.format(
                chat_history=query_list,
                industry_name = input_industry_name
            )

    # response = llm_70b_vers_creative.invoke(formatted_prompt)
    # input_text = response.content
    # results = extract_query_list(input_text) # FINAL OUTPUT TO BE SHOW(will return a list of queries along with their module names)
    # return results

    response = llm_70b_vers_creative.invoke(formatted_prompt)
    input_text = response.content
    return input_text



# def extract_query_list(text: str):
#     """
#     Extract the first list of dictionaries (queries + modules) from raw text.
#     """
#     # Match a list of dictionaries like: [ { "query": ..., "module": ... }, {...} ]
#     pattern = r"\[\s*\{[\s\S]*?\}\s*\]"

#     match = re.search(pattern, text, re.DOTALL)
#     if match:
#         try:
#             return ast.literal_eval(match.group(0))  # safely evaluate list of dicts
#         except Exception as e:
#             print("⚠️ Error evaluating list:", e)
#     else:
#         print("❌ No list of queries found in input text.")
#     return []

@frappe.whitelist()
def extract_query_list(query_list, input_industry_name):

    raw_query_hints = generate_query_hints(query_list = query_list, input_industry_name=input_industry_name)

    """
    Extract the first list of dictionaries (queries + modules) from raw text.
    """
    # Match a list of dictionaries like: [ { "query": ..., "module": ... }, {...} ]
    pattern = r"\[\s*\{[\s\S]*?\}\s*\]"

    match = re.search(pattern, raw_query_hints, re.DOTALL)
    if match:
        try:
            return ast.literal_eval(match.group(0))  # safely evaluate list of dicts
        except Exception as e:
            print("⚠️ Error evaluating list:", e)
            return f"Error evaluating list:, {e}"
            
    else:
        print("❌ No list of queries found in input text.")
    return "No relevant queries found in the input text"

nlp = spacy.load("en_core_web_sm")  # run: python -m spacy download en_core_web_sm if not installed

def extract_location(query):
    """
    Use spaCy NER to extract first GPE (location) if present.
    Returns None if not present.
    """
    doc = nlp(query)
    for ent in doc.ents:
        if ent.label_ == "GPE":   # Geo-Political Entity
            return ent.text
    return None

@frappe.whitelist(allow_guest=True)
def normalize_queries_with_known_cities(query_list, input_industry_name):
    city_list = get_cities()
    known_locations = [k['city_name'] for k in city_list]
    known_lower = [k.lower() for k in known_locations]
    final_results = []

    extracted_queries = extract_query_list(query_list=query_list, input_industry_name=input_industry_name)

    if isinstance(extracted_queries, list):
        for qd in extracted_queries:
            query = qd['query']
            detected = extract_location(query)

            # Case 1: Valid location already present
            if detected and detected.lower() in known_lower:
                final_results.append(qd)
                continue

            # Case 2: Unknown location detected -> replace it with a random known city
            if detected:
                replacement = random.choice(known_locations)
                pattern = re.compile(re.escape(detected), re.IGNORECASE)
                new_query = pattern.sub(replacement, query)
                final_results.append({"query": new_query, "module": qd["module"]})
                continue

            # Case 3: No location detected at all -> keep as-is
            final_results.append(qd)

        return final_results
    
    else:
        return extracted_queries

# if isinstance(results, list):
#     normalized = normalize_queries(results, known_locations)
#     print(normalized)
# else:
#     results

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
@frappe.whitelist(allow_guest=True)
def insert_solution_result():

    try:
        child_row_id = frappe.form_dict.get("child_row_id")
        updated_solutions = frappe.form_dict.get("updated_solutions")
        intension = frappe.form_dict.get("intension")

        if  child_row_id == None or updated_solutions == None or intension == None:
            return {
                "status": "fail",
                "message": "The data is NONE"
            }
        # STEP 1: Always parse string to dict if possible
        if isinstance(updated_solutions, str):
            try:
                updated_solutions = json.loads(updated_solutions)
            except json.JSONDecodeError:
                # If it's not a JSON string, keep as is
                log_to_file("data", "updated_solutions is not JSON — using as plain string.")
        
        # STEP 2: Now convert any dict/list to JSON string for SQL
        if isinstance(updated_solutions, (dict, list)):
            # updated_solutions = json.dumps({"result": {"Analytics_response": updated_solutions}})
            updated_solutions = json.dumps({"result": updated_solutions})

        # STEP 3: Ensure final value is string — required for SQL
        if not isinstance(updated_solutions, str):
            updated_solutions = str(updated_solutions)

        # STEP 4: Safe SQL update
        frappe.db.sql("""
            UPDATE `tabChat history`
            SET result = %s,
                intension = %s,
                modified = NOW()
            WHERE name = %s
        """, (
            updated_solutions,
            intension,
            child_row_id
        ))

        frappe.db.commit()

        return {
            "status": "success",
            "message": "Chat history updated successfully."
        }

    except Exception as e:
        frappe.throw(f"Server error: {str(e)}")

@frappe.whitelist()
def excute_Property_Creation(method_name=None,param=None,childBlockId=None):
    python_exe = "/home/mars/property_seg_env/bin/python"
    script_path = "/home/mars/frappe-bench/AeroShape/FinalCode.py"

    # Build args safely
    args = [python_exe, script_path, method_name]
    if param is not None:
        args.append(str(param))  # Ensure it's a string
    if childBlockId is not None:
        args.append(str(childBlockId))  # Ensure it's a string
    
    try:
        result = subprocess.run(
            args,
            check=True,
            capture_output=True,
            text=True,
            cwd="/home/mars/frappe-bench/AeroShape"  # set working directory
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        gc.collect()  # Run garbage collection to free up memory
        frappe.log_error(e.stderr, "FinalCode Script Error")
        return f"Error running script: {e.stderr}"

@frappe.whitelist()
def trigger_script(method_name=None,param=None,childBlockId=None):    
    frappe.enqueue('frontend_app.Management_Class.helpers.utility.excute_Property_Creation', queue='long', job_name="Property Creation Job",method_name=method_name,param=param,childBlockId=childBlockId)    
    return "excute_Property_Creation executed successfully"

@frappe.whitelist()
def UpdatePropertySegStatus(message):
    frappe.publish_realtime('Property_Seg_Status_Update', {'message': message})


@frappe.whitelist()
def send_realtime_update(doc,method=None):
    # Get the currently logged-in user (who is updating the document)
    current_user = frappe.session.user
    if current_user == doc.owner:
        frappe.publish_realtime(
            event="feasibility_update",
            message={
                "docname": doc.name,
                "status": doc.status,
                "user": current_user
            },
            user=current_user  # Send only to that user
        )

def haversine(coord1, coord2):
    
    R = 6371  # Earth radius in km
    distance = geodesic(coord1, coord2).kilometers
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Differences
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Haversine formula
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c  # in kilometers

@frappe.whitelist()
def updateNearestConnectivity():
    surveyNoList = frappe.db.get_list('Survey No', filters=[['name', '!=', "002"]], fields=['*'])
    doctype_list  = ['Railway Station','Substation','Airport','Seaport']
    distaceObj = {
        'RailwayStationDist' :None,
        'SubstationDist' :None,
        'AirportDist' :None,
        'SearportDist' :None
    }
    frappe.log_error("Total Property to Update",len(surveyNoList))
    for surveyNo in surveyNoList:
        frappe.log_error("Updating Property Started",surveyNo.get("name"))
        # propertyCoord = surveyNo.get("latitude_longitude").replace(" ","")

        if(surveyNo.get("latitude_longitude") != None and surveyNo.get("latitude_longitude") != "" and surveyNo.get("latitude_longitude") != " " and surveyNo.get("latitude_longitude") != "0.000000000"):
            propertylat,propertLan = map(float, surveyNo.get("latitude_longitude").replace(" ","").split(',')) 
            
            updateValue = False
            for doctype in doctype_list:
                data = frappe.get_all(doctype,fields=['*'])
                lowestDistance = float('inf')  # Start with infinity
                
                id = None
                
                for item in data:
                    if(item.get("coordinates")):
                        lat, lon =  map(float, item.get("coordinates").replace(" ","").split(','))                    
                        dis = haversine([lat,lon],[propertylat,propertLan])
                        if dis < lowestDistance:    
                            id = item.get('name')
                            lowestDistance = dis
                            if doctype == "Railway Station":
                                updateValue = True
                                distaceObj['RailwayStationDist'] = lowestDistance
                            elif doctype == "Substation":
                                updateValue = True
                                distaceObj['SubstationDist'] = lowestDistance
                            elif doctype == "Airport":
                                updateValue = True
                                distaceObj['AirportDist'] = lowestDistance
                            else:
                                updateValue = True
                                distaceObj['SearportDist'] = lowestDistance
            if(updateValue):
                # get an existing document
                doc = frappe.get_doc('Survey No', surveyNo.get("name"))
                doc.distance_from_power_source = distaceObj['SubstationDist']
                doc.distance_from_nearest_railway_station = distaceObj['RailwayStationDist']
                doc.distance_from_nearest_airport = distaceObj['AirportDist']
                doc.distance_from_nearest_seaport = distaceObj['SearportDist']
                doc.save()
            frappe.log_error("Updating Property Ended",surveyNo.get("name"))