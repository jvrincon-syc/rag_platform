"""Launch the full SST API (with platform routes) on port 8000 via uvicorn."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "back", "src"))

from api.app import create_app
from api.dependencies import build_pipeline_services

os.environ.setdefault("CHATBOT_RUNTIME_WORKER_MODE", "warm")

services = build_pipeline_services()
app = create_app(services=services)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
