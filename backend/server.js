import express from 'express'
import cors from 'cors'
import dotenv from 'dotenv'
import { body, validationResult } from 'express-validator'
import supabase from './supabaseClient.js'
import axios from 'axios'
import gmailService from './gmailService.js'

// Load environment variables
dotenv.config()

const app = express()
const PORT = process.env.PORT || 8000
const GMAIL_AGENT_API_URL = process.env.GMAIL_AGENT_API_URL || 'http://localhost:5000/api'
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:5173'

// Google OAuth configuration
const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID
const GOOGLE_CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET
const GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
const GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'

// Middleware
app.use(cors())
app.use(express.json())

// Validation middleware
const validateUserData = [
  body('Name').trim().notEmpty().withMessage('Name is required'),
  body('Gmail_Account')
    .trim()
    .notEmpty()
    .withMessage('Email is required')
    .isEmail()
    .withMessage('Invalid email format'),
  body('Phone_Number')
    .trim()
    .notEmpty()
    .withMessage('Phone number is required')
    .matches(/^[+]?[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6}$/)
    .withMessage('Invalid phone number format'),
]

// Routes
app.get('/api/health', (req, res) => {
  res.status(200).json({ status: 'ok', message: 'Server is running' })
})

// Create a new user
app.post('/api/users', validateUserData, async (req, res) => {
  // Check for validation errors
  const errors = validationResult(req)
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() })
  }

  try {
    const { Name, Gmail_Account, Phone_Number } = req.body

    // Insert data into Supabase
    const { data, error } = await supabase
      .from('User Info')
      .insert([{ 
        Name,
        'Gmail Account': Gmail_Account, 
        'Phone Number': Phone_Number,
        'is_gmail_connected': false
      }])
      .select()

    if (error) {
      console.error('Supabase error:', error)
      return res.status(500).json({ 
        error: 'Failed to save user data',
        details: error.message 
      })
    }

    return res.status(201).json({ 
      message: 'User created successfully',
      user: data[0]
    })
  } catch (err) {
    console.error('Server error:', err)
    return res.status(500).json({ 
      error: 'Internal server error',
      details: err.message 
    })
  }
})

// Get Gmail authentication URL
app.get('/api/auth/gmail/url', async (req, res) => {
  try {
    const { user_id, redirect_uri = `${FRONTEND_URL}/auth/callback` } = req.query
    
    if (!user_id) {
      return res.status(400).json({
        error: 'User ID is required'
      })
    }
    
    if (!GOOGLE_CLIENT_ID) {
      return res.status(500).json({
        error: 'Google client ID is not configured'
      })
    }
    
    // Create a state parameter to include the user ID
    const state = Buffer.from(JSON.stringify({ user_id })).toString('base64')
    
    // Generate authorization URL
    const authUrl = new URL(GOOGLE_AUTH_URL)
    authUrl.searchParams.append('client_id', GOOGLE_CLIENT_ID)
    authUrl.searchParams.append('redirect_uri', redirect_uri)
    authUrl.searchParams.append('response_type', 'code')
    authUrl.searchParams.append('scope', 'https://mail.google.com/')
    authUrl.searchParams.append('access_type', 'offline')
    authUrl.searchParams.append('prompt', 'consent')
    authUrl.searchParams.append('state', state)
    
    return res.status(200).json({
      authUrl: authUrl.toString()
    })
  } catch (err) {
    console.error('Error generating auth URL:', err)
    return res.status(500).json({
      error: 'Failed to generate authorization URL',
      details: err.message
    })
  }
})

// Handle Gmail OAuth callback
app.post('/api/auth/gmail/callback', async (req, res) => {
  try {
    const { code, state, redirect_uri = `${FRONTEND_URL}/auth/callback` } = req.body
    
    if (!code || !state) {
      return res.status(400).json({
        error: 'Authorization code and state are required'
      })
    }
    
    if (!GOOGLE_CLIENT_ID || !GOOGLE_CLIENT_SECRET) {
      return res.status(500).json({
        error: 'Google OAuth credentials are not configured'
      })
    }
    
    // Decode state to get user ID
    let stateData
    try {
      stateData = JSON.parse(Buffer.from(state, 'base64').toString())
    } catch (err) {
      return res.status(400).json({
        error: 'Invalid state parameter'
      })
    }
    
    const { user_id } = stateData
    if (!user_id) {
      return res.status(400).json({
        error: 'User ID not found in state'
      })
    }
    
    // Exchange code for tokens
    const tokenResponse = await axios.post(GOOGLE_TOKEN_URL, {
      code,
      client_id: GOOGLE_CLIENT_ID,
      client_secret: GOOGLE_CLIENT_SECRET,
      redirect_uri,
      grant_type: 'authorization_code'
    })
    
    const { access_token, refresh_token, expires_in } = tokenResponse.data
    
    if (!access_token || !refresh_token) {
      return res.status(500).json({
        error: 'Failed to obtain access tokens'
      })
    }
    
    // Store tokens in Supabase
    const tokenData = {
      access_token,
      refresh_token,
      expires_at: new Date(Date.now() + expires_in * 1000).toISOString()
    }
    
    const { error } = await supabase
      .from('User Info')
      .update({
        oath_tokens: tokenData,
        is_gmail_connected: true
      })
      .eq('id', user_id)
    
    if (error) {
      console.error('Supabase update error:', error)
      return res.status(500).json({
        error: 'Failed to store OAuth tokens',
        details: error.message
      })
    }
    
    return res.status(200).json({
      success: true,
      message: 'Gmail account connected successfully'
    })
  } catch (err) {
    console.error('Error processing OAuth callback:', err)
    return res.status(500).json({
      error: 'Failed to process authorization callback',
      details: err.message
    })
  }
})

