from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend_app.routes import voice  # import your new voice route file

# Create FastAPI app instance
app = FastAPI(
    title="Prince Backend",
    description="Backend API for Prince application",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the route
app.include_router(voice.router)

@app.get("/")
async def root():
    return {"message": "Prince Backend API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
