#!/usr/bin/env python3
"""
Setup script for ArticleCraft application
"""

import os
import sys
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    directories = [
        'templates',
        'static', 
        'models',
        'vector_db'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")

def check_required_files():
    """Check if all required files exist"""
    required_files = [
        'final_nlp_data.csv',
        'models/nextword_model.h5',
        'models/tokenizer.pkl',
        'models/tfidf_vectorizer.pkl',
        'models/tfidf_matrix.pkl',
        'models/nearest_neighbors.pkl'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease ensure all model files and data files are available.")
        return False
    else:
        print("✓ All required files found")
        return True

def check_environment():
    """Check environment variables"""
    if not os.getenv('GROQ_API_KEY'):
        print("⚠️  GROQ_API_KEY environment variable not set")
        print("   You can set it in a .env file or as an environment variable")
        return False
    else:
        print("✓ GROQ_API_KEY found")
        return True

def main():
    """Main setup function"""
    print("🚀 Setting up ArticleCraft application...")
    print("=" * 50)
    
    # Create directories
    create_directories()
    print()
    
    # Check required files
    files_ok = check_required_files()
    print()
    
    # Check environment
    env_ok = check_environment()
    print()
    
    if files_ok and env_ok:
        print("✅ Setup complete! You can now run:")
        print("   python main.py")
    else:
        print("❌ Setup incomplete. Please address the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()