"""
Run the FastAPI web server.
"""
import uvicorn
import os
import sys
sys.path.insert(0, '/app')

from securnote.logging_config import setup_logging
from securnote.web.main import app

if __name__ == "__main__":
    # Setup logging first
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    setup_logging(log_level)

    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)