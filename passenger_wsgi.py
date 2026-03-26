import sys
import os

# Configure explicit absolute directory binding
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import the core ASGI FastAPI orchestrator
from main import app as fastapi_app

# Execute standard WSGI encapsulation utilizing the generic a2wsgi standard required by Hostinger
try:
    from a2wsgi import ASGIMiddleware
    application = ASGIMiddleware(fastapi_app)
except ImportError:
    # Failsafe logging strictly for deployment tracking
    with open(os.path.join(current_dir, "wsgi_error.log"), "a") as f:
        f.write("CRITICAL: a2wsgi dependency not found in execution environment.\n")
