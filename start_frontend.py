#!/usr/bin/env python3
"""
Quick startup script for the WorthIt Basketball Shoe Recommendation System
with beautiful frontend
"""

import os
import sys
import subprocess
import time
import webbrowser

def main():
    print("🏀 Starting WorthIt Basketball Shoe Recommendation System")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("❌ Error: main.py not found. Please run this from the project root.")
        sys.exit(1)
    
    # Start the API server
    print("🚀 Starting API server...")
    print("📡 Server will be available at http://localhost:8000")
    print("🎨 Beautiful frontend at http://localhost:8000")
    print("📚 API documentation at http://localhost:8000/docs")
    print("")
    print("💡 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Wait a moment then open browser
        def open_browser():
            time.sleep(2)
            webbrowser.open("http://localhost:8000")
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Start the server
        subprocess.run([
            sys.executable, "main.py", "serve", "--port", "8000"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down WorthIt system. Thanks for using it!")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 