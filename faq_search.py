
import os
from dotenv import load_dotenv
from google import genai
import chromadb

# Load environment variables
load_dotenv()

# Initialize Gemini
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Connect to the existing ChromaDB database
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Access the stored FAQ collection
collection = chroma_client.get_collection(name="fitzone_faqs")


def search_faq(question):
    # Convert the user's question into an embedding
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=question,
        config={
            "task_type": "RETRIEVAL_QUERY",
            "output_dimensionality": 768
        }
    )

    question_embedding = response.embeddings[0].values

    # Search for the most relevant FAQ
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=1
    )

    # Return the matching FAQ
    if results["documents"] and results["documents"][0]:
        return results["documents"][0][0]

    return "Sorry, I could not find a relevant answer."


# Test the search function
if __name__ == "__main__":
    question = "Can I pause my gym membership?"
    answer = search_faq(question)

    print("User Question:", question)
    print("Retrieved FAQ:", answer)
