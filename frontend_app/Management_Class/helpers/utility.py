import frappe
from datetime import datetime
import random #added by jenith on 22-5-25
import subprocess
import sys
import gc
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
 
@frappe.whitelist()
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

def generate_followups(query_list):
    prompt_template = """You are an intelligent assistant that helps users continue their inquiry by suggesting meaningful follow-up questions. Based on the user's current and previous questions (1 to 10), generate 4 thoughtful, relevant, and natural follow-up questions. These questions should reflect what an informed user might logically ask next.

Use concise, clear language. The suggestions should feel like natural extensions of the user's curiosity or goals.

Here are a few examples:

Example 1  
User Questions:  
1. "How do I check if my business idea is practical?"
2. "What things should I research before starting a factory?"
3. "What if my supplier is too far away? How does that affect costs?"
4. "How do I know if a vendor is trustworthy?"
5. "How do I find workers for my new factory?"
6. "Are there enough skilled people in [city] for my business?"
7. "What's the average salary for factory workers in Gujarat?"
8. "How long does it take to get factory approvals?"
9. "Does the government give money to help start businesses?"
10. "Who do I contact for pollution clearance for my plant?"

Follow-up Suggestions: 
1. "What are the most common mistakes people make when checking if their business will work?"
2. "How can I negotiate better prices or contracts with suppliers once I find them?"
3. "What training programs are available if local workers need skill upgrades?"
4. "Can I start any construction or hiring while waiting for approvals?"

Example 2  
User Questions:  
1. "Can you explain what a feasibility report does in simple terms?"
2. "Will I need to train workers or can I hire ready-trained staff?"
3. "Where can I buy raw materials for my product?"
4. "How do I find reliable suppliers near my factory?"
5. "What legal papers do I need to open a manufacturing unit?"

Follow-up Suggestions:  
1. "What's the difference between a feasibility report and a business plan - do I need both?"  
2. "If I need to train workers, are there government programs that can help cover the costs?"
3. "How do I balance quality versus cost when choosing between different suppliers?" 
4. "What's the typical timeline from submitting paperwork to getting all approvals for a new factory?"

Example 3  
User Questions:  
1. "What’s the most common reason for approval delays?"
2. "Can I hire local workers, or will I need people from other cities?"
3. "Are there tax benefits for new factories in Gujarat?"

Follow-up Suggestions:  
1. "What documents should I prepare in advance to avoid common approval bottlenecks?"
2. "If I need to bring in workers from other cities, what housing or relocation support should I consider?"  
3. "Do these tax benefits apply differently to foreign investors versus local businesses?" 
4. "How do the tax benefits compare if I set up in Gujarat versus neighboring states?"

Example 4  
User Questions:
1.what approvals should i get to build cement factory in bharuch city of gujarat state?

Follow-up Suggestions:
1. "What's the typical timeline to get all required approvals for a cement plant in Bharuch, from first application to final clearance?"                 
2. "Which government departments in Gujarat handle cement factory approvals, and do I need to approach them separately or through a single window?"
3. "Are there any special environmental or zoning regulations for cement plants near Bharuch's river/industrial zones that differ from other parts of Gujarat?"
4. "After getting initial approvals, what ongoing compliance reports or renewals will my cement factory need to maintain operational legality?"

Now generate 4 intelligent and useful follow-up questions based on the user's past questions below.

User Questions:  
{query_list}

Follow-up Suggestions:"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant who suggests relevant follow-up questions."),
        ("human", prompt_template)
    ])
    
    chain = prompt | llm_70b_vers_creative
    
    try:
        response = chain.invoke({"query_list": query_list})
        # return response.content.strip()
        final_response = response.content.strip()
        # print(final_response)
    except Exception as e:
        print(f"Error generating follow-ups: {e}")
        return "Could not generate follow-up questions at this time."
    
    def qwerty(input_string):

        lines = input_string.split('\n')

        questions = []

        for line in lines:
            # Checking if line starts with a number (for numbered questions)
            if line.strip() and line.strip()[0].isdigit():
                # to Find the opening and closing quotes
                start = line.find('"') + 1  # +1 to skip the opening quote
                end = line.rfind('"')       # to find the last quote
                
                # Extract the question between the quotes
                if start != -1 and end != -1:
                    question = line[start:end]
                    questions.append(question)

        return questions 
    
    return qwerty(final_response)

user_query = ["what approvals should i get to build cement factory in bharuch city of gujarat state?"]
no_user_query = []

if len(user_query) > 0:
    follow_ups = generate_followups(user_query)
else:
    no_user_query
print("Suggested follow-up questions:\n", follow_ups)


@frappe.whitelist()
def excute_Property_Creation():
    python_exe = "/home/mars/property_seg_env/bin/python"
    script_path = "/home/mars/frappe-bench/AeroShape/FinalCode.py"
    try:
        result = subprocess.run(
            [python_exe, script_path],
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
def trigger_script():
    frappe.enqueue('frontend_app.Management_Class.helpers.utility.excute_Property_Creation', queue='long', job_name="Property Creation Job")
    return "excute_Property_Creation executed successfully"