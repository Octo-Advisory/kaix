import os
import re
# from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq 
# from langchain_openai import ChatOpenAI

# load_dotenv()
groq_api_key = "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"
# openai_key = os.getenv("OPENAI_API_KEY")

# Initialize LLM    
llm_70b_vers = ChatGroq(groq_api_key=groq_api_key, model_name="llama-3.3-70b-versatile", temperature=0.0)
llm_70b_vers_creative = ChatGroq(groq_api_key=groq_api_key, model_name="llama-3.3-70b-versatile", temperature=0.7)
llm_8b_inst=ChatGroq(groq_api_key=groq_api_key,model_name="llama-3.3-8b-instant", temperature=0.0)
# llm_openai = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.0, api_key=openai_key)
# llm_openai_inf_mini = ChatOpenAI(model="gpt-4o-mini", temperature=0.0, api_key=openai_key)
# llm_openai_inf_4o = ChatOpenAI(model="gpt-4o", temperature=0.0, api_key=openai_key)
# llm_openai_inf_4 = ChatOpenAI(model="gpt-4", temperature=0.0, api_key=openai_key)
# llm_openai_inf_3_5 = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0.0, api_key=openai_key)

# Define a function to refine the query using history
def refine_query_with_history(history, latest_query, llm=llm_70b_vers):
    # Define retriever prompt
    retriever_prompt_template = """  
    Given the chat history and the latest user input, reformulate a standalone query that maintains the intent and structure of the latest user input.  
    Use the AI's messages for context only to understand the user's intent better, but do not take examples or suggestions from AI responses as the user's actual input unless the user explicitly agrees or repeats them.  

    Instructions:  
    1. Preserve the original structure of the user input.  
    - If the user’s latest input is a statement, the reformulated query must remain a statement.  
    - If the user’s latest input is a question, the reformulated query must remain a question.  
    2. If the latest user input is completely different and unrelated to the past conversation, return it as-is without modification.  
    3. If the latest user input is related to the past conversation, refine it by integrating relevant details from the chat history while ensuring clarity.  
    4. Strictly do not infer or carry forward any industries or products from past AI responses unless the user explicitly acknowledges, agrees to, or repeats those industries or products in their latest input.  
    5. Strictly do not infer or carry forward any industries or products from past user inputs unless they are explicitly mentioned in the latest user input.  
    6. If the latest user input mentions only one industry or product, ensure only that industry or product appears in the reformulated query.  
    - Do not include multiple industries or products unless the user explicitly mentions multiple ones in their latest query.  
    7. Do not add any explanations, reasoning, or justifications in the reformulated standalone query. The output must be a clean and direct reformulation of the user’s intent without unnecessary elaboration.  

    Chat History:  
    {history}  

    Latest User Input:  
    {latest_query}  

    Reformulated Standalone Query:  
    """
    
    prompt = PromptTemplate(
        input_variables=["history", "latest_query"],
        template=retriever_prompt_template
    )
    chain = prompt | llm
    refined_query = chain.invoke({"history": "\n".join(history), "latest_query": latest_query})
    refined_text = refined_query.content.strip()
    
    # Extract the reformulated standalone query
    match = re.search(r'reformulated standalone query:\s*(?:"(.*?)"|\'(.*?)\'|(.*))$', refined_text, re.IGNORECASE)
    if match:
        # Return the captured group that is not None
        return next(group for group in match.groups() if group)
    
    # Fallback to the entire response if no match is found
    return refined_text

