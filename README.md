# Gmail Agent with Email Response Review UI

A web application that connects to Gmail accounts, identifies insurance-related emails, and generates professional responses that users can review before sending.

## Project Structure

- **Frontend**: React application deployed on Vercel
  - URL: [scaling-doctor.vercel.app](https://scaling-doctor.vercel.app)
  
- **Backend**: Express API deployed on Render
  - URL: [scaling-doctor.onrender.com](https://scaling-doctor.onrender.com)
  
- **Database**: Supabase for user data and OAuth token storage

## Features

- User registration and account management
- Gmail account authentication
- Insurance email identification
- AI-generated response drafts
- Pre-send review interface

## Setup Instructions

### Prerequisites

- Node.js (v16+)
- npm or yarn
- Google Cloud Platform account

### Backend Setup

1. Clone the repository
2. Navigate to the backend directory: `cd backend`
3. Install dependencies: `npm install`
4. Create a `.env` file with the following variables:
   ```
   PORT=8000
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   FRONTEND_URL=https://scaling-doctor.vercel.app
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   ```
5. Start the server: `npm run dev`

### Frontend Setup

1. Navigate to the frontend directory: `cd frontend`
2. Install dependencies: `npm install`
3. Create a `.env` file with the following variables:
   ```
   VITE_API_URL=https://scaling-doctor.onrender.com/api
   ```
4. Start the development server: `npm run dev`

### Gmail OAuth Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project 
3. Navigate to APIs & Services > Credentials
4. Configure the OAuth consent screen:
   - Add "mail.google.com" to the scopes
   - Add your domain as an authorized domain
5. Create OAuth client ID credentials:
   - Application type: Web application
   - Authorized JavaScript origins: 
     - https://scaling-doctor.vercel.app
     - http://localhost:5173 (for development)
   - Authorized redirect URIs:
     - https://scaling-doctor.vercel.app/auth/callback
     - http://localhost:5173/auth/callback (for development)
6. Copy the Client ID and Client Secret to your backend `.env` file

### Database Setup

1. Create a Supabase project
2. Create a `User Info` table with the following columns:
   - `id` (int8, primary key)
   - `created_at` (timestamp, default: now())
   - `Name` (text)
   - `Gmail Account` (text)
   - `Phone Number` (text)
   - `is_gmail_connected` (boolean, default: false)
   - `oath_tokens` (jsonb)
3. Get your Supabase URL and anon key from the API settings
4. Add these credentials to your backend `.env` file

## Deployment

### Frontend (Vercel)

1. Connect your GitHub repository to Vercel
2. Set the following environment variables:
   - `VITE_API_URL=https://scaling-doctor.onrender.com/api`
3. Deploy the frontend directory

### Backend (Render)

1. Connect your GitHub repository to Render
2. Set the following environment variables:
   - `PORT=8000`
   - `SUPABASE_URL=your_supabase_url`
   - `SUPABASE_KEY=your_supabase_anon_key`
   - `FRONTEND_URL=https://scaling-doctor.vercel.app`
   - `GOOGLE_CLIENT_ID=your_google_client_id`
   - `GOOGLE_CLIENT_SECRET=your_google_client_secret`
3. Deploy the backend directory

## Usage

1. Register with your name, Gmail address, and phone number
2. Connect your Gmail account by clicking the "Connect Gmail Account" button
3. After authentication, you'll be redirected to the Insurance Emails page
4. Select an email to view the AI-generated draft response
5. Review and edit the draft as needed
6. Send the response when you're satisfied with it 