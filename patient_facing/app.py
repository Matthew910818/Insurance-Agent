# Simple Medical Debt Negotiation Agent
import os
from flask import Flask, request, render_template, redirect, url_for, jsonify, send_from_directory
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
from dotenv import load_dotenv
import openai
import uuid
from werkzeug.utils import secure_filename
import PyPDF2
from datetime import datetime
import json
from pathlib import Path

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize OpenAI client
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Initialize Twilio client
twilio_client = Client(
    os.environ.get("TWILIO_ACCOUNT_SID"),
    os.environ.get("TWILIO_AUTH_TOKEN")
)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Add after the UPLOAD_FOLDER configuration
DATA_FOLDER = 'data'
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# Store user data temporarily (in a real app, use a database)
user_data = {}

# Home route - show upload form
@app.route("/", methods=["GET"])
def index():
    return render_template("upload.html", message=None, message_type=None)

# Handle file uploads
@app.route("/upload", methods=["POST"])
def upload_file():
    if 'bill_pdf' not in request.files:
        return render_template("upload.html", message="No file part", message_type="danger")
    
    file = request.files['bill_pdf']
    if file.filename == '':
        return render_template("upload.html", message="No file selected", message_type="danger")
    
    if file and file.filename.endswith('.pdf'):
        # Generate unique ID for this user session
        session_id = str(uuid.uuid4())
        
        # Save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
        file.save(file_path)
        
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(file_path)
        
        # For demo purposes, hardcode some patient information
        # In a real app, you would extract this from the PDF
        patient_info = {
            'name': 'Jane Doe',
            'age': '42',
            'location': 'Seattle, WA',
            'debt_amount': '$2,547.83',
            'insurance': 'Blue Cross Blue Shield (Out of Network)',
            'hospital': 'City General Hospital',
            'service_date': '03/15/2023',
            'bill_date': '04/20/2023',
            'payment_plan': None,
            'last_call_summary': None,
            'call_history': []
        }
        
        # Store user data
        user_data[session_id] = {
            'patient_info': patient_info,
            'pdf_path': file_path,
            'pdf_text': pdf_text,
            'uploaded_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'conversation_history': [],  # Track the conversation
            'payment_arrangement': None  # Store payment arrangement details
        }
        
        return render_template(
            "profile.html", 
            session_id=session_id,
            patient=patient_info
        )
    else:
        return render_template(
            "upload.html", 
            message="Only PDF files are allowed", 
            message_type="danger"
        )

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                text += reader.pages[page_num].extract_text() + "\n"
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        text = "Error extracting text from PDF"
    return text

# Route to view patient profile
@app.route("/profile/<session_id>")
def profile(session_id):
    try:
        print(f"Loading profile for session: {session_id}")
        # Always try to load the latest data from file first
        file_path = os.path.join('data', f'patient_{session_id}.json')
        if os.path.exists(file_path):
            print(f"Found data file: {file_path}")
            with open(file_path, 'r') as f:
                # Update the in-memory data with the latest from file
                user_data[session_id] = json.load(f)
                print(f"Loaded data from file. Payment plan: {user_data[session_id].get('patient_info', {}).get('payment_plan')}")
        else:
            print(f"File not found: {file_path}")
            # If file doesn't exist, check if we have it in memory
            if session_id not in user_data:
                return "Patient not found", 404
            print(f"Using in-memory data. Payment plan: {user_data[session_id].get('patient_info', {}).get('payment_plan')}")
        
        # Now render the template with the latest data
        return render_template("profile.html", 
                              patient=user_data[session_id]['patient_info'], 
                              session_id=session_id)
    except Exception as e:
        print(f"Error loading patient data: {str(e)}")
        return "Error loading patient data", 500
        print(f"Error loading patient data: {str(e)}")
        return "Error loading patient data", 500

