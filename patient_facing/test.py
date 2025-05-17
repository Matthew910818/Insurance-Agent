# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
twilio_number = os.environ["TWILIO_PHONE_NUMBER"]
test_number = os.environ["TEST_NUMBER"]
client = Client(account_sid, auth_token)

call = client.calls.create(
    from_=twilio_number,
    to=test_number,
    url="http://demo.twilio.com/docs/voice.xml",
)

print(call.sid)