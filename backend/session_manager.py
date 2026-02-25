from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

# In-memory session storage (for production, use Redis or database)
sessions: Dict[str, Dict[str, Any]] = {}

# Session timeout (30 minutes)
SESSION_TIMEOUT = timedelta(minutes=30)


def create_session(session_id: str) -> Dict[str, Any]:
    """
    Create a new session with empty state.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        New session dictionary
    """
    session = {
        "session_id": session_id,
        "conversation_history": [],
        "extracted_filters": {},
        "last_query": "",
        "clarification_count": 0,
        "created_at": datetime.now(),
        "last_accessed": datetime.now()
    }
    sessions[session_id] = session
    return session


def get_session(session_id: str) -> Dict[str, Any]:
    """
    Get existing session or create new one.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Session dictionary
    """
    # Clean up expired sessions
    cleanup_expired_sessions()
    
    if session_id in sessions:
        session = sessions[session_id]
        session["last_accessed"] = datetime.now()
        return session
    else:
        return create_session(session_id)


def update_session(session_id: str, query: str, response: Any) -> None:
    """
    Update session with new query and response.
    
    Args:
        session_id: Unique session identifier
        query: User's query
        response: Agent's response
    """
    session = get_session(session_id)
    
    # Add to conversation history
    session["conversation_history"].append({
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "response": response
    })
    
    # Update last query
    session["last_query"] = query
    
    # Track clarification count
    if isinstance(response, dict) and response.get("status") == "needs_clarification":
        session["clarification_count"] += 1
    
    # Merge filters from response if available
    if isinstance(response, dict) and "filters" in response:
        session["extracted_filters"].update(response["filters"])
    
    session["last_accessed"] = datetime.now()


def merge_context(session: Dict[str, Any], current_query: str) -> str:
    """
    Merge session context with current query for better understanding.
    
    Args:
        session: Current session state
        current_query: User's current query
        
    Returns:
        Enhanced query with context
    """
    if not session["conversation_history"]:
        return current_query
    
    # Get previously extracted filters
    previous_filters = session.get("extracted_filters", {})
    
    # Build context string
    context_parts = []
    
    if previous_filters:
        context_parts.append(f"Previous preferences: {json.dumps(previous_filters)}")
    
    # Get last 2 interactions for context
    recent_history = session["conversation_history"][-2:]
    if recent_history:
        for interaction in recent_history:
            context_parts.append(f"Previous query: {interaction['query']}")
    
    if context_parts:
        context = " | ".join(context_parts)
        return f"{current_query} [Context: {context}]"
    
    return current_query


def get_accumulated_filters(session: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get accumulated filters from session history.
    
    Args:
        session: Current session state
        
    Returns:
        Dictionary of accumulated filters
    """
    return session.get("extracted_filters", {})


def cleanup_expired_sessions() -> None:
    """
    Remove sessions that have exceeded the timeout period.
    """
    now = datetime.now()
    expired_sessions = [
        sid for sid, session in sessions.items()
        if now - session["last_accessed"] > SESSION_TIMEOUT
    ]
    
    for sid in expired_sessions:
        del sessions[sid]


def clear_session(session_id: str) -> None:
    """
    Clear a specific session.
    
    Args:
        session_id: Unique session identifier
    """
    if session_id in sessions:
        del sessions[session_id]


def get_session_stats() -> Dict[str, Any]:
    """
    Get statistics about active sessions.
    
    Returns:
        Dictionary with session statistics
    """
    return {
        "active_sessions": len(sessions),
        "total_conversations": sum(len(s["conversation_history"]) for s in sessions.values()),
        "sessions_needing_clarification": sum(1 for s in sessions.values() if s["clarification_count"] > 0)
    }
