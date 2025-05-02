import axios from 'axios';
import supabase from './supabaseClient.js';

// Refreshes the access token if expired
async function refreshAccessToken(userId, refreshToken, clientId, clientSecret) {
  try {
    const response = await axios.post('https://oauth2.googleapis.com/token', {
      client_id: clientId,
      client_secret: clientSecret,
      refresh_token: refreshToken,
      grant_type: 'refresh_token'
    });

    const { access_token, expires_in } = response.data;
    
    // Calculate new expiry time
    const expiresAt = new Date(Date.now() + (expires_in * 1000)).toISOString();
    
    // Update stored tokens in database
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

// Get valid access token
export async function getAccessToken(userId) {
  try {
    // Get user OAuth tokens from database
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
    
    // Check if token has expired or will expire in the next 5 minutes
    if (expiresAt <= new Date(Date.now() + 5 * 60 * 1000)) {
      console.log('Access token expired or about to expire, refreshing...');
      // Get client credentials from environment
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

// Get insurance-related emails
export async function getInsuranceEmails(userId) {
  try {
    const accessToken = await getAccessToken(userId);
    
    // Query for insurance-related emails
    const searchQuery = 'subject:(insurance OR claim OR policy OR coverage OR medical OR health OR benefits)';
    
    // Get list of messages that match the query
    const response = await axios.get('https://gmail.googleapis.com/gmail/v1/users/me/messages', {
      headers: {
        Authorization: `Bearer ${accessToken}`
      },
      params: {
        q: searchQuery,
        maxResults: 10
      }
    });
    
    if (!response.data.messages || response.data.messages.length === 0) {
      return [];
    }
    
    // Fetch details for each message
    const emails = [];
    for (const message of response.data.messages) {
      const emailData = await getEmailDetails(message.id, accessToken);
      emails.push(emailData);
    }
    
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
    
    // For now, call your existing Gmail agent logic
    // Later, integrate your Gmail_Agent system properly
    // This is a placeholder for the actual agent response generation
    const response = await axios.post('http://localhost:5000/api/generate-response', {
      email: emailDetails
    });
    
    return response.data.draft || await generateMockResponse(emailDetails);
  } catch (error) {
    console.error('Error generating draft response:', error);
    // Fallback to mock response if the agent is not available
    return generateMockResponse(emailDetails);
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

export default {
  getAccessToken,
  getInsuranceEmails,
  getEmailDetails,
  generateDraftResponse,
  sendEmailResponse
}; 