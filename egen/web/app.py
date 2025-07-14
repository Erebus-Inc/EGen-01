"""Streamlit web interface for the EGen platform."""

import os
import requests
import streamlit as st
import json
import time

# Set page configuration
st.set_page_config(
    page_title="EGen Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Define API connection parameters
API_HOST = os.environ.get("API_HOST", "localhost")
API_PORT = os.environ.get("API_PORT", "8000")
API_URL = f"http://{API_HOST}:{API_PORT}"

# Initialize session state
if "conversation" not in st.session_state:
    st.session_state.conversation = []

# Header
st.title("🧠 EGen Platform: Unified AI Ecosystem")

# Sidebar
with st.sidebar:
    st.image("https://cdn-avatars.huggingface.co/v1/production/uploads/66d6d5bf429249ec731ab9f1/l8wozd27QoCO6PqDEkj-6.png", width=150)
    st.header("Navigation")
    page = st.radio(
        "Select a page:",
        ["Assistant", "Model Playground", "Monitoring", "Settings"],
    )
    
    st.header("Model Configuration")
    model_precision = st.selectbox(
        "Model Precision",
        ["fp16", "fp32", "int8", "int4"],
        index=0,
    )
    
    st.header("About")
    st.markdown("""
    **EGen Platform** combines enterprise-grade AI infrastructure with personal assistant capabilities.
    
    - **EGen V1**: Self-healing, self-optimizing enterprise AI system
    - **EGen-01**: Next-generation personal assistant
    
    [GitHub](https://github.com/Erebus-Inc/EGen-01.git) | [Documentation](https://docs.egen.ai)
    """)

# Main content
if page == "Assistant":
    st.header("EGen-01 Personal Assistant")
    
    # Chat interface
    st.subheader("Chat")
    
    # Display conversation history
    for message in st.session_state.conversation:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Input for new message
    prompt = st.chat_input("Ask me anything...")
    if prompt:
        # Add user message to conversation
        st.session_state.conversation.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get response from API
        try:
            with st.spinner("Thinking..."):
                # Simulate API call (replace with actual API call when available)
                time.sleep(1)  # Simulate processing time
                
                # Mock response (replace with actual API call)
                response = {
                    "text": f"I understand your query about '{prompt[:30]}...'. This is a placeholder response from the EGen-01 assistant.",
                    "tools_used": [],
                    "confidence": 0.95,
                }
                
                # Add assistant response to conversation
                st.session_state.conversation.append({"role": "assistant", "content": response["text"]})
                
                # Display assistant response
                with st.chat_message("assistant"):
                    st.write(response["text"])
        except Exception as e:
            st.error(f"Error: {str(e)}")

elif page == "Model Playground":
    st.header("Model Playground")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Input")
        prompt_type = st.selectbox(
            "Prompt Type",
            ["Text", "Code", "Math"],
            index=0,
        )
        
        prompt = st.text_area("Enter your prompt:", height=200)
        
        temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
        max_tokens = st.slider("Max Tokens", 10, 4096, 1024, 10)
        
        if st.button("Generate"):
            with st.spinner("Generating..."):
                # Simulate API call (replace with actual API call when available)
                time.sleep(2)  # Simulate processing time
                
                # Mock response (replace with actual API call)
                response = f"This is a placeholder response for the prompt: '{prompt[:30]}...'"
                
                # Display response in the second column
                with col2:
                    st.subheader("Output")
                    st.text_area("Generated output:", response, height=400)
    
    if "output" not in locals():
        with col2:
            st.subheader("Output")
            st.text_area("Generated output will appear here...", "", height=400)

elif page == "Monitoring":
    st.header("System Monitoring")
    
    tabs = st.tabs(["Performance", "Logs", "Resources"])
    
    with tabs[0]:
        st.subheader("Performance Metrics")
        st.markdown("""Grafana dashboard integration will be available here.""")
        
        # Placeholder metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Inference Speed", "45 ms/token", "-5 ms")
        with col2:
            st.metric("Error Rate", "0.3%", "-0.1%")
        with col3:
            st.metric("Uptime", "99.9%", "")
    
    with tabs[1]:
        st.subheader("System Logs")
        st.text_area(
            "",
            """2025-06-15 12:34:56 INFO Starting EGen platform
2025-06-15 12:34:57 INFO Loading THL-150 model
2025-06-15 12:35:02 INFO Model loaded successfully
2025-06-15 12:35:03 INFO API server started at 0.0.0.0:8000""",
            height=300,
        )
    
    with tabs[2]:
        st.subheader("Resource Usage")
        
        # Placeholder resource usage
        st.markdown("**GPU Usage**")
        st.progress(0.7)
        st.markdown("**Memory Usage**")
        st.progress(0.5)
        st.markdown("**CPU Usage**")
        st.progress(0.3)

elif page == "Settings":
    st.header("Settings")
    
    st.subheader("User Preferences")
    st.checkbox("Enable notifications")
    st.checkbox("Dark mode")
    
    st.subheader("API Configuration")
    st.text_input("API Host", API_HOST)
    st.text_input("API Port", API_PORT)
    
    st.subheader("Security")
    st.text_input("Username", "admin")
    st.text_input("Password", "", type="password")
    
    if st.button("Save Settings"):
        st.success("Settings saved successfully!")