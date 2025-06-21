#!/usr/bin/env python3
"""
Browser Monitor Script
Launches Firefox browser and monitors student activity with logging and screenshots
"""

import os
import time
import csv
import argparse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import pytesseract
from PIL import Image
import threading
import queue
import json


class BrowserMonitor:
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        self.monitoring = False
        self.log_queue = queue.Queue()
        self.screenshot_queue = queue.Queue()
        self.ocr_queue = queue.Queue()
        
        # Create directories
        os.makedirs("screenshots", exist_ok=True)
        
        # Initialize CSV file
        self.init_csv()
        
    def init_csv(self):
        """Initialize the CSV log file with headers"""
        csv_file = "logs.csv"
        if not os.path.exists(csv_file):
            with open(csv_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    'timestamp', 'timestamp_seconds', 'url', 'title', 
                    'screenshot_path', 'ocr_summary', 'tab_count'
                ])
    
    def launch_firefox(self, start_url="https://www.google.com"):
        """Launch Firefox browser"""
        try:
            firefox_options = FirefoxOptions()
            
            if self.headless:
                firefox_options.add_argument("--headless")
            
            # Additional options for better experience
            firefox_options.add_argument("--width=1920")
            firefox_options.add_argument("--height=1080")
            
            print("Launching Firefox...")
            self.driver = webdriver.Firefox(options=firefox_options)
            
            # Maximize window if not headless
            if not self.headless:
                self.driver.maximize_window()
            
            self.driver.get(start_url)
            print(f"Firefox launched successfully! Opened: {start_url}")
            return True
            
        except Exception as e:
            print(f"Error launching Firefox: {e}")
            return False
    
    def log_activity(self):
        """Log current browser activity to CSV"""
        if not self.driver:
            return
            
        try:
            timestamp = datetime.now()
            timestamp_seconds = int(timestamp.timestamp())
            current_url = self.driver.current_url
            title = self.driver.title
            tab_count = len(self.driver.window_handles)
            
            # Generate screenshot filename
            screenshot_filename = f"screenshot_{timestamp_seconds}.png"
            screenshot_path = os.path.join("screenshots", screenshot_filename)
            
            # Take screenshot
            self.driver.save_screenshot(screenshot_path)
            
            # OCR the screenshot
            try:
                image = Image.open(screenshot_path)
                ocr_text = pytesseract.image_to_string(image)
                # Truncate OCR text to reasonable length
                ocr_summary = ocr_text[:500] + "..." if len(ocr_text) > 500 else ocr_text
            except Exception as e:
                ocr_summary = f"OCR failed: {str(e)}"
            
            # Log to CSV
            with open("logs.csv", 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    timestamp_seconds,
                    current_url,
                    title,
                    screenshot_path,
                    ocr_summary,
                    tab_count
                ])
            
            print(f"Logged: {current_url} at {timestamp.strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"Error logging activity: {e}")
    
    def open_new_tab(self, url):
        """Open a new tab with the specified URL"""
        if not self.driver:
            return False
            
        try:
            # Open new tab
            self.driver.execute_script("window.open('');")
            
            # Switch to new tab
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # Navigate to URL
            self.driver.get(url)
            
            print(f"Opened new tab: {url}")
            return True
            
        except Exception as e:
            print(f"Error opening new tab: {e}")
            return False
    
    def close_current_tab(self):
        """Close the current tab"""
        if not self.driver:
            return False
            
        try:
            if len(self.driver.window_handles) > 1:
                self.driver.close()
                # Switch to the last remaining tab
                self.driver.switch_to.window(self.driver.window_handles[-1])
                print("Closed current tab")
                return True
            else:
                print("Cannot close the last remaining tab")
                return False
                
        except Exception as e:
            print(f"Error closing tab: {e}")
            return False
    
    def show_notification(self, message, duration=5):
        """Show a notification in the browser"""
        if not self.driver:
            return False
            
        try:
            # Create a notification overlay
            notification_script = f"""
            var notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #4CAF50;
                color: white;
                padding: 15px 20px;
                border-radius: 5px;
                z-index: 10000;
                font-family: Arial, sans-serif;
                font-size: 14px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                max-width: 300px;
                word-wrap: break-word;
            `;
            notification.textContent = '{message}';
            document.body.appendChild(notification);
            
            setTimeout(function() {{
                if (notification.parentNode) {{
                    notification.parentNode.removeChild(notification);
                }}
            }}, {duration * 1000});
            """
            
            self.driver.execute_script(notification_script)
            print(f"Showed notification: {message}")
            return True
            
        except Exception as e:
            print(f"Error showing notification: {e}")
            return False
    
    def get_current_page_info(self):
        """Get current page information"""
        if not self.driver:
            return None
            
        try:
            return {
                'url': self.driver.current_url,
                'title': self.driver.title,
                'timestamp': int(datetime.now().timestamp()),
                'tab_count': len(self.driver.window_handles)
            }
        except Exception as e:
            print(f"Error getting page info: {e}")
            return None
    
    def navigate_to(self, url):
        """Navigate to a specific URL in current tab"""
        if not self.driver:
            return False
            
        try:
            self.driver.get(url)
            print(f"Navigated to: {url}")
            return True
        except Exception as e:
            print(f"Error navigating to {url}: {e}")
            return False
    
    def start_monitoring(self, interval=5):
        """Start monitoring the browser activity"""
        if not self.driver:
            print("Browser not launched. Cannot start monitoring.")
            return
            
        self.monitoring = True
        print(f"Started monitoring browser activity every {interval} seconds...")
        
        while self.monitoring:
            try:
                self.log_activity()
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\nMonitoring stopped by user.")
                break
            except Exception as e:
                print(f"Error during monitoring: {e}")
                time.sleep(interval)
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        print("Monitoring stopped.")
    
    def close_browser(self):
        """Close the browser"""
        if self.driver:
            try:
                self.stop_monitoring()
                self.driver.quit()
                print("Browser closed successfully.")
            except Exception as e:
                print(f"Error closing browser: {e}")


def main():
    parser = argparse.ArgumentParser(description="Browser Monitor for Student Activity")
    parser.add_argument("--headless", action="store_true", 
                       help="Launch browser in headless mode")
    parser.add_argument("--url", "-u", default="https://www.google.com", 
                       help="URL to open (default: https://www.google.com)")
    parser.add_argument("--interval", "-i", type=int, default=5, 
                       help="Monitoring interval in seconds (default: 5)")
    
    args = parser.parse_args()
    
    monitor = BrowserMonitor(headless=args.headless)
    
    try:
        if monitor.launch_firefox(start_url=args.url):
            print("Browser launched successfully!")
            print("Press Ctrl+C to stop monitoring and close browser.")
            monitor.start_monitoring(interval=args.interval)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        monitor.close_browser()


if __name__ == "__main__":
    main() 