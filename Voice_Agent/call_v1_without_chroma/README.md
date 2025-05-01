TOOL_CALL -> the tool that can call users with an Open AI realtime voice assistant
Bryan Huang 2/4/25

API Endpoint:
POST /create-call
ex. userPhone = +17473347145
    instruction = "you are to engage in a rap battle with the user."
=> http://localhost:3000/create-call?userPhone=+17473347145&instruction=you are to engage in a rap battle with the user.




index.js:
createCall function:
- async function createCall(userPhone, instruction) {...}
  - userPhone is the target user's phone number
  - instruction is the initial prompt that is given to the AI voice assistant
- returns JSON: {datetime, transcription}
  - dateTime: the Date().toISOString() when the call was initiated.
  - transcription: string of the transcription of the conversation.
    - ex. "AI: Hey there! It's fantastic to see you! How can I brighten your day today? | User: Can you tell me a joke, please? | AI: Of course! Why did the scarecrow win an award? Because he was outstanding in his field! 🌾😄 |"
    - note transcription may not be exactly what AI voice responds to, and order of events may be misordered, but generally pretty close to on time.

call details
- the AI will speak first, greeting the user.
- the AI can be interrupted, depending on the speed of the connection
- conversation continues until user hangs up

status-callback
- Provides ability to send a GET request to SERVER_URL/api/status-callback in order to get status
- const response = await fetch(`${import.meta.env.VITE_API_URL}/api/status-callback?callSid=${callSid}`, { method: 'GET', headers: { 'Content-Type': 'application/json', } });
- currently console.logs the updates to status


TODO: 
- replace environment variable TWILIO_PHONE with our project's twilio account phone number. that's all there is to set up.
- allow AI to hang up?
