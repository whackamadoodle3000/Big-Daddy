#!/usr/bin/env python3
"""
Combined Student Monitor
Runs both browser monitoring and AI agent together
Enhanced with Smart AI Analysis
"""

import os
import sys
import time
import threading
import argparse
from datetime import datetime

# Import our modules
from browser_monitor_fixed import BrowserMonitor
from ai_agent import SmartStudentAIAgent


class SmartStudentMonitor:
    def __init__(self, openai_api_key: str = None, headless: bool = False, lmnt_api_key: str = None):
        """Initialize the smart student monitoring system"""
        self.openai_api_key = openai_api_key
        self.lmnt_api_key = lmnt_api_key
        self.headless = headless
        self.running = False
        
        # Initialize components
        self.browser_monitor = None
        self.ai_agent = None
        
        # Monitoring settings
        self.browser_interval = 5  # Browser monitoring every 5 seconds
        self.ai_interval = 15      # AI analysis every 15 seconds
        
    def initialize_components(self):
        """Initialize browser monitor and AI agent"""
        try:
            print("🚀 Initializing Smart Student Monitoring System...")
            
            # Initialize browser monitor
            print("📱 Starting browser monitor...")
            self.browser_monitor = BrowserMonitor(headless=self.headless)
            
            # Initialize AI agent
            print("🧠 Starting smart AI agent...")
            self.ai_agent = SmartStudentAIAgent(
                openai_api_key=self.openai_api_key,
                lmnt_api_key=self.lmnt_api_key
            )
            
            # Connect browser monitor to AI agent
            self.ai_agent.set_browser_monitor(self.browser_monitor)
            
            print("✅ All components initialized successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing components: {e}")
            return False
    
    def start_browser_monitoring(self):
        """Start browser monitoring in a separate thread"""
        def browser_thread():
            try:
                if self.browser_monitor.launch_firefox():
                    print(f"🌐 Browser monitoring started (interval: {self.browser_interval}s)")
                    self.browser_monitor.start_monitoring(interval=self.browser_interval)
                else:
                    print("❌ Failed to launch browser")
                    self.running = False
            except Exception as e:
                print(f"❌ Browser monitoring error: {e}")
                self.running = False
        
        browser_thread_obj = threading.Thread(target=browser_thread, daemon=True)
        browser_thread_obj.start()
        return browser_thread_obj
    
    def start_ai_monitoring(self):
        """Start AI monitoring in a separate thread"""
        def ai_thread():
            try:
                print(f"🤖 AI monitoring started (interval: {self.ai_interval}s)")
                
                while self.running:
                    try:
                        # Get recent activity
                        recent_activity = self.ai_agent.get_recent_activity(minutes=10)
                        
                        if recent_activity:
                            # Perform AI analysis (using fast mode by default)
                            analysis = self.ai_agent.analyze_student_behavior(recent_activity, use_fast_mode=True)
                            
                            # Save analysis to log
                            self.ai_agent.save_analysis_log(analysis)
                            
                            # Take action if needed
                            recommendation = analysis.get('recommendation', 'continue_monitoring')
                            
                            if recommendation != 'continue_monitoring':
                                mode_indicator = "⚡ FAST" if analysis.get('fast_mode', False) else "🧠 FULL"
                                print(f"\n🎯 AI Decision ({mode_indicator}): {recommendation.upper()}")
                                print(f"💬 Message: {analysis.get('message', 'N/A')}")
                                print(f"⏱️ Timeout: {analysis.get('timeout', 0)}s")
                                print(f"🔍 Reasoning: {analysis.get('reasoning', 'N/A')}")
                                print(f"⚡ Urgency: {analysis.get('urgency', 'medium')}")
                                
                                # Show screenshot analysis if available and not in fast mode
                                screenshot_analysis = analysis.get('screenshot_analysis', {})
                                if screenshot_analysis and screenshot_analysis.get('description') != 'No screenshot available' and not analysis.get('fast_mode', False):
                                    print(f"📸 Screenshot: {screenshot_analysis.get('description', 'N/A')}")
                                    print(f"📚 Educational value: {screenshot_analysis.get('educational_value', 0)}/10")
                                    print(f"📱 Distraction level: {screenshot_analysis.get('distraction_level', 0)}/10")
                                elif analysis.get('fast_mode', False):
                                    print(f"📸 Screenshot: Skipped for faster response")
                                
                                # Perform the action
                                success = self.ai_agent.perform_action(analysis)
                                if success:
                                    print(f"✅ Action completed successfully")
                                else:
                                    print(f"❌ Action failed")
                        
                        # Wait before next analysis
                        time.sleep(self.ai_interval)
                        
                    except Exception as inner_e:
                        print(f"⚠️ AI monitoring error: {inner_e}")
                        time.sleep(self.ai_interval)
                        
            except Exception as e:
                print(f"❌ AI monitoring thread error: {e}")
                self.running = False
        
        ai_thread_obj = threading.Thread(target=ai_thread, daemon=True)
        ai_thread_obj.start()
        return ai_thread_obj
    
    def start_monitoring(self):
        """Start the complete monitoring system"""
        if not self.initialize_components():
            return False
        
        self.running = True
        
        try:
            print("\n🎯 Starting Smart Student Monitoring System")
            print("=" * 50)
            print("🔍 Computer Vision Analysis: ENABLED")
            print("🧠 Intelligent Decision Making: ENABLED")  
            print("⏱️ Dynamic Timeouts: ENABLED")
            print("💬 Contextual Messages: ENABLED")
            print("📊 Pattern Analysis: ENABLED")
            speech_status = "ENABLED" if self.ai_agent.speech_enabled else "DISABLED"
            print(f"🗣️ Speech Feedback: {speech_status}")
            print("=" * 50)
            
            # Start browser monitoring thread
            browser_thread = self.start_browser_monitoring()
            
            # Wait a moment for browser to start
            time.sleep(3)
            
            # Start AI monitoring thread
            ai_thread = self.start_ai_monitoring()
            
            print(f"\n✅ All systems running!")
            print(f"📱 Browser Monitor: Active")
            print(f"🤖 AI Agent: Active")
            print(f"\n📋 Instructions:")
            print(f"• Browse normally - the system will monitor your activity")
            print(f"• AI will analyze screenshots and make intelligent decisions")
            print(f"• Notifications will appear based on AI analysis")
            print(f"• Press Ctrl+C to stop monitoring")
            
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
                
                # Check if threads are still alive
                if not browser_thread.is_alive():
                    print("⚠️ Browser thread stopped")
                    break
                if not ai_thread.is_alive():
                    print("⚠️ AI thread stopped")
                    break
                    
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")
        finally:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop all monitoring"""
        print("\n🛑 Stopping monitoring system...")
        self.running = False
        
        if self.browser_monitor:
            self.browser_monitor.stop_monitoring()
            self.browser_monitor.close_browser()
        
        print("✅ Monitoring stopped successfully")
    
    def generate_session_report(self):
        """Generate a comprehensive session report"""
        if not self.ai_agent:
            return "No AI agent available for report generation"
        
        try:
            print("\n📊 Generating Session Report...")
            
            # Get AI-generated progress report
            progress_report = self.ai_agent.generate_progress_report()
            
            # Get session statistics
            session_duration = (datetime.now() - self.ai_agent.student_activity['session_start']).total_seconds() / 60
            
            report = f"""
