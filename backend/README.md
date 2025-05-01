# Gmail Agent Backend

This is the backend server for the Gmail Agent application, built with Express and Supabase.

## Setup

1. Clone the repository
2. Navigate to the backend directory
3. Install dependencies:

```bash
npm install
```

4. Create a `.env` file in the root of the backend directory with the following variables:

```
PORT=8000
SUPABASE_URL=your-supabase-url-here
SUPABASE_SERVICE_KEY=your-supabase-service-key-here
```

5. Start the development server:

```bash
npm run dev
```

## API Endpoints

### Health Check
- **URL**: `/api/health`
- **Method**: `GET`
- **Response**: `{ "status": "ok", "message": "Server is running" }`

### Create User
- **URL**: `/api/users`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "Name": "User Name",
    "Gmail_Account": "user@gmail.com",
    "Phone_Number": "1234567890"
  }
  ```
- **Response Success**: 
  ```json
  {
    "message": "User created successfully",
    "user": { ... } // User data
  }
  ```
- **Response Error**:
  ```json
  {
    "errors": [ ... ] // Validation errors
  }
  ```

## Supabase Configuration

To use the backend, you need to set up a Supabase project:

1. Create a new project at [https://supabase.com](https://supabase.com)
2. Create a new table called `User Info` with the following columns:
   - `id` (uuid, primary key)
   - `created_at` (timestamp with time zone, default now())
   - `Name` (text, not null)
   - `Gmail Account` (text, not null)
   - `Phone Number` (text, not null)
3. Get your project URL and service key from the API settings and add them to the `.env` file 