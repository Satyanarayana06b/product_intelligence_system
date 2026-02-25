import streamlit as st
import requests
import os

st.title("Industrial Tool Recommendor")

# Initialize session state for conversation tracking
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "conversation_count" not in st.session_state:
    st.session_state.conversation_count = 0

user_input = st.text_input("Ask about tools")

if user_input:
    with st.spinner("Finding the best tool for you..."):
        try:
            payload = {
                "question": user_input,
                "session_id": st.session_state.session_id
            }
            response = requests.post(
                "http://127.0.0.1:8000/chat", json=payload)
            
            response_data = response.json()
            data = response_data["response"]
            
            # Update session ID
            if "session_id" in response_data:
                st.session_state.session_id = response_data["session_id"]
                st.session_state.conversation_count += 1
        except Exception as e:
            st.error(f"Failed to connect to backend: {str(e)}")
            st.stop()
    
    # Check if clarification is needed
    if isinstance(data, dict) and data.get("status") == "needs_clarification":
        st.warning("🤔 I need more information to help you better")
        st.info(data.get("message", "Could you provide more details?"))
        
        # Display clarification questions
        questions = data.get("questions", [])
        if questions:
            st.markdown("**Please answer:**")
            for q in questions:
                st.markdown(f"• {q}")
        
        # Display suggestions if available
        suggestions = data.get("suggestions", {})
        if suggestions:
            with st.expander("💡 Available Options"):
                for key, values in suggestions.items():
                    if isinstance(values, list) and values:
                        st.markdown(f"**{key.replace('_', ' ').title()}:**")
                        st.write(", ".join(str(v) for v in values))
        
        st.markdown("---")
        st.info("💭 Try rephrasing your query with more specific details from the options above")
    
    # Check if there's an error
    elif isinstance(data, dict) and "error" in data:
        st.warning("⚠️ No matching tools found")
        st.info("Try rephrasing your query or use more general terms like 'nutrunner', 'screwdriver', or 'torque tool'")
        if "raw" in data:
            with st.expander("Debug Info"):
                st.text(data["raw"])
    elif isinstance(data, dict) and data.get("tool_name") and data.get("tool_name") != "N/A":
        # Display results from JSON only if valid data exists
        st.header("Recommended Tool")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(data.get("tool_name", "N/A"))
            st.write(f"**Model:** {data.get('model', 'N/A')}")
            
            if data.get("why_recommended"):
                st.write("**Why this tool:**")
                st.write(data["why_recommended"])
            
            st.write("### Technical Specifications")
            key_specs = data.get("key_specs", [])
            if key_specs:
                for spec in key_specs:
                    st.write(f"• {spec}")
            else:
                st.write("No specifications available")
            
            st.write(f"**Voltage:** {data.get('voltage', 'N/A')}")
            st.write(f"**IP Rating:** {data.get('ip_rating', 'N/A')}")
        
        with col2:
            image_path = data.get("image_path")
            if image_path and os.path.exists(image_path):
                st.image(image_path, use_container_width=True)
            else:
                st.info("Image not available")
    else:
        st.warning("⚠️ No matching tools found")
        st.info("Try rephrasing your query or use more general terms like 'nutrunner', 'screwdriver', or 'torque tool'")
else:
    # Show placeholder when no input
    st.info("👆 Enter a tool name or description to get started")
    
    # Show session info if active
    if st.session_state.session_id:
        with st.expander("ℹ️ Session Info"):
            st.write(f"**Session ID:** `{st.session_state.session_id[:8]}...`")
            st.write(f"**Queries in session:** {st.session_state.conversation_count}")
            st.caption("The system remembers your preferences within this session")
    
    st.markdown("""
    **Examples:**
    - nutrunner
    - handheld screwdriver
    - torque tool for assembly
    """)

