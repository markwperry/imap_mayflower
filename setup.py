#!/usr/bin/env python3
"""
Setup script for imap_mayflower
This script helps users set up their environment for the first time.
"""

import os
import shutil
import sys

def main():
    print("🚀 Setting up imap_mayflower...")
    
    # Check if .env already exists
    if os.path.exists('.env'):
        print("⚠️  .env file already exists. Skipping creation.")
        print("   If you want to reconfigure, delete .env and run this script again.")
        return
    
    # Check if .env.example exists
    if not os.path.exists('.env.example'):
        print("❌ .env.example file not found. Please ensure you're in the correct directory.")
        sys.exit(1)
    
    # Copy .env.example to .env
    try:
        shutil.copy('.env.example', '.env')
        print("✅ Created .env file from template")
        print("\n📝 Next steps:")
        print("   1. Edit .env file with your actual email credentials")
        print("   2. Run: python execute.py")
        print("\n🔒 Security reminder:")
        print("   - Never commit your .env file to version control")
        print("   - Use app-specific passwords when possible")
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
