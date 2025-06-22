#!/usr/bin/env python3
"""
Debug script to understand LMNT API response format
"""

import asyncio
import os
from lmnt.api import Speech

async def debug_lmnt():
    """Debug LMNT API response format"""
    try:
        print("🧪 Debugging LMNT API response format...")
        
        # Set API key
        api_key = os.getenv('LMNT_API_KEY') or "ak_GkxGopYg9FwhJaQkJ9huMC"
        
        async with Speech(api_key=api_key) as speech:
            synthesis = await speech.synthesize('Hello world.', 'leah')
            
            print(f"✅ Synthesis completed")
            print(f"📊 Synthesis type: {type(synthesis)}")
            print(f"📊 Synthesis keys: {synthesis.keys() if hasattr(synthesis, 'keys') else 'No keys'}")
            print(f"📊 Synthesis dir: {dir(synthesis)}")
            
            # Try different ways to access audio data
            if hasattr(synthesis, 'audio'):
                print(f"✅ Found synthesis.audio: {type(synthesis.audio)}")
                audio_data = synthesis.audio
            elif 'audio' in synthesis:
                print(f"✅ Found synthesis['audio']: {type(synthesis['audio'])}")
                audio_data = synthesis['audio']
            else:
                print(f"❌ Could not find audio data in synthesis")
                print(f"📊 Full synthesis object: {synthesis}")
                return
            
            print(f"✅ Audio data type: {type(audio_data)}")
            print(f"✅ Audio data length: {len(audio_data)} bytes")
            
            # Save test file
            with open('debug_test.mp3', 'wb') as f:
                f.write(audio_data)
            print("✅ Test audio saved as debug_test.mp3")
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_lmnt()) 