# Route to initiate a call
@app.route("/initiate-call/<session_id>", methods=["POST"])
def initiate_call(session_id):
    if session_id not in user_data:
        return jsonify({"error": "Invalid session ID"}), 400
    
    try:
        # Get Twilio credentials
        from_number = os.environ.get("TWILIO_PHONE_NUMBER")
        to_number = os.environ.get("TEST_NUMBER")
        
        # URL that Twilio will request when the call is answered
        callback_url = f"{request.url_root}start-call?session_id={session_id}"
        
        # Reset conversation history for new call
        user_data[session_id]['conversation_history'] = []
        user_data[session_id]['payment_arrangement'] = None
        
        # Initiate the call
        call = twilio_client.calls.create(
            to=to_number,
            from_=from_number,
            url=callback_url, 
            method='POST', 
            status_callback=f"{request.url_root}call-status?session_id={session_id}",
            status_callback_event=['completed'],
            status_callback_method='POST'  # Explicitly set POST method
        )
        
        user_data[session_id]['call_sid'] = call.sid
        user_data[session_id]['call_start_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return jsonify({
            "success": True,
            "message": "Call initiated",
            "call_sid": call.sid,
            "session_id": session_id
        })
    except Exception as e:
        print(f"Error initiating call: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# This endpoint handles the start of the call
@app.route("/start-call", methods=['GET', 'POST'])
def start_call():
    session_id = request.args.get('session_id')
    print(f"Starting call for session: {session_id}")
    
    response = VoiceResponse()
    
    if not session_id or session_id not in user_data:
        print(f"Error: Invalid session ID: {session_id}")
        response.say("Sorry, there was an error with this call. Goodbye.")
        return str(response)
    
    # Get user data
    user = user_data[session_id]
    patient = user['patient_info']
    
    # Calculate minimum acceptable amount
    original_debt = patient['debt_amount'].replace('$', '').replace(',', '')
    try:
        original_debt_float = float(original_debt)
        minimum_amount = max(1000, original_debt_float * 0.4)  # Minimum $1000 or 40% of debt, whichever is higher
    except ValueError:
        # Fallback if debt amount can't be converted to float
        pass
    
    # Prepare our first message to the patient with a focus on negotiation
    initial_message = f"Hello, this is Bargain Medical Billing. I'm calling about your outstanding medical bill from {patient['hospital']} for {patient['debt_amount']}. I'd like to discuss payment options and see if we can find a solution that works for your situation. Do you have a moment to talk about this?"
    
    # Add the message to the response with proper Gather parameters
    gather = Gather(
        input='speech', 
        action=f'/handle-response?session_id={session_id}&attempt=0', 
        timeout=7,
        speechTimeout='auto',
        language='en-US'
    )
    gather.say(initial_message)
    response.append(gather)
    
    # Add a fallback if no input is received
    response.say("I didn't hear a response. Let me try again.")
    
    # Track the conversation
    user_data[session_id]['conversation_history'].append({
        'role': 'agent',
        'text': initial_message,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    print("TwiML response generated for initial call")
    return str(response)

# This endpoint handles the responses during the call
@app.route("/handle-response", methods=['POST'])
def handle_response():
    # Get the session ID
    session_id = request.args.get('session_id')
    print(f"Handling response for session: {session_id}")
    
    # Get the speech result from the caller
    caller_speech = request.values.get('SpeechResult', '')
    
    # Check if there was no speech detected
    no_speech = not caller_speech or caller_speech.strip() == ''
    
    # Get the attempt counter (for handling multiple no-responses)
    attempt = int(request.args.get('attempt', '0'))
    print(f"Attempt: {attempt}, Patient said: {caller_speech if not no_speech else '[No response]'}")
    
    # Get the payment confirmation status
    awaiting_confirmation = request.args.get('awaiting_confirmation', 'false') == 'true'
    print(f"Awaiting confirmation: {awaiting_confirmation}")
    
    response = VoiceResponse()
    
    if not session_id or session_id not in user_data:
        print(f"Error: Invalid session ID: {session_id}")
        response.say("Sorry, there was an error with this call. Goodbye.")
        return str(response)
    
    # Get user data
    user = user_data[session_id]
    patient = user['patient_info']
    
    # Track the patient's response in conversation history
    if not no_speech:
        user_data[session_id]['conversation_history'].append({
            'role': 'patient',
            'text': caller_speech,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    # Calculate minimum acceptable amount (for example, 40% of original debt)
    original_debt = patient['debt_amount'].replace('$', '').replace(',', '')
    try:
        original_debt_float = float(original_debt)
        minimum_amount = max(1000, original_debt_float * 0.4)  # Minimum $1000 or 40% of debt, whichever is higher
        minimum_amount_formatted = "${:,.2f}".format(minimum_amount)
    except ValueError:
        # Fallback if debt amount can't be converted to float
        minimum_amount_formatted = "$1,000.00"
    
    # If no speech was detected, prompt the patient again
    if no_speech:
        # Increment the attempt counter
        attempt += 1
        
        # Different prompts based on attempt number
        if attempt == 1:
            prompt_message = "I didn't hear anything. Are you still there? I'm calling about your medical bill from " + patient['hospital'] + ". Please let me know if you can hear me."
        elif attempt == 2:
            prompt_message = "I'm still having trouble hearing you. If you're there, please say something, even just 'yes' so I know you can hear me."
        else:
            # Final attempt
            prompt_message = "This is my final attempt to connect. If you're interested in discussing your medical bill, please say something now."
        
        gather = Gather(
            input='speech', 
            action=f'/handle-response?session_id={session_id}&attempt={attempt}&awaiting_confirmation={awaiting_confirmation}', 
            timeout=7,
            speechTimeout='auto',
            language='en-US'
        )
        gather.say(prompt_message)
        response.append(gather)
        
        # Only hang up if we've tried multiple times
        if attempt >= 3:
            response.say("I still don't hear a response. I'll try calling back at a better time. Thank you.")
        
        print(f"Sent prompt for no response (attempt {attempt})")
        return str(response)
    
    # Reset attempt counter if we got a response
    attempt = 0
    
    # Check if we're awaiting confirmation of a payment plan
    if awaiting_confirmation and 'proposed_payment_arrangement' in user and user['proposed_payment_arrangement']:
        print(f"Checking confirmation for proposed plan: {user['proposed_payment_arrangement']}")
        
        # Check if the response sounds like a confirmation
        confirmation_prompt = f"""
        The patient was asked to confirm this payment plan:
        Total amount: {user['proposed_payment_arrangement']['total_amount']}
        Frequency: {user['proposed_payment_arrangement']['frequency']}
        Amount per payment: {user['proposed_payment_arrangement']['amount_per_payment']}
        Start date: {user['proposed_payment_arrangement']['start_date']}
        
        The patient responded: "{caller_speech}"
        
        Based on this response, did the patient confirm the payment plan? Answer with just YES or NO.
        """
        
        try:
            confirmation_response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You determine if a response is a confirmation."},
                    {"role": "user", "content": confirmation_prompt}
                ],
                max_tokens=10,
                temperature=0.3
            )
            
            confirmation_result = confirmation_response.choices[0].message.content.strip().upper()
            print(f"Confirmation result: {confirmation_result}")
            
            if "YES" in confirmation_result:
                # Payment plan confirmed
                user_data[session_id]['payment_arrangement'] = user['proposed_payment_arrangement']
                
                # Final confirmation and goodbye
                goodbye_message = f"Great! I've recorded your payment plan of {user['proposed_payment_arrangement']['amount_per_payment']} {user['proposed_payment_arrangement']['frequency']} starting {user['proposed_payment_arrangement']['start_date']}. We'll send a confirmation email with all the details. Thank you for working with us today. Have a great day!"
                
                response.say(goodbye_message)
                
                # Track the agent's final response
                user_data[session_id]['conversation_history'].append({
                    'role': 'agent',
                    'text': goodbye_message,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                # Save the user data to a file for persistence
                save_user_data(session_id, user_data[session_id])
                
                print("Payment plan confirmed, ending call")
                return str(response)
            else:
                # Payment plan not confirmed, continue negotiation
                user_data[session_id]['proposed_payment_arrangement'] = None
                
                # Create a message to continue negotiation
                continue_message = "I understand you're not ready to confirm this plan. Let's discuss what would work better for you. What payment amount would be more manageable for your budget?"
                
                # Track the agent's response
                user_data[session_id]['conversation_history'].append({
                    'role': 'agent',
                    'text': continue_message,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                # Create TwiML response to continue conversation
                gather = Gather(
                    input='speech', 
                    action=f'/handle-response?session_id={session_id}&attempt=0&awaiting_confirmation=false', 
                    timeout=7,
                    speechTimeout='auto',
                    language='en-US'
                )
                gather.say(continue_message)
                response.append(gather)
                
                # Add a fallback if no input is received
                response.say("I didn't hear a response. Let me try again.")
                
                print("Payment plan not confirmed, continuing negotiation")
                return str(response)
        except Exception as e:
            print(f"Error checking confirmation: {str(e)}")
            # Continue with normal conversation if there's an error
    
    # Create system prompt for GPT with updated approach including minimum amount
    system_prompt = f"""
    You are an AI agent from Bargain Medical Billing, calling a patient to discuss their medical bill. 
    
    IMPORTANT: Bargain Medical Billing is NOT a traditional collection agency. We are patient advocates who work WITH patients, not against them. Our mission is to help patients understand their bills and find manageable payment solutions that work for their financial situation.
    
    Patient information:
    - Name: {patient['name']}
    - Age: {patient['age']}
    - Location: {patient['location']}
    - Debt Amount: {patient['debt_amount']}
    - Insurance: {patient['insurance']}
    - Hospital: {patient['hospital']}
    - Service Date: {patient['service_date']}
    - Bill Date: {patient['bill_date']}
    
    NEGOTIATION PARAMETERS:
    - Original debt amount: {patient['debt_amount']}
    - Minimum acceptable amount: {minimum_amount_formatted}
    - Your goal: Negotiate to get as close to the full amount as possible
    - Hard limit: Do not accept less than {minimum_amount_formatted}
    - Preferred payment method: Lump sum, but payment plans are acceptable
    
    PDF Content Summary:
    {user['pdf_text'][:1000]}... (truncated)
    
    Your negotiation approach:
    1. Start by asking about their financial situation to understand what they can afford
    2. Initially offer a small discount (10-15%) to see if they can pay the majority of the bill
    3. If they express financial hardship, gradually increase the discount offer
    4. Never go below the minimum amount of {minimum_amount_formatted}
    5. For payment plans, try to keep the term under 24 months
    6. Be willing to pause and listen to the patient's concerns
    7. If they mention bankruptcy or legal action, emphasize that you want to find a solution that avoids those routes
    
    IMPORTANT: If the patient seems agreeable to a payment plan or settlement amount, propose specific terms and then ASK FOR CONFIRMATION. Do not assume agreement until they explicitly confirm.
    
    Your tone should be:
    - Warm and friendly, not cold and corporate
    - Patient and understanding, not rushed or pushy
    - Educational and helpful, not condescending
    - Flexible but firm on the minimum amount
    
    Keep responses brief (under 30 words) since this is a phone call. Be conversational and human.
    """
    
    # Add conversation history for context
    conversation_context = ""
    if len(user['conversation_history']) > 0:
        last_exchanges = user['conversation_history'][-6:]  # Get last 6 exchanges for context
        for exchange in last_exchanges:
            conversation_context += f"{exchange['role'].capitalize()}: {exchange['text']}\n"
    
    # Get response from GPT based on what the caller said
    try:
        print("Requesting response from OpenAI...")
        gpt_response = openai.chat.completions.create(
            model="gpt-4",  # You can also use "gpt-3.5-turbo" for a more economical option
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Recent conversation:\n{conversation_context}\n\nThe patient just said: {caller_speech}\n\nRespond to the patient. If you're proposing a specific payment plan, include the details in this format at the end of your message: [PAYMENT_PLAN: total_amount, frequency, amount_per_payment, start_date]"}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        # Get the text response from GPT
        agent_response = gpt_response.choices[0].message.content
        print(f"AI response: {agent_response}")
        
        # Check if a payment plan was proposed
        payment_plan_proposed = False
        if "[PAYMENT_PLAN:" in agent_response:
            # Extract the payment plan details
            payment_plan_text = agent_response[agent_response.find("[PAYMENT_PLAN:"):].split("]")[0] + "]"
            # Remove the payment plan marker from the response
            agent_response = agent_response.replace(payment_plan_text, "").strip()
            
            # Parse the payment plan details
            payment_details = payment_plan_text.replace("[PAYMENT_PLAN:", "").replace("]", "").split(",")
            if len(payment_details) >= 4:
                proposed_plan = {
                    "total_amount": payment_details[0].strip(),
                    "frequency": payment_details[1].strip(),
                    "amount_per_payment": payment_details[2].strip(),
                    "start_date": payment_details[3].strip(),
                    "proposed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                user_data[session_id]['proposed_payment_arrangement'] = proposed_plan
                payment_plan_proposed = True
                print(f"Payment plan proposed: {proposed_plan}")
                
                # Add a confirmation request to the response
                agent_response += f" To confirm, you'll pay {proposed_plan['amount_per_payment']} {proposed_plan['frequency']} starting {proposed_plan['start_date']} for a total of {proposed_plan['total_amount']}. Is that correct? Please say yes or no."
    except Exception as e:
        print(f"Error getting response from OpenAI: {str(e)}")
        agent_response = "I'm sorry, I'm having trouble understanding. Could you please repeat that?"
        payment_plan_proposed = False
    
    # Track the agent's response in conversation history
    user_data[session_id]['conversation_history'].append({
        'role': 'agent',
        'text': agent_response,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    # Create TwiML response with improved Gather parameters
    gather = Gather(
        input='speech', 
        action=f'/handle-response?session_id={session_id}&attempt=0&awaiting_confirmation={"true" if payment_plan_proposed else "false"}',
        timeout=7,
        speechTimeout='auto',
        language='en-US'
    )
    gather.say(agent_response)
    response.append(gather)
    
    # Add a fallback if no input is received (this will only trigger if the Gather times out)
    response.say("I didn't hear a response. Let me try again.")
    
    print("TwiML response generated for conversation")
    return str(response)

# Handle call status callbacks
@app.route("/call-status", methods=['GET', 'POST'])
def call_status():
    session_id = request.args.get('session_id')
    call_status = request.values.get('CallStatus')
    call_duration = request.values.get('CallDuration', '0')
    
    print(f"Call status update for session {session_id}: {call_status}, duration: {call_duration}s")
    
    if session_id in user_data and call_status == 'completed':
        # Update the patient profile with call information
        user = user_data[session_id]
        
        # Generate a call summary using GPT
        try:
            conversation_text = ""
            for exchange in user.get('conversation_history', []):
                conversation_text += f"{exchange['role'].capitalize()}: {exchange['text']}\n"
            
            summary_prompt = f"""
            Please summarize the following conversation between a medical billing agent and a patient.
            Focus on:
            1. Key points discussed
            2. Any payment arrangements made
            3. Next steps agreed upon
            
            Conversation:
            {conversation_text}
            
            Provide a concise summary (3-5 sentences).
            """
            
            summary_response = openai.chat.completions.create(
                model="gpt-3.5-turbo",  # Using a smaller model for summaries
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes conversations."},
                    {"role": "user", "content": summary_prompt}
                ],
                max_tokens=150,
                temperature=0.5
            )
            
            call_summary = summary_response.choices[0].message.content
            
            # Update patient info with call summary and payment plan
            user['patient_info']['last_call_summary'] = call_summary
            
            if user.get('payment_arrangement'):
                user['patient_info']['payment_plan'] = user['payment_arrangement']
            
            # Add to call history
            call_record = {
                'date': user.get('call_start_time', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                'duration': f"{call_duration} seconds",
                'summary': call_summary,
                'payment_arrangement': user.get('payment_arrangement')
            }
            
            if 'call_history' not in user['patient_info']:
                user['patient_info']['call_history'] = []
                
            user['patient_info']['call_history'].append(call_record)
            
            # Save the updated user data to file
            save_user_data(session_id, user)
            
            print(f"Updated and saved patient profile with call summary and payment information")
        except Exception as e:
            print(f"Error generating call summary: {str(e)}")
    
    return "OK"

# Simple route for testing that the server is up
@app.route("/test", methods=["GET"])
def test():
    return "Bargain Medical Billing System is running!"

# Add these new functions after extract_text_from_pdf()
def save_user_data(session_id, data):
    try:
        # Create data directory if it doesn't exist
        data_dir = 'data'
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # Save to a JSON file
        file_path = os.path.join(data_dir, f'patient_{session_id}.json')
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"Saved user data to {file_path}")
    except Exception as e:
        print(f"Error saving user data: {str(e)}")

def load_user_data(session_id):
    """Load user data from JSON file"""
    try:
        filename = f"patient_{session_id}.json"
        filepath = os.path.join(DATA_FOLDER, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading user data: {str(e)}")
    return None

# API endpoint to get patient data
@app.route("/api/patient/<session_id>", methods=["GET"])
def get_patient_data(session_id):
    # First check if the data is in memory
    if session_id in user_data:
        return jsonify(user_data[session_id])
    
    # If not in memory, try to load from file
    try:
        file_path = os.path.join('data', f'patient_{session_id}.json')
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Store back in memory for future access
                user_data[session_id] = data
                return jsonify(data)
    except Exception as e:
        print(f"Error loading patient data: {str(e)}")
    
    return jsonify({"error": "Patient not found"}), 404

# Serve React app
@app.route("/react/<path:path>")
def serve_react_files(path):
    return send_from_directory('static/react', path)

# Serve React app for profile
@app.route("/profile-react/<session_id>")
def profile_react(session_id):
    return send_from_directory('static/react', 'index.html')

# Redirect old profile URLs to React app
@app.route("/profile/<session_id>")
def profile_redirect(session_id):
    return redirect(f"/profile-react/{session_id}")

@app.route("/api/call-status/<session_id>", methods=["GET"])
def check_call_status(session_id):
    # Check if the session exists
    if session_id not in user_data:
        # Try to load from file
        try:
            file_path = os.path.join('data', f'patient_{session_id}.json')
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    user_data[session_id] = json.load(f)
        except Exception as e:
            print(f"Error loading patient data: {str(e)}")
            return jsonify({"error": "Patient not found", "call_completed": False}), 404
    
    # Get the call SID
    call_sid = user_data[session_id].get('call_sid')
    
    if not call_sid:
        return jsonify({"call_completed": False})
    
    try:
        # Check call status from Twilio
        call = twilio_client.calls(call_sid).fetch()
        call_completed = call.status in ['completed', 'failed', 'canceled', 'busy', 'no-answer']
        
        return jsonify({
            "call_completed": call_completed,
            "call_status": call.status
        })
    except Exception as e:
        print(f"Error checking call status: {str(e)}")
        # If we can't check with Twilio, assume it's completed after 3 minutes
        call_start_time = user_data[session_id].get('call_start_time')
        if call_start_time:
            try:
                start_time = datetime.strptime(call_start_time, "%Y-%m-%d %H:%M:%S")
                time_elapsed = (datetime.now() - start_time).total_seconds()
                if time_elapsed > 180:  # 3 minutes
                    return jsonify({"call_completed": True, "call_status": "assumed_completed"})
            except:
                pass
        
        return jsonify({"call_completed": False, "call_status": "unknown"})

if __name__ == "__main__":
    app.run(debug=True, port=8080)