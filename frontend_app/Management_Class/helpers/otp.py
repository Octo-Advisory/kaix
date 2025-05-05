# import frappe
# import random
# import time

# @frappe.whitelist(allow_guest=True)
# def forgot_password(action, email=None, otp=None, new_password=None):
#     if action == "request_otp":
#         return send_email_otp(email)
#     elif action == "verify_otp":
#         return verify_email_otp(email, otp)
#     # You can add more logic here for resetting password securely
#     else:
#         return {"status": "error", "message": "Invalid action"}
# @frappe.whitelist(allow_guest=True)
# def send_email_otp(email):
#     otp = str(random.randint(100000, 999999))
#     timestamp = int(time.time())  # current time in seconds

#     # Store as dict: {"otp": "123456", "ts": 1234567890}
#     frappe.cache().hset("email_otp", email, frappe.as_json({"otp": otp, "ts": timestamp}))

#     frappe.sendmail(
#         recipients=[email],
#         subject="Your OTP Code",
#         message=f"Your OTP is: {otp}"
#     )
#     return {"status": "success", "message": "OTP sent"}
# @frappe.whitelist(allow_guest=True)
# def verify_email_otp(email, otp):
#     data = frappe.cache().hget("email_otp", email)
#     if not data:
#         return {"status": "fail", "verified": False, "message": "No OTP found"}

#     otp_data = frappe.parse_json(data)
#     stored_otp = otp_data.get("otp")
#     timestamp = otp_data.get("ts")

#     if stored_otp != otp:
#         return {"status": "fail", "verified": False, "message": "Invalid OTP"}

#     if int(time.time()) - timestamp > 300:
#         frappe.cache().hdel("email_otp", email)
#         return {"status": "fail", "verified": False, "message": "OTP expired"}

#     frappe.cache().hdel("email_otp", email)
#     return {"status": "success", "verified": True, "message": "OTP verified"}

import frappe
import random
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Function to send OTP via email using SMTP
def send_email_otp(email):
    otp = str(random.randint(100000, 999999))
    timestamp = int(time.time())  # current time in seconds

    # Store OTP and timestamp in cache
    frappe.cache().hset("email_otp", email, frappe.as_json({"otp": otp, "ts": timestamp}))

    # SMTP settings
    sender_email = "krunalprajapati1904@gmail.com"  # Your email
    sender_password = "qgri dxzs izbg xkjz"  # Your email password
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    # Prepare the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = "Your OTP Code"
    message_body = f"Your OTP is: {otp}"
    msg.attach(MIMEText(message_body, 'plain'))

    try:
        # Connect to the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection with TLS
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, email, text)  # Send the email
        server.quit()  # Terminate the SMTP session
        print(f"Email sent to {email} successfully.")
        
        return {"status": "success", "message": "OTP sent via email"}
    
    except Exception as e:
        print(f"Error sending email: {e}")
        return {"status": "fail", "message": f"Failed to send OTP: {str(e)}"}

# Verify OTP function
@frappe.whitelist(allow_guest=True)
def verify_email_otp(email, otp):
    data = frappe.cache().hget("email_otp", email)
    if not data:
        return {"status": "fail", "verified": False, "message": "No OTP found"}

    otp_data = frappe.parse_json(data)
    stored_otp = otp_data.get("otp")
    timestamp = otp_data.get("ts")

    if stored_otp != otp:
        return {"status": "fail", "verified": False, "message": "Invalid OTP"}

    if int(time.time()) - timestamp > 300:  # OTP expiration time (5 minutes)
        frappe.cache().hdel("email_otp", email)
        return {"status": "fail", "verified": False, "message": "OTP expired"}

    frappe.cache().hdel("email_otp", email)  # Clean up OTP after successful verification
    return {"status": "success", "verified": True, "message": "OTP verified"}

def reset_user_password(email, new_pass):
    try:
        user = frappe.get_doc("User", email)
        frappe.log_error("use",user)
        frappe.log_error("pass",new_pass)
        if user:
            user.new_password = new_pass
            user.save(ignore_permissions=True)
            frappe.db.commit()
            return {"status": "success", "message": "Password reset successfully"}
        else:
            return {"status": "fail", "message": "User not found"}
    except Exception as e:
        return {"status": "fail", "message": f"Error resetting password: {str(e)}"}

# Main handler function to handle the forgot password process
@frappe.whitelist(allow_guest=True)
def forgot_password(action, email=None, otp=None, new_password=None):
    if action == "request_otp":
        return send_email_otp(email)  # Send OTP
    elif action == "verify_otp":
        return verify_email_otp(email, otp)  # Verify OTP
    elif action == "reset_password" and email and new_password:
        return reset_user_password(email, new_password)
    else:
        return {"status": "error", "message": "Invalid action"}
