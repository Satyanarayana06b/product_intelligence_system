from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.schemas import Query
from backend.crew_setup import run_agent
from backend.session_manager import get_session, update_session, create_session
import uuid

app = FastAPI()

# Add CORS middleware to allow requests from Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.post("/chat")
def chat(query: Query):
    # Get or create session
    session_id = query.session_id or str(uuid.uuid4())
    session = get_session(session_id)
    
    # Run agent with session context
    response = run_agent(query.question, session)
    
    # Update session with new interaction
    update_session(session_id, query.question, response)
    
    return {
        "response": response,
        "session_id": session_id
    }