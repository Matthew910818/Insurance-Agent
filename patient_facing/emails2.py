import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from openai import OpenAI

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dotenv import load_dotenv
load_dotenv()




# Email credentials
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "bargainmedicalbill@gmail.com"
EMAIL_PASSWORD = "vyvw rbcl yfcq wocg"


import certifi
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://bargainmedicalbill:L1CYQftydqS9jKiO@medical-billing.vdcvo.mongodb.net/?appName=medical-billing"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'), tlsCAFile=certifi.where())

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client.patientbills  
collection = db.patients    # 'patients' is the collection name

# Define the patient data to insert
patient_info = {
    "patient_info": {
        "name": "Jane Doe",
        "age": 42,
        "location": "Seattle, WA",
        "debt_amount": "$2,547.83",
        "insurance": "Blue Cross Blue Shield (Out of Network)",
        "hospital": "City General Hospital",
        "service_date": "03/15/2025",
        "bill_date": "04/20/2025",
        "payment_plan": {
            "total_amount": "",
            "frequency": "",
            "amount_per_payment": "",
            "start_date": "",
            "proposed_at": ""
        }
    }
}

collection.insert_one(patient_info)
print("Patient data inserted successfully!")

# OpenAI API setup
client = OpenAI(api_key=OPENAI_API_KEY)



def generate_email_body(patient_name, amount_due, due_date):
    """Generate a billing email body using OpenAI API."""
    prompt = f"""
    You are a Debt Relief Associate named Claudia. Write a professional and polite medical billing reminder email for {patient_name} on behalf of BargAIn.
    The bill amount is ${amount_due} and is due on {due_date}. 
    The tone should be formal but friendly, encouraging prompt payment.
    Include a placeholder for the payment link, which is bargainmedicalbilling.com/payments, and mention customer support for any queries. Our contact phone # is (415) 636-7820 and our email is bargainmedicalbill@gmail.com.
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a professional medical billing assistant."},
                  {"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content

def send_billing_email(to_email, patient_name, amount_due, due_date, pdf):
    """Send a billing email using SMTP."""
    subject = f"Medical Bill Due - {due_date}"
    body = generate_email_body(patient_name, amount_due, due_date)

    # Create the email container
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Attach the PDF
    with open(pdf, "rb") as file:
        pdf_attachment = MIMEApplication(file.read(), _subtype="pdf")
        pdf_attachment.add_header('Content-Disposition', 'attachment', filename="bill.pdf")
        msg.attach(pdf_attachment)

    # Send the email
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())

    print(f"Billing email sent to {to_email}")


patients = [
    {"name": "Jane Doe", "email": "ishaan@freeventures.org", "amount_due": 150, "due_date": "March 28, 2025"},
]



import imaplib
import email
from openai import OpenAI

# IMAP Server settings (for Gmail, use imap.gmail.com)
IMAP_SERVER = "imap.gmail.com"

def check_inbound_emails():
    """Fetch unread emails and process them."""
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    mail.select("inbox")

    # Search for unread emails
    _, search_data = mail.search(None, "UNSEEN")
    
    for num in search_data[0].split():
        _, data = mail.fetch(num, "(RFC822)")
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        sender = msg["From"]
        subject = msg["Subject"]
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if "text/plain" in content_type:
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()

        print(f"New email from {sender}: {subject}\n{body}")

        # Generate AI-powered response
        reply = generate_ai_response(body)

        # Send reply
        send_reply_email(sender, f"Re: {subject}", reply)

    mail.logout()

def send_reply_email(to_email, subject, body):
    """Send a reply email using SMTP."""
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())

    print(f"Reply email sent to {to_email}")

def generate_ai_response(user_message):
    """Generate an AI response to an inbound email."""
    prompt = f"""
    You are a professional medical billing assistant. Your name is Claudia, and you are a Debt Relief Associate for BargAIn Medical Billing.
    You reached out to the patient, and they have responded with the following message:

    "{user_message}"

    Please generate a polite and helpful response. Since this is a response, keep it concise. If the user confirms they can pay the full amount and/or asks for info on how to pay, refer them to our payment portal bargainmedical.com/payments. 
    If the user asks for an extension, disputes the charge, has questions, or sounds confused, offer to set up a call with them. Tell them to receive a call from our company phone number, 415-636-7380, and include a day and time (pick a time during business hours the following day). 
    In that event, also tell the user that they can call us at anytime, or propose a new time to call in theur response.

    If the user's response is unrelated to medical debt/billing and/or contains inappropriate or vulgar material, only respond by ploitely thanking them for their response and that you have forwarded their message to your superviser, who will reach out to them.
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a professional medical billing assistant."},
                  {"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content  # Ensure correct attribute access 

import time

if __name__ == "__main__":
    # Send initial emails (optional)
    for patient in patients:
        send_billing_email(patient["email"], patient["name"], patient["amount_due"], patient["due_date"], 'medical_bill.pdf')

    # Continuously check for inbound emails every 10 seconds
    while True:
        print("Checking for new emails...")
        check_inbound_emails()
        time.sleep(10)  # Wait for 10 seconds before checking again 