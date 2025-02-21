import frappe
import json
from frontend_app.Validations.approval_validation import approval_validation
from frontend_app.Validations.Validation_for_build_Industry_from_strach import search_industry

@frappe.whitelist()
def validation(aiResponse,user_intension):
    try:
        # with open("log.txt", "a") as file:
        #     file.write(f"\naiResponse1 {aiResponse}")
        aiResponse = json.loads(aiResponse)
        aiResponse = aiResponse[0]

        if user_intension == "Query to Get Approvals":
            param = {
                "location_info" : aiResponse['Validation Data']['Location_info'],
                "Industry_info" : aiResponse['Validation Data']['Industry_info']
            }
            with open("log.txt", "a") as file:
                file.write(f"\nparam {param}")
        
            return approval_validation(param)
        elif user_intension == "Query to build industry from Scratch":
             state = aiResponse['state']
             capacity = state.get('Capacity')
             main_industry = state.get('Main-Industry')
             sub_sector = state.get('Sub-Sector')
             segment = state.get('Segment')
             return search_industry(main_industry,sub_sector,segment,capacity)

    except Exception as e:
        with open("log.txt", "a") as file:
                file.write(f"\nExeption {e}")
        return e