# Define the function
def classify_query(user_query):
    # Define the refined prompt template
    prompt_template = """
    You are an expert in understanding business-related queries and classifying them into specific categories.
    Based on the provided query, classify it into one of the following categories:

    Categories:
    1. Query to build industry from Scratch:
        - Example: I want to build 1 TPA Cement Factory.
        - This refers to queries about establishing an industry or a business from the ground up, including any initial setup requirements and purchasing the land.
        
    2. Query to search Vendors:
        - Example: I am searching for a vendor who supplies pharmaceutical-grade raw chemicals for drug manufacturing.
        - This refers to queries related to finding suppliers, manufacturers, or vendors for products or services.
        
    3. Query to search Incentives:
        - Example: What benefits are available for setting up a cement manufacturing plant in this XYZ area?
        - This refers to queries asking about government incentives, grants, or subsidies related to starting or expanding an industry.
        
    4. Query to Get Approvals:
        - Example: I want to get approval for my Cement Factory.
        - This refers to queries related to obtaining permits, licenses, or regulatory approvals for an industry or business.
        
    5. Query to Get Employee Search:
        - Example: What is the availability of employment in XYZ area for the Pharmaceutical industry?
        - This refers to queries about recruiting or finding employees for a specific industry or area.

    If the user's intent does not match any of these categories, classify it as:
    - Other industry-related queries:
        - Example: "What is the role of AI in manufacturing?"
        - This refers to queries discussing trends, innovations, or technology related to industries but not fitting into the above categories.
        
    - Valueless queries:
        - Example: "Who is Donald Trump?" or "What is the culture of India?"
        - This refers to queries that are irrelevant to business or industry building, processes, or any business-related domain.
        - Example: "I'm going to buy a new bike, for that which approvals do I need?"
        - This includes queries where industry-related keywords are used, but the overall context or intent does not pertain to meaningful business processes.

    Additional Notes:
    - Do not classify a query into a category based solely on the presence of keywords like "approval," "vendor," or "incentive." Evaluate the overall context and intent to ensure it aligns with the business-related domain described in the categories.

    Query: {query}

    Your output should only be the name of the category or "Other industry-related queries" or "Valueless queries." 
    Do not provide explanations or details, just the category name.
    """
 

    # Initialize the LLM

    # Create the prompt
    prompt = PromptTemplate(
        input_variables=["query"],
        template=prompt_template
    )

    # Create the LLM chain
    chain = prompt | llm_70b_vers

    # Run the query through the chain
    category = chain.invoke({"query": user_query})

    return category.content.strip()
    
# user_query = input("\n\nWrite your query here: ").strip()
# classified_class = classify_query(user_query)
# print("\n\nClassified Intention is:", classified_class)

# if "Query to build industry from Scratch" in classified_class:
#     main_industry = ["Cement", "Pharmaceuticals", "Automobile", "Chemical", "Renewable", "Textile", "Food", "agricultural"]
#     sub_sector = ["Cement", "Allopathy", "Ayurvedic", "Homeopathy", "Vehicle Manufacture", "Automotive Components", "Chemical", "Wind Energy", "Solar Energy", "Textile", "Beverages", "Snacks", "agricultural chemical"]

#     gathered_details = gather_industry_details(user_query, main_industry, sub_sector)
#     if len(gathered_details) == 3:
#         msg,complete_details, chat_history = gathered_details
#         print("\n\nComplete Extracted Data:\n", complete_details)
#         print("\nUser Message:\n", msg)
#         print("\nConversation History:\n", "\n".join(chat_history))
#         # Example Usage
#         # product_name = "Crude Oil"
#         # user_quantity = 1000
#         # user_unit = "kg"
#         # user_time_period = "per annum"
#         # db_standard_unit = "Metric tonne"
#         # db_standard_time_period = "per annum"

#         # converted_output = convert_to_standard_unit(
#         #     user_quantity, user_unit, user_time_period, db_standard_unit, db_standard_time_period, product_name, llm_70b_vers
#         # )
#         # print(converted_output)
#     else:
#         complete_details, chat_history = gathered_details
#         print("\n\nComplete Extracted Data:\n", complete_details)
#         print("\nConversation History:\n", "\n".join(chat_history))
#         # Example Usage
#         # product_name = "Cement"
#         # user_quantity = "1 million"
#         # user_unit = "units"
#         # user_time_period = "per annum"
#         # db_standard_unit = "tonne"
#         # db_standard_time_period = "per annum"

#         # converted_output = convert_to_standard_unit(
#         #     user_quantity, user_unit, user_time_period, db_standard_unit, db_standard_time_period, product_name, llm_70b_vers
#         # )
#         # print(converted_output)