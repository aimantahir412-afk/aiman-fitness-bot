
import os
import json
from dotenv import load_dotenv
from google import genai
import chromadb

# Load environment variables
load_dotenv()

# Create Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Connect to a local ChromaDB database
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Create or access the FAQ collection
collection = chroma_client.get_or_create_collection(
    name="fitzone_faqs"
)

# Read FAQs from JSON file
with open("gym_faqs.json", "r", encoding="utf-8") as file:
    faqs = json.load(file)

# Prepare FAQ text for embedding
documents = [
    f"Question: {faq['question']} Answer: {faq['answer']}"
    for faq in faqs
]

# Generate embeddings using Gemini
response = client.models.embed_content(
    model="gemini-embedding-001",
    contents=documents,
    config={
        "task_type": "RETRIEVAL_DOCUMENT",
        "output_dimensionality": 768
    }
)

embeddings = [item.values for item in response.embeddings]

# Store FAQs and embeddings in ChromaDB
collection.upsert(
    ids=[f"faq_{i}" for i in range(len(faqs))],
    documents=documents,
    embeddings=embeddings,
    metadatas=[
        {"category": faq["category"]}
        for faq in faqs
    ]
)

print("FAQ ingestion completed successfully!")
print("Total FAQs stored:", collection.count())
