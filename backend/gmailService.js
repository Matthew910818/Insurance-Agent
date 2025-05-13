import axios from 'axios';
import supabase from './supabaseClient.js';
import { google } from 'googleapis';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { promises as fs } from 'fs';
import { execSync } from 'child_process';

// For running the agent
import { fileURLToPath as fileURLToPathESM } from 'url';
import { dirname as dirnameESM } from 'path';
import { join as joinESM } from 'path';

// Track if agent is initialized
let agentInitialized = false;
let agentGraph = null;

// Import Gmail adapter
import { getGmailService, getEmailBody, getOrCreateLabel } from './gmail_agent/utils/gmailAdapter.js';

async function refreshAccessToken(userId, refreshToken, clientId, clientSecret) {
  try {
    const response = await axios.post('https://oauth2.googleapis.com/token', {
      client_id: clientId,
      client_secret: clientSecret,
      refresh_token: refreshToken,
      grant_type: 'refresh_token'
    });

    const { access_token, expires_in } = response.data;
    const expiresAt = new Date(Date.now() + (expires_in * 1000)).toISOString();
    
    const { error } = await supabase
      .from('User Info')
      .update({
        oath_tokens: {
          access_token,
          refresh_token: refreshToken,
          expires_at: expiresAt
        }
      })
      .eq('id', userId);
    
    if (error) {
      console.error('Error updating tokens in database:', error);
      throw new Error('Failed to update tokens');
    }
    
    return access_token;
  } catch (error) {
    console.error('Error refreshing access token:', error);
    throw new Error('Failed to refresh access token');
  }
}

export async function getAccessToken(userId) {
  try {
    const { data, error } = await supabase
      .from('User Info')
      .select('oath_tokens')
      .eq('id', userId)
      .single();
    
    if (error || !data || !data.oath_tokens) {
      throw new Error('User not found or OAuth tokens not available');
    }
    
    const tokens = data.oath_tokens;
    const expiresAt = new Date(tokens.expires_at);
    

    if (expiresAt <= new Date(Date.now() + 5 * 60 * 1000)) {
      console.log('Access token expired or about to expire, refreshing...');
      const clientId = process.env.GOOGLE_CLIENT_ID;
      const clientSecret = process.env.GOOGLE_CLIENT_SECRET;
      
      return await refreshAccessToken(userId, tokens.refresh_token, clientId, clientSecret);
    }
    
    return tokens.access_token;
  } catch (error) {
    console.error('Error getting access token:', error);
    throw error;
  }
}

export async function getInsuranceEmails(userId) {
  try {
    const accessToken = await getAccessToken(userId);
    
    const response = await axios.get('https://gmail.googleapis.com/gmail/v1/users/me/messages', {
      headers: {
        Authorization: `Bearer ${accessToken}`
      },
      params: {
        maxResults: 20
      }
    });
    
    const messages = response.data.messages || [];
    const emailPromises = messages.map(async (message) => {
      const details = await getEmailDetails(message.id, accessToken);
      return details;
    });
    
    const emails = await Promise.all(emailPromises);
    return emails;
  } catch (error) {
    console.error('Error fetching insurance emails:', error);
    throw error;
  }
}

// Get details for a specific email
export async function getEmailDetails(messageId, accessToken) {
  try {
    const response = await axios.get(`https://gmail.googleapis.com/gmail/v1/users/me/messages/${messageId}`, {
      headers: {
        Authorization: `Bearer ${accessToken}`
      },
      params: {
        format: 'full'
      }
    });
    
    const message = response.data;
    const headers = message.payload.headers;
    const subject = headers.find(h => h.name.toLowerCase() === 'subject')?.value || 'No Subject';
    const from = headers.find(h => h.name.toLowerCase() === 'from')?.value || '';
    const date = headers.find(h => h.name.toLowerCase() === 'date')?.value || '';
    
    // Extract body content
    let body = '';
    
    // Function to extract text from parts
    function extractTextFromParts(parts) {
      for (const part of parts) {
        if (part.mimeType === 'text/plain' && part.body.data) {
          body += Buffer.from(part.body.data, 'base64').toString('utf-8');
        } else if (part.parts) {
          extractTextFromParts(part.parts);
        }
      }
    }
    
    // Check for body in different places
    if (message.payload.body && message.payload.body.data) {
      body = Buffer.from(message.payload.body.data, 'base64').toString('utf-8');
    } else if (message.payload.parts) {
      extractTextFromParts(message.payload.parts);
    }
    
    return {
      id: message.id,
      threadId: message.threadId,
      sender: from,
      subject,
      date,
      snippet: message.snippet || '',
      body
    };
  } catch (error) {
    console.error(`Error fetching email details for message ${messageId}:`, error);
    throw error;
  }
}

