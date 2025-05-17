import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Assuming you have these variables already
EMAIL_ADDRESS = "bargainmedicalbill@gmail.com"
EMAIL_PASSWORD = "vyvw rbcl yfcq wocg"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_billing_email_with_hardcoded_body(to_email, pdf_path):
    """Send a billing email with hardcoded body and PDF attachment using SMTP."""
    subject = "Medical Bill Due - March 28, 2025"
    body = """
Dear Jane Doe,

I hope this message finds you well.

Thank you for speaking with us regarding your medical bill. As discussed, we have updated your payment plan to reflect the new total amount due and adjusted terms. Below are the updated details of your payment plan:

Total Amount Due: $2,547.83
Monthly Payment Amount: $212.32
Payment Frequency: Monthly
Payment Start Date: May 20, 2023

This updated payment plan will ensure your account remains in good standing while making your payments manageable. If you have any further questions or need additional assistance with your account, please don’t hesitate to reach out.

To make your payment, you can visit our secure payment portal at:
bargainmedicalbilling.com/payments

If you need any further support or would like to discuss your payment plan in more detail, feel free to contact our customer service team at:

Phone: (415) 636-7820
Email: bargainmedicalbill@gmail.com

Thank you for working with us to resolve your account. We’re here to assist you with anything you need.

Best regards,
Claudia
BargAIn Medical Billing Team
    """

    # Create the email container
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Attach the PDF
    with open(pdf_path, "rb") as file:
        pdf_attachment = MIMEApplication(file.read(), _subtype="pdf")
        pdf_attachment.add_header('Content-Disposition', 'attachment', filename="bill.pdf")
        msg.attach(pdf_attachment)

    # Send the email
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())

    print(f"Billing email sent to {to_email}")

send_billing_email_with_hardcoded_body("ishaan@freeventures.org", "medical_bill.pdf")
