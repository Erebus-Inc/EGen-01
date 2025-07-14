API Reference
============

Overview
--------

The EGen platform provides a comprehensive REST API built with FastAPI. This API allows you to interact with the THL-150 model, the EGen-01 assistant, and various platform components.

Endpoints
---------

Health Check
~~~~~~~~~~~

.. code-block:: text

    GET /health

Returns the health status of the API.

**Response**:

.. code-block:: json

    {
        "status": "ok",
        "version": "1.0.0"
    }

Model Inference
~~~~~~~~~~~~~

.. code-block:: text

    POST /v1/generate

Generate text using the THL-150 model.

**Request Body**:

.. code-block:: json

    {
        "prompt": "def fibonacci(n):",
        "max_length": 100,
        "temperature": 0.7,
        "domain": "code"
    }

**Response**:

.. code-block:: json

    {
        "generated_text": "def fibonacci(n):\n    if n <= 0:\n        return 0\n    elif n == 1:\n        return 1\n    else:\n        return fibonacci(n-1) + fibonacci(n-2)",
        "model": "thl150",
        "generation_time": 0.856
    }

Assistant Query
~~~~~~~~~~~~~

.. code-block:: text

    POST /v1/assistant/query

Send a query to the EGen-01 assistant.

**Request Body**:

.. code-block:: json

    {
        "query": "What's the best way to implement a binary search tree in Python?",
        "conversation_id": "conv_123456",
        "user_id": "user_789"
    }

**Response**:

.. code-block:: json

    {
        "response": "To implement a binary search tree in Python, you can start by creating a Node class...",
        "conversation_id": "conv_123456",
        "tools_used": ["code_search", "documentation_lookup"]
    }

System Monitoring
~~~~~~~~~~~~~~~

.. code-block:: text

    GET /v1/system/metrics

Get system metrics.

**Response**:

.. code-block:: json

    {
        "cpu_usage": 45.2,
        "memory_usage": 8.7,
        "gpu_usage": 78.3,
        "requests_per_minute": 120,
        "average_latency_ms": 156
    }

Authentication
-------------

The API uses API key authentication. Include your API key in the request header:

.. code-block:: text

    Authorization: Bearer YOUR_API_KEY

Error Handling
-------------

The API returns standard HTTP status codes:

- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error

Error responses include a JSON body with error details:

.. code-block:: json

    {
        "error": {
            "code": "invalid_input",
            "message": "The prompt field is required"
        }
    }

Rate Limiting
------------

The API implements rate limiting to ensure fair usage. Limits are included in response headers:

.. code-block:: text

    X-RateLimit-Limit: 100
    X-RateLimit-Remaining: 95
    X-RateLimit-Reset: 1620000000

Client Libraries
--------------

Python Client
~~~~~~~~~~~~

.. code-block:: python

    from egen_client import EGenClient
    
    client = EGenClient(api_key="YOUR_API_KEY")
    
    # Generate text
    response = client.generate(prompt="def fibonacci(n):", max_length=100, domain="code")
    print(response.generated_text)
    
    # Query assistant
    response = client.assistant_query("What's the best way to implement a binary search tree in Python?")
    print(response.response)

JavaScript Client
~~~~~~~~~~~~~~~

.. code-block:: javascript

    import { EGenClient } from 'egen-client';
    
    const client = new EGenClient({ apiKey: 'YOUR_API_KEY' });
    
    // Generate text
    client.generate({
      prompt: 'def fibonacci(n):',
      maxLength: 100,
      domain: 'code'
    }).then(response => {
      console.log(response.generatedText);
    });
    
    // Query assistant
    client.assistantQuery({
      query: "What's the best way to implement a binary search tree in Python?"
    }).then(response => {
      console.log(response.response);
    });