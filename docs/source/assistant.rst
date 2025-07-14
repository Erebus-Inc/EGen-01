EGen-01 Assistant
===============

Overview
--------

The EGen-01 Assistant is a next-generation personal assistant built on the THL-150 model architecture. It provides contextual understanding, proactive assistance, multi-domain expertise, and personalized interactions to enhance daily productivity.

Architecture
-----------

.. code-block::

    EGen-01 Assistant
    ├── Core
    │   ├── THL-150 Model
    │   ├── Context Manager
    │   └── Tool Registry
    ├── Conversation
    │   ├── Dialog Manager
    │   ├── Memory System
    │   └── Response Generator
    ├── Tools
    │   ├── Web Search
    │   ├── Code Execution
    │   ├── Document Processing
    │   └── External API Connectors
    └── Personalization
        ├── User Preferences
        ├── Interaction History
        └── Adaptation Engine

Components
---------

Core
~~~~

The Core component provides the foundation for the assistant:

- **THL-150 Model**: The underlying transformer model
- **Context Manager**: Maintains conversation context and state
- **Tool Registry**: Manages available tools and their capabilities

Conversation
~~~~~~~~~~~

The Conversation component handles dialog flow:

- **Dialog Manager**: Controls conversation flow and turn-taking
- **Memory System**: Stores and retrieves conversation history
- **Response Generator**: Creates natural language responses

Tools
~~~~~

The Tools component extends the assistant's capabilities:

- **Web Search**: Retrieves information from the internet
- **Code Execution**: Runs and debugs code in various languages
- **Document Processing**: Analyzes and extracts information from documents
- **External API Connectors**: Integrates with third-party services

Personalization
~~~~~~~~~~~~~

The Personalization component adapts to individual users:

- **User Preferences**: Stores user-specific settings and preferences
- **Interaction History**: Tracks past interactions for context
- **Adaptation Engine**: Adjusts behavior based on user patterns

API Reference
------------

Core Module
~~~~~~~~~~

.. code-block:: python

    from egen.assistant.core import EGen01
    
    # Initialize assistant
    assistant = EGen01(
        model_path="/path/to/model",
        tools_config="/path/to/tools_config.json"
    )
    
    # Process a query
    response = assistant.query(
        "What's the weather like today in New York?",
        conversation_id="conv_123",
        user_id="user_456"
    )
    
    # Register a custom tool
    assistant.register_tool(
        name="weather_api",
        description="Get current weather information",
        function=get_weather,
        parameters={
            "location": {"type": "string", "description": "City name"},
            "units": {"type": "string", "enum": ["metric", "imperial"]}
        }
    )
    
    # Set user preferences
    assistant.set_user_preference(
        user_id="user_456",
        preference="temperature",
        value=0.7
    )
    
    # Clear conversation history
    assistant.clear_conversation_history("conv_123")

Conversation Module
~~~~~~~~~~~~~~~~

.. code-block:: python

    from egen.assistant.conversation import ConversationManager
    
    # Initialize conversation manager
    conversation_manager = ConversationManager(
        memory_type="vector_store"  # or "in_memory", "database"
    )
    
    # Add message to conversation
    conversation_manager.add_message(
        conversation_id="conv_123",
        role="user",
        content="What's the weather like today in New York?"
    )
    
    # Get conversation history
    history = conversation_manager.get_history(
        conversation_id="conv_123",
        max_messages=10
    )
    
    # Search conversations
    results = conversation_manager.search(
        query="weather new york",
        user_id="user_456",
        max_results=5
    )
    
    # Export conversation
    exported = conversation_manager.export_conversation(
        conversation_id="conv_123",
        format="json"  # or "markdown", "text"
    )

Tools Module
~~~~~~~~~~