// Add this new endpoint to get user by ID
app.get('/api/users/:id', async (req, res) => {
  try {
    const userId = req.params.id;
    
    if (!userId) {
      return res.status(400).json({
        error: 'User ID is required'
      });
    }
    
    // Get user data from Supabase
    const { data, error } = await supabase
      .from('User Info')
      .select('*')
      .eq('id', userId)
      .single();
    
    if (error) {
      console.error('Error fetching user:', error);
      return res.status(404).json({
        error: 'User not found'
      });
    }
    
    return res.status(200).json({
      user: data
    });
  } catch (err) {
    console.error('Error fetching user:', err);
    return res.status(500).json({
      error: 'Failed to retrieve user data',
      details: err.message
    });
  }
});

// Get insurance-related emails
app.get('/api/emails/insurance', async (req, res) => {
  try {
    // Get user ID from query params
    const userId = req.query.user_id;
    
    if (!userId) {
      return res.status(400).json({
        error: 'User ID is required'
      });
    }
    
    // Check if user exists and has Gmail connected
    const { data, error } = await supabase
      .from('User Info')
      .select('is_gmail_connected')
      .eq('id', userId)
      .single();
    
    if (error || !data) {
      return res.status(404).json({
        error: 'User not found'
      });
    }
    
    if (!data.is_gmail_connected) {
      return res.status(400).json({
        error: 'Gmail account not connected for this user',
        needsConnection: true
      });
    }
    
    // Fetch insurance-related emails
    const emails = await gmailService.getInsuranceEmails(userId);
    
    return res.status(200).json({
      emails: emails
    });
  } catch (err) {
    console.error('Error fetching insurance emails:', err);
    return res.status(500).json({
      error: 'Failed to retrieve insurance emails',
      details: err.message
    });
  }
});

// Add a new endpoint to communicate with the Gmail Agent API
app.post('/api/agent/generate-response', async (req, res) => {
  try {
    const { email } = req.body;
    
    if (!email) {
      return res.status(400).json({
        error: 'Email data is required'
      });
    }
    
    // Call the Gmail Agent API to generate a response
    console.log(`Calling Gmail Agent API at ${GMAIL_AGENT_API_URL}/generate-response`);
    const response = await axios.post(`${GMAIL_AGENT_API_URL}/generate-response`, {
      email: email
    });
    
    return res.status(200).json({
      draft: response.data.response || response.data.draft || response.data
    });
  } catch (err) {
    console.error('Error calling Gmail Agent API:', err);
    return res.status(500).json({
      error: 'Failed to generate response from Gmail Agent',
      details: err.message
    });
  }
});

// Get draft response for an email
app.post('/api/emails/draft-response', async (req, res) => {
  try {
    const { email_id, user_id } = req.body;
    
    if (!email_id || !user_id) {
      return res.status(400).json({
        error: 'Email ID and User ID are required'
      });
    }
    
    // Generate draft response
    const draft = await gmailService.generateDraftResponse(email_id, user_id);
    
    return res.status(200).json({
      draft: draft
    });
  } catch (err) {
    console.error('Error generating draft response:', err);
    return res.status(500).json({
      error: 'Failed to generate draft response',
      details: err.message
    });
  }
});

// Send email response after user confirmation
app.post('/api/emails/send-response', async (req, res) => {
  try {
    const { email_id, response, user_id, thread_id } = req.body;
    
    if (!email_id || !response || !user_id || !thread_id) {
      return res.status(400).json({
        error: 'Email ID, User ID, Thread ID and response are required'
      });
    }
    
    // Send email response
    await gmailService.sendEmailResponse(user_id, thread_id, response);
    
    return res.status(200).json({
      success: true,
      message: 'Email response sent successfully'
    });
  } catch (err) {
    console.error('Error sending email response:', err);
    return res.status(500).json({
      error: 'Failed to send email response',
      details: err.message
    });
  }
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`)
}) 