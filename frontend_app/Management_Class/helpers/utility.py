import frappe
from datetime import datetime

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