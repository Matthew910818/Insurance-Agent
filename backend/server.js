import express from 'express'
import cors from 'cors'
import dotenv from 'dotenv'
import { body, validationResult } from 'express-validator'
import supabase from './supabaseClient.js'
import gmailAuth from './gmailAuth.js'

// Load environment variables
dotenv.config()

const app = express()
const PORT = process.env.PORT || 8000

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
    .withMessage('Invalid email format')
    .matches(/@gmail\.com$/)
    .withMessage('Email must be a Gmail address'),
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
        is_gmail_connected: false
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

// Get Gmail OAuth URL
app.get('/api/auth/gmail', (req, res) => {
  try {
    // Check if Gmail setup is configured
    const setup = gmailAuth.checkGmailSetup();
    if (!setup.credentialsExist) {
      return res.status(500).json({
        error: 'Gmail API credentials not found',
        details: `Credentials file not found at ${setup.credentialsPath}`
      });
    }

    // Generate authentication URL
    const authUrl = gmailAuth.getAuthUrl();
    
    return res.status(200).json({
      auth_url: authUrl
    });
  } catch (err) {
    console.error('Error getting auth URL:', err);
    return res.status(500).json({
      error: 'Failed to generate authentication URL',
      details: err.message
    });
  }
});

// Handle OAuth callback
app.get('/api/auth/callback', async (req, res) => {
  const { code, state } = req.query;
  const userId = state; // The user ID should be passed in the state parameter

  if (!code) {
    return res.status(400).json({
      error: 'Missing authorization code',
      details: 'No code was received from Google OAuth'
    });
  }

  try {
    // Exchange code for tokens
    const tokens = await gmailAuth.getTokensFromCode(code);
    
    // If state contains user ID, save tokens to user record
    if (userId) {
      await gmailAuth.saveUserTokens(userId, tokens, supabase);
    }

    // Redirect to frontend success page
    return res.redirect(`${process.env.FRONTEND_URL || 'http://localhost:3000'}/auth-success`);
  } catch (err) {
    console.error('Error in OAuth callback:', err);
    return res.status(500).json({
      error: 'Authentication failed',
      details: err.message
    });
  }
});

// Run Gmail agent for a user
app.post('/api/run-agent/:userId', async (req, res) => {
  const { userId } = req.params;

  if (!userId) {
    return res.status(400).json({
      error: 'Missing user ID',
      details: 'User ID is required to run the Gmail agent'
    });
  }

  try {
    const result = await gmailAuth.runGmailAgent(userId, supabase);
    return res.status(200).json(result);
  } catch (err) {
    console.error('Error running Gmail agent:', err);
    return res.status(500).json({
      error: 'Failed to run Gmail agent',
      details: err.message
    });
  }
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`)
}) 