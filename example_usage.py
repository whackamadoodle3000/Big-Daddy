#!/usr/bin/env python3
"""
Example usage of the BrowserLauncher class
"""

from browser_launcher import BrowserLauncher
import time

def example_chrome_usage():
    """Example of using Chrome browser"""
    print("=== Chrome Browser Example ===")
    launcher = BrowserLauncher()
    
    # Launch Chrome and open Google
    if launcher.launch_chrome(start_url="https://www.google.com"):
        print("Chrome launched successfully!")
        
        # Wait a bit
        time.sleep(3)
        
        # Navigate to another site
        launcher.navigate_to("https://www.github.com")
        print("Navigated to GitHub")
        
        # Keep the browser open for 10 seconds
        time.sleep(10)
        
        # Close the browser
        launcher.close_browser()
    else:
        print("Failed to launch Chrome")

def example_firefox_usage():
    """Example of using Firefox browser"""
    print("\n=== Firefox Browser Example ===")
    launcher = BrowserLauncher()
    
    # Launch Firefox and open YouTube
    if launcher.launch_firefox(start_url="https://www.youtube.com"):
        print("Firefox launched successfully!")
        
        # Keep the browser open for 15 seconds
        time.sleep(15)
        
        # Close the browser
        launcher.close_browser()
    else:
        print("Failed to launch Firefox")

def example_interactive_session():
    """Example of an interactive browser session"""
    print("\n=== Interactive Browser Session ===")
    launcher = BrowserLauncher()
    
    # Launch Chrome
    if launcher.launch_chrome(start_url="https://www.google.com"):
        print("Chrome launched! You can now interact with the browser.")
        print("The browser will stay open until you close it manually.")
        print("Or press Ctrl+C in this terminal to close the script.")
        
        # Keep the browser open indefinitely
        launcher.keep_alive()
    else:
        print("Failed to launch Chrome")

if __name__ == "__main__":
    print("Browser Launcher Examples")
    print("Choose an example to run:")
    print("1. Chrome example (auto-close after 10 seconds)")
    print("2. Firefox example (auto-close after 15 seconds)")
    print("3. Interactive Chrome session (keep open until manual close)")
    
    try:
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == "1":
            example_chrome_usage()
        elif choice == "2":
            example_firefox_usage()
        elif choice == "3":
            example_interactive_session()
        else:
            print("Invalid choice. Running Chrome example...")
            example_chrome_usage()
            
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}") 