import re
from typing import Dict, Any

def extract_filters(query: str) -> Dict[str, Any]:
    """
    Extract metadata filters from user query.
    
    Args:
        query: User's search query
        
    Returns:
        Dictionary of filters (voltage, torque, ip_rating, application_type)
    """
    filters = {}
    query_lower = query.lower()
    
    # Extract voltage (e.g., "18V", "230V", "400V")
    voltage_match = re.search(r'(\d+\s?V)', query, re.IGNORECASE)
    if voltage_match:
        filters['voltage'] = voltage_match.group().replace(" ", "").upper()

    # Extract torque (e.g., "50Nm", "100 Nm")
    torque_match = re.search(r'(\d+)\s*Nm', query, re.IGNORECASE)
    if torque_match:
        filters['torque'] = int(torque_match.group(1))
    
    # Extract IP rating (e.g., "IP40", "IP54")
    ip_match = re.search(r'(IP\d+)', query, re.IGNORECASE)
    if ip_match:
        filters['ip_rating'] = ip_match.group().upper()

    # Application type keywords (check in order of specificity)
    if "cordless" in query_lower or "portable" in query_lower:
        filters['application_type'] = "Manual / Portable"
    elif "automation" in query_lower or "assembly line" in query_lower or "automated" in query_lower:
        filters['application_type'] = "Automation"
    elif "manual" in query_lower and "portable" not in query_lower:
        filters['application_type'] = "Manual"
    elif "controller" in query_lower or "control system" in query_lower:
        filters['application_type'] = "Control System"
    elif "verification" in query_lower or "calibration" in query_lower:
        filters['application_type'] = "Quality / Verification"
    
    return filters


def apply_metadata_filters(tools: list, filters: Dict[str, Any]) -> list:
    """
    Filter tools based on extracted metadata.
    
    Args:
        tools: List of tool dictionaries
        filters: Dictionary of filter criteria
        
    Returns:
        Filtered list of tools
    """
    if not filters:
        return tools
    
    filtered_tools = tools
    
    # Filter by voltage (partial match to handle "18V" matching "18V DC")
    if 'voltage' in filters:
        filtered_tools = [
            tool for tool in filtered_tools 
            if filters['voltage'] in tool.get('voltage', '').upper()
        ]
    
    # Filter by IP rating
    if 'ip_rating' in filters:
        filtered_tools = [
            tool for tool in filtered_tools 
            if tool.get('ip_rating', '').upper() == filters['ip_rating']
        ]
    
    # Filter by application type
    if 'application_type' in filters:
        filtered_tools = [
            tool for tool in filtered_tools 
            if tool.get('application_type') == filters['application_type']
        ]
    
    # Filter by torque (if tool's torque range includes the requested torque)
    if 'torque' in filters:
        requested_torque = filters['torque']
        filtered_tools = [
            tool for tool in filtered_tools
            if _torque_in_range(requested_torque, tool.get('torque_range', ''))
        ]
    
    return filtered_tools


def _torque_in_range(requested_torque: int, torque_range) -> bool:
    """
    Check if requested torque falls within tool's torque range.
    
    Args:
        requested_torque: Requested torque value in Nm
        torque_range: Tool's torque range string (e.g., "5–100 Nm") or NaN
        
    Returns:
        True if torque is in range, False otherwise
    """
    # Handle NaN, None, empty, or non-string values
    if not torque_range or not isinstance(torque_range, str):
        return False
    
    if torque_range == "NaN" or torque_range.strip() == "":
        return False
    
    # Parse torque range (e.g., "5–100 Nm" or "2-80 Nm")
    match = re.search(r'(\d+)[–\-](\d+)', torque_range)
    if match:
        min_torque = int(match.group(1))
        max_torque = int(match.group(2))
        return min_torque <= requested_torque <= max_torque
    
    return False