.. code-block:: python

    from egen.assistant.tools import ToolRegistry, WebSearch, CodeExecutor
    
    # Initialize tool registry
    tool_registry = ToolRegistry()
    
    # Register built-in tools
    web_search = WebSearch(api_key="YOUR_SEARCH_API_KEY")
    tool_registry.register(web_search)
    
    code_executor = CodeExecutor(supported_languages=["python", "javascript"])
    tool_registry.register(code_executor)
    
    # Create custom tool
    from egen.assistant.tools import Tool
    
    def get_weather(location, units="metric"):
        # Implementation
        return {"temperature": 22, "conditions": "sunny"}
    
    weather_tool = Tool(
        name="weather_api",
        description="Get current weather information",
        function=get_weather,
        parameters={
            "location": {"type": "string", "description": "City name"},
            "units": {"type": "string", "enum": ["metric", "imperial"]}
        }
    )
    
    tool_registry.register(weather_tool)
    
    # Execute tool
    result = tool_registry.execute(
        tool_name="weather_api",
        parameters={"location": "New York", "units": "metric"}
    )

Personalization Module
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from egen.assistant.personalization import PersonalizationManager
    
    # Initialize personalization manager
    personalization = PersonalizationManager(
        storage_path="/path/to/user_data"
    )
    
    # Set user preference
    personalization.set_preference(
        user_id="user_456",
        preference="temperature",
        value=0.7
    )
    
    # Get user preference
    temperature = personalization.get_preference(
        user_id="user_456",
        preference="temperature",
        default=0.8
    )
    
    # Track interaction
    personalization.track_interaction(
        user_id="user_456",
        interaction_type="query",
        data={"query": "weather", "tools_used": ["weather_api"]}
    )
    
    # Get user profile
    profile = personalization.get_user_profile("user_456")

Configuration
-------------

The EGen-01 Assistant can be configured through a JSON configuration file:

.. code-block:: json

    {
      "model": {
        "path": "/path/to/model",
        "temperature": 0.7,
        "max_tokens": 1000
      },
      "conversation": {
        "memory_type": "vector_store",
        "memory_path": "/path/to/memory",
        "max_history": 20
      },
      "tools": {
        "web_search": {
          "enabled": true,
          "api_key": "${SEARCH_API_KEY}"
        },
        "code_execution": {
          "enabled": true,
          "supported_languages": ["python", "javascript", "bash"],
          "timeout": 10
        },
        "document_processing": {
          "enabled": true,
          "supported_formats": ["pdf", "docx", "txt"]
        }
      },
      "personalization": {
        "enabled": true,
        "storage_path": "/path/to/user_data",
        "adaptation": {
          "enabled": true,
          "learning_rate": 0.1
        }
      }
    }

Usage Examples
-------------

Basic Assistant Usage
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from egen.assistant import EGen01
    
    # Initialize assistant
    assistant = EGen01(config_path="assistant_config.json")
    
    # Simple query
    response = assistant.query("What's the capital of France?")
    print(response)
    
    # Query with conversation context
    response = assistant.query(
        "What's the population?",  # Follow-up question
        conversation_id="conv_123"
    )
    print(response)
    
    # Query with tool usage
    response = assistant.query(
        "What's the weather like in Paris today?",
        conversation_id="conv_123",
        allow_tools=["web_search", "weather_api"]
    )
    print(response)

Custom Tool Integration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from egen.assistant import EGen01
    
    # Define custom tool function
    def database_query(query, database="users"):
        # Implementation to query database
        if database == "users":
            return [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
        return []
    
    # Initialize assistant
    assistant = EGen01()
    
    # Register custom tool
    assistant.register_tool(
        name="database_query",
        description="Query database for information",
        function=database_query,
        parameters={
            "query": {"type": "string", "description": "SQL query or natural language query"},
            "database": {"type": "string", "description": "Database name", "default": "users"}
        }
    )
    
    # Use assistant with custom tool
    response = assistant.query(
        "How many users are in the database?",
        allow_tools=["database_query"]
    )
    print(response)

Web Application Integration
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import streamlit as st
    from egen.assistant import EGen01
    
    # Initialize assistant
    assistant = EGen01()
    
    # Streamlit UI
    st.title("EGen-01 Assistant")
    
    # Initialize session state
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = "conv_" + str(hash(st.session_state))
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    user_input = st.chat_input("Ask something...")
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
        
        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = assistant.query(
                    user_input,
                    conversation_id=st.session_state.conversation_id
                )
                st.write(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})