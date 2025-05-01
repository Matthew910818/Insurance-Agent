# scripts/test_chroma.py

from backend_app.core import database


# Use a fixed fake student ID
STUDENT_ID = "t8t234cxbyeio2cd"

# models:
# stundet wedefine the strucutre of the metadata and then the LLM will alwys query in such form
# jobs

#documtents is all of the data that we want to search through and do rag on

# Fake profile data

document = "I'm a computer science student at Stanford focused on LLMs and robotics."
metadata = {
    "name": "Test User",
    "phone": "+15107017501",

    "email": "test@test.com",
    "linkedin": "https://www.linkedin.com/in/test/",
    "github": "https://github.com/test/",
    "website": "https://www.test.com/",
    "twitter": "https://twitter.com/test/",
    "devpost": "https://devpost.com/test/",
    "location": "San Francisco, CA",
    "language": "English",
    "timezone": "America/Los_Angeles",
    "country": "United States",
    "school": "Stanford",
    "grad_year": 2025,
    "skills": "LLMs, robotics",
    "interested_in": "early-stage AI startups"
}

print("👉 Upserting test student into Chroma...")
database.upsert_student(STUDENT_ID, document, metadata)

print("✅ Upsert complete.")

print("\n🔍 Fetching student back by ID...")
result = database.students_collection.get(ids=[STUDENT_ID])

print("\n✅ Found student:")
print("ID:", result["ids"][0])
print("Document:", result["documents"][0])
print("Metadata:", result["metadatas"][0])

