# Gmail Agent Frontend

This is the frontend for the Gmail Agent application, built with React and Vite.

## Setup

1. Clone the repository
2. Navigate to the frontend directory
3. Install dependencies:

```bash
npm install
```

4. Create a `.env` file in the root of the frontend directory with the following variables:

```
VITE_API_URL=http://localhost:8000/api
```

5. Start the development server:

```bash
npm run dev
```

## Supabase Configuration

To use the application, you need to set up a Supabase project:

1. Create a new project at [https://supabase.com](https://supabase.com)
2. Create a new table called `User Info` with the following columns:
   - `id` (uuid, primary key)
   - `created_at` (timestamp with time zone, default now())
   - `Name` (text, not null)
   - `Gmail Account` (text, not null)
   - `Phone Number` (text, not null)

## Building for Production

To build the app for production:

```bash
npm run build
```

The built files will be in the `dist` directory.

## Deploying to Vercel

This frontend is configured for easy deployment on Vercel.

### Steps to deploy:

1. Push your code to a GitHub repository
2. Go to [Vercel](https://vercel.com) and sign up or log in
3. Click "New Project" and import your GitHub repository
4. Configure the project:
   - Set the framework preset to "Vite"
   - Set the root directory to "frontend"
   - Add the following environment variable:
     - `VITE_API_URL`: URL of your deployed backend API (e.g., https://yourdomain.com/api)
5. Click "Deploy"

Vercel will automatically build and deploy your frontend application. 