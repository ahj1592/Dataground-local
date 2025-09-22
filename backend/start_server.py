#!/usr/bin/env python3
"""
Startup script for DataGround backend with environment variable debugging
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Check if environment variables are properly set"""
    print("🔍 Checking environment variables...")
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found")
    else:
        print("❌ .env file not found")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("✅ OPENAI_API_KEY is set")
        print(f"   Key starts with: {api_key[:10]}...")
    else:
        print("❌ OPENAI_API_KEY is not set")
        return False
    
    # Check other important variables
    secret_key = os.getenv("SECRET_KEY")
    if secret_key:
        print("✅ SECRET_KEY is set")
    else:
        print("⚠️  SECRET_KEY is not set (using default)")
    
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        print("✅ DATABASE_URL is set")
    else:
        print("⚠️  DATABASE_URL is not set (using default SQLite)")
    
    return True

def start_server():
    """Start the FastAPI server"""
    print("\n🚀 Starting DataGround backend server...")
    
    try:
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Server startup error: {e}")
        return False

def main():
    """Main function"""
    print("=" * 50)
    print("DataGround Backend Startup")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please fix the issues above.")
        sys.exit(1)
    
    print("\n✅ Environment check passed!")
    
    # Start server
    start_server()

if __name__ == "__main__":
    main() 