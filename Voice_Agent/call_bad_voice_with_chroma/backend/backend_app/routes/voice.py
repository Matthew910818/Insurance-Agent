# backend_app/routes/voice.py
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from backend_app.core.database import (
    get_student_by_phone,
    create_student_with_phone,
    update_conversation_history,
    update_full_name,
    query_by_prompt
)
from backend_app.agents.functions import function_definitions
import openai
import os
import json

router = APIRouter()

@router.post("/twilio/voice")
async def twilio_voice_handler(request: Request):
    return await voice_webhook(request)


@router.get("/debug/memory/{phone_number}")
def view_conversation_history(phone_number: str):
    record = get_student_by_phone(phone_number)
    if not record:
        return JSONResponse(content={"error": "User not found"}, status_code=404)

    return {
        "id": record.get("ids", ["unknown"])[0],
        "document": record.get("documents", [""])[0],
        "metadata": record.get("metadatas", [{}])[0],
    }


@router.post("/voice/incoming-call")
async def voice_webhook(request: Request):
    form = await request.form()
    phone_number = form.get("From")
    user_input = form.get("SpeechResult") or ""

    # Add simple conversation logging
    if user_input:
        print(f"[👤] User ({phone_number}): {user_input}")

    openai.api_key = os.getenv("OPENAI_API_KEY")

    # STEP 1: Get/create user
    profile = get_student_by_phone(phone_number)
    if not profile or not profile.get("documents"):
        create_student_with_phone(phone_number)
    profile = get_student_by_phone(phone_number)  # Refresh profile from DB

    # STEP 2: Get memory
    updated_profile = get_student_by_phone(phone_number)
    history_text = (updated_profile.get("documents", [""])[0])[:12000]  # Truncate long history
    metadata = updated_profile.get("metadatas", [{}])[0]
    full_name = metadata.get("full_name")

    # STEP 3: Generate first message if no input
    if not user_input:
        if full_name:
            gpt_reply = f"Hey {full_name}, how's everything going?"
        else:
            gpt_reply = "Hi! Before we get started, may I know your name?"
    else:
        # Initialize gpt_reply with a default value
        gpt_reply = None
        
        # STEP 4: Call GPT to extract info + maybe run function
        extraction_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract only important user information (e.g. Full name, goals, facts, preferences, identity) "
                        "from this input. Format as a bullet point list. Omit filler or small talk. "
                        "if the user ask you to be connected to someone, use the query_by_prompt function to find the user's profile."                        
                    )
                },
                {"role": "user", "content": user_input}
            ],
            functions=function_definitions,
            function_call="auto"
        )
        choice = extraction_response.choices[0]

        # STEP 4.5: Handle function call
        if choice.finish_reason == "function_call": #if the models thinks it needs to run a function
            func_name = choice.message["function_call"]["name"]
            raw_args = choice.message["function_call"]["arguments"]
            try:
                args = json.loads(raw_args)
            except Exception as e:
                print(f"[❌] Failed to parse tool args: {e}")
                args = {}
            # the functions 
            if func_name == "update_user_name": #if the function is to update the user's name
                full_name = args.get("full_name", "")
                if full_name and not metadata.get("full_name"):  # Only update if name not already set
                    update_full_name(phone_number, full_name)
                    print(f"[✅] Updated name to: {full_name}")
                else:
                    print("[ℹ️] Name already set or missing in args")

            if func_name == "query_by_prompt":
                prompt = args.get("prompt", "")
                if prompt:
                    matches = query_by_prompt(prompt, exclude_user_id=phone_number)
                    print(f"[🔍] Query results: {json.dumps(matches, indent=2)}")  # Debug log
                    
                    if matches and len(matches) > 0:
                        # Get the first (and only) result object
                        result = matches[0]
                        
                        # Format results for better LLM interpretation
                        formatted_results = []
                        for i in range(len(result["id"])):
                            if result["id"][i] != phone_number:  # Skip current user
                                formatted_results.append({
                                    "id": result["id"][i],
                                    "document": result["document"][i],
                                    "metadata": result["metadata"][i]
                                })
                        
                        # Let GPT interpret the results with more specific instructions
                        interpretation_response = openai.ChatCompletion.create(
                            model="gpt-4",
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                        "You are helping to match users based on their profiles. "
                                        "Given the search results and the user's specific request, find the MOST RELEVANT match. "
                                        "Pay special attention to educational background, work experience, and specific institutions mentioned. "
                                        "Prioritize exact matches for institutions and fields mentioned in the user's request. "
                                        "Return ONLY the full name of the best match, or empty string if no good match found."
                                    )
                                },
                                {
                                    "role": "user",
                                    "content": (
                                        f"User request: {prompt}\n\n"
                                        f"Search results: {json.dumps(formatted_results, indent=2)}"
                                    )
                                }
                            ]
                        )
                        
                        matched_name = interpretation_response.choices[0].message.content.strip()
                        print(f"[🤖] LLM interpreted match: {matched_name}")
                        
                        if matched_name and matched_name != "":
                            # Find the matched person's document to include relevant details
                            matched_doc = None
                            for i, metadata in enumerate(result["metadata"]):
                                if metadata.get("full_name") == matched_name:
                                    matched_doc = result["document"][i]
                                    break
                            
                            print(f"[✅] Match found: {matched_name}")
                            if matched_doc:
                                # Extract first line of their background for context
                                background = matched_doc.strip().split('\n')[0].replace('- ', '')
                                gpt_reply = f"I found someone you might connect with: {matched_name}, who is {background.lower()}"
                            else:
                                gpt_reply = f"I found someone you might connect with: {matched_name}."
                        else:
                            print("[❌] No valid matches found")
                            gpt_reply = "I looked around but couldn't find someone matching your specific criteria just yet."
                    else:
                        print("[❌] No matches returned from search")
                        gpt_reply = "I looked around but couldn't find someone just yet."
                else:
                    print("[❌] Prompt missing in function call args.")

        # STEP 5: Save only user's input info
        extracted_info = choice.message.get("content", "")
        if extracted_info:
            update_conversation_history(phone_number, extracted_info)

        # STEP 6: Generate reply to user if not already set by function calls
        if gpt_reply is None:
            chat_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You're a friendly buddy learning about the user's life, uniqueness, past work experience, goals, and preferences, what he is building, and what he is looking for. You remember the user's past responses and use them "
                            "to carry a meaningful, helpful conversation. Ask thoughtful follow-up questions"
                            "if you receive a gpt_reply from the function, use it as the reply to the user."
                        )
                    },
                    {"role": "system", "content": f"User memory:\n{history_text}"},
                    {"role": "user", "content": user_input}
                ]
            )
            gpt_reply = chat_response['choices'][0]['message']['content']

    # STEP 7: Twilio XML response
    twiml = f"""
    <Response>
        <Say>{gpt_reply}</Say>
        <Gather input="speech" action="/twilio/voice" method="POST" timeout="3" />
    </Response>
    """
    print(f"[🤖] Assistant: {gpt_reply}")
    return Response(content=twiml.strip(), media_type="application/xml")
