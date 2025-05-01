# scripts/read_memory.py
#this script is used to read the memory of a user
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import tiktoken
from backend_app.core.database import get_student_by_phone


# Add the backend directory to the Python path
backend_dir = str(Path(__file__).parent.parent / "backend")
sys.path.append(backend_dir)

# Load environment variables
load_dotenv()

# Force connection settings for direct script execution
os.environ["CHROMA_HOST"] = "localhost"
os.environ["CHROMA_PORT"] = "8001"

# Debug: Print environment variables
print("🔍 Debug Info:")
print("CHROMA_HOST:", os.environ.get("CHROMA_HOST"))
print("CHROMA_PORT:", os.environ.get("CHROMA_PORT"))
print("Python Path:", sys.path)

try:
   
    print("\n📡 Importing database module...")

    def view_user(phone):
        data = get_student_by_phone(phone)
        if not data or not data.get("metadatas") or not data.get("documents"):
            print("❌ No data found for this phone number")
            return
        print("🧠 User:", data["metadatas"][0].get("full_name", "N/A"))
        print("📞 Phone:", data["metadatas"][0].get("user_id", "N/A"))
        print("📝 Memory:\n", data["documents"][0])

        print("\n🚀 Importing tiktoken module...")
        enc = tiktoken.encoding_for_model("gpt-4")
        print("🔍 Encoding length for YOUR_TEXT_HERE:", len(enc.encode(data["documents"][0])))


    if __name__ == "__main__":
        phone = input("Enter phone number (e.g. +18667398151): ")
        view_user(phone)
except Exception as e:
    print("❌ Error:", str(e))