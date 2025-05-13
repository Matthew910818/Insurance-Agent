import axios from 'axios';
import supabase from './supabaseClient.js';
import { google } from 'googleapis';

// Function to refresh OAuth2 access token
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

// Get access token for a user
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

// Get all emails for a user
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
    
    // Prepare email data for the Python Gmail Agent API
    const emailForAgent = {
      email: {
        subject: emailDetails.subject,
        body: emailDetails.body,
        sender: emailDetails.sender,
        id: emailDetails.id,
        threadId: emailDetails.threadId
      }
    };
    
    // Call the external Python Gmail Agent API
    console.log("Calling Gmail Agent API for email:", emailDetails.subject);
    
    // Get the API URL from environment variables or use default
    const GMAIL_AGENT_API_URL = process.env.GMAIL_AGENT_API_URL || 'http://localhost:5000/api';
    
    // Call the external Python Gmail Agent service
    const response = await axios.post(`${GMAIL_AGENT_API_URL}/generate-response`, emailForAgent);
    
    // Extract the generated response
    if (!response.data || !response.data.response) {
      throw new Error('Invalid response from Gmail Agent API');
    }
    
    const draftResponse = response.data.response;
    
    return {
      subject: `Re: ${emailDetails.subject}`,
      body: draftResponse,
      to: emailDetails.sender,
      threadId: emailDetails.threadId,
      originalEmailId: emailDetails.id
    };
  } catch (error) {
    console.error('Error generating draft response:', error);
    
    // Fallback to a generic response if the API call fails
    return {
      subject: `Re: Regarding your inquiry`,
      body: "Thank you for your email. We're currently processing your request and will get back to you shortly with a more detailed response.\n\nBest regards,\nYour Insurance Team",
      to: "recipient@example.com",
      threadId: null,
      originalEmailId: emailId
    };
  }
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

export default {
  getAccessToken,
  getInsuranceEmails,
  getEmailDetails,
  generateDraftResponse,
  sendEmailResponse
}; 