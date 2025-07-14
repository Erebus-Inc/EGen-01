Web Interface
============

Overview
--------

The EGen platform includes a web-based user interface built with Streamlit. This interface provides access to the EGen-01 assistant, model playground, system monitoring, and settings.

Components
---------

Assistant
~~~~~~~~~

The Assistant page provides a chat interface for interacting with the EGen-01 personal assistant:

- Real-time conversation with the EGen-01 assistant
- Conversation history tracking
- File upload capability for document analysis
- Tool usage visualization
- Conversation export/import

.. figure:: _static/assistant_screenshot.png
   :alt: Assistant Interface
   :width: 600px

   The EGen-01 Assistant interface

Model Playground
~~~~~~~~~~~~~~

The Model Playground allows direct interaction with the THL-150 model:

- Text generation with customizable parameters
- Domain selection (code, math, security, general)
- Parameter tuning (temperature, top-p, max length)
- Generation history
- Export generated content

.. figure:: _static/playground_screenshot.png
   :alt: Model Playground
   :width: 600px

   The Model Playground interface

System Monitoring
~~~~~~~~~~~~~~~

The System Monitoring page provides real-time metrics and logs:

- CPU, memory, and GPU usage
- Request rate and latency
- Error rate tracking
- Log viewer with search and filter
- Component status indicators

.. figure:: _static/monitoring_screenshot.png
   :alt: System Monitoring
   :width: 600px

   The System Monitoring interface

Settings
~~~~~~~

The Settings page allows configuration of the EGen platform:

- API connection settings
- Model parameters
- User preferences
- Theme selection
- Log level configuration

.. figure:: _static/settings_screenshot.png
   :alt: Settings
   :width: 600px

   The Settings interface

Usage
-----

Starting the Web Interface
~~~~~~~~~~~~~~~~~~~~~~~~

To start the web interface:

.. code-block:: bash

    # Using Python module
    python -m egen.web.app
    
    # Using Docker
    docker-compose up egen-ui

The interface will be available at http://localhost:8501 by default.

API Connection
~~~~~~~~~~~~

The web interface connects to the EGen API. By default, it connects to http://localhost:8000. You can change this in the Settings page or by setting the `EGEN_API_URL` environment variable.

User Authentication
~~~~~~~~~~~~~~~~~

The web interface supports user authentication. To enable authentication:

1. Set `EGEN_AUTH_ENABLED=true` in your `.env` file
2. Configure authentication providers in the Settings page

Supported authentication methods:

- Username/password
- OAuth (Google, GitHub)
- API key

Customization
------------

Themes
~~~~~~

The web interface supports multiple themes:

- Light
- Dark
- System (follows system preference)
- Custom (user-defined color scheme)

To change the theme, go to the Settings page and select your preferred theme.

Layout
~~~~~~

The layout can be customized in the Settings page:

- Wide mode (full width)
- Centered mode (fixed width)
- Sidebar position (left/right)
- Component visibility

Keyboard Shortcuts
~~~~~~~~~~~~~~~~

The web interface supports keyboard shortcuts:

- `Ctrl+Enter`: Submit message/query
- `Ctrl+L`: Clear conversation
- `Ctrl+S`: Save conversation
- `Ctrl+/`: Show keyboard shortcuts
- `Esc`: Cancel current operation