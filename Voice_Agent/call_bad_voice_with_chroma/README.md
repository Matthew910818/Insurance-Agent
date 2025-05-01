# Prince AI

Prince AI is a voice application system that uses ChromaDB for memory storage and processing phone calls.

## Getting Started

This guide will help you set up and run the Prince AI system from scratch.

### Prerequisites

- [Docker](https://www.docker.com/get-started) and Docker Compose
- [Python 3.11+](https://www.python.org/downloads/)
- A Twilio account for phone call functionality
- An OpenAI API key for embeddings and AI responses

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd prince
```

### Step 2: Set Up Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your API keys:
   - Add your OpenAI API key
   - Add your Twilio credentials (Account SID, Auth Token, Phone Number)
   - The ChromaDB settings are preconfigured but can be adjusted if needed

### Step 3: Setting Up Twilio

1. Sign up for a [Twilio account](https://www.twilio.com/try-twilio)
2. Purchase a phone number with voice capabilities
3. In your Twilio dashboard:
   - Navigate to the Phone Numbers section
   - Select your number and configure the voice webhook
   - Set the webhook URL to point to your deployed backend: `https://your-domain.com/voice/incoming-call`
   - For local testing, use a service like [ngrok](https://ngrok.com/) to expose your local server

### Step 4: Running the Application

#### Option 1: Using Docker (Recommended)

1. Build and start the Docker containers:
   ```bash
   cd backend
   docker-compose build --no-cache
   docker-compose up
   ```

2. The backend will be available at `http://localhost:8080`
3. ChromaDB will be available at `http://localhost:8001`

#### Option 2: Running Locally

1. Set up a Python virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start ChromaDB separately:
   ```bash
   # In a separate terminal
   docker run -p 8001:8000 ghcr.io/chroma-core/chroma:latest
   ```

4. Run the FastAPI backend:
   ```bash
   cd backend
   uvicorn backend_app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Step 5: Making a Phone Call

1. Ensure the backend and ChromaDB services are running
2. Call your Twilio phone number from any phone
3. The system will answer and interact using the Prince AI voice experience

### Troubleshooting

#### ChromaDB Connection Issues

If you encounter issues connecting to ChromaDB:

- When running directly with Python scripts, ensure you're using `localhost:8001`
- When running with Docker, services should use `chroma:8000`
- The `.env` file and docker-compose.yml contain the correct settings

#### Testing the ChromaDB Connection

You can test if ChromaDB is working correctly:

```bash
python test_chroma_connection.py
```

## Development Notes

- The root `requirements.txt` is for the local development environment
- Docker uses the requirements in the backend directory
- Always update both requirement files when adding new dependencies

## Scripts

- `scripts/read_memory.py`: Utility to view user data stored in ChromaDB
  ```bash
  python scripts/read_memory.py
  ```
  You will be prompted to enter a phone number to look up user data.

## License

[Include license information here]
