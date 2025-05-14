import axios from 'axios';
import supabase from './supabaseClient.js';
import { google } from 'googleapis';

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
    let body = '';
    
    function extractTextFromParts(parts) {
      for (const part of parts) {
        if (part.mimeType === 'text/plain' && part.body.data) {
          body += Buffer.from(part.body.data, 'base64').toString('utf-8');
        } else if (part.parts) {
          extractTextFromParts(part.parts);
        }
      }
    }
    
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

export async function generateDraftResponse(emailId, userId) {
  try {
    const accessToken = await getAccessToken(userId);
    const emailDetails = await getEmailDetails(emailId, accessToken);
    
    const emailForAgent = {
      email: {
        subject: emailDetails.subject,
        body: emailDetails.body,
        sender: emailDetails.sender,
        id: emailDetails.id,
        threadId: emailDetails.threadId
      }
    };
    
    console.log("Calling Gmail Agent API for email:", emailDetails.subject);
    const GMAIL_AGENT_API_URL = process.env.GMAIL_AGENT_API_URL || 'http://localhost:10000';
    console.log(`Sending request to ${GMAIL_AGENT_API_URL}/generate-response`);
    const response = await axios.post(`${GMAIL_AGENT_API_URL}/generate-response`, emailForAgent);
    console.log("Raw response from Gmail Agent:", JSON.stringify(response.data).substring(0, 200));
    let draftResponse;
    
    if (typeof response.data === 'string') {
      draftResponse = response.data;
    } else if (response.data && response.data.draft) {
      draftResponse = response.data.draft;
    } else if (response.data && response.data.response) {
      draftResponse = response.data.response;
    } else if (response.data && typeof response.data === 'object') {
      console.log("Unexpected response format from agent:", JSON.stringify(response.data));
      draftResponse = JSON.stringify(response.data);
    } else {
      throw new Error('Invalid or empty response from Gmail Agent API');
    }
    
    return draftResponse;
  } catch (error) {
    console.error('Error generating draft response:', error);
    console.error('Error details:', error.response?.data || error.message);
    
    return "API call failed...";
  }
}

export async function sendEmailResponse(userId, threadId, message) {
  try {
    const accessToken = await getAccessToken(userId);
    
    const email = [
      'Content-Type: text/plain; charset="UTF-8"',
      'MIME-Version: 1.0',
      'Content-Transfer-Encoding: 7bit',
      'to: recipient@example.com',
      'subject: Re: Insurance Claim',
      '',
      message
    ].join('\n');
    
    const encodedEmail = Buffer.from(email).toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');
    
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