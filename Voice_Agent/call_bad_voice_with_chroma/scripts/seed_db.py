#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import chromadb
import json

load_dotenv()

def connect_to_chroma():
    CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
    CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))
    
    print(f"🔄 Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}")
    
    client = chromadb.HttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT
    )
    return client

# Sample profiles with impressive backgrounds
PROFILES = [
    {
        "phone": "+14155551001",
        "full_name": "Sarah Chen",
        "document": """
- PhD candidate in AI at Stanford, focusing on large language models and their applications in healthcare
- Previously worked at DeepMind on protein folding algorithms
- Founded an AI startup that was acquired by Google
- Interested in: AGI safety, biotech applications, and founding another startup
- Looking to connect with: Other technical founders and AI researchers
- Skills: PyTorch, JAX, Large-scale ML systems, Distributed computing
"""
    },
    {
        "phone": "+14155551002",
        "full_name": "Alex Kumar",
        "document": """
- Serial entrepreneur, sold last startup to Meta for $200M
- YC alumni, currently building in stealth mode
- Previously ML Lead at OpenAI
- Interested in: AI agents, autonomous systems, and climate tech
- Looking to connect with: Technical cofounders and early employees
- Skills: Product strategy, Team building, Python, Rust, MLOps
"""
    },
    {
        "phone": "+14155551003",
        "full_name": "Emily Zhang",
        "document": """
- Research Scientist at  Anthropic working on AI alignment
- MIT CS graduate, published at NeurIPS, ICML, and ICLR
- Built open-source LLM framework used by 100k+ developers
- Interested in: AI safety, interpretability research, and education
- Looking to connect with: Researchers and engineers in AI safety
- Skills: Transformers, Reinforcement Learning, Mathematical optimization
"""
    },
    {
        "phone": "+14155551004",
        "full_name": "Marcus Johnson",
        "document": """
- Founder & CEO of quantum computing startup, raised $50M Series A
- PhD in Physics from Caltech
- Previously quantum researcher at IBM
- Interested in: Quantum algorithms, cryptography, and AI acceleration
- Looking to connect with: Hardware engineers and quantum physicists
- Skills: Quantum circuits, Superconducting qubits, Python, C++
"""
    },
    {
        "phone": "+14155551005",
        "full_name": "Sophia Rodriguez",
        "document": """ 
- Leading computer vision team at Tesla Autopilot
- Stanford MS in CS, specialized in robotics
- Published pioneering work on 3D scene understanding
- Interested in: Autonomous systems, robotics, and computer vision
- Looking to connect with: ML engineers and roboticists
- Skills: Computer Vision, SLAM, PyTorch, ROS
"""
    }
]

def seed_database():
    try:
        client = connect_to_chroma()
        collection = client.get_collection("students")
        
        print("\n🌱 Seeding database with profiles...")
        
        for profile in PROFILES:
            # Create metadata with only required fields
            metadata = {
                "user_id": profile["phone"],
                "full_name": profile["full_name"]
            }
            
            # Insert the profile
            collection.upsert(
                ids=[profile["phone"]],
                documents=[profile["document"].strip()],
                metadatas=[metadata]
            )
            print(f"✅ Added profile for {profile['full_name']}")
        
        print("\n✨ Database seeding complete!")
        
        # Verify the seeding
        results = collection.get()
        print(f"\n📊 Total profiles in database: {len(results['ids'])}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    seed_database()
