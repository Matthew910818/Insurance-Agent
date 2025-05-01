# database.py
from dotenv import load_dotenv
import os
import chromadb
from chromadb.utils import embedding_functions
from backend_app.core import embeddings

load_dotenv()
# openai_embed = embedding_functions.OpenAIEmbeddingFunction(
#     api_key=os.getenv("OPENAI_API_KEY"),
#     model_name="text-embedding-3-small"
# )

# In Docker, use the service name 'chroma' as host, otherwise use 'localhost'
CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")  # Default to 'localhost' for local dev
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8001"))  # Use port 8001 for local dev to match docker-compose

print("🔄 Initializing  ChromaDB with:", CHROMA_HOST, CHROMA_PORT)  # Debug line

# Use BGE-small model for embeddings
embedding_function = embeddings.BGEEmbeddingFunction()

# chroma_client = chromadb.HttpClient(host="chroma", port=8000)
chroma_client = chromadb.HttpClient(
    host=CHROMA_HOST,
    port=CHROMA_PORT
)

students_collection = chroma_client.get_or_create_collection(
    name="students",
    embedding_function=embedding_function
)

jobs_collection = chroma_client.get_or_create_collection(
    name="jobs",
    embedding_function=embedding_function
)

#upsert = add or update (update  ake replace if uuid already exists)
def upsert_student(student_id: str, document: str, metadata: dict):
    students_collection.upsert(
        ids=[student_id],
        documents=[document],
        metadatas=[metadata]
    )

#query via promp excluding the user's profile
def query_by_prompt(prompt: str, exclude_user_id: str = None, n_results=5):
    results = students_collection.query(
        query_texts=[prompt],
        n_results=n_results + 1  # get extra to filter
    )

    # Filter out the current user by ID if needed
    if exclude_user_id:
        filtered = []
        for i, student_id in enumerate(results["ids"]):
            if student_id != exclude_user_id:
                filtered.append({
                    "id": student_id,
                    "document": results["documents"][i],
                    "metadata": results["metadatas"][i]
                })
        return filtered[:n_results]

    return results

#query = search
def query_jobs(student_profile: str, n_results=5):
    return jobs_collection.query(
        query_texts=[student_profile],
        n_results=n_results
    )

#query best match for 1 student profile
def query_best_match(student_profile: str, n_results=1):
    return students_collection.query(
        query_texts=[student_profile],
        n_results=n_results
    )



#create a that updates the user profile in chroma without deleting the existing profile
def update_user_profile_by_id(user_id: str, user_profile: dict):
    students_collection.update(
        ids=[user_id],
        documents=[user_profile.model_dump_json()],
        metadatas=[user_profile.model_dump()]
    )


#get student profile from chroma
def get_student_profile(user_id: str):
    #returns looks like this:
    # {
    #     "ids": ["1234567890"],
    #     "documents": ["user profile"],
    #     "metadatas": [{"user_id": "1234567890"}]
    # }
    return students_collection.get(
        ids=[user_id]
    )

#get stundet profile from chroma based on one metadata field
def get_student_profile_by_metadata(metadata_field: str, metadata_value: str):
    #returns looks like this:
    # {
    #     "ids": ["1234567890"],
    #     "documents": ["user profile"],
    #     "metadatas": [{"user_id": "1234567890"}]
    # }
    return students_collection.get(
        where={metadata_field: metadata_value}
    )

#get student profile by phone number
def get_student_by_phone(phone_number: str):
    return students_collection.get(
        where={"user_id": phone_number}
    )

#create new student entry with phone number
def create_student_with_phone(phone_number: str, full_name: str = None):
    metadata = {
        "user_id": phone_number,
    }

    if full_name is not None:
        metadata["full_name"] = full_name

    students_collection.upsert(
        ids=[phone_number],
        documents=[""],  # Start with empty memory
        metadatas=[metadata]
    )
    return metadata

#find closest matching student by name query
def find_student_by_name_query(name_query: str, n_results: int = 1):
    results = students_collection.query(
        query_texts=[name_query],
        n_results=n_results,
        where={"full_name": {"$ne": None}}  # Only search where full_name exists
    )
    return results

#update conversation history in document
def update_conversation_history(phone_number: str, conversation_text: str):
    existing = get_student_by_phone(phone_number)

    current_doc = ""
    metadata = {"user_id": phone_number}

    if existing:
        if existing.get("documents") and existing["documents"][0]:
            current_doc = existing["documents"][0]
        if existing.get("metadatas") and existing["metadatas"][0]:
            metadata = existing["metadatas"][0]

    # Make sure conversation_text is a string
    conversation_text = conversation_text or ""

    # Skip upsert if there's nothing to store
    if not conversation_text.strip():
        return

    updated_doc = (current_doc + "\n" + conversation_text).strip()

    students_collection.upsert(
        ids=[phone_number],
        documents=[updated_doc],
        metadatas=[metadata]
    )



def update_full_name(phone_number: str, full_name: str):
    existing = get_student_by_phone(phone_number)

    if not existing or not existing.get("ids"):
        print("[❌] No existing user found for update_full_name.")
        return

    doc = existing.get("documents", [""])[0] or ""
    metadata = existing.get("metadatas", [{}])[0]
    metadata["full_name"] = full_name

    students_collection.upsert(
        ids=[phone_number],
        documents=[doc],  # non-empty
        metadatas=[metadata]
    )