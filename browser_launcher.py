#!/usr/bin/env python3
"""
Browser Launcher Script
Opens Chrome, Chromium, or Firefox using Selenium in a normal window
"""

import sys
import time
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BrowserLauncher:
    def __init__(self):
        self.driver = None
        
    def launch_chrome(self, headless=False, start_url="https://www.google.com"):
        """Launch Chrome browser"""
        try:
            chrome_options = ChromeOptions()
            
            if not headless:
                # Normal window mode
                chrome_options.add_argument("--start-maximized")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
            else:
                chrome_options.add_argument("--headless")
            
            # Additional options for better experience
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            print("Launching Chrome...")
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Remove automation indicators
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver.get(start_url)
            print(f"Chrome launched successfully! Opened: {start_url}")
            return True
            
        except Exception as e:
            print(f"Error launching Chrome: {e}")
            return False
    
    def launch_chromium(self, headless=False, start_url="https://www.google.com"):
        """Launch Chromium browser"""
        try:
            chrome_options = ChromeOptions()
            
            if not headless:
                # Normal window mode
                chrome_options.add_argument("--start-maximized")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
            else:
                chrome_options.add_argument("--headless")
            
            # Additional options for better experience
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            print("Launching Chromium...")
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Remove automation indicators
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver.get(start_url)
            print(f"Chromium launched successfully! Opened: {start_url}")
            return True
            
        except Exception as e:
            print(f"Error launching Chromium: {e}")
            return False
    
    def launch_firefox(self, headless=False, start_url="https://www.google.com"):
        """Launch Firefox browser"""
        try:
            firefox_options = FirefoxOptions()
            
            if headless:
                firefox_options.add_argument("--headless")
            
            # Additional options for better experience
            firefox_options.add_argument("--width=1920")
            firefox_options.add_argument("--height=1080")
            
            print("Launching Firefox...")
            self.driver = webdriver.Firefox(options=firefox_options)
            
            # Maximize window if not headless
            if not headless:
                self.driver.maximize_window()
            
            self.driver.get(start_url)
            print(f"Firefox launched successfully! Opened: {start_url}")
            return True
            
        except Exception as e:
            print(f"Error launching Firefox: {e}")
            return False
    
    def keep_alive(self):
        """Keep the browser window open until user closes it"""
        if self.driver:
            print("\nBrowser is now open. Close the browser window to exit.")
            print("Or press Ctrl+C in this terminal to close the script.")
            
            try:
                while True:
                    # Check if browser is still open
                    try:
                        # Try to get current URL to check if browser is responsive
                        current_url = self.driver.current_url
                        time.sleep(1)
                    except:
                        print("Browser window was closed.")
                        break
                        
            except KeyboardInterrupt:
                print("\nClosing browser...")
                self.close_browser()
    
    def close_browser(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
                print("Browser closed successfully.")
            except Exception as e:
                print(f"Error closing browser: {e}")
    
    def navigate_to(self, url):
        """Navigate to a specific URL"""
        if self.driver:
            try:
                self.driver.get(url)
                print(f"Navigated to: {url}")
            except Exception as e:
                print(f"Error navigating to {url}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Launch a browser using Selenium")
    parser.add_argument("--browser", "-b", choices=["chrome", "chromium", "firefox"], 
                       default="chrome", help="Browser to launch (default: chrome)")
    parser.add_argument("--headless", action="store_true", 
                       help="Launch browser in headless mode")
    parser.add_argument("--url", "-u", default="https://www.google.com", 
                       help="URL to open (default: https://www.google.com)")
    parser.add_argument("--keep-alive", "-k", action="store_true", 
                       help="Keep browser open until manually closed")
    
    args = parser.parse_args()
    
    launcher = BrowserLauncher()
    success = False
    
    try:
        if args.browser == "chrome":
            success = launcher.launch_chrome(headless=args.headless, start_url=args.url)
        elif args.browser == "chromium":
            success = launcher.launch_chromium(headless=args.headless, start_url=args.url)
        elif args.browser == "firefox":
            success = launcher.launch_firefox(headless=args.headless, start_url=args.url)
        
        if success and args.keep_alive:
            launcher.keep_alive()
        elif success:
            print(f"\nBrowser launched successfully!")
            print("The browser will close automatically in 10 seconds...")
            print("Use --keep-alive flag to keep it open indefinitely.")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        launcher.close_browser()


if __name__ == "__main__":
    main() 