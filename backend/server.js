import express from 'express'
import cors from 'cors'
import dotenv from 'dotenv'
import { body, validationResult } from 'express-validator'
import supabase from './supabaseClient.js'

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
        'Phone Number': Phone_Number
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

// Start the server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`)
}) 