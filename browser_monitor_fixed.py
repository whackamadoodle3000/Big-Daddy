#!/usr/bin/env python3
"""
Browser Monitor Script - Fixed Version
Launches Firefox browser and monitors student activity with logging and screenshots
Improved error handling for heavy sites like YouTube
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
        """Initialize the browser monitor"""
        self.driver = None
        self.headless = headless
        self.monitoring = False
        self.log_queue = queue.Queue()
        self.screenshot_queue = queue.Queue()
        self.ocr_queue = queue.Queue()
        
        # Tracking variables
        self.last_url = ""
        self.last_title = ""
        
        # Error handling
        self.consecutive_errors = 0
        self.max_consecutive_errors = 10  # Increased from 5 to be more resilient
        
        # Create directories
        os.makedirs("screenshots", exist_ok=True)
        
        # Initialize CSV file
        self.init_csv()
        
    def init_csv(self):
        """Initialize the CSV file with headers"""
        csv_file = "logs.csv"
        if not os.path.exists(csv_file):
            with open(csv_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    'timestamp',
                    'timestamp_seconds', 
                    'url',
                    'page_title',
                    'screenshot_path',
                    'ocr_summary',
                    'tab_count',
                    'search_query',
                    'page_content'
                ])
            print(f"Created new log file: {csv_file}")
        else:
            print(f"Using existing log file: {csv_file}")
    
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
            
            # Initialize tracking variables
            self.last_url = self.driver.current_url
            self.last_title = self.driver.title
            
            return True
            
        except Exception as e:
            print(f"Error launching Firefox: {e}")
            return False
    
    def get_current_page_info(self):
        """Get current page URL, title, and other info"""
        if not self.driver:
            return None, None, None, None
        
        try:
            # Check if browser is still responsive
            current_url = self.driver.current_url
            current_title = self.driver.title
            
            # Extract search query if it's a search URL
            search_query = self.extract_search_query(current_url)
            
            # Try to extract page content (with error handling)
            try:
                page_content = self.extract_page_content()
            except Exception as content_error:
                print(f"Warning: Could not extract page content: {content_error}")
                page_content = ""
            
            return current_url, current_title, search_query, page_content
            
        except Exception as e:
            # Handle browser context issues
            if "Browsing context has been discarded" in str(e) or "no such window" in str(e).lower():
                print("Browser context lost - attempting to recover...")
                
                # Try to recover by switching to an available window
                try:
                    available_windows = self.driver.window_handles
                    if available_windows:
                        # Switch to the first available window
                        self.driver.switch_to.window(available_windows[0])
                        print(f"Recovered: switched to available window")
                        
                        # Try to get page info again
                        current_url = self.driver.current_url
                        current_title = self.driver.title
                        search_query = self.extract_search_query(current_url)
                        
                        print(f"Recovery successful: now on {current_url}")
                        return current_url, current_title, search_query, ""
                    else:
                        print("No available windows found")
                        return None, None, None, None
                        
                except Exception as recovery_error:
                    print(f"Recovery failed: {recovery_error}")
                    
                    # Last resort: try to create a new window
                    try:
                        self.driver.execute_script("window.open('https://www.google.com', '_blank');")
                        available_windows = self.driver.window_handles
                        if available_windows:
                            self.driver.switch_to.window(available_windows[-1])
                            print("Created new window and switched to it")
                            return self.driver.current_url, self.driver.title, "", ""
                    except Exception as last_resort_error:
                        print(f"Last resort recovery failed: {last_resort_error}")
                        self.consecutive_errors += 1
                        return None, None, None, None
            else:
                print(f"Error getting page info: {e}")
                self.consecutive_errors += 1
                return None, None, None, None
    
    def log_activity(self):
        """Log current browser activity to CSV with improved error handling"""
        if not self.driver:
            return
            
        try:
            # Get current page info - now returns tuple (url, title, search_query, page_content)
            page_info = self.get_current_page_info()
            if not page_info or page_info[0] is None:
                self.consecutive_errors += 1
                print(f"Failed to get page info. Consecutive errors: {self.consecutive_errors}")
                if self.consecutive_errors >= self.max_consecutive_errors:
                    print("Too many consecutive errors. Stopping monitoring.")
                    self.stop_monitoring()
                return
            
            current_url, current_title, search_query, page_content = page_info
            timestamp = datetime.now()
            timestamp_seconds = int(timestamp.timestamp())
            
            # Get tab count
            try:
                tab_count = len(self.driver.window_handles)
            except:
                tab_count = 1
            
            # Check if page has changed
            page_changed = (current_url != self.last_url or current_title != self.last_title)
            
            # Generate screenshot filename
            screenshot_filename = f"screenshot_{timestamp_seconds}.png"
            screenshot_path = os.path.join("screenshots", screenshot_filename)
            
            # Take screenshot with error handling (skip if too many errors)
            screenshot_success = False
            if self.consecutive_errors < 3:  # Only try screenshots if not having many errors
                try:
                    # Create screenshots directory if it doesn't exist
                    os.makedirs("screenshots", exist_ok=True)
                    self.driver.save_screenshot(screenshot_path)
                    screenshot_success = True
                except Exception as e:
                    print(f"Warning: Failed to take screenshot: {e}")
                    screenshot_path = "screenshot_failed.png"
            else:
                screenshot_path = "screenshot_skipped.png"
            
            # OCR the screenshot with error handling (skip if having errors)
            ocr_summary = "OCR not available"
            if screenshot_success and os.path.exists(screenshot_path) and self.consecutive_errors < 3:
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
                    current_title,
                    screenshot_path,
                    ocr_summary,
                    tab_count,
                    search_query,
                    page_content
                ])
            
            # Update tracking variables
            self.last_url = current_url
            self.last_title = current_title
            
            # Reset error counter on successful log - this is key for recovery!
            if self.consecutive_errors > 0:
                print(f"Successfully recovered from {self.consecutive_errors} consecutive errors!")
            self.consecutive_errors = 0
            
            # Print status
            if page_changed:
                print(f"Page changed: {current_url} - {current_title}")
                if search_query:
                    print(f"Search query detected: {search_query}")
            else:
                print(f"Logged: {current_url} at {timestamp.strftime('%H:%M:%S')}")
            
        except Exception as e:
            self.consecutive_errors += 1
            print(f"Error logging activity: {e}")
            print(f"Consecutive errors: {self.consecutive_errors}")
            
            if self.consecutive_errors >= self.max_consecutive_errors:
                print("Too many consecutive errors. Stopping monitoring.")
                self.stop_monitoring()
    
    def extract_search_query(self, url: str) -> str:
        """Extract search query from search engine URLs"""
        try:
            from urllib.parse import urlparse, parse_qs
            
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            # Google search
            if 'google.com' in parsed_url.netloc and 'q' in query_params:
                return query_params['q'][0]
            
            # YouTube search
            elif 'youtube.com' in parsed_url.netloc and 'search_query' in query_params:
                return query_params['search_query'][0]
            
            # Bing search
            elif 'bing.com' in parsed_url.netloc and 'q' in query_params:
                return query_params['q'][0]
            
            # DuckDuckGo search
            elif 'duckduckgo.com' in parsed_url.netloc and 'q' in query_params:
                return query_params['q'][0]
            
            # Yahoo search
            elif 'search.yahoo.com' in parsed_url.netloc and 'p' in query_params:
                return query_params['p'][0]
            
            return ""
            
        except Exception as e:
            print(f"Error extracting search query: {e}")
            return ""
    
    def extract_page_content(self) -> str:
        """Extract page content for analysis"""
        try:
            # Try to get page content via JavaScript
            content_script = """
            try {
                // Get main content areas
                var content = '';
                
                // Try to get main content
                var mainContent = document.querySelector('main') || 
                                 document.querySelector('#main') || 
                                 document.querySelector('.main') ||
                                 document.querySelector('article') ||
                                 document.querySelector('.content') ||
                                 document.querySelector('#content');
                
                if (mainContent) {
                    content = mainContent.textContent || mainContent.innerText || '';
                } else {
                    // Fallback to body content
                    content = document.body.textContent || document.body.innerText || '';
                }
                
                // Clean up the content
                content = content.replace(/\\s+/g, ' ').trim();
                
                // Limit length to avoid huge logs
                return content.substring(0, 1000);
            } catch(e) {
                return 'Content extraction failed: ' + e.message;
            }
            """
            
            content = self.driver.execute_script(content_script)
            return content if content else "No content extracted"
            
        except Exception as e:
            print(f"Error extracting page content: {e}")
            return f"Content extraction failed: {str(e)}"
    
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
            
            # Update tracking variables
            self.last_url = self.driver.current_url
            self.last_title = self.driver.title
            
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
                
                # Update tracking variables
                self.last_url = self.driver.current_url
                self.last_title = self.driver.title
                
                print("Closed current tab")
                return True
            else:
                print("Cannot close the last remaining tab")
                return False
                
        except Exception as e:
            print(f"Error closing tab: {e}")
            return False
    
    def show_notification(self, message, duration=10):
        """Show a notification in the browser with better compatibility"""
        if not self.driver:
            return False
            
        try:
            # Escape the message for JavaScript - avoid backslash in f-string
            escaped_message = message.replace("'", "&#39;").replace('"', '&quot;')
            
            # Try multiple notification methods for better compatibility
            notification_methods = [
                # Method 1: Simple notification with minimal styling
                f"""
                try {{
                    var notif = document.createElement('div');
                    notif.style.position = 'fixed';
                    notif.style.top = '20px';
                    notif.style.right = '20px';
                    notif.style.background = '#ff4444';
                    notif.style.color = 'white';
                    notif.style.padding = '10px 15px';
                    notif.style.borderRadius = '5px';
                    notif.style.zIndex = '999999';
                    notif.style.fontFamily = 'Arial, sans-serif';
                    notif.style.fontSize = '14px';
                    notif.style.maxWidth = '300px';
                    notif.style.wordWrap = 'break-word';
                    notif.style.boxShadow = '0 2px 10px rgba(0,0,0,0.3)';
                    notif.innerHTML = '{escaped_message}';
                    document.body.appendChild(notif);
                    
                    setTimeout(function() {{
                        if (notif.parentNode) {{
                            notif.parentNode.removeChild(notif);
                        }}
                    }}, {duration * 1000});
                }} catch(e) {{
                    console.log('Notification failed:', e);
                }}
                """,
                
                # Method 2: Even simpler notification
                f"""
                try {{
                    var div = document.createElement('div');
                    div.style.cssText = 'position:fixed;top:20px;right:20px;background:red;color:white;padding:10px;z-index:999999;font-family:Arial;';
                    div.innerHTML = '{escaped_message}';
                    document.body.appendChild(div);
                    setTimeout(function() {{ if(div.parentNode) div.parentNode.removeChild(div); }}, {duration * 1000});
                }} catch(e) {{
                    console.log('Simple notification failed:', e);
                }}
                """,
                
                # Method 3: Aggressive overlay notification
                f"""
                try {{
                    var overlay = document.createElement('div');
                    overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:999999;display:flex;align-items:center;justify-content:center;';
                    var msgBox = document.createElement('div');
                    msgBox.style.cssText = 'background:white;padding:20px;border-radius:10px;max-width:400px;text-align:center;font-family:Arial;';
                    msgBox.innerHTML = '<h3 style="color:red;margin:0 0 10px 0;">INAPPROPRIATE CONTENT DETECTED</h3><p>{escaped_message}</p><button onclick="this.parentNode.parentNode.remove()" style="padding:10px 20px;background:red;color:white;border:none;border-radius:5px;cursor:pointer;">OK</button>';
                    overlay.appendChild(msgBox);
                    document.body.appendChild(overlay);
                    
                    setTimeout(function() {{
                        if (overlay.parentNode) {{
                            overlay.parentNode.removeChild(overlay);
                        }}
                    }}, {duration * 1000});
                }} catch(e) {{
                    console.log('Overlay notification failed:', e);
                }}
                """,
                
                # Method 4: Alert fallback
                f"""
                try {{
                    alert('INAPPROPRIATE CONTENT DETECTED: {escaped_message}');
                }} catch(e) {{
                    console.log('Alert failed:', e);
                }}
                """
            ]
            
            # Try each notification method
            for i, method in enumerate(notification_methods):
                try:
                    self.driver.execute_script(method)
                    print(f"Showed notification (method {i+1}): {message}")
                    return True
                except Exception as e:
                    print(f"Notification method {i+1} failed: {e}")
                    continue
            
            # If all methods fail, just print to console
            print(f"All notification methods failed. Message: {message}")
            return False
            
        except Exception as e:
            print(f"Error showing notification: {e}")
            return False
    
    def navigate_to(self, url):
        """Navigate to a specific URL in current tab"""
        if not self.driver:
            return False
            
        try:
            # Make sure we're on an active window
            try:
                current_windows = self.driver.window_handles
                if current_windows:
                    self.driver.switch_to.window(current_windows[0])
            except:
                pass
            
            # Navigate to the URL
            self.driver.get(url)
            
            # Wait a moment for the page to start loading
            time.sleep(1)
            
            # Update tracking variables
            try:
                self.last_url = self.driver.current_url
                self.last_title = self.driver.title
            except:
                # If we can't get the current info, just use what we tried to navigate to
                self.last_url = url
                self.last_title = "Navigation in progress"
            
            print(f"Navigated to: {url}")
            return True
            
        except Exception as e:
            print(f"Error navigating to {url}: {e}")
            
            # Try to recover by opening in a new tab
            try:
                self.driver.execute_script(f"window.open('{url}', '_blank');")
                available_windows = self.driver.window_handles
                if available_windows:
                    self.driver.switch_to.window(available_windows[-1])
                    print(f"Opened {url} in new tab as fallback")
                    return True
            except Exception as fallback_error:
                print(f"Fallback navigation also failed: {fallback_error}")
                return False
    
    def start_monitoring(self, interval=5):
        """Start monitoring the browser activity"""
        if not self.driver:
            print("Browser not launched. Cannot start monitoring.")
            return
            
        self.monitoring = True
        print(f"Started monitoring browser activity every {interval} seconds...")
        print("You can now browse normally - the system will track your activity.")
        print("Note: Heavy sites like YouTube may have limited screenshot/OCR functionality.")
        
        while self.monitoring:
            try:
                # Check if browser is still responsive
                if not self.driver:
                    print("Browser driver lost. Stopping monitoring.")
                    break
                
                self.log_activity()
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\nMonitoring stopped by user.")
                break
            except Exception as e:
                print(f"Error during monitoring: {e}")
                # Try to continue monitoring
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
    parser = argparse.ArgumentParser(description="Browser Monitor for Student Activity - Fixed Version")
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
            print("You can now browse normally - the system will track your activity.")
            print("Press Ctrl+C to stop monitoring and close browser.")
            monitor.start_monitoring(interval=args.interval)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        monitor.close_browser()


if __name__ == "__main__":
    main() 