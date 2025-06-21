#!/usr/bin/env python3
"""
AI Agent for Student Browser Monitoring
Uses LangChain to monitor student activity and provide appropriate guidance
"""

import os
import time
import csv
import json
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.tools import DuckDuckGoSearchRun
from langchain.agents import initialize_agent, AgentType, Tool
from langchain.memory import ConversationBufferMemory
import re
from urllib.parse import urlparse


class StudentAIAgent:
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it to constructor.")
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            temperature=0.7,
            openai_api_key=self.openai_api_key,
            model_name="gpt-3.5-turbo"
        )
        
        # Initialize search tool
        self.search_tool = DuckDuckGoSearchRun()
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize tools
        self.tools = [
            Tool(
                name="web_search",
                func=self.search_tool.run,
                description="Search the web for educational resources, appropriate websites, or information about websites"
            )
        ]
        
        # Initialize agent
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True
        )
        
        # Site categories
        self.educational_sites = [
            'ixl.com', 'khanacademy.org', 'duolingo.com', 'codecademy.com',
            'brilliant.org', 'coursera.org', 'edx.org', 'udemy.com',
            'wikipedia.org', 'wolframalpha.com', 'desmos.com', 'geogebra.org',
            'scratch.mit.edu', 'typing.com', 'mathway.com', 'symbolab.com'
        ]
        
        self.distracting_sites = [
            'youtube.com', 'facebook.com', 'instagram.com', 'tiktok.com',
            'twitter.com', 'reddit.com', 'netflix.com', 'hulu.com',
            'twitch.tv', 'discord.com', 'snapchat.com', 'pinterest.com'
        ]
        
        self.inappropriate_sites = [
            'porn', 'gambling', 'violence', 'drugs', 'alcohol',
            'dating', 'adult', 'mature', 'explicit'
        ]
        
        # Action thresholds
        self.encouragement_threshold = 30  # 5 minutes on educational site
        self.distraction_threshold = 20    # 10 minutes on distracting site
        self.inappropriate_threshold = 5   # 30 seconds on inappropriate site
        
        # Track student activity
        self.student_activity = {
            'current_site': None,
            'site_start_time': None,
            'last_action_time': None,
            'encouragement_count': 0,
            'warning_count': 0,
            'intervention_count': 0
        }
        
        # Browser monitor reference (will be set by external script)
        self.browser_monitor = None
        
    def categorize_site(self, url: str) -> str:
        """Categorize a website based on its URL"""
        domain = urlparse(url).netloc.lower()
        
        # Check for inappropriate content
        for inappropriate in self.inappropriate_sites:
            if inappropriate in url.lower():
                return 'inappropriate'
        
        # Check educational sites
        for educational in self.educational_sites:
            if educational in domain:
                return 'educational'
        
        # Check distracting sites
        for distracting in self.distracting_sites:
            if distracting in domain:
                return 'distracting'
        
        return 'neutral'
    
    def get_recent_activity(self, minutes: int = 10) -> List[Dict]:
        """Get recent student activity from logs.csv"""
        try:
            if not os.path.exists('logs.csv'):
                return []
            
            df = pd.read_csv('logs.csv')
            if df.empty:
                return []
            
            # Check if timestamp column exists
            if 'timestamp' not in df.columns:
                print("Warning: timestamp column not found in logs.csv")
                return []
            
            # Convert timestamp to datetime with error handling
            try:
                df['datetime'] = pd.to_datetime(df['timestamp'])
            except Exception as e:
                print(f"Error parsing timestamps: {e}")
                # Try alternative timestamp formats
                try:
                    df['datetime'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S')
                except Exception as e2:
                    print(f"Error with alternative timestamp format: {e2}")
                    return []
            
            # Get recent entries
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            recent_activity = df[df['datetime'] >= cutoff_time].to_dict('records')
            
            return recent_activity
            
        except Exception as e:
            print(f"Error reading activity logs: {e}")
            return []
    
    def analyze_student_behavior(self, recent_activity: List[Dict]) -> Dict[str, Any]:
        """Analyze student behavior based on recent activity"""
        if not recent_activity:
            return {'status': 'no_activity', 'recommendation': 'continue_monitoring'}
        
        # Get current site info
        latest_activity = recent_activity[-1]
        current_url = latest_activity['url']
        current_time = datetime.now()
        
        # Update student activity tracking
        if self.student_activity['current_site'] != current_url:
            self.student_activity['current_site'] = current_url
            self.student_activity['site_start_time'] = current_time
        
        site_category = self.categorize_site(current_url)
        time_on_site = (current_time - self.student_activity['site_start_time']).total_seconds()
        
        analysis = {
            'current_url': current_url,
            'site_category': site_category,
            'time_on_site': time_on_site,
            'recommendation': 'continue_monitoring'
        }
        
        # Check for inappropriate content in search queries and page content
        inappropriate_content_detected = self.check_for_inappropriate_content(latest_activity)
        if inappropriate_content_detected:
            analysis['site_category'] = 'inappropriate'
            analysis['recommendation'] = 'intervene'
            analysis['message'] = f"Inappropriate content detected: {inappropriate_content_detected}. Redirecting to educational content."
            return analysis
        
        # Determine appropriate action based on site category and time
        if site_category == 'educational':
            if time_on_site > self.encouragement_threshold:
                analysis['recommendation'] = 'encourage'
                analysis['message'] = f"Great work! You've been studying for {int(time_on_site/60)} minutes. Keep up the excellent effort!"
        
        elif site_category == 'distracting':
            if time_on_site > self.distraction_threshold:
                analysis['recommendation'] = 'warn'
                analysis['message'] = f"You've been on this site for {int(time_on_site/60)} minutes. Consider getting back to your studies."
        
        elif site_category == 'inappropriate':
            if time_on_site > self.inappropriate_threshold:
                analysis['recommendation'] = 'intervene'
                analysis['message'] = "This site may not be appropriate for your studies. Let me help you find something better."
        
        return analysis
    
    def check_for_inappropriate_content(self, activity: Dict) -> str:
        """Check for inappropriate content in search queries and page content"""
        # Keywords that indicate inappropriate content
        inappropriate_keywords = [
            'porn', 'pornography', 'adult', 'mature', 'explicit', 'nude', 'naked',
            'sex', 'sexual', 'dating', 'hookup', 'tinder', 'bumble', 'grindr',
            'gambling', 'casino', 'bet', 'poker', 'slot', 'lottery',
            'drugs', 'marijuana', 'cocaine', 'heroin', 'weed', 'alcohol', 'beer', 'wine',
            'violence', 'gore', 'blood', 'kill', 'murder', 'suicide', 'self-harm',
            'hack', 'crack', 'cheat', 'steal', 'illegal', 'weapon', 'gun'
        ]
        
        # Check URL - ensure it's a string
        url = str(activity.get('url', '')).lower()
        for keyword in inappropriate_keywords:
            if keyword in url:
                return f"inappropriate keyword '{keyword}' in URL"
        
        # Check search query (if available) - ensure it's a string
        search_query = str(activity.get('search_query', '')).lower()
        if search_query:
            for keyword in inappropriate_keywords:
                if keyword in search_query:
                    return f"inappropriate keyword '{keyword}' in search query"
        
        # Check page title (if available) - ensure it's a string
        page_title = str(activity.get('page_title', '')).lower()
        if page_title:
            for keyword in inappropriate_keywords:
                if keyword in page_title:
                    return f"inappropriate keyword '{keyword}' in page title"
        
        # Check page content (if available) - ensure it's a string
        page_content = str(activity.get('page_content', '')).lower()
        if page_content:
            for keyword in inappropriate_keywords:
                if keyword in page_content:
                    return f"inappropriate keyword '{keyword}' in page content"
        
        return None
    
    def take_action(self, analysis: Dict[str, Any]) -> bool:
        """Take appropriate action based on analysis"""
        if not self.browser_monitor:
            print("Browser monitor not connected. Cannot take action.")
            return False
        
        recommendation = analysis.get('recommendation', 'continue_monitoring')
        message = analysis.get('message', '')
        
        try:
            if recommendation == 'encourage':
                self.browser_monitor.show_notification(message, duration=8)
                self.student_activity['encouragement_count'] += 1
                print(f"Encouraged student: {message}")
                
            elif recommendation == 'warn':
                self.browser_monitor.show_notification(message, duration=6)
                self.student_activity['warning_count'] += 1
                print(f"Warned student: {message}")
                
            elif recommendation == 'intervene':
                # Show immediate warning
                self.browser_monitor.show_notification(message, duration=10)
                
                # Search for appropriate educational alternatives
                search_query = f"educational websites for students learning"
                try:
                    search_results = self.search_tool.run(search_query)
                    
                    # Use LLM to find the best alternative
                    prompt = f"""
                    The student is accessing inappropriate content: {analysis.get('current_url', '')}
                    Search results for educational alternatives: {search_results}
                    
                    Please suggest the best educational website URL that would be appropriate for students.
                    Return only ONE URL that starts with http or https.
                    """
                    
                    response = self.llm.invoke([HumanMessage(content=prompt)])
                    alternatives = response.content.strip().split('\n')
                    
                    # Find the first valid URL
                    alternative_url = None
                    for alt in alternatives:
                        alt = alt.strip()
                        if alt.startswith('http'):
                            alternative_url = alt
                            break
                    
                    # If no valid URL found, use a default educational site
                    if not alternative_url:
                        alternative_url = "https://www.khanacademy.org"
                    
                    # Navigate to educational alternative (don't close tab)
                    if self.browser_monitor.navigate_to(alternative_url):
                        self.browser_monitor.show_notification(
                            f"Redirected to educational content: {alternative_url}", 
                            duration=15
                        )
                        print(f"Intervened: redirected to {alternative_url}")
                    else:
                        # Fallback: open in new tab if navigation fails
                        if self.browser_monitor.open_new_tab(alternative_url):
                            self.browser_monitor.show_notification(
                                f"Opened educational content in new tab: {alternative_url}", 
                                duration=15
                            )
                            print(f"Intervened: opened new tab with {alternative_url}")
                
                except Exception as e:
                    print(f"Error finding educational alternatives: {e}")
                    # Fallback to a known educational site
                    fallback_url = "https://www.khanacademy.org"
                    if self.browser_monitor.navigate_to(fallback_url):
                        self.browser_monitor.show_notification(
                            f"Redirected to educational content: {fallback_url}", 
                            duration=15
                        )
                        print(f"Intervened with fallback: redirected to {fallback_url}")
                
                self.student_activity['intervention_count'] += 1
                
            return True
            
        except Exception as e:
            print(f"Error taking action: {e}")
            return False
    
    def generate_encouragement_message(self, context: str) -> str:
        """Generate a personalized encouragement message"""
        prompt = f"""
        You are a supportive educational assistant helping a student stay focused on their studies.
        
        Context: {context}
        
        Generate a brief, encouraging message (1-2 sentences) that will motivate the student to continue their good work.
        Be positive, specific, and age-appropriate.
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            print(f"Error generating encouragement: {e}")
            return "Great job staying focused on your studies!"
    
    def run_agent_loop(self, interval: int = 30):
        """Main agent loop that continuously monitors and takes actions"""
        print(f"Starting AI agent loop with {interval}-second intervals...")
        print("Press Ctrl+C to stop the agent.")
        
        while True:
            try:
                # Get recent activity
                recent_activity = self.get_recent_activity(minutes=15)
                
                # Analyze behavior
                analysis = self.analyze_student_behavior(recent_activity)
                
                # Take action if needed
                if analysis['recommendation'] != 'continue_monitoring':
                    self.take_action(analysis)
                
                # Log agent activity
                self.log_agent_activity(analysis)
                
                # Wait before next check
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\nAgent loop stopped by user.")
                break
            except Exception as e:
                print(f"Error in agent loop: {e}")
                time.sleep(interval)
    
    def log_agent_activity(self, analysis: Dict[str, Any]):
        """Log agent decisions and actions"""
        log_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'current_url': analysis.get('current_url', ''),
            'site_category': analysis.get('site_category', ''),
            'time_on_site': analysis.get('time_on_site', 0),
            'recommendation': analysis.get('recommendation', ''),
            'message': analysis.get('message', ''),
            'encouragement_count': self.student_activity['encouragement_count'],
            'warning_count': self.student_activity['warning_count'],
            'intervention_count': self.student_activity['intervention_count']
        }
        
        # Append to agent log file
        agent_log_file = 'agent_logs.csv'
        file_exists = os.path.exists(agent_log_file)
        
        with open(agent_log_file, 'a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=log_entry.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(log_entry)
    
    def set_browser_monitor(self, browser_monitor):
        """Set the browser monitor instance for taking actions"""
        self.browser_monitor = browser_monitor


def main():
    parser = argparse.ArgumentParser(description="AI Agent for Student Browser Monitoring")
    parser.add_argument("--interval", "-i", type=int, default=30, 
                       help="Agent check interval in seconds (default: 30)")
    parser.add_argument("--api-key", "-k", 
                       help="OpenAI API key (or set OPENAI_API_KEY environment variable)")
    
    args = parser.parse_args()
    
    try:
        # Initialize agent
        agent = StudentAIAgent(openai_api_key=args.api_key)
        print("AI Agent initialized successfully!")
        
        # Run agent loop
        agent.run_agent_loop(interval=args.interval)
        
    except Exception as e:
        print(f"Error initializing agent: {e}")
        print("Make sure you have set the OPENAI_API_KEY environment variable.")


if __name__ == "__main__":
    main() 