🎓 SMART MONITORING SESSION REPORT
{'=' * 50}
📅 Session Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
⏱️ Session Duration: {session_duration:.1f} minutes

📈 AI ANALYSIS SUMMARY:
{progress_report}

📊 SESSION STATISTICS:
• Encouragements Given: {self.ai_agent.student_activity['encouragement_count']}
• Warnings Issued: {self.ai_agent.student_activity['warning_count']}
• Interventions Performed: {self.ai_agent.student_activity['intervention_count']}

💡 SYSTEM FEATURES USED:
• Computer Vision Analysis ✅
• Intelligent Decision Making ✅
• Dynamic Timeout Adjustment ✅
• Contextual Messaging ✅
• Pattern Recognition ✅

📁 LOG FILES CREATED:
• Browser Activity: logs.csv
• AI Analysis: ai_analysis.csv
• Screenshots: screenshots/ directory
            """
            
            return report
            
        except Exception as e:
            return f"Error generating report: {e}"


def main():
    parser = argparse.ArgumentParser(description="Smart Student Monitoring System with AI Analysis")
    parser.add_argument("--headless", action="store_true", 
                       help="Run browser in headless mode")
    parser.add_argument("--api-key", 
                       help="OpenAI API key (or set OPENAI_API_KEY environment variable)")
    parser.add_argument("--lmnt-key", 
                       help="LMNT API key for speech synthesis")
    parser.add_argument("--browser-interval", type=int, default=5,
                       help="Browser monitoring interval in seconds (default: 5)")
    parser.add_argument("--ai-interval", type=int, default=15,
                       help="AI analysis interval in seconds (default: 15)")
    parser.add_argument("--test", action="store_true",
                       help="Run AI test analysis only (no browser monitoring)")
    
    args = parser.parse_args()
    
    # Check for OpenAI API key
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key and not args.test:
        print("❌ OpenAI API key is required!")
        print("Set OPENAI_API_KEY environment variable or use --api-key argument")
        print("Example: export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    # LMNT API key (optional)
    lmnt_key = args.lmnt_key or "ak_GkxGopYg9FwhJaQkJ9huMC"
    
    try:
        if args.test:
            # Run AI test analysis only
            print("🧪 Running AI Test Analysis...")
            from ai_agent import SmartStudentAIAgent
            
            agent = SmartStudentAIAgent(
                openai_api_key=api_key,
                lmnt_api_key=lmnt_key
            )
            recent_activity = agent.get_recent_activity(minutes=30)
            
            if recent_activity:
                print(f"📊 Found {len(recent_activity)} recent activities")
                analysis = agent.analyze_student_behavior(recent_activity)
                
                print("\n🎯 AI ANALYSIS RESULTS:")
                print(f"Current URL: {analysis.get('current_url', 'N/A')}")
                print(f"Recommendation: {analysis.get('recommendation', 'N/A')}")
                print(f"Timeout: {analysis.get('timeout', 0)} seconds")
                print(f"Message: {analysis.get('message', 'N/A')}")
                print(f"Reasoning: {analysis.get('reasoning', 'N/A')}")
                print(f"Urgency: {analysis.get('urgency', 'N/A')}")
                
                # Show detailed analysis
                screenshot_analysis = analysis.get('screenshot_analysis', {})
                if screenshot_analysis:
                    print(f"\n📸 SCREENSHOT ANALYSIS:")
                    print(f"Content type: {screenshot_analysis.get('content_type', 'N/A')}")
                    print(f"Educational value: {screenshot_analysis.get('educational_value', 0)}/10")
                    print(f"Distraction level: {screenshot_analysis.get('distraction_level', 0)}/10")
                    print(f"Description: {screenshot_analysis.get('description', 'N/A')}")
                
                pattern_analysis = analysis.get('pattern_analysis', {})
                if pattern_analysis:
                    print(f"\n📈 PATTERN ANALYSIS:")
                    print(f"Browsing pattern: {pattern_analysis.get('pattern', 'N/A')}")
                    print(f"Focus score: {pattern_analysis.get('focus_score', 0)}/10")
                    print(f"Educational ratio: {pattern_analysis.get('educational_ratio', 0):.2f}")
                
                print(f"\n📋 PROGRESS REPORT:")
                report = agent.generate_progress_report()
                print(report)
                
            else:
                print("❌ No recent activity found to analyze")
                print("💡 Try browsing some websites first, then run the test again")
        
        else:
            # Run full monitoring system
            monitor = SmartStudentMonitor(
                openai_api_key=api_key, 
                headless=args.headless,
                lmnt_api_key=lmnt_key
            )
            
            # Set custom intervals if provided
            if args.browser_interval:
                monitor.browser_interval = args.browser_interval
            if args.ai_interval:
                monitor.ai_interval = args.ai_interval
            
            # Start monitoring
            monitor.start_monitoring()
            
            # Generate final report
            final_report = monitor.generate_session_report()
            print(final_report)
            
    except KeyboardInterrupt:
        print("\n👋 Program interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 