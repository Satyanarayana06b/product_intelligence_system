from crewai import Agent, Task, Crew
from backend.agents.retriever import retrieve_tools
from backend.query_parser import extract_filters
from backend.clarification import needs_clarification, generate_clarification_question
from backend.session_manager import get_accumulated_filters, merge_context
from openai import OpenAI
import json
import re

# Configuration
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.7

PROMPT_TEMPLATE = """
## User Query
{user_query}

## Available Tools Database
{tool_context}

## Your Task
Analyze the user's requirements and recommend the BEST matching tool from the available database.

## Required Output Format
Please provide a comprehensive recommendation with the following details:

Return ONLY valid JSON in this format:
{{
  "tool_name": "",
  "model": "",
  "why_recommended": "",
  "key_specs": [],
  "voltage": "",
  "ip_rating": "",
  "image_path": "",
  "confidence": ""
}}

## Important Guidelines
- Only recommend tools from the provided database
- Ensure all specifications are accurate and from the database
- If multiple tools match, recommend the one that best fits the user's needs
- Be specific and detailed in your justification
"""

def run_agent(user_query, session=None, model=DEFAULT_MODEL, temperature=DEFAULT_TEMPERATURE):
    """
    Run the tool recommendation agent with session context, clarification and metadata filtering.
    
    Args:
        user_query: User's search query for tools
        session: Session dictionary with conversation history (optional)
        model: LLM model to use (default: gpt-4)
        temperature: Model temperature for creativity (default: 0.7)
    
    Returns:
        Recommendation result from the crew, or clarification request
    """
    # Get accumulated filters from session
    accumulated_filters = {}
    
    if session:
        accumulated_filters = get_accumulated_filters(session)
    
    # Extract filters from current query
    current_filters = extract_filters(user_query)
    
    # Check if current query contains a new specific tool name (different from previous)
    from backend.clarification import _load_tool_names
    specific_tools = _load_tool_names()
    has_new_specific_tool = any(tool_keyword in user_query.lower() for tool_keyword in specific_tools)
    
    # Build enhanced query with session context
    enhanced_query = user_query
    if session and session.get("last_query"):
        # Only combine with previous query if:
        # 1. Current query is very short (<=2 words)
        # 2. Current query doesn't contain a new specific tool name
        # 3. Current query appears to be a refinement (e.g., "18V", "manual", "portable")
        if len(user_query.split()) <= 2 and not has_new_specific_tool:
            previous_context = session.get("last_query", "")
            enhanced_query = f"{previous_context} {user_query}"
    
    # Merge accumulated filters with current filters (current takes precedence)
    # But only if we're not searching for a new specific tool
    if has_new_specific_tool:
        # Fresh search - only use current filters
        merged_filters = current_filters
    else:
        # Refinement - merge with accumulated filters
        merged_filters = {**accumulated_filters, **current_filters}
    
    # Retrieve tools using enhanced query
    tools = retrieve_tools(enhanced_query)
    
    # Apply merged filters if we have any filters (current or accumulated)
    # Note: retrieve_tools() already applies filters internally, but we need to
    # re-apply merged filters if we have accumulated filters from session
    if merged_filters and accumulated_filters:
        from backend.query_parser import apply_metadata_filters
        tools = apply_metadata_filters(tools, merged_filters) if tools else []
    
    # Load all tools for clarification context
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "data", "tools.json")
    with open(data_path) as f:
        all_tools = json.load(f)
    
    # Check if clarification is needed (use original query for checking, not enhanced)
    if needs_clarification(user_query, merged_filters, tools):
        clarification = generate_clarification_question(user_query, merged_filters, tools, all_tools)
        # Include merged filters in response for session tracking
        clarification["filters"] = merged_filters
        return clarification

    tool_context = str(tools)
    
    # Add filter information to the context if filters were applied
    filter_info = ""
    if merged_filters:
        filter_info = f"\n\n## Applied Filters\n{json.dumps(merged_filters, indent=2)}"

    recommender = Agent(
        role="Industrial Tool Expert",
        goal="Recommend the best tool from provided database",
        backstory="Expert in industrial tightening systems with deep knowledge of tool specifications, use cases, and industry standards",
        llm=model,
        temperature=temperature
    )

    task = Task(
        description=PROMPT_TEMPLATE.format(
            user_query=user_query,
            tool_context=tool_context
        ) + filter_info,
        agent=recommender,
        expected_output="A structured recommendation with tool name, model, justification, 5 key specs, voltage, IP rating, and image path"
    )
    
    crew = Crew(agents=[recommender], tasks=[task], verbose=True)
    result = crew.kickoff()

    # Extract JSON from result
    result_str = str(result)
    if isinstance(result, dict):
        result_str = result.get("raw", str(result))
    
    # Try to extract JSON from the response
    try:
        # Look for JSON in the response
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result_str)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            return {"error": "No JSON found in response", "raw": result_str}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON", "raw": result_str}
