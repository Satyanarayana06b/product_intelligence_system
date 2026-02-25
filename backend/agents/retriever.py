import faiss
import json
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import os
import httpx
from backend.query_parser import extract_filters, apply_metadata_filters

load_dotenv()

# Configure httpx client to bypass proxy issues
httpx_client = httpx.Client(
    proxy=None,  # Bypass proxy
    timeout=60.0  # Increase timeout
)
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    http_client=httpx_client
)

def embed_query(query):
    response = client.embeddings.create(
        input=query,
        model="text-embedding-3-small",
    )
    return response.data[0].embedding

def retrieve_tools(query, top_k=3, use_filters=True):
    """
    Retrieve tools using semantic search and optional metadata filtering.
    
    Args:
        query: User's search query
        top_k: Number of results to retrieve from vector search
        use_filters: Whether to apply metadata filtering
        
    Returns:
        List of matching tools (top 1 after filtering, or empty list if no matches)
    """
    # Get the script's directory and construct absolute paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(script_dir, "..", "vector_store", "tools.index")
    data_path = os.path.join(script_dir, "..", "data", "tools.json")
    
    # Load all tools
    with open(data_path) as f:
        tools = json.load(f)
    
    # Extract metadata filters from query
    filters = extract_filters(query) if use_filters else {}
    
    # If filters are present, apply them first
    if filters:
        filtered_tools = apply_metadata_filters(tools, filters)
        
        # If filtering resulted in matches, use semantic search on filtered results
        if filtered_tools:
            # Perform semantic search on filtered tools
            return semantic_search_on_subset(query, filtered_tools, tools, index_path, top_k=1)
        else:
            # No matches after filtering - return empty list to trigger clarification
            return []
    
    # No filters applied - perform standard semantic search
    index = faiss.read_index(index_path)
    query_vector = np.array(embed_query(query)).astype('float32')
    query_vector = query_vector.reshape(1, -1)
    _, indices = index.search(query_vector, top_k)
    
    results = [tools[i] for i in indices[0]]
    return results[:1]  # Return top result


def semantic_search_on_subset(query, filtered_tools, all_tools, index_path, top_k=1):
    """
    Perform semantic search only on a filtered subset of tools.
    
    Args:
        query: User's search query
        filtered_tools: Pre-filtered list of tools
        all_tools: Complete list of all tools
        index_path: Path to FAISS index
        top_k: Number of results to return
        
    Returns:
        Top matching tools from the filtered subset
    """
    # Get indices of filtered tools in the original tools list
    filtered_indices = [all_tools.index(tool) for tool in filtered_tools]
    
    # Load index and get query vector
    index = faiss.read_index(index_path)
    query_vector = np.array(embed_query(query)).astype('float32')
    query_vector = query_vector.reshape(1, -1)
    
    # Search in full index but only consider filtered indices
    # Get more candidates to ensure we find matches in filtered set
    _, all_indices = index.search(query_vector, len(all_tools))
    
    # Find which of the retrieved indices are in our filtered set
    matched_indices = [idx for idx in all_indices[0] if idx in filtered_indices]
    
    # Return top_k matches
    results = [all_tools[idx] for idx in matched_indices[:top_k]]
    return results if results else filtered_tools[:top_k]
