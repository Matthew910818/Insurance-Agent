// Gmail adapter for the LangGraph agent
import { google } from 'googleapis';

/**
 * Initialize the Gmail service with the provided access token
 * @param {string} accessToken - OAuth2 Access Token
 * @returns {Object} Gmail service instance
 */
export function getGmailService(accessToken) {
  if (!accessToken) {
    console.error("No access token provided to getGmailService");
    return null;
  }
  
  try {
    const auth = new google.auth.OAuth2();
    auth.setCredentials({ access_token: accessToken });
    
    const gmail = google.gmail({
      version: 'v1',
      auth: auth
    });
    
    return gmail;
  } catch (error) {
    console.error("Error initializing Gmail service:", error);
    return null;
  }
}

/**
 * Extract the email body from Gmail message parts
 * @param {Object} payload - Gmail message payload
 * @returns {string} Extracted email body text
 */
export function getEmailBody(payload) {
  let body = '';
  
  const extractText = (part) => {
    if (part.mimeType === 'text/plain' && part.body && part.body.data) {
      body += Buffer.from(part.body.data, 'base64').toString('utf-8');
    } else if (part.parts && Array.isArray(part.parts)) {
      part.parts.forEach(extractText);
    }
  };
  
  if (payload.body && payload.body.data) {
    body = Buffer.from(payload.body.data, 'base64').toString('utf-8');
  } else if (payload.parts && Array.isArray(payload.parts)) {
    payload.parts.forEach(extractText);
  }
  
  return body;
}

/**
 * Get or create a Gmail label
 * @param {Object} service - Gmail service instance
 * @param {string} labelName - Name of the label to get or create
 * @returns {string} Label ID
 */
export async function getOrCreateLabel(service, labelName) {
  try {
    const res = await service.users.labels.list({ userId: 'me' });
    const labels = res.data.labels;
    
    const existingLabel = labels.find(label => label.name === labelName);
    if (existingLabel) {
      return existingLabel.id;
    }
    
    // Create label if it doesn't exist
    const newLabel = await service.users.labels.create({
      userId: 'me',
      requestBody: {
        name: labelName,
        labelListVisibility: 'labelShow',
        messageListVisibility: 'show'
      }
    });
    
    return newLabel.data.id;
  } catch (error) {
    console.error(`Error getting or creating label "${labelName}":`, error);
    throw error;
  }
} 