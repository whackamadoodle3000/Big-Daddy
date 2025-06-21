#!/usr/bin/env python3
"""
Student Monitor - Combined Browser Monitor and AI Agent
Runs both monitoring and AI agent together
"""

import os
import time
import threading
import argparse
from browser_monitor_fixed import BrowserMonitor
from ai_agent import StudentAIAgent


class StudentMonitor:
    def __init__(self, openai_api_key=None, headless=False):
        self.browser_monitor = BrowserMonitor(headless=headless)
        self.ai_agent = StudentAIAgent(openai_api_key=openai_api_key)
        
        # Connect the AI agent to the browser monitor
        self.ai_agent.set_browser_monitor(self.browser_monitor)
        
        # Threading control
        self.running = False
        self.monitor_thread = None
        self.agent_thread = None
        
    def start_monitoring(self, start_url="https://www.google.com", 
                        monitor_interval=5, agent_interval=30):
        """Start both browser monitoring and AI agent"""
        try:
            # Launch browser
            if not self.browser_monitor.launch_firefox(start_url=start_url):
                print("Failed to launch browser. Exiting.")
                return False
            
            print("Browser launched successfully!")
            self.running = True
            
            # Start browser monitoring in a separate thread
            self.monitor_thread = threading.Thread(
                target=self._run_browser_monitor,
                args=(monitor_interval,),
                daemon=True
            )
            self.monitor_thread.start()
            
            # Start AI agent in a separate thread
            self.agent_thread = threading.Thread(
                target=self._run_ai_agent,
                args=(agent_interval,),
                daemon=True
            )
            self.agent_thread.start()
            
            print(f"Student monitoring started!")
            print(f"- Browser monitoring every {monitor_interval} seconds")
            print(f"- AI agent checking every {agent_interval} seconds")
            print("Press Ctrl+C to stop monitoring.")
            
            # Keep main thread alive
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping student monitoring...")
                self.stop_monitoring()
            
            return True
            
        except Exception as e:
            print(f"Error starting monitoring: {e}")
            return False
    
    def _run_browser_monitor(self, interval):
        """Run browser monitoring in separate thread"""
        try:
            while self.running:
                if self.browser_monitor.driver:
                    self.browser_monitor.log_activity()
                time.sleep(interval)
        except Exception as e:
            print(f"Error in browser monitor thread: {e}")
    
    def _run_ai_agent(self, interval):
        """Run AI agent in separate thread"""
        try:
            while self.running:
                # Get recent activity
                recent_activity = self.ai_agent.get_recent_activity(minutes=15)
                
                # Analyze behavior
                analysis = self.ai_agent.analyze_student_behavior(recent_activity)
                
                # Take action if needed
                if analysis['recommendation'] != 'continue_monitoring':
                    self.ai_agent.take_action(analysis)
                
                # Log agent activity
                self.ai_agent.log_agent_activity(analysis)
                
                time.sleep(interval)
        except Exception as e:
            print(f"Error in AI agent thread: {e}")
    
    def stop_monitoring(self):
        """Stop all monitoring"""
        print("Stopping student monitoring...")
        self.running = False
        
        # Stop browser monitoring
        if self.browser_monitor:
            self.browser_monitor.stop_monitoring()
        
        # Wait for threads to finish
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        if self.agent_thread and self.agent_thread.is_alive():
            self.agent_thread.join(timeout=5)
        
        # Close browser
        if self.browser_monitor:
            self.browser_monitor.close_browser()
        
        print("Student monitoring stopped.")


def main():
    parser = argparse.ArgumentParser(description="Student Monitor - Browser + AI Agent")
    parser.add_argument("--headless", action="store_true", 
                       help="Launch browser in headless mode")
    parser.add_argument("--url", "-u", default="https://www.google.com", 
                       help="URL to open (default: https://www.google.com)")
    parser.add_argument("--monitor-interval", "-m", type=int, default=5, 
                       help="Browser monitoring interval in seconds (default: 5)")
    parser.add_argument("--agent-interval", "-a", type=int, default=30, 
                       help="AI agent check interval in seconds (default: 30)")
    parser.add_argument("--api-key", "-k", 
                       help="OpenAI API key (or set OPENAI_API_KEY environment variable)")
    
    args = parser.parse_args()
    
    try:
        # Initialize student monitor
        monitor = StudentMonitor(
            openai_api_key=args.api_key,
            headless=args.headless
        )
        
        # Start monitoring
        monitor.start_monitoring(
            start_url=args.url,
            monitor_interval=args.monitor_interval,
            agent_interval=args.agent_interval
        )
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have set the OPENAI_API_KEY environment variable.")


if __name__ == "__main__":
    main() 