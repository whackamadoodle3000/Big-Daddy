#!/usr/bin/env python3
"""
Test script for intervention speech feedback
Demonstrates how the AI speaks when performing serious interventions
"""

import asyncio
import sys
import os
from ai_agent import SmartStudentAIAgent

async def test_intervention_speech():
    """Test speech feedback for different types of interventions"""
    print("🎤 Testing Intervention Speech Feedback...")
    
    try:
        # Initialize AI agent
        agent = SmartStudentAIAgent()
        
        # Test scenarios with different urgency levels
        test_scenarios = [
            {
                "name": "🚨 High Urgency - Inappropriate Content",
                "analysis": {
                    'recommendation': 'intervene',
                    'current_url': 'https://tinder.com',
                    'time_on_site': 120,
                    'message': 'Inappropriate content detected. Redirecting to educational resources.',
                    'reasoning': 'inappropriate domain "tinder.com" detected',
                    'urgency': 'high',
                    'pattern_analysis': {'focus_score': 3}
                }
            },
            {
                "name": "⚠️ Medium Urgency - Long Distraction",
                "analysis": {
                    'recommendation': 'intervene',
                    'current_url': 'https://youtube.com/watch?v=funny_video',
                    'time_on_site': 450,  # 7.5 minutes
                    'message': 'Extended time on distracting content. Redirecting to educational resources.',
                    'reasoning': 'Extended time on distracting site',
                    'urgency': 'medium',
                    'pattern_analysis': {'focus_score': 4}
                }
            },
            {
                "name": "🎉 Encouragement - Educational Content",
                "analysis": {
                    'recommendation': 'encourage',
                    'current_url': 'https://khanacademy.org/math',
                    'time_on_site': 300,
                    'message': 'Great job staying focused on your studies!',
                    'reasoning': 'Educational site detected',
                    'urgency': 'low',
                    'pattern_analysis': {'focus_score': 8}
                }
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n{'='*50}")
            print(f"🧪 Test {i}: {scenario['name']}")
            print(f"{'='*50}")
            
            analysis = scenario['analysis']
            
            # Show scenario details
            print(f"📍 URL: {analysis['current_url']}")
            print(f"⏱️ Time on site: {analysis['time_on_site']/60:.1f} minutes")
            print(f"🎯 Recommendation: {analysis['recommendation']}")
            print(f"⚡ Urgency: {analysis['urgency']}")
            print(f"🔍 Reasoning: {analysis['reasoning']}")
            
            # Test if speech should be given
            should_speak = agent.should_give_speech_feedback(analysis)
            print(f"🗣️ Should give speech: {'YES' if should_speak else 'NO'}")
            
            if should_speak:
                # Generate speech message
                speech_message = agent.generate_speech_message(analysis)
                print(f"💬 Generated speech: \"{speech_message}\"")
                
                # Test speech synthesis (but don't play to avoid spam)
                print("🎤 Testing speech synthesis...")
                audio_data = await agent.synthesize_speech(speech_message)
                if audio_data:
                    print(f"✅ Speech synthesized successfully ({len(audio_data)} bytes)")
                else:
                    print("❌ Speech synthesis failed")
            
            # Wait between tests
            if i < len(test_scenarios):
                print("\n⏳ Waiting 3 seconds before next test...")
                await asyncio.sleep(3)
        
        print(f"\n🎉 All intervention speech tests completed!")
        print(f"\n💡 Key Features Demonstrated:")
        print(f"• 🚨 High urgency interventions ALWAYS get speech feedback")
        print(f"• 💬 AI generates contextual, caring messages")
        print(f"• 🎯 Different message styles for different intervention types")
        print(f"• 🗣️ Explains the reasoning and suggests alternatives")
        
    except Exception as e:
        print(f"❌ Test error: {e}")

def main():
    """Main test function"""
    print("🧪 Intervention Speech Feedback Test")
    print("=" * 40)
    print("This test demonstrates how the AI provides")
    print("detailed speech feedback for interventions,")
    print("especially serious ones involving inappropriate content.")
    print()
    
    # Run async test
    asyncio.run(test_intervention_speech())

if __name__ == "__main__":
    main() 