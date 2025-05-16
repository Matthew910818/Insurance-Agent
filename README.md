# Gmail Agent

A web application that connects to Gmail accounts, identifies insurance-related emails, and generates professional responses that users can review before sending.

## Project Structure

- **Frontend**: React application deployed on Vercel
  - URL: [https://insurance-agent-five.vercel.app](https://insurance-agent-five.vercel.app)
  
- **Backend**: Express API deployed on Render
  
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
   FRONTEND_URL=https://insurance-agent-five.vercel.app
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   ```
5. Start the server: `npm run dev`

### Frontend Setup

1. Navigate to the frontend directory: `cd frontend`
2. Install dependencies: `npm install`
3. Create a `.env` file with the following variables:
   ```
   VITE_API_URL=https://insurance-agent-lpe0.onrender.com
   ```
4. Start the development server: `npm run dev`


## Usage

1. Register with your name, Gmail address, and phone number
2. Connect your Gmail account by clicking the "Connect Gmail Account" button
3. After authentication, you'll be redirected to the Insurance Emails page
4. Select an email to view the AI-generated draft response
5. Review and edit the draft as needed
6. Send the response when you're satisfied with it 
