import uvicorn
import os
import argparse
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()
import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Default configuration
DEFAULT_HOST = os.getenv("HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("PORT", "8000"))
DEFAULT_WORKERS = int(os.getenv("WORKERS", "1"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

def parse_args():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(description="SympAI API Server")
    
    parser.add_argument(
        "--host",
        type=str,
        default=DEFAULT_HOST,
        help=f"Host to bind the server to (default: {DEFAULT_HOST})"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to bind the server to (default: {DEFAULT_PORT})"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Number of worker processes (default: {DEFAULT_WORKERS})"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        default=True,
        help="Enable auto-reload on code changes (development mode)"
    )
    
    return parser.parse_args()

def main():
    """
    Main entry point for the server
    """
    args = parse_args()
    
    # Configure uvicorn logging
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    
    if DEBUG:
        print("Starting server with configuration:")
        print(f"  Host: {args.host}")
        print(f"  Port: {args.port}")
        print(f"  Workers: {args.workers}")
        print(f"  Reload: {args.reload}")
        print(f"  Debug: {DEBUG}")
    
    # Start the server
    uvicorn.run(
        "server.app.main:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        log_config=log_config,
        log_level="debug" if DEBUG else "info"
    )

if __name__ == "__main__":
    main()
