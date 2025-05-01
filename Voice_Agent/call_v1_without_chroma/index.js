import Fastify from 'fastify';
import WebSocket from 'ws';
import dotenv from 'dotenv';
import fastifyFormBody from '@fastify/formbody';
import fastifyWs from '@fastify/websocket';
import twilio from 'twilio';

dotenv.config();

// ================== ENV VALIDATION ===================
const { 
  OPENAI_API_KEY, 
  SERVER_URL, 
  TWILIO_PHONE, 
  TWILIO_ACCOUNT_SID,
  TWILIO_AUTH_TOKEN
} = process.env;

if (!OPENAI_API_KEY) {
  console.error('Missing OpenAI API key. Please set it in the .env file.');
  process.exit(1);
}

if (!SERVER_URL) {
  console.error('Missing SERVER_URL. Please set it in the .env file or env variables.');
  process.exit(1);
}

if (!TWILIO_PHONE || !TWILIO_ACCOUNT_SID || !TWILIO_AUTH_TOKEN) {
  console.error('Missing one or more Twilio environment variables. Check TWILIO_PHONE, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN.');
  process.exit(1);
}

// ================== FASTIFY INIT ===================
function build() {
  const fastify = Fastify({ trustProxy: true });
  return fastify;
}

async function start() {
  const IS_GOOGLE_CLOUD_RUN = process.env.K_SERVICE !== undefined;
  const port = process.env.PORT || 8080;
  const host = IS_GOOGLE_CLOUD_RUN ? "0.0.0.0" : undefined;

  try {
    const server = build();
    // We do the actual .listen() below
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
}

start();

const IS_GOOGLE_CLOUD_RUN = process.env.K_SERVICE !== undefined;
const PORT = process.env.PORT || 8080;
const host = IS_GOOGLE_CLOUD_RUN ? "0.0.0.0" : undefined;

const fastify = Fastify({ trustProxy: true });
fastify.register(fastifyFormBody); // Needed to parse Twilio's x-www-form-urlencoded POST body
fastify.register(fastifyWs);

// ================== CONSTANTS & MAPS ===================

const VOICE = 'alloy';

// Maps to track calls, instructions, and transcription
const activeCallInstructions = new Map();
const callStatuses = new Map();
const callInformation = new Map();

// ================== ROUTES ===================

// Root Route
fastify.get('/', async (request, reply) => {
  reply.send({ message: 'Twilio Media Stream Server is running!' });
});

// POST /create-call -> triggers a call
fastify.post('/create-call', async (request, reply) => {
  const { userPhone, instruction } = request.body;

  if (!userPhone || !instruction) {
    return reply.code(400).send({ error: 'Missing required fields' });
  }
  try {
    const result = await createCall(userPhone, instruction);
    return reply.send({ success: true, transcription: result.transcription });
  } catch (error) {
    console.error('Error creating call:', error);
    return reply.code(500).send({ error: 'Error creating call' });
  }
});

// ================== CREATE CALL FUNCTION ===================
async function createCall(userPhone, instruction) {
  if (!userPhone || !instruction) {
    throw new Error('Missing required arguments: userPhone and instruction are required');
  }

  const twilioClient = twilio(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN);
  const callDT = new Date().toISOString();

  // Store instruction & transcription data
  activeCallInstructions.set(callDT, instruction);
  callInformation.set(callDT, { dateTime: callDT, transcription: '' });
  console.log("Stored callDT:", callDT, "with instruction:", instruction);

  try {
    const call = await twilioClient.calls.create({
      to: userPhone,
      from: TWILIO_PHONE,
      url: `${SERVER_URL}/api/incoming-call?callDT=${encodeURIComponent(callDT)}`,
      record: true,
      statusCallbackEvent: ['initiated', 'ringing', 'answered', 'completed'],
      statusCallback: `${SERVER_URL}/api/status-callback`,
      statusCallbackMethod: 'POST',
      // Add these parameters to ensure proper call routing
      timeout: 30,  // Call timeout in seconds
      machineDetection: 'DetectMessageEnd',
      asyncAmd: true
    });

    callStatuses.set(call.sid, 'initiated');
    console.log(`Created call SID: ${call.sid}`);

    // Return a promise that resolves once the call completes
    return new Promise((resolve, reject) => {
      const checkCallStatus = setInterval(() => {
        const status = callStatuses.get(call.sid);
        console.log(`Checking call status: ${status} for SID: ${call.sid}`);
        
        if (status === 'completed' || status === 'failed' || status === 'busy' || status === 'no-answer') {
          clearInterval(checkCallStatus);
          if (status === 'completed') {
            const info = callInformation.get(callDT);
            resolve(info);
          } else {
            reject(new Error(`Call ended with status: ${status}`));
          }
        }
      }, 1000);

      // Add timeout to prevent hanging
      setTimeout(() => {
        clearInterval(checkCallStatus);
        reject(new Error('Call timed out'));
      }, 300000); // 5 minute timeout
    });
  } catch (error) {
    console.error('Error creating Twilio call:', error);
    throw error;
  }
}

// ================== /api/incoming-call ===================
fastify.all('/api/incoming-call', async (request, reply) => {
  try {
    const callDT = decodeURIComponent(request.query.callDT);
    console.log("Incoming callDT from Twilio:", callDT);

    const encodedCallDT = encodeURIComponent(callDT);
    
    // Simplified TwiML with minimal delay
    const twimlResponse = `<?xml version="1.0" encoding="UTF-8"?>
      <Response>
          <Connect>
              <Stream url="wss://${request.headers.host}/api/media-stream/${encodedCallDT}">
                  <Parameter name="callDT" value="${encodedCallDT}"/>
              </Stream>
          </Connect>
      </Response>`;

    reply.type('text/xml').send(twimlResponse);
  } catch (error) {
    console.error("Error in incoming-call handler:", error);
    reply.code(400).send("Bad Request");
  }
});

// ================== /api/media-stream/:callDT (WebSocket) ===================
fastify.register(async (fastify) => {
  fastify.get('/api/media-stream/:callDT', { websocket: true }, (connection, req) => {
      console.log('Client connected');

      let streamSid = null;
      let latestMediaTimestamp = 0;
      let lastAssistantItem = null;
      let markQueue = [];
      let responseStartTimestampTwilio = null;

      // Retrieve the param from the route
      let { callDT } = req.params;
      // decode it
      callDT = decodeURIComponent(callDT);

      console.log("Decoded callDT in /api/media-stream route:", callDT);
      const instruction = activeCallInstructions.get(callDT);

      console.log("Instruction found:", instruction);
      if (!instruction) {
        console.warn(`No instruction found for callDT: ${callDT}`);
      }

      // Connect to OpenAI Realtime API
      const openAiWs = new WebSocket(
        'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17',
        {
          headers: {
            Authorization: `Bearer ${OPENAI_API_KEY}`,
            "OpenAI-Beta": "realtime=v1"
          }
        }
      );

      const sendMark = (connection, streamSid) => {
        if (streamSid) {
            const markEvent = {
                event: 'mark',
                streamSid: streamSid,
                mark: { name: 'responsePart' }
            };
            connection.send(JSON.stringify(markEvent));
            markQueue.push('responsePart');
        }
    };


      const handleSpeechStartedEvent = () => {
        if (markQueue.length > 0 && responseStartTimestampTwilio != null) {
            const elapsedTime = latestMediaTimestamp - responseStartTimestampTwilio;
            
            if (lastAssistantItem) {
                const truncateEvent = {
                    type: 'conversation.item.truncate',
                    item_id: lastAssistantItem,
                    content_index: 0,
                    audio_end_ms: elapsedTime
                };
                console.log('Sending truncation event:', truncateEvent);
                openAiWs.send(JSON.stringify(truncateEvent));
            }

            // Send clear event to Twilio
            if (streamSid) {
                connection.send(JSON.stringify({
                    event: 'clear',
                    streamSid: streamSid
                }));
            }

            // Reset state
            markQueue = [];
            lastAssistantItem = null;
            responseStartTimestampTwilio = null;
        }
      };

      const sendSessionUpdate = () => {
        const sessionUpdate = {
          event_id: "event_123",
          type: 'session.update',
          session: {
            modalities: ["text", "audio"],
            instructions: instruction, // Retaining the original instruction
            voice: "sage",
            input_audio_format: "g711_ulaw",
            output_audio_format: "g711_ulaw",
            input_audio_transcription: {
              model: 'whisper-1' // Retaining the original input audio transcription model
            },
            turn_detection: {
              type: "server_vad",
              threshold: 0.5,
              prefix_padding_ms: 300,
              silence_duration_ms: 500,
              create_response: true
            },
            temperature: 0.8,
            max_response_output_tokens: "inf"
          }
        };
        openAiWs.send(JSON.stringify(sessionUpdate));
      };

      const sendInitialConversationItem = () => {
        const initialConversationItem = {
          type: "conversation.item.create",
          item: {
            type: "message",
            role: "user",
            content: [
              {
                type: "input_text",
                text: "Greet the user."
              }
            ]
          }
        };
        openAiWs.send(JSON.stringify(initialConversationItem));
        openAiWs.send(JSON.stringify({ type: "response.create" }));
      };

      // OpenAI WebSocket opened
      openAiWs.on('open', async () => {
        console.log('Connected to the OpenAI Realtime API');
        setTimeout(sendSessionUpdate, 250);
        //console.log(instruction);
        setTimeout(sendInitialConversationItem, 250);
      });

      // Messages from OpenAI
      openAiWs.on('message', (data) => {
        try {
          const response = JSON.parse(data);
            
          // If user speech is transcribed
          if (response.type === 'conversation.item.input_audio_transcription.completed') {
            const info = callInformation.get(callDT);
            if (info) {
              const cleanedTranscript = response.transcript.replace(/\n/g, '');
              info.transcription += `User: ${cleanedTranscript} | `;
            }
          }

          // If AI speech is transcribed
          if (response.type === 'response.audio_transcript.done') {
            const info = callInformation.get(callDT);
            if (info) {
              const cleanedTranscript = response.transcript.replace(/\n/g, '');
              info.transcription += `AI: ${cleanedTranscript} | `;
            }
          }

          if (response.type === 'input_audio_buffer.speech_started') {
            handleSpeechStartedEvent();
          }

          // If we get audio delta from AI, forward to Twilio
          if (response.type === 'response.audio.delta' && response.delta) {
            const audioDelta = {
              event: 'media',
              streamSid: streamSid,
              media: { payload: response.delta }
            };
            connection.send(JSON.stringify(audioDelta));

            // Set start timestamp for new response
            if (!responseStartTimestampTwilio) {
              responseStartTimestampTwilio = latestMediaTimestamp;
            }

            if (response.item_id) {
              lastAssistantItem = response.item_id;
            }
            
            sendMark(connection, streamSid);
          }
        } catch (error) {
          console.error('Error processing OpenAI message:', error, 'Raw message:', data);
        }
      });

      // Messages from Twilio
      connection.on('message', (message) => {
        try {
          const data = JSON.parse(message);
          switch (data.event) {
            case 'media':
              latestMediaTimestamp = data.media.timestamp;
              if (openAiWs.readyState === WebSocket.OPEN) {
                const audioAppend = {
                  type: 'input_audio_buffer.append',
                  audio: data.media.payload
                };
                openAiWs.send(JSON.stringify(audioAppend));
              }
              break;
            case 'start':
              streamSid = data.start.streamSid;
              console.log('Incoming stream has started', streamSid);
              // Reset timestamps on new stream
              responseStartTimestampTwilio = null;
              latestMediaTimestamp = 0;
              break;
            case 'mark':
              if (markQueue.length > 0) {
                markQueue.shift();
              }
              break;
            default:
              console.log('Received non-media event:', data.event);
          }
        } catch (error) {
          console.error('Error parsing message:', error, 'Message:', message);
        }
      });

      // Handle WebSocket close
      connection.on('close', () => {
        if (openAiWs.readyState === WebSocket.OPEN) {
          openAiWs.close();
        }
        console.log('Client disconnected.');
      });

      // Handle OpenAI WebSocket close/errors
      openAiWs.on('close', () => {
        console.log('Disconnected from the OpenAI Realtime API');
      });
      openAiWs.on('error', (error) => {
        console.error('Error in the OpenAI WebSocket:', error);
      });
  });
});

// ================== STATUS CALLBACKS ===================
fastify.post('/api/status-callback', async (request, reply) => {
  try {
    // Twilio sends x-www-form-urlencoded by default
    // Check what Twilio actually sends by logging:
    console.log("Twilio status-callback body:", request.body);

    const { CallSid, CallStatus } = request.body;
    if (!CallSid || !CallStatus) {
      console.error('Missing required fields in Twilio callback:', request.body);
      return reply.code(400).send({ error: 'CallSid and CallStatus are required' });
    }
    
    callStatuses.set(CallSid, CallStatus);
    console.log(`Call ${CallSid} status updated to: ${CallStatus}`);

    return reply.code(200).send();
  } catch (error) {
    console.error('Error in status-callback POST:', error);
    return reply.code(500).send({ error: 'Internal server error' });
  }
});



// (Optional) GET status-callback (debugging)
fastify.get('/api/status-callback', async (request, reply) => {
  try {
    const { callSid } = request.query;
    if (!callSid) {
      console.error('Missing callSid in GET request');
      return reply.code(400).send({ error: 'CallSid is required' });
    }
    const status = callStatuses.get(callSid);
    if (!status) {
      console.log(`No status found for callSid: ${callSid}`);
      return reply.code(404).send({ error: 'Call status not found' });
    }
    return reply.send({ status });
  } catch (error) {
    console.error('Error in status-callback GET:', error);
    return reply.code(500).send({ error: 'Internal server error' });
  }
});

// ================== START SERVER ===================
const address = await fastify.listen({ port: PORT, host: host });
console.log(`Listening on ${address}`);

// Optionally test via an immediate call creation
/*
(async () => {
  const result = await createCall('+17473347145', "You are a helpful and bubbly AI assistant who loves to chat about anything the user is interested about and is prepared to offer them facts. You have a penchant for dad jokes, owl jokes, and rickrolling – subtly. Always stay positive, but work in a joke when appropriate.");
  console.log(result.transcription); 
})();
*/