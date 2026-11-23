# Aiman Fitness Bot — FitZone Gym Assistant

An AI-powered Fitness and Gym Coach chatbot built with **Python, Google Gemini API, FastAPI, WebSockets, Streamlit, and ChromaDB**.

The chatbot answers gym-related questions, remembers conversation context, checks trainer availability using a custom tool, and retrieves relevant information from a gym FAQ knowledge base.

## Features

- **AI-Powered Conversations:** Uses Google Gemini to generate helpful responses.
- **Conversation Memory:** Maintains conversation history within the active chat session.
- **Trainer Booking Tool:** Uses the custom `book_session` function to check mock trainer availability.
- **FAQ Search (RAG):** Uses the `search_faq` tool to retrieve relevant information from the gym FAQ knowledge base.
- **Streaming Responses:** Uses FastAPI WebSockets to communicate between the backend and frontend.
- **User Interface:** Provides a simple chat interface built with Streamlit.

## Technologies Used

- Python
- Google Gemini API (`google-genai`)
- FastAPI
- WebSockets
- Streamlit
- ChromaDB
- Python Dotenv

## Project Structure

```text
aiman-fitness-bot/
│
├── main.py
├── app.py
├── gym_faqs.json
├── ingest_faqs.py
├── faq_search.py
├── test_client.py
├── test_faq_client.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

The `chroma_db/` directory is created locally when the FAQ knowledge base is ingested.

## Prerequisites

Before running the project, make sure you have:

- Python installed.
- Git installed.
- A Google Gemini API key.
- VS Code or another code editor.

## Installation and Setup

### 1. Clone the Repository

Open your terminal and run:

```bash
git clone https://github.com/aimantahir412-afk/aiman-fitness-bot.git
```

Navigate into the project directory:

```bash
cd aiman-fitness-bot
```

### 2. Create a Virtual Environment

On Windows PowerShell:

```powershell
python -m venv venv
```

Activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell activation is unavailable, you can use the virtual environment's Python executable directly:

```powershell
.\venv\Scripts\python.exe
```

### 3. Install Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create your local `.env` file by copying the example file.

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Open `.env` and add your Gemini API configuration:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_configured_gemini_model
```

Replace the placeholder values with your own configuration.

**Important:** Never share your API key or upload your private `.env` file to GitHub.

### 5. Prepare the FAQ Knowledge Base

The project uses ChromaDB to store and retrieve gym FAQ information.

Run the ingestion script:

```bash
python ingest_faqs.py
```

This processes the FAQ data from `gym_faqs.json` and creates the local vector database.

Run ingestion again if you need to rebuild the local FAQ database.

## Running the Application

The application requires two separate terminals: one for the FastAPI backend and another for the Streamlit frontend.

### 1. Start the FastAPI Backend

Open the first terminal in the project directory and run:

```bash
uvicorn main:app --reload
```

The FastAPI backend will start locally at:

```text
http://localhost:8000
```

The chatbot WebSocket endpoint is:

```text
ws://localhost:8000/ws/chat
```

### 2. Start the Streamlit Frontend

Keep the backend running.

Open a second terminal in the same project directory and run:

```bash
streamlit run app.py
```

The Streamlit application will open in your browser, usually at:

```text
http://localhost:8501
```

You can now start chatting with the FitZone Gym Assistant.

## Example Questions

Try asking the chatbot:

- Can I pause my gym membership?
- What fitness classes do you offer?
- Can I book a session with Ali on Monday?
- Is Ali available on Tuesday?
- What should I bring when I visit the gym?

## Project Notes

- Trainer schedules and bookings use mock demonstration data; this is not a live gym booking system.
- Conversation memory is maintained in application memory for the active session.
- The FAQ knowledge base is stored locally using ChromaDB.
- The local `.env` file and `chroma_db/` directory should not be committed to GitHub.

## Author

**Aiman Tahir**

GitHub: https://github.com/aimantahir412-afk/aiman-fitness-bot

---

Developed as part of the **Zigron AI Engineering Internship — 5-Day Chatbot Sprint**.