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
# from frontend_app.Ai_module.Query_Classification_And_Analysis import llm_70b_vers_creative

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import configparser


# from langchain_openai import ChatOpenAI
config_file = '/home/mars/frappe-bench/apps/frontend_app/frontend_app/Log_management/mars.ini'
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
def generate_followups(query_list,industry_name):
    prompt_template = """You are an intelligent assistant that helps users explore key factors involved in setting up an industry in a specific region in India.

Your task is to generate 4-5 compact, hint-style follow-up queries that the user might logically ask next.

You will receive:
• A list of 5 user query batches, each representing a past chat session  
• A fallback industry name (used only in rare cases)

📥 [User Query Sessions]:
You will be given a list of 5 session-wise query lists:
• Session 1 – Least recent (oldest)
• Session 5 – Most recent (latest)

Format:
Session 1: [ ... list of 5–10 queries ... ]  
Session 2: [ ... ]  
Session 3: [ ... ]  
Session 4: [ ... ]  
Session 5: [ ... ]  
{query_list}

📥 [Industry Name]:
{industry_name}

🎯 OBJECTIVE  
Help the user dive deeper into realistic, decision-relevant aspects of industry setup — such as land availability, vendor options, workforce access, required approvals, and government incentives.

---

✅ GENERATION STRATEGY

1. *RELEVANCE CHECK FIRST (MANDATORY):*
   • Carefully evaluate each query in all five sessions.
   • Determine which queries are relevant by checking whether they align with:
     – Project scope and module capabilities (listed below)
     – Structure and tone of good example queries
     – Avoidance of bad example formats, topics, and phrasing

2. *WEIGHTED RELEVANCE STRATEGY:*
   • Prioritize relevant queries from more recent sessions (descending from Session 5 → 1).
   • Output must reflect more influence from the *most recent session (Session 5)* than older ones.
   • However, do *not ignore* earlier sessions entirely — include relevant industry-location pairs from older sessions if not already covered.

3. *OUTPUT DIVERSITY REQUIREMENT:*
   • Ensure that the generated 7-10 follow-up queries collectively *represent all distinct, relevant industries and locations* found in the query sessions.
   • Avoid clustering all queries around just one industry or city, unless the user input does so.

4. *FALLBACK MODE (RARE):*
   • If *none* of the queries across all sessions are relevant, fallback to the provided industry_name.
   • In this case:
     – Use realistic city names from Gujarat (Ahmedabad, Surat, Vadodara, Rajkot, Bharuch, etc.)
     – Each query must include both the fallback industry name and a Gujarat city
     – Do not use vague location phrasing like “nearby” or “suitable areas”

5. *KEYWORD AWARENESS (ONLY WHEN RELEVANT):*
   If relevant queries include:
   • Product quantity and unit (e.g., 100000 tablets)
   • Specific raw materials
   • Approval or incentive scheme names
   • Specific industry types or city names  
   → Include these meaningfully in output queries.

---

✅ FORMATTING & SCOPE RULES

Each generated query must:
• Be 10–15 words or fewer  
• Be compact and non-repetitive  
• Address one supported topic: land availability, labor access, vendor proximity, approvals, or incentives  
• Include both *industry and location* (from input) or fallback values  
• Output must reflect diversity across sessions, especially prioritizing newer sessions  

🚫 STRICT BAD EXAMPLES BLOCKING

DO NOT generate queries that involve:
• Price or cost (e.g., labor cost)  
• Raw material quality or checks  
• Land allocation processes  
• Workforce skill types (e.g., “engineers”)  
• Vague location references (e.g., “nearby”, “suitable area”)

🧠 INTERNAL PROJECT AND MODULE SCOPE (REFERENCE ONLY)

— Project Capabilities:
• Suggest land *availability* based on location and industry  
• Recommend suppliers (raw materials, equipment) by proximity  
• Provide labor availability by general skill type  
• Identify necessary government approvals  
• Suggest applicable government incentives  

— Module Focus:
• Build from Scratch: holistic industry setup  
• Employment: workforce availability  
• Vendor Search: raw material suppliers  
• Incentives: industry-location schemes  
• Approval: industry-level permissions  

— GOOD QUERY STRUCTURE EXAMPLES:
• What is the vendor availability for cement industry in Vadodara, Gujarat?  
• Tell me all the incentives available for pharmaceutical industry in Surat city?  
• What are the employment options around the Anand city?  
• I want to build a toy factory with 100000 toys capacity?  
• What are the approvals available for building electrochemical storage unit in Bharuch?

---

📤 OUTPUT FORMAT:

Return only a clean, syntactically correct Python list of 4–5 questions.

NO HEADINGS. NO EXTRA TEXT. NO MARKDOWN.

Each must:
• Be based on relevant queries across all sessions  
• Prioritize content from *Session 5*, while ensuring coverage of key elements from Sessions 1–4  
• Match tone and structure of good examples  
• Avoid all bad example types and unsupported phrasing

📤 OUTPUT EXAMPLE:

```python
[
    "What are the vendor options for pharmaceutical industry in Anand city?",
    "What land availability exists for cement industry in Ahmedabad?",
    "Tell me the government incentives for pharmaceutical industry in Gujarat",
    "What are the labor options for plastic industry in Surat?",
    "What are the approvals needed for cement industry in Ahmedabad?"
]
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant who suggests relevant follow-up questions."),
        ("human", prompt_template)
    ])

    chain = prompt | llm_70b_vers_creative

    try:
        response = chain.invoke({"query_list": query_list, "industry_name":industry_name})
        # return response.content.strip()
        final_response = response.content.strip()
      
        return final_response
    except Exception as e:
        return "Could not generate follow-up questions at this time."

@frappe.whitelist(allow_guest=True) 
def formatting_input_query_list(raw_nested_list, input_industry_name):
    # Format sessions as strings
    user_query_1 = [f"Session {idx}: {session}" for idx, session in enumerate(raw_nested_list, start=1)]
    query_list_text = "\n".join(user_query_1)

    input_text = generate_followups(query_list=query_list_text, industry_name=input_industry_name)
    # Extract list portion using regex
    list_match = re.search(r"\[(.*?)\]", input_text, re.DOTALL)
    if not list_match:
        print("⚠ No valid list found in model output")
        return []

    list_str = "[" + list_match.group(1).strip() + "]"

    # Parse result
    try:
        questions_list = ast.literal_eval(list_str)
        return questions_list
    except Exception as e:
        return e

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