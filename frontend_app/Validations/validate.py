import frappe
import json
from frontend_app.Validations.approval_validation import approval_validation
from frontend_app.Validations.Validation_for_build_Industry_from_strach import search_industry
from frontend_app.Validations.vendors_validation import vendor_validation
from frontend_app.Validations.incentive_validation import incentive_validation
from frontend_app.Validations.employeement_validation import employment_query_validation

@frappe.whitelist(allow_guest=True)
def validation(aiResponse,user_intension):
    try:
        with open("log.txt", "a") as file:
            file.write(f"\naiResponse1 {aiResponse}")
            file.write(f"\nuser_intension {user_intension}")
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
        elif user_intension == "Query to search Vendors":
            param = aiResponse.get('Validation Data')
            with open("log.txt", "a") as file:
                file.write(f"\nparam {param}")
            result =  vendor_validation(param)
            with open("log.txt", "a") as file:
                file.write(f"\nresult by ushan {result}")
            location_check = result.get('location_check',{})
            with open("log.txt", "a") as file:
                file.write(f"\nlocation_check {location_check}")

            final_check = result.get('pass_to_analytics',False)
            return (final_check, result)
            # supply_check = result.get('supply_check',{})
            # industry_check = result.get('industry_check',{})
            # pass_to_analytics_module1 = location_check.get('pass_to_analytics_module',None)
            # pass_to_analytics_module2 = supply_check.get('pass_to_analytics_module',None)
            # pass_to_analytics_module3 = industry_check.get('pass_to_analytics_module',None)
            # with open("log.txt", "a") as file:
            #     file.write(f"\nlocation_check {pass_to_analytics_module1}, supply_check {pass_to_analytics_module2}, industry_check {pass_to_analytics_module3}, ")

            # # Collect only values that are not None
            # values = [v for v in (pass_to_analytics_module1, pass_to_analytics_module2, pass_to_analytics_module3) if v is not None]

            # with open("log.txt", "a") as file:
            #     file.write(f"\nvalues {values}")
            
            # # if all none found then return False
            # if not values:
            #     return (True, result)

            # if all(value is True for value in values):
            #     return (True, result)
            # else:
            #     return (False, result)
            
        elif user_intension == "Query to search Incentives":
            param = aiResponse['State']
            result = incentive_validation(param)
            pass_to_analytics_module = result.get('pass_to_analytics')
            return (pass_to_analytics_module,result)
        
        elif user_intension == "Query to Get Employee Search":
            param = aiResponse
            result = employment_query_validation(param)
            pass_to_analytics_module = result.get('pass_to_analytics')
            return (pass_to_analytics_module,result)

    except Exception as e:
        import traceback
        error_message = traceback.format_exc()
        with open("log.txt", "a") as file:
            file.write(f"\nerror_message from validation {error_message}")
        return e