#!/usr/bin/env python3
"""
Setup script for Smart Student Monitor
Helps users create their .env file with API keys
"""

import os
import sys

def create_env_file():
    """Create a .env file with user input"""
    print("🎓 Smart Student Monitor - Environment Setup")
    print("=" * 50)
    
    # Check if .env already exists
    if os.path.exists('.env'):
        print("⚠️ .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ").lower()
        if response != 'y':
            print("Setup cancelled.")
            return
    
    print("\n📝 Let's set up your configuration:")
    
    # Get OpenAI API key
    print("\n🔑 OpenAI API Key:")
    print("   Get your API key from: https://platform.openai.com/api-keys")
    openai_key = input("   Enter your OpenAI API key: ").strip()
    
    if not openai_key:
        print("❌ OpenAI API key is required!")
        return
    
    # Get LMNT API key (optional)
    print("\n🗣️ LMNT API Key (optional):")
    print("   Get your API key from: https://lmnt.com/")
    print("   Leave blank to use default")
    lmnt_key = input("   Enter your LMNT API key: ").strip()
    
    # Get monitoring intervals
    print("\n⏱️ Monitoring Intervals:")
    browser_interval = input("   Browser monitoring interval (default: 5): ").strip() or "5"
    ai_interval = input("   AI analysis interval (default: 15): ").strip() or "15"
    
    # Get other settings
    print("\n⚙️ Other Settings:")
    speech_enabled = input("   Enable speech feedback? (Y/n): ").lower() != 'n'
    headless_mode = input("   Run in headless mode? (y/N): ").lower() == 'y'
    
    # Create .env content
    env_content = f"""# OpenAI API Configuration
OPENAI_API_KEY={openai_key}

# LMNT API Configuration (optional - uses default if not set)
LMNT_API_KEY={lmnt_key or "ak_GkxGopYg9FwhJaQkJ9huMC"}

# Monitoring Configuration
BROWSER_INTERVAL={browser_interval}
AI_INTERVAL={ai_interval}

# Speech Configuration
SPEECH_ENABLED={'true' if speech_enabled else 'false'}
SPEECH_COOLDOWN=120

# Browser Configuration
HEADLESS_MODE={'true' if headless_mode else 'false'}
"""
    
    # Write .env file
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print(f"\n✅ .env file created successfully!")
        print(f"📁 Location: {os.path.abspath('.env')}")
        
        # Test configuration
        print("\n🧪 Testing configuration...")
        try:
            from config import validate_config, get_config_summary
            if validate_config():
                print("✅ Configuration is valid!")
                print("\n📋 Current settings:")
                config_summary = get_config_summary()
                for key, value in config_summary.items():
                    print(f"   • {key}: {value}")
            else:
                print("❌ Configuration validation failed!")
        except Exception as e:
            print(f"⚠️ Could not validate configuration: {e}")
        
        print(f"\n🚀 You're ready to run the Smart Student Monitor!")
        print(f"   Run: python main_ui.py")
        print(f"   Or: python student_monitor.py")
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Smart Student Monitor Environment Setup")
        print("Usage: python setup_env.py")
        print("\nThis script will help you create a .env file with your API keys and settings.")
        return
    
    create_env_file()

if __name__ == "__main__":
    main() 