// Generate a response draft for an insurance email
export async function generateDraftResponse(emailId, userId) {
  try {
    const accessToken = await getAccessToken(userId);
    const emailDetails = await getEmailDetails(emailId, accessToken);
    
    // Initialize agent if not already initialized
    if (!agentInitialized) {
      await initializeAgent();
    }
    
    // Prepare email data for agent
    const emailForAgent = {
      id: emailDetails.id,
      threadId: emailDetails.threadId,
      payload: {
        headers: [
          { name: 'From', value: emailDetails.sender },
          { name: 'Subject', value: emailDetails.subject },
          { name: 'Date', value: emailDetails.date }
        ],
        body: { data: Buffer.from(emailDetails.body).toString('base64') }
      }
    };
    
    // Run the agent workflow
    console.log("Starting Gmail Agent workflow for email:", emailDetails.subject);
    
    const initialState = {
      initialized: true,
      new_email: emailForAgent,
      processed_email_ids: [emailDetails.id],
      continue_polling: false
    };
    
    // Using dynamic import for ESM compatibility with the agent
    const { default: runAgentWorkflow } = await import('./gmail_agent/runAgent.js');
    const result = await runAgentWorkflow(initialState, accessToken);
    
    // Extract the generated response from agent result
    const draftResponse = result.llm_output || "The agent was unable to generate a response.";
    
    return {
      subject: `Re: ${emailDetails.subject}`,
      body: draftResponse,
      to: emailDetails.sender,
      threadId: emailDetails.threadId,
      originalEmailId: emailDetails.id
    };
  } catch (error) {
    console.error('Error generating draft response:', error);
    throw error;
  }
}

// Initialize the agent
async function initializeAgent() {
  try {
    console.log("Initializing Gmail Agent...");
    
    // Create runAgent.js file if it doesn't exist
    const __filename = fileURLToPath(import.meta.url);
    const __dirname = dirname(__filename);
    const runAgentPath = join(__dirname, 'gmail_agent', 'runAgent.js');
    
    // Check if necessary files exist and create directory structure if needed
    try {
      await fs.mkdir(join(__dirname, 'gmail_agent'), { recursive: true });
      await fs.mkdir(join(__dirname, 'gmail_agent', 'utils'), { recursive: true });
    } catch (err) {
      console.log("Directories already exist:", err.message);
    }
    
    // Update utils/nodes.js to use the access token from global space if it exists
    const nodesPath = join(__dirname, 'gmail_agent', 'utils', 'nodes.js');
    try {
      const nodesExists = await fs.access(nodesPath).then(() => true).catch(() => false);
      
      if (nodesExists) {
        const nodesContent = await fs.readFile(nodesPath, 'utf8');
        const updatedNodesContent = nodesContent.replace(
          /const service = getGmailService\(\)/g, 
          'const service = getGmailService(global.gmailAccessToken)'
        );
        await fs.writeFile(nodesPath, updatedNodesContent);
      }
    } catch (err) {
      console.log("Could not update nodes.js, will be created by installation process:", err.message);
    }
    
    // Install required packages
    console.log("Installing required packages for Gmail Agent...");
    
    try {
      execSync('cd ' + join(__dirname, 'gmail_agent') + ' && npm install --legacy-peer-deps', { stdio: 'inherit' });
      console.log("Packages installed successfully");
    } catch (error) {
      console.error("Failed to install packages:", error);
      throw new Error("Failed to install required packages for Gmail Agent");
    }
    
    agentInitialized = true;
    console.log("Gmail Agent initialized successfully");
  } catch (error) {
    console.error("Error initializing agent:", error);
    throw error;
  }
}

// Temporary mock response generator
function generateMockResponse(email) {
  return `Dear Insurance Provider,

Thank you for your message regarding ${email.subject}. I am writing to address several concerns with this matter.

POLICY DETAILS
Based on my policy, I believe this should be covered under my current plan. According to my documentation, these services are included in my coverage.

REQUEST FOR CLARIFICATION
I would appreciate additional information about the specific details mentioned in your email. If there are any forms or documentation needed from my side, please let me know.

I would appreciate a written response within 30 days, as required by state insurance regulations. If you have any questions, please contact me directly.

Thank you for your prompt attention to this matter.

Sincerely,
[Your Name]`;
}

// Send an email response
export async function sendEmailResponse(userId, threadId, message) {
  try {
    const accessToken = await getAccessToken(userId);
    
    // Create email in RFC 2822 format
    const email = [
      'Content-Type: text/plain; charset="UTF-8"',
      'MIME-Version: 1.0',
      'Content-Transfer-Encoding: 7bit',
      'to: recipient@example.com', // Should be extracted from the original email
      'subject: Re: Insurance Claim',
      '',
      message
    ].join('\n');
    
    // Encode the email to base64url format
    const encodedEmail = Buffer.from(email).toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');
    
    // Send the email
    await axios.post(`https://gmail.googleapis.com/gmail/v1/users/me/messages/send`, {
      raw: encodedEmail,
      threadId: threadId
    }, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    return true;
  } catch (error) {
    console.error('Error sending email response:', error);
    throw error;
  }
}

// Function to initialize the Gmail service adapter
function initializeGmailService(accessToken) {
  // Store the access token in global space for the agent to use
  global.gmailAccessToken = accessToken;
  return getGmailService(accessToken);
}

export default {
  getAccessToken,
  getInsuranceEmails,
  getEmailDetails,
  generateDraftResponse,
  sendEmailResponse,
  initializeGmailService
}; 