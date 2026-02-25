import json
import faiss
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import os
import httpx

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

def create_embedding(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small",
    )
    return response.data[0].embedding

def build_vector_store():
    # Get the script's directory and construct absolute paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data", "tools.json")
    vector_store_path = os.path.join(script_dir, "..", "vector_store", "tools.index")
    
    with open(data_path) as f:
        tools = json.load(f)
    
    vectors = []
    for tool in tools:
        text = f"""
        {tool['tool_name']}
        {tool['use_case']}
        {tool['torque_range']}
        {tool['application_type']}
        {' '.join(tool['specifications'])}
        """
        vectors.append(create_embedding(text))
    
    dim = len(vectors[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(vectors).astype('float32'))

    faiss.write_index(index, vector_store_path)
    print(f"Vector store created successfully with {len(vectors)} vectors at {vector_store_path}")

if __name__ == "__main__":
    build_vector_store()