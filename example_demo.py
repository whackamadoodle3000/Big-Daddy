#!/usr/bin/env python3
"""
Example Demo - Student Monitoring System
Demonstrates how to use the browser monitor and AI agent
"""

import time
import threading
from browser_monitor import BrowserMonitor
from ai_agent import StudentAIAgent


def demo_basic_monitoring():
    """Demo basic browser monitoring"""
    print("=== Basic Browser Monitoring Demo ===")
    
    monitor = BrowserMonitor(headless=False)
    
    try:
        # Launch browser
        if monitor.launch_firefox(start_url="https://www.google.com"):
            print("Browser launched! You can now browse normally.")
            print("The system will log your activity every 5 seconds.")
            print("Press Ctrl+C to stop.")
            
            # Start monitoring
            monitor.start_monitoring(interval=5)
            
    except KeyboardInterrupt:
        print("\nDemo stopped by user.")
    finally:
        monitor.close_browser()


def demo_ai_agent():
    """Demo AI agent functionality"""
    print("\n=== AI Agent Demo ===")
    print("Note: This demo requires OpenAI API key.")
    print("Set OPENAI_API_KEY environment variable or pass --api-key")
    
    try:
        agent = StudentAIAgent()
        
        # Simulate some activity analysis
        print("AI Agent initialized successfully!")
        print("The agent will analyze browser activity and take appropriate actions.")
        print("Press Ctrl+C to stop.")
        
        agent.run_agent_loop(interval=30)
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have set the OPENAI_API_KEY environment variable.")


def demo_combined_system():
    """Demo the combined monitoring and AI agent system"""
    print("\n=== Combined System Demo ===")
    print("This runs both browser monitoring and AI agent together.")
    print("Note: Requires OpenAI API key.")
    
    try:
        from student_monitor import StudentMonitor
        
        monitor = StudentMonitor(headless=False)
        
        print("Starting combined system...")
        monitor.start_monitoring(
            start_url="https://www.google.com",
            monitor_interval=5,
            agent_interval=30
        )
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have set the OPENAI_API_KEY environment variable.")


def demo_browser_controls():
    """Demo browser control functions"""
    print("\n=== Browser Controls Demo ===")
    
    monitor = BrowserMonitor(headless=False)
    
    try:
        if monitor.launch_firefox(start_url="https://www.google.com"):
            print("Browser launched! Demonstrating controls...")
            
            # Wait a bit
            time.sleep(3)
            
            # Show notification
            monitor.show_notification("Hello! This is a test notification.", duration=5)
            time.sleep(2)
            
            # Open new tab
            monitor.open_new_tab("https://www.github.com")
            time.sleep(3)
            
            # Show another notification
            monitor.show_notification("Opened GitHub in new tab!", duration=5)
            time.sleep(3)
            
            # Close current tab
            monitor.close_current_tab()
            time.sleep(2)
            
            # Show final notification
            monitor.show_notification("Demo completed! Browser will close in 5 seconds.", duration=5)
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nDemo stopped by user.")
    finally:
        monitor.close_browser()


def main():
    print("Student Monitoring System - Demo")
    print("Choose a demo to run:")
    print("1. Basic browser monitoring")
    print("2. AI agent (requires OpenAI API key)")
    print("3. Combined system (requires OpenAI API key)")
    print("4. Browser controls demo")
    print("5. Exit")
    
    try:
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            demo_basic_monitoring()
        elif choice == "2":
            demo_ai_agent()
        elif choice == "3":
            demo_combined_system()
        elif choice == "4":
            demo_browser_controls()
        elif choice == "5":
            print("Exiting...")
        else:
            print("Invalid choice. Running basic monitoring demo...")
            demo_basic_monitoring()
            
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main() 