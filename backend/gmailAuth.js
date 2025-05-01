import { google } from 'googleapis';
import { OAuth2Client } from 'google-auth-library';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';
import dotenv from 'dotenv';

dotenv.config();

// Get the directory name of the current module
const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Path to the credentials and token files
const CREDENTIALS_PATH = process.env.GMAIL_CREDENTIALS_PATH || path.join(__dirname, '..', 'Gmail_Agent', 'my_agent', 'credentials.json');
const TOKEN_PATH = process.env.GMAIL_TOKEN_PATH || path.join(__dirname, '..', 'Gmail_Agent', 'my_agent', 'token.json');

// Gmail API scopes
const SCOPES = ['https://mail.google.com/'];

// Create OAuth2 client
let oauth2Client = null;

// Initialize OAuth client from credentials file
const initOAuth2Client = () => {
  try {
    if (!fs.existsSync(CREDENTIALS_PATH)) {
      console.error(`Credentials file not found at ${CREDENTIALS_PATH}`);
      return null;
    }

    const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
    const { client_secret, client_id, redirect_uris } = credentials.installed || credentials.web;
    
    // Create OAuth2 client
    oauth2Client = new OAuth2Client(
      client_id,
      client_secret,
      // Use the first redirect URI or a default one if not provided
      redirect_uris[0] || process.env.OAUTH_REDIRECT_URI || 'http://localhost:8000/api/auth/callback'
    );

    return oauth2Client;
  } catch (error) {
    console.error('Error initializing OAuth2 client:', error);
    return null;
  }
};

// Generate authentication URL
export const getAuthUrl = () => {
  if (!oauth2Client) {
    oauth2Client = initOAuth2Client();
    if (!oauth2Client) {
      throw new Error('Failed to initialize OAuth2 client');
    }
  }

  return oauth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: SCOPES,
    prompt: 'consent' // Force re-consent to get refresh token
  });
};

// Get tokens from code and save them
export const getTokensFromCode = async (code) => {
  if (!oauth2Client) {
    oauth2Client = initOAuth2Client();
    if (!oauth2Client) {
      throw new Error('Failed to initialize OAuth2 client');
    }
  }

  try {
    const { tokens } = await oauth2Client.getToken(code);
    oauth2Client.setCredentials(tokens);

    // Save tokens to file
    fs.writeFileSync(TOKEN_PATH, JSON.stringify(tokens));
    
    return tokens;
  } catch (error) {
    console.error('Error getting tokens:', error);
    throw error;
  }
};

// Save tokens for a specific user
export const saveUserTokens = async (userId, tokens, supabase) => {
  try {
    // Store tokens in Supabase
    const { data, error } = await supabase
      .from('User Info')
      .update({ 
        oauth_tokens: tokens,
        is_gmail_connected: true 
      })
      .eq('id', userId);

    if (error) {
      console.error('Error saving tokens to Supabase:', error);
      throw error;
    }

    return true;
  } catch (error) {
    console.error('Error saving user tokens:', error);
    throw error;
  }
};

// Run the Gmail Agent with the user's token
export const runGmailAgent = async (userId, supabase) => {
  try {
    // Get user data from Supabase
    const { data, error } = await supabase
      .from('User Info')
      .select('oauth_tokens, "Gmail Account"')
      .eq('id', userId)
      .single();

    if (error || !data) {
      console.error('Error fetching user data:', error);
      throw error || new Error('User not found');
    }

    // Check if user has OAuth tokens
    if (!data.oauth_tokens) {
      throw new Error('User does not have Gmail OAuth tokens');
    }

    // Save tokens to token.json file
    fs.writeFileSync(TOKEN_PATH, JSON.stringify(data.oauth_tokens));

    // Run the Gmail Agent as a child process
    console.log('Starting Gmail Agent for user:', userId);
    const agentProcess = spawn('python', [
      path.join(__dirname, '..', 'Gmail_Agent', 'my_agent', 'test_email.py')
    ], {
      env: {
        ...process.env,
        GMAIL_TOKEN_FILE: TOKEN_PATH,
        GMAIL_CLIENT_SECRETS: CREDENTIALS_PATH,
        USER_EMAIL: data['Gmail Account']
      }
    });

    agentProcess.stdout.on('data', (data) => {
      console.log(`Agent stdout: ${data}`);
    });

    agentProcess.stderr.on('data', (data) => {
      console.error(`Agent stderr: ${data}`);
    });

    agentProcess.on('close', (code) => {
      console.log(`Agent process exited with code ${code}`);
    });

    return { success: true, message: 'Gmail Agent started successfully' };
  } catch (error) {
    console.error('Error running Gmail Agent:', error);
    throw error;
  }
};

// Check if credentials and token files exist
export const checkGmailSetup = () => {
  const credentialsExist = fs.existsSync(CREDENTIALS_PATH);
  const tokenExist = fs.existsSync(TOKEN_PATH);
  
  return {
    credentialsExist,
    tokenExist,
    credentialsPath: CREDENTIALS_PATH,
    tokenPath: TOKEN_PATH
  };
};

export default {
  getAuthUrl,
  getTokensFromCode,
  saveUserTokens,
  runGmailAgent,
  checkGmailSetup
}; 