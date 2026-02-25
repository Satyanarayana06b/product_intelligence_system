import json
import os
from typing import Set

# Cache for tool names to avoid repeated file reads
_tool_names_cache: Set[str] = set()
_categories_cache: Set[str] = set()


def _clear_cache():
    """Clear the tool names cache (useful for testing or reloading)."""
    global _tool_names_cache, _categories_cache
    _tool_names_cache = set()
    _categories_cache = set()


def _load_tool_names() -> Set[str]:
    """
    Load tool names and categories from JSON file.
    
    Returns:
        Set of tool names and keywords
    """
    global _tool_names_cache, _categories_cache
    
    if _tool_names_cache:
        return _tool_names_cache
    
    # Get path to tools.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "data", "tools.json")
    
    try:
        with open(data_path) as f:
            tools = json.load(f)
        
        # Extract tool names and extract keywords
        tool_keywords = set()
        for tool in tools:
            # Add full tool name (lowercase for matching)
            if tool.get('tool_name'):
                tool_keywords.add(tool['tool_name'].lower())
            
            # Extract key words from tool names (e.g., "nutrunner", "spindle")
            if tool.get('tool_name'):
                words = tool['tool_name'].lower().split()
                tool_keywords.update(words)
            
            # Add categories
            if tool.get('category'):
                _categories_cache.add(tool['category'].lower())
                # Add category words
                cat_words = tool['category'].lower().split()
                tool_keywords.update(cat_words)
        
        # Remove common words and generic terms that aren't tool-specific
        common_words = {
            'the', 'a', 'an', 'for', 'with', 'and', 'or', '-',
            'tool', 'machine', 'device', 'equipment', 'system'
        }
        tool_keywords = {word for word in tool_keywords if word not in common_words}
        
        _tool_names_cache = tool_keywords
        return tool_keywords
    except Exception:
        # Fallback to empty set if file not found
        return set()


def needs_clarification(query, filters, filtered_tools):
    """
    Determine if query needs clarification.
    
    Args:
        query: User's current query
        filters: Extracted/accumulated filters
        filtered_tools: Filtered tool results
    
    Returns:
        True if clarification needed
    """
    query_lower = query.lower()
    query_words = query_lower.split()
    
    # If we have filters and results, no clarification needed (session context helps)
    if filters and len(filtered_tools) > 0 and len(filtered_tools) <= 3:
        return False
    
    # Load tool names dynamically from JSON
    specific_tools = _load_tool_names()
    
    # Check if query contains any specific tool keywords
    has_specific_tool = any(tool_keyword in query_lower for tool_keyword in specific_tools)
    
    # If query contains specific tool name, don't ask for clarification unless no results
    if has_specific_tool and len(filtered_tools) > 0:
        # Only ask if too many matches
        if len(filtered_tools) > 3:
            return True
        return False
    
    # Check for generic/vague queries
    generic_terms = ['tool', 'machine', 'device', 'equipment']
    vague_phrases = [
        'i want', 'i need', 'looking for', 'show me', 
        'give me', 'find me', 'help with'
    ]
    
    has_generic_term = any(term in query_words for term in generic_terms)
    has_vague_phrase = any(phrase in query_lower for phrase in vague_phrases)
    
    # If query is generic/vague without specific tool type and no filters, ask for clarification
    if (has_generic_term or has_vague_phrase) and not has_specific_tool and not filters:
        return True
    
    # Too vague (very short query with no filters and no specific tool)
    if len(query_words) < 2 and not filters and not has_specific_tool:
        return True
    
    # Too many matches (ambiguous)
    if len(filtered_tools) > 3:
        return True
    
    # No matches (might be out of domain)
    if len(filtered_tools) == 0:
        return True
    
    return False

def generate_clarification_question(query, filters, filtered_tools, all_tools):
    """
    Generate contextual clarification questions based on the situation.
    
    Args:
        query: User's search query
        filters: Extracted metadata filters
        filtered_tools: Tools after applying filters
        all_tools: Complete tool database
        
    Returns:
        Dictionary with clarification message and suggestions
    """
    # Case 1: No matches found
    if len(filtered_tools) == 0:
        available_types = sorted(set(t.get('application_type', 'N/A') for t in all_tools))
        available_categories = sorted(set(t.get('category', 'N/A') for t in all_tools))
        
        return {
            "status": "needs_clarification",
            "message": "I couldn't find any tools matching your criteria. Could you provide more details?",
            "questions": [
                "What type of tool are you looking for?",
                "What will be the primary use case?"
            ],
            "suggestions": {
                "categories": available_categories,
                "application_types": available_types,
                "examples": [
                    "cordless nutrunner",
                    "handheld screwdriver",
                    "automation spindle",
                    "verification system"
                ]
            }
        }
    
    # Case 2: Too many matches (> 3)
    if len(filtered_tools) > 3:
        questions = []
        suggestions = {}
        
        # Suggest voltage options if not specified
        if "voltage" not in filters:
            voltages = sorted(set(t.get('voltage', 'N/A') for t in filtered_tools if t.get('voltage')))
            if len(voltages) > 1:
                questions.append("What voltage do you need?")
                suggestions["voltage_options"] = voltages
        
        # Suggest application type if not specified
        if "application_type" not in filters:
            app_types = sorted(set(t.get('application_type', 'N/A') for t in filtered_tools))
            if len(app_types) > 1:
                questions.append("Is this for manual use or automation?")
                suggestions["application_types"] = app_types
        
        # Suggest torque range if not specified
        if "torque" not in filters:
            torque_ranges = [t.get('torque_range', 'N/A') for t in filtered_tools 
                           if t.get('torque_range') and t.get('torque_range') != 'NaN']
            if torque_ranges:
                questions.append("What torque range do you require?")
                suggestions["torque_examples"] = torque_ranges[:3]
        
        # Suggest IP rating if not specified
        if "ip_rating" not in filters and not questions:
            ip_ratings = sorted(set(t.get('ip_rating', 'N/A') for t in filtered_tools if t.get('ip_rating')))
            if len(ip_ratings) > 1:
                questions.append("Do you need a specific IP rating?")
                suggestions["ip_rating_options"] = ip_ratings
        
        return {
            "status": "needs_clarification",
            "message": f"I found {len(filtered_tools)} tools that might match. Please provide more details:",
            "questions": questions[:2],  # Limit to 2 questions
            "suggestions": suggestions
        }
    
    # Case 3: Very vague query (< 2 words, no filters)
    if len(query.split()) < 2 and not filters:
        return {
            "status": "needs_clarification",
            "message": "Your query is too vague. Could you be more specific?",
            "questions": [
                "What type of tool are you looking for?",
                "What is your intended use case?"
            ],
            "suggestions": {
                "examples": [
                    "cordless nutrunner",
                    "handheld screwdriver",
                    "automation spindle",
                    "torque verification system"
                ]
            }
        }
    
    # Default fallback
    questions = []
    if "torque" not in filters:
        questions.append("What torque range do you require (in Nm)?")
    if "application_type" not in filters:
        questions.append("Is this for automation or manual use?")
    if "voltage" not in filters:
        questions.append("Do you have any voltage preference (e.g., 18V, 230V, 400V)?")
    
    return {
        "status": "needs_clarification",
        "message": "Could you provide more details about your requirements?",
        "questions": questions[:2],
        "suggestions": {}
    }