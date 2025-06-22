#!/usr/bin/env python3
"""
Test script for speech synthesis and audio playback
"""

import asyncio
import sys
import os
from ai_agent import SmartStudentAIAgent

# Test LMNT SDK directly
try:
    from lmnt.api import Speech
    LMNT_AVAILABLE = True
except ImportError:
    LMNT_AVAILABLE = False

async def test_lmnt_direct():
    """Test LMNT SDK directly"""
    if not LMNT_AVAILABLE:
        print("⚠️ LMNT SDK not available for direct testing")
        return False
    
    try:
        print("🧪 Testing LMNT SDK directly...")
        
        # Set API key
        api_key = os.getenv('LMNT_API_KEY') or "ak_GkxGopYg9FwhJaQkJ9huMC"
        
        async with Speech(api_key=api_key) as speech:
            synthesis = await speech.synthesize('Hello! This is a direct LMNT test.', 'lily')
            
            # Handle different possible response formats
            if hasattr(synthesis, 'audio'):
                audio_data = synthesis.audio
            elif isinstance(synthesis, dict) and 'audio' in synthesis:
                audio_data = synthesis['audio']
            else:
                # Try to access as bytes directly
                audio_data = synthesis
            
            print(f"✅ Direct LMNT synthesis successful ({len(audio_data)} bytes)")
            
            # Save test file
            with open('lmnt_test.mp3', 'wb') as f:
                f.write(audio_data)
            print("✅ Test audio saved as lmnt_test.mp3")
            return True
            
    except Exception as e:
        print(f"❌ Direct LMNT test failed: {e}")
        return False

async def test_speech():
    """Test speech synthesis and playback"""
    print("🎤 Testing Speech Synthesis System...")
    
    try:
        # Initialize AI agent
        agent = SmartStudentAIAgent()
        
        # Test messages
        test_messages = [
            "Hello! This is a test of the speech system.",
            "Great job staying focused on your studies!",
            "Let's get back to productive learning activities."
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n🗣️ Test {i}: {message}")
            
            # Test synthesis
            audio_data = await agent.synthesize_speech(message)
            if audio_data:
                print(f"✅ Speech synthesized successfully ({len(audio_data)} bytes)")
                
                # Test playback
                success = agent.play_speech(audio_data)
                if success:
                    print("✅ Audio playback successful")
                else:
                    print("❌ Audio playback failed")
            else:
                print("❌ Speech synthesis failed")
            
            # Wait between tests
            if i < len(test_messages):
                print("⏳ Waiting 2 seconds...")
                await asyncio.sleep(2)
        
        print("\n🎉 Speech test completed!")
        
    except Exception as e:
        print(f"❌ Test error: {e}")

def main():
    """Main test function"""
    print("🧪 Speech System Test")
    print("=" * 30)
    
    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ Warning: No OpenAI API key found")
        print("Speech synthesis will use fallback methods only")
    
    async def run_all_tests():
        # Test LMNT directly first
        await test_lmnt_direct()
        print("\n" + "="*30 + "\n")
        
        # Test through AI agent
        await test_speech()
    
    # Run async tests
    asyncio.run(run_all_tests())

if __name__ == "__main__":
    main() 