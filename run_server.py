#!/usr/bin/env python3
"""Simple script to run the MCP Firmware Analysis Server."""

import sys
import os
import subprocess

def main():
    """Run the MCP Firmware Analysis Server."""
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Set PYTHONPATH environment variable
    os.environ['PYTHONPATH'] = current_dir
    
    try:
        # Run uvicorn with the proper module path
        cmd = [
            sys.executable, "-m", "uvicorn",
            "src.api.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ]
        
        print("🚀 Starting MCP Firmware Analysis Server...")
        print("📍 Server will be available at: http://localhost:8000")
        print("🔧 API documentation at: http://localhost:8000/docs")
        print("💡 Health check at: http://localhost:8000/health")
        print("\nPress Ctrl+C to stop the server.\n")
        
        subprocess.run(cmd, cwd=current_dir)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user.")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("\n💡 Try running directly with:")
        print("   python -c \"import sys; sys.path.insert(0, '.'); from src.api.main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)\"")

if __name__ == "__main__":
    main() 