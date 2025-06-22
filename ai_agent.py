#!/usr/bin/env python3
"""
AI Agent for Student Browser Monitoring
Uses LangChain and Computer Vision to intelligently monitor student activity
Enhanced with Text-to-Speech feedback using LMNT
"""

import os
import time
import csv
import json
import argparse
import base64
import asyncio
import subprocess
import platform
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import pandas as pd
from langchain_community.llms import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import initialize_agent, AgentType, Tool
from langchain.memory import ConversationBufferMemory
import re
from urllib.parse import urlparse
from PIL import Image
import pytesseract

# Import configuration
from config import (
    OPENAI_API_KEY, LMNT_API_KEY, SPEECH_ENABLED, SPEECH_COOLDOWN,
    DEFAULT_MODEL, FAST_MODEL, TEMPERATURE, MAX_TOKENS
)

# LMNT SDK import
try:
    from lmnt.api import Speech
    LMNT_AVAILABLE = True
except ImportError:
    LMNT_AVAILABLE = False
    print("⚠️ LMNT SDK not available - speech synthesis will be limited")

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("⚠️ pygame not available - will use system audio commands")


class SmartStudentAIAgent:
    def __init__(self, openai_api_key: str = None, lmnt_api_key: str = None):
        # Use provided API keys or fall back to config
        self.openai_api_key = openai_api_key or OPENAI_API_KEY
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in .env file or pass it to constructor.")
        
        # LMNT API for text-to-speech
        self.lmnt_api_key = lmnt_api_key or LMNT_API_KEY
        self.lmnt_voice = "daniel"  # Changed to male voice
        self.speech_enabled = SPEECH_ENABLED and (LMNT_AVAILABLE or platform.system().lower() == "darwin")
        
        # Initialize pygame for audio playback if available
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
                print("🔊 Audio system initialized")
            except Exception as e:
                print(f"⚠️ Audio initialization failed: {e}")
        
        # Set API key as environment variable for LMNT
        if LMNT_AVAILABLE and not os.getenv('LMNT_API_KEY'):
            os.environ['LMNT_API_KEY'] = self.lmnt_api_key
        
        # Initialize LLM with vision capabilities
        self.llm = ChatOpenAI(
            temperature=TEMPERATURE,
            openai_api_key=self.openai_api_key,
            model_name=DEFAULT_MODEL,
            max_tokens=MAX_TOKENS,
            timeout=10
        )
        
        # Faster LLM for quick decisions
        self.fast_llm = ChatOpenAI(
            temperature=0.1,
            openai_api_key=self.openai_api_key,
            model_name=FAST_MODEL,
            max_tokens=200,
            timeout=5
        )
        
        # Fallback LLM for text-only tasks
        self.text_llm = ChatOpenAI(
            temperature=0.7,
            openai_api_key=self.openai_api_key,
            model_name=FAST_MODEL,
            max_tokens=300,
            timeout=8
        )
        
        # Initialize search tool
        self.search_tool = DuckDuckGoSearchRun()
        
        # Initialize memory for learning student patterns
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
            llm=self.text_llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True
        )
        
        # Site categories (now used as hints for AI)
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
        
        self.inappropriate_keywords = [
            'porn', 'pornography', 'adult', 'mature', 'explicit', 'nude', 'naked',
            'sex', 'sexual', 'dating', 'hookup', 'tinder', 'bumble', 'grindr',
            'gambling', 'casino', 'bet', 'poker', 'slot', 'lottery',
            'drugs', 'marijuana', 'cocaine', 'heroin', 'weed', 'alcohol', 'beer', 'wine',
            'violence', 'gore', 'blood', 'murder', 'suicide', 'self-harm',
            'hack', 'crack', 'cheat', 'steal', 'illegal', 'weapon', 'gun'
        ]
        
        # Track student activity and patterns
        self.student_activity = {
            'current_site': None,
            'site_start_time': None,
            'last_action_time': None,
            'encouragement_count': 0,
            'warning_count': 0,
            'intervention_count': 0,
            'session_start': datetime.now(),
            'total_study_time': 0,
            'total_distraction_time': 0,
            'browsing_patterns': {}
        }
        
        # Browser monitor reference
        self.browser_monitor = None
        
        # Speech feedback settings
        self.last_speech_time = None
        self.speech_cooldown = SPEECH_COOLDOWN
        self.speech_count = 0
        
    def encode_image_for_vision(self, image_path: str) -> str:
        """Encode image to base64 for vision API"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error encoding image: {e}")
            return None
    
    def analyze_screenshot(self, screenshot_path):
        """Analyze screenshot using GPT-4 Vision to determine content appropriateness"""
        try:
            # Read and encode the image
            with open(screenshot_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            response = self.llm.invoke([
                HumanMessage(content=[
                    {
                        "type": "text",
                        "text": """Analyze this screenshot and determine if it contains inappropriate content for a student monitoring system. 
                        
                        Look for:
                        - Adult/explicit content
                        - Violence or disturbing imagery
                        - Gambling or betting sites
                        - Social media during study time
                        - Gaming or entertainment sites during study time
                        - Any content that would be inappropriate for educational purposes
                        
                        Respond with a JSON object containing:
                        {
                            "inappropriate": true/false,
                            "category": "category of content if inappropriate",
                            "confidence": 0.0-1.0,
                            "description": "brief description of what you see",
                            "action_needed": "suggested action if inappropriate"
                        }"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ])
            ])
            
            # Parse the response
            content = response.content
            
            # Try to extract JSON from the response
            try:
                # Look for JSON in the response
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = content[start:end]
                    analysis = json.loads(json_str)
                else:
                    # Fallback if no JSON found
                    analysis = {
                        "inappropriate": False,
                        "category": "unknown",
                        "confidence": 0.5,
                        "description": content,
                        "action_needed": "none"
                    }
            except json.JSONDecodeError:
                # Fallback analysis
                analysis = {
                    "inappropriate": "inappropriate" in content.lower() or "explicit" in content.lower(),
                    "category": "analysis_failed",
                    "confidence": 0.3,
                    "description": content,
                    "action_needed": "manual_review"
                }
            
            return analysis
            
        except Exception as e:
            print(f"Screenshot analysis failed: {e}")
            return {
                "inappropriate": False,
                "category": "analysis_error",
                "confidence": 0.0,
                "description": f"Error analyzing screenshot: {str(e)}",
                "action_needed": "manual_review"
            }
    
    def analyze_browsing_patterns(self, recent_activity: List[Dict]) -> Dict[str, Any]:
        """Analyze student's browsing patterns and history"""
        if not recent_activity:
            return {"pattern": "no_data", "trend": "neutral", "focus_score": 5}
        
        try:
            # Analyze recent activity patterns
            educational_time = 0
            distraction_time = 0
            site_switches = 0
            unique_sites = set()
            
            for i, activity in enumerate(recent_activity):
                url = str(activity.get('url', ''))
                unique_sites.add(urlparse(url).netloc)
                
                # Count site switches (indicator of focus vs jumping around)
                if i > 0:
                    prev_url = str(recent_activity[i-1].get('url', ''))
                    if urlparse(url).netloc != urlparse(prev_url).netloc:
                        site_switches += 1
                
                # Categorize time spent
                if any(edu_site in url for edu_site in self.educational_sites):
                    educational_time += 1
                elif any(dist_site in url for dist_site in self.distracting_sites):
                    distraction_time += 1
            
            # Calculate pattern metrics
            total_entries = len(recent_activity)
            focus_score = max(0, 10 - (site_switches / max(1, total_entries) * 10))
            educational_ratio = educational_time / max(1, total_entries)
            distraction_ratio = distraction_time / max(1, total_entries)
            
            # Determine pattern
            if educational_ratio > 0.7:
                pattern = "focused_study"
            elif distraction_ratio > 0.6:
                pattern = "heavy_distraction"
            elif site_switches > total_entries * 0.5:
                pattern = "scattered_browsing"
            else:
                pattern = "mixed_activity"
            
            # Determine trend
            if educational_ratio > distraction_ratio * 2:
                trend = "improving"
            elif distraction_ratio > educational_ratio * 2:
                trend = "declining"
            else:
                trend = "stable"
            
            return {
                "pattern": pattern,
                "trend": trend,
                "focus_score": focus_score,
                "educational_ratio": educational_ratio,
                "distraction_ratio": distraction_ratio,
                "site_switches": site_switches,
                "unique_sites": len(unique_sites),
                "total_entries": total_entries
            }
            
        except Exception as e:
            print(f"Error analyzing browsing patterns: {e}")
            return {"pattern": "analysis_error", "trend": "neutral", "focus_score": 5}
    
    def make_intelligent_decision(self, current_activity: Dict, screenshot_analysis: Dict, 
                                pattern_analysis: Dict, time_on_site: float) -> Dict[str, Any]:
        """Use AI to make intelligent decisions about student intervention"""
        
        # Create comprehensive context for AI decision making
        context = f"""
        STUDENT MONITORING CONTEXT:
        
        Current Activity:
        - URL: {current_activity.get('url', 'unknown')}
        - Title: {current_activity.get('page_title', 'unknown')}
        - Time on site: {time_on_site:.1f} seconds
        - Search query: {current_activity.get('search_query', 'none')}
        
        Screenshot Analysis:
        - Content type: {screenshot_analysis.get('content_type', 'unknown')}
        - Educational value: {screenshot_analysis.get('educational_value', 0)}/10
        - Distraction level: {screenshot_analysis.get('distraction_level', 0)}/10
        - Activity: {screenshot_analysis.get('specific_activity', 'unknown')}
        - Description: {screenshot_analysis.get('description', 'none')}
        
        Browsing Patterns:
        - Pattern: {pattern_analysis.get('pattern', 'unknown')}
        - Trend: {pattern_analysis.get('trend', 'neutral')}
        - Focus score: {pattern_analysis.get('focus_score', 5)}/10
        - Educational ratio: {pattern_analysis.get('educational_ratio', 0):.2f}
        - Site switches: {pattern_analysis.get('site_switches', 0)}
        
        Student History:
        - Total encouragements: {self.student_activity['encouragement_count']}
        - Total warnings: {self.student_activity['warning_count']}
        - Total interventions: {self.student_activity['intervention_count']}
        - Session duration: {(datetime.now() - self.student_activity['session_start']).total_seconds() / 60:.1f} minutes
        """
        
        # Check for immediate inappropriate content
        inappropriate_content = self.check_for_inappropriate_content(current_activity)
        if inappropriate_content:
            return {
                'recommendation': 'intervene',
                'timeout': 0,  # Immediate intervention
                'message': f"Inappropriate content detected. Redirecting to educational resources.",
                'reasoning': f"Detected: {inappropriate_content}",
                'urgency': 'high',
                'emotion': False
            }
        
        # Use AI to make nuanced decision
        decision_prompt = f"""
        You are an intelligent tutoring system monitoring a student's computer activity. Based on the context below, make a QUICK decision about how to respond.
        
        {context}
        
        Decide between three actions:
        1. ENCOURAGE: Student is doing well, give positive reinforcement
        2. WARN: Student is getting distracted, give gentle reminder
        3. INTERVENE: Student needs redirection to educational content
        
        For your decision, consider:
        - How long they've been on the current site
        - Whether the content is educational or distracting
        - Their recent browsing patterns
        - Previous interventions (avoid being too pushy)
        
        Provide your response as JSON with:
        {{
            "recommendation": "encourage|warn|intervene",
            "timeout": <seconds to wait before this action>,
            "message": "<brief, personalized message for the student>",
            "reasoning": "<brief explanation of your decision>",
            "urgency": "low|medium|high"
            "emotion": <just fill this with False>
        }}
        
        IMPORTANT - Keep timeouts SHORT for faster responses:
        - ENCOURAGE: Educational content, focused work (timeout: 3-10 seconds)
        - WARN: Mild distraction, some off-task behavior (timeout: 5-15 seconds)  
        - INTERVENE: Heavy distraction, inappropriate content (timeout: 0-5 seconds)
        
        Make the message brief, encouraging, and age-appropriate.
        """
        
        try:
            response = self.text_llm.invoke([HumanMessage(content=decision_prompt)])
            decision = json.loads(response.content)
            
            # Validate and set defaults
            if decision.get('recommendation') not in ['encourage', 'warn', 'intervene']:
                decision['recommendation'] = 'warn'
            if not isinstance(decision.get('timeout'), (int, float)) or decision['timeout'] < 0:
                decision['timeout'] = 30
            if not decision.get('message'):
                decision['message'] = "Keep up the good work with your studies!"
                
            return decision
            
        except Exception as e:
            print(f"Error in AI decision making: {e}")
            # Fallback to simple rule-based decision
            return self.fallback_decision(screenshot_analysis, time_on_site)
    
    def fallback_decision(self, screenshot_analysis: Dict, time_on_site: float) -> Dict[str, Any]:
        """Fallback rule-based decision if AI fails"""
        educational_value = screenshot_analysis.get('educational_value', 5)
        distraction_level = screenshot_analysis.get('distraction_level', 5)
        
        if educational_value >= 7:
            return {
                'recommendation': 'encourage',
                'timeout': 5,  # Reduced from 60
                'message': "Great job staying focused on your studies!",
                'reasoning': "High educational value detected",
                'urgency': 'low',
                'emotion': False
            }
        elif distraction_level >= 7 or time_on_site > 300:
            return {
                'recommendation': 'intervene',
                'timeout': 3,  # Reduced from 15
                'message': "Let's get back to your studies. I'll help you find some educational content.",
                'reasoning': "High distraction or long time off-task",
                'urgency': 'high',
                'emotion': False
            }
        else:
            return {
                'recommendation': 'warn',
                'timeout': 8,  # Reduced from 30
                'message': "Remember to stay focused on your learning goals!",
                'reasoning': "Moderate distraction detected",
                'urgency': 'medium',
                'emotion': False
            }
    
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
                return []
            
            # Get recent entries
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            recent_activity = df[df['datetime'] >= cutoff_time].to_dict('records')
            
            return recent_activity
            
        except Exception as e:
            print(f"Error reading activity logs: {e}")
            return []
    
    def analyze_student_behavior(self, recent_activity: List[Dict], use_fast_mode: bool = False) -> Dict[str, Any]:
        """Main analysis function that coordinates all AI components"""
        if not recent_activity:
            return {'status': 'no_activity', 'recommendation': 'continue_monitoring'}
        
        # Get current activity
        latest_activity = recent_activity[-1]
        current_url = str(latest_activity.get('url', ''))
        current_time = datetime.now()
        
        # Update tracking
        if self.student_activity['current_site'] != current_url:
            self.student_activity['current_site'] = current_url
            self.student_activity['site_start_time'] = current_time
        
        time_on_site = (current_time - self.student_activity['site_start_time']).total_seconds()
        
        # Quick pattern analysis (lightweight)
        pattern_analysis = self.analyze_browsing_patterns(recent_activity)
        
        # Use fast mode only for very simple cases
        if use_fast_mode:
            decision = self.make_fast_decision(latest_activity, pattern_analysis, time_on_site)
            
            # Use full AI analysis more frequently - only skip for very obvious cases
            needs_full_analysis = (
                decision['recommendation'] != 'encourage' or  # Any non-encouragement needs full analysis
                time_on_site > 120 or  # More than 2 minutes on same site
                pattern_analysis.get('pattern') != 'focused_study' or  # Not clearly focused
                self.student_activity.get('intervention_count', 0) > 0  # Previous interventions
            )
            
            if not needs_full_analysis:
                return {
                    'current_url': current_url,
                    'time_on_site': time_on_site,
                    'screenshot_analysis': {'description': 'Fast mode - no screenshot analysis'},
                    'pattern_analysis': pattern_analysis,
                    'recommendation': decision['recommendation'],
                    'timeout': decision['timeout'],
                    'message': decision['message'],
                    'reasoning': decision.get('reasoning', ''),
                    'urgency': decision.get('urgency', 'medium'),
                    'emotion': decision.get('emotion', False),
                    'ai_enhanced': False,
                    'fast_mode': True
                }
        
        # Full AI analysis (use this as default now)
        screenshot_path = latest_activity.get('screenshot_path', '')
        
        # Run AI analyses
        screenshot_analysis = self.analyze_screenshot(screenshot_path)
        
        # Make intelligent decision
        decision = self.make_intelligent_decision(
            latest_activity, screenshot_analysis, pattern_analysis, time_on_site
        )
        
        # Compile comprehensive analysis
        analysis = {
            'current_url': current_url,
            'time_on_site': time_on_site,
            'screenshot_analysis': screenshot_analysis,
            'pattern_analysis': pattern_analysis,
            'recommendation': decision['recommendation'],
            'timeout': decision['timeout'],
            'message': decision['message'],
            'reasoning': decision.get('reasoning', ''),
            'urgency': decision.get('urgency', 'medium'),
            'emotion': decision.get('emotion', False),
            'ai_enhanced': True,
            'fast_mode': False
        }
        
        return analysis
    
    def check_for_inappropriate_content(self, activity: Dict) -> str:
        """Check for inappropriate content in search queries and page content"""
        url = str(activity.get('url', '')).lower()
        
        # Check for obviously inappropriate domains first
        inappropriate_domains = [
            '4chan.org', '4chan.com', 'pornhub.com', 'xvideos.com', 'redtube.com',
            'youporn.com', 'xhamster.com', 'tinder.com', 'grindr.com', 'bumble.com',
            'onlyfans.com', 'chaturbate.com', 'cam4.com', 'myfreecams.com',
            'livejasmin.com', 'stripchat.com', 'bet365.com', 'draftkings.com',
            'fanduel.com', 'pokerstars.com', 'casino.com'
        ]
        
        for domain in inappropriate_domains:
            if domain in url:
                return f"inappropriate domain '{domain}' detected"
        
        # Check for inappropriate keywords in URL and search queries (more targeted)
        url_keywords = [
            'porn', 'xxx', 'adult', 'nude', 'naked', 'sex', 'dating', 'hookup',
            'tinder', 'grindr', 'bumble', 'hinge', 'onlyfans',  # Added dating apps
            'gambling', 'casino', 'bet', 'poker', 'slots', 'lottery',
            'drugs', 'weed', 'cocaine', 'heroin', 'marijuana'
        ]
        
        for keyword in url_keywords:
            if keyword in url:
                return f"inappropriate keyword '{keyword}' in URL"
            if keyword in str(activity.get('search_query', '')).lower():
                return f"inappropriate keyword '{keyword}' in search query"
        
        # More conservative content checking (avoid false positives)
        page_title = str(activity.get('page_title', '')).lower()
        explicit_title_keywords = ['porn', 'xxx', 'adult content', 'nude', 'dating app']
        
        for keyword in explicit_title_keywords:
            if keyword in page_title:
                return f"inappropriate keyword '{keyword}' in page title"
        
        return None
    
    def perform_action(self, analysis: Dict[str, Any]) -> bool:
        """Perform the recommended action based on AI analysis"""
        recommendation = analysis.get('recommendation', 'continue_monitoring')
        message = analysis.get('message', '')
        timeout = analysis.get('timeout', 30)
        urgency = analysis.get('urgency', 'medium')
        emotion = analysis.get('emotion', False)
        
        if recommendation == 'continue_monitoring':
            return True
            
        # Wait for the AI-determined timeout before taking action
        if timeout > 0:
            # Reduce maximum timeout for faster response
            actual_timeout = min(timeout, 3)  # Cap at 3 seconds max
            print(f"AI recommends waiting {actual_timeout} seconds before action (urgency: {urgency})")
            time.sleep(actual_timeout)
        
        # Check if speech feedback should be given
        speech_given = False
        speech_message = ""
        if self.speech_enabled:
            try:
                # Run speech feedback asynchronously
                loop = None
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                speech_given = loop.run_until_complete(self.give_speech_feedback(analysis))
                if speech_given:
                    speech_message = getattr(self, '_last_speech_text', '')
                
            except Exception as e:
                print(f"⚠️ Speech feedback error: {e}")
        
        try:
            if recommendation == 'encourage':
                self.student_activity['encouragement_count'] += 1
                success = self.show_encouragement(message)
                if success:
                    feedback_type = "🗣️ + 🎉" if speech_given else "🎉"
                    print(f"✅ {feedback_type} Encouragement shown: {message}")
                    if speech_given:
                        print(f"🎤 Speech given: {speech_message}")
                return success
                
            elif recommendation == 'warn':
                self.student_activity['warning_count'] += 1
                success = self.show_warning(message)
                if success:
                    feedback_type = "🗣️ + ⚠️" if speech_given else "⚠️"
                    print(f"✅ {feedback_type} Warning shown: {message}")
                    if speech_given:
                        print(f"🎤 Speech given: {speech_message}")
                return success
                
            elif recommendation == 'intervene':
                print("trigger intervention")
                self.student_activity['intervention_count'] += 1
                success = self.perform_intervention(analysis)
                if success:
                    if urgency == 'high':
                        feedback_type = "🗣️ + 🚨 SERIOUS" if speech_given else "🚨 SERIOUS"
                    else:
                        feedback_type = "🗣️ + 🚨" if speech_given else "🚨"
                    print(f"✅ {feedback_type} Intervention performed: {message}")
                    if speech_given:
                        print(f"🎤 Detailed speech explanation: {speech_message}")
                return success
                
        except Exception as e:
            print(f"Error performing action {recommendation}: {e}")
            return False
            
        return True
    
    def show_encouragement(self, message: str) -> bool:
        """Show encouraging message to student"""
        if not self.browser_monitor:
            print(f"Encouragement: {message}")
            return True
            
        return self.browser_monitor.show_notification(f"🎉 {message}", duration=6)
    
    def show_warning(self, message: str) -> bool:
        """Show warning message to student"""
        if not self.browser_monitor:
            print(f"Warning: {message}")
            return True
            
        return self.browser_monitor.show_notification(f"⚠️ {message}", duration=8)
    
    def perform_intervention(self, analysis: Dict[str, Any]) -> bool:
        """Perform intervention by redirecting to educational content"""
        if not self.browser_monitor:
            print(f"Intervention needed: {analysis.get('message', 'Redirecting to educational content')}")
            return True
        
        try:
            # Show immediate notification
            message = analysis.get('message', 'Redirecting to educational content for better learning. Focus on sites for younger children such as iXL or Khan Academy')
            self.browser_monitor.show_notification(f"🚨 {message}", duration=6)
            
            # Wait a moment for notification to be seen
            time.sleep(2)
            
            # Get AI-suggested educational alternative
            current_activity = {
                'url': analysis.get('current_url', ''),
                'search_query': '',
                'page_content': ''
            }
            
            educational_url = self.get_educational_alternative(current_activity)
            
            if educational_url and educational_url.startswith('http'):
                # Navigate to educational content
                success = self.browser_monitor.navigate_to(educational_url)
                if success:
                    print(f"✅ Successfully redirected to educational content: {educational_url}")
                    return True
                else:
                    print("❌ Failed to navigate to educational content")
            
            # Fallback to a known educational site
            fallback_url = "https://www.khanacademy.org"
            success = self.browser_monitor.navigate_to(fallback_url)
            if success:
                print(f"✅ Redirected to fallback educational site: {fallback_url}")
                return True
            else:
                print("❌ Failed to redirect to fallback educational site")
                return False
                
        except Exception as e:
            print(f"Error during intervention: {e}")
            return False
    
    def get_educational_alternative(self, activity: Dict) -> str:
        """Get AI-suggested educational alternative based on current activity"""
        try:
            current_url = activity.get('url', '')
            search_query = activity.get('search_query', '')
            
            # Create context for AI to suggest educational alternatives
            context = f"""
            The student is currently on: {current_url}
            Recent search query: {search_query}
            
            Suggest ONE educational website URL that would be appropriate for a student.
            Consider their apparent interests but redirect to educational content. This content should be focused on sites for younger children such as iXL or Khan Academy.
            
            Respond with only the URL, nothing else.
            Example: https://www.khanacademy.org/math
            """
            
            response = self.text_llm.invoke([HumanMessage(content=context)])
            suggested_url = response.content.strip()
            
            # Validate the URL
            if suggested_url and suggested_url.startswith('http') and len(suggested_url) < 200:
                return suggested_url
            else:
                return "https://www.khanacademy.org"
                
        except Exception as e:
            print(f"Error getting educational alternative: {e}")
            return "https://www.khanacademy.org"
    
    def generate_progress_report(self) -> str:
        """Generate AI-powered progress report for the student"""
        try:
            # Get recent activity for analysis
            recent_activity = self.get_recent_activity(minutes=30)
            
            if not recent_activity:
                return "No recent activity to analyze."
            
            # Analyze patterns
            pattern_analysis = self.analyze_browsing_patterns(recent_activity)
            
            # Create context for AI report generation
            context = f"""
            Generate a brief, encouraging progress report for a student based on their recent computer activity.
            
            Activity Summary:
            - Total activities tracked: {len(recent_activity)}
            - Browsing pattern: {pattern_analysis.get('pattern', 'unknown')}
            - Focus score: {pattern_analysis.get('focus_score', 5)}/10
            - Educational ratio: {pattern_analysis.get('educational_ratio', 0):.2f}
            - Site switches: {pattern_analysis.get('site_switches', 0)}
            - Session duration: {(datetime.now() - self.student_activity['session_start']).total_seconds() / 60:.1f} minutes
            
            Student Stats:
            - Encouragements received: {self.student_activity['encouragement_count']}
            - Warnings received: {self.student_activity['warning_count']}
            - Interventions needed: {self.student_activity['intervention_count']}
            
            Write a positive, constructive report (2-3 sentences) that:
            1. Acknowledges their effort
            2. Highlights any positive patterns
            3. Gives gentle suggestions for improvement if needed
            
            Keep it encouraging and age-appropriate.
            """
            
            response = self.text_llm.invoke([HumanMessage(content=context)])
            return response.content.strip()
            
        except Exception as e:
            print(f"Error generating progress report: {e}")
            return "Keep up the great work with your studies! Remember to stay focused and take breaks when needed."
    
    def save_analysis_log(self, analysis: Dict[str, Any]):
        """Save detailed analysis to log file"""
        try:
            log_entry = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'current_url': analysis.get('current_url', ''),
                'time_on_site': analysis.get('time_on_site', 0),
                'recommendation': analysis.get('recommendation', ''),
                'timeout': analysis.get('timeout', 0),
                'message': analysis.get('message', ''),
                'reasoning': analysis.get('reasoning', ''),
                'urgency': analysis.get('urgency', 'medium'),
                'emotion': analysis.get('emotion', False),
                'ai_enhanced': analysis.get('ai_enhanced', False),
                'screenshot_analysis': json.dumps(analysis.get('screenshot_analysis', {})),
                'pattern_analysis': json.dumps(analysis.get('pattern_analysis', {})),
                'encouragement_count': self.student_activity['encouragement_count'],
                'warning_count': self.student_activity['warning_count'],
                'intervention_count': self.student_activity['intervention_count']
            }
            
            # Save to CSV
            log_file = "ai_analysis.csv"
            file_exists = os.path.exists(log_file)
            
            with open(log_file, 'a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=log_entry.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(log_entry)
                
        except Exception as e:
            print(f"Error saving analysis log: {e}")
    
    def set_browser_monitor(self, browser_monitor):
        """Set the browser monitor instance for taking actions"""
        self.browser_monitor = browser_monitor

    def make_fast_decision(self, current_activity: Dict, pattern_analysis: Dict, time_on_site: float) -> Dict[str, Any]:
        """Make quick decisions without screenshot analysis for faster response"""
        
        # Check for immediate inappropriate content first (both domains AND keywords)
        inappropriate_content = self.check_for_inappropriate_content(current_activity)
        if inappropriate_content:
            return {
                'recommendation': 'intervene',
                'timeout': 0,  # Immediate intervention
                'message': f"Inappropriate content detected. Redirecting to educational resources.",
                'reasoning': f"Detected: {inappropriate_content}",
                'urgency': 'high',
                'emotion': False
            }
        
        # Quick rule-based decisions for clean content
        current_url = str(current_activity.get('url', '')).lower()
        
        # Educational sites - quick encouragement
        if any(edu_site in current_url for edu_site in self.educational_sites):
            return {
                'recommendation': 'encourage',
                'timeout': 5,  # Much faster
                'message': "Great choice! Keep up the focused learning!",
                'reasoning': "Educational site detected",
                'urgency': 'low',
                'emotion': False
            }
        
        # Distracting sites - quick warning (only if no inappropriate content)
        if any(dist_site in current_url for dist_site in self.distracting_sites):
            if time_on_site > 120:  # 2 minutes
                return {
                    'recommendation': 'intervene',
                    'timeout': 5,
                    'message': "Time to refocus! Let's get back to productive learning.",
                    'reasoning': "Extended time on distracting site",
                    'urgency': 'medium',
                    'emotion': False
                }
            else:
                return {
                    'recommendation': 'warn',
                    'timeout': 10,
                    'message': "Remember to stay focused on your learning goals!",
                    'reasoning': "Distracting site detected",
                    'urgency': 'medium',
                    'emotion': False
                }
        
        # Default - continue monitoring with minimal delay
        return {
            'recommendation': 'continue_monitoring',
            'timeout': 0,
            'message': "",
            'reasoning': "Normal browsing activity",
            'urgency': 'low',
            'emotion': False
        }

    async def synthesize_speech(self, text: str) -> bytes:
        """Synthesize speech using LMNT SDK"""
        if not LMNT_AVAILABLE:
            print("⚠️ LMNT SDK not available")
            return None
            
        try:
            # Set API key as environment variable if not already set
            if not os.getenv('LMNT_API_KEY'):
                os.environ['LMNT_API_KEY'] = self.lmnt_api_key
            
            # Use the correct LMNT API pattern based on working example
            async with Speech(api_key=self.lmnt_api_key) as speech:
                synthesis = await speech.synthesize(text, self.lmnt_voice)
                
                # Handle different possible response formats
                if hasattr(synthesis, 'audio'):
                    audio_data = synthesis.audio
                elif isinstance(synthesis, dict) and 'audio' in synthesis:
                    audio_data = synthesis['audio']
                else:
                    # Try to access as bytes directly
                    audio_data = synthesis
                
                print(f"✅ Speech synthesized successfully ({len(audio_data)} bytes)")
                return audio_data
                
        except Exception as e:
            print(f"⚠️ Speech synthesis error: {e}")
            return None
    
    def play_speech(self, audio_data: bytes) -> bool:
        """Play synthesized speech audio with multiple fallback methods"""
        if not self.speech_enabled:
            return False
            
        temp_file = f"temp_speech_{int(time.time())}.mp3"
        
        try:
            # Save audio to temporary file
            with open(temp_file, 'wb') as f:
                f.write(audio_data)
            
            # Try pygame first if available
            if PYGAME_AVAILABLE:
                try:
                    # Initialize mixer for MP3 if needed
                    if not pygame.mixer.get_init():
                        pygame.mixer.init(frequency=24000, size=-16, channels=2, buffer=1024)
                    
                    # Stop any currently playing audio
                    pygame.mixer.music.stop()
                    
                    # Load and play audio
                    pygame.mixer.music.load(temp_file)
                    pygame.mixer.music.play()
                    
                    # Wait for playback to finish with timeout
                    max_wait = 10  # Maximum 10 seconds
                    wait_time = 0
                    while pygame.mixer.music.get_busy() and wait_time < max_wait:
                        time.sleep(0.1)
                        wait_time += 0.1
                    
                    print("✅ Audio played successfully with pygame")
                    return True
                    
                except Exception as pygame_error:
                    print(f"⚠️ pygame audio failed: {pygame_error}")
                    # Fall through to system command
            
            # Fallback to system audio commands
            system = platform.system().lower()
            
            if system == "darwin":  # macOS
                # Try multiple macOS audio players
                players = [
                    ["afplay", temp_file],
                    ["ffplay", "-nodisp", "-autoexit", temp_file],
                    ["mpg123", temp_file],
                    ["open", temp_file]  # Use default system player
                ]
                
                for player_cmd in players:
                    try:
                        result = subprocess.run(player_cmd, check=True, timeout=10,
                                              stdout=subprocess.DEVNULL, 
                                              stderr=subprocess.DEVNULL)
                        print(f"✅ Audio played successfully with {player_cmd[0]}")
                        return True
                    except subprocess.TimeoutExpired:
                        print(f"⚠️ {player_cmd[0]} timed out")
                        continue
                    except subprocess.CalledProcessError as e:
                        print(f"⚠️ {player_cmd[0]} failed: {e}")
                        continue
                    except FileNotFoundError:
                        continue  # Try next player
                
                # Final fallback: Use macOS built-in 'say' command with original text
                try:
                    # Extract original text from the speech generation context
                    speech_text = getattr(self, '_last_speech_text', 'Please focus on your studies')
                    subprocess.run(["say", "-v", "Daniel", speech_text], check=True, timeout=10)
                    print("✅ Audio played successfully with macOS 'say' command")
                    return True
                except Exception as say_error:
                    print(f"⚠️ macOS 'say' command failed: {say_error}")
            
            elif system == "linux":
                # Try multiple Linux audio players
                for player in ["mpg123", "ffplay", "paplay", "aplay", "play"]:
                    try:
                        subprocess.run([player, temp_file], check=True, timeout=10, 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        print(f"✅ Audio played successfully with {player}")
                        return True
                    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                        continue
            
            elif system == "windows":
                try:
                    # Use Windows Media Player or PowerShell
                    subprocess.run(["powershell", "-c", f"(New-Object Media.SoundPlayer '{temp_file}').PlaySync()"], 
                                 check=True, timeout=10)
                    print("✅ Audio played successfully with PowerShell")
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    pass
            
            print("❌ All audio playback methods failed")
            return False
            
        except Exception as e:
            print(f"⚠️ Audio playback error: {e}")
            return False
            
        finally:
            # Clean up temp file
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
    
    def should_give_speech_feedback(self, analysis: Dict[str, Any]) -> bool:
        """Determine if speech feedback should be given based on context"""
        current_time = datetime.now()
        
        # Check cooldown (but allow override for serious interventions)
        recommendation = analysis.get('recommendation', '')
        urgency = analysis.get('urgency', 'medium')
        reasoning = analysis.get('reasoning', '').lower()
        emotion = analysis.get('emotion', '')
        #If emotion, speak
        if emotion:
            print("Emotion is true")
            return True
        # Always speak for high urgency interventions (inappropriate content) - OVERRIDE COOLDOWN
        if recommendation == 'intervene' and urgency == 'high':
            print("🗣️ High urgency intervention - speech feedback ENABLED (cooldown bypassed)")
            return True
        
        # Always speak for any intervention with inappropriate content
        if recommendation == 'intervene' and 'inappropriate' in reasoning:
            print("🗣️ Inappropriate content detected - speech feedback ENABLED")
            return True
        
        # Always speak for interventions (but respect cooldown for non-urgent ones)
        if recommendation == 'intervene':
            if not self.last_speech_time or (current_time - self.last_speech_time).total_seconds() > 60:  # Shorter cooldown for interventions
                print("🗣️ Intervention detected - speech feedback ENABLED")
                return True
            else:
                print("🗣️ Intervention detected but in cooldown period")
                return False
        
        # More frequent speech for warnings too
        if recommendation == 'warn':
            if not self.last_speech_time or (current_time - self.last_speech_time).total_seconds() > 90:  # 1.5 minutes for warnings
                print("🗣️ Warning detected - speech feedback ENABLED")
                return True
        
        # Check normal cooldown for other cases
        if self.last_speech_time and (current_time - self.last_speech_time).total_seconds() < self.speech_cooldown:
            return False
        
        # Context-based speech triggers
        current_url = analysis.get('current_url', '').lower()
        time_on_site = analysis.get('time_on_site', 0)
        pattern_analysis = analysis.get('pattern_analysis', {})
        
        # Trigger speech for:
        # 1. Long time on distracting sites (YouTube > 3 minutes instead of 5)
        if 'youtube.com' in current_url and time_on_site > 180:
            print("🗣️ Long YouTube session - speech feedback ENABLED")
            return True
        
        # 2. Any gaming sites (diep.io, coolmathgames after some time)
        gaming_sites = ['diep.io', 'coolmathgames.com', 'poki.com', 'miniclip.com']
        if any(game_site in current_url for game_site in gaming_sites) and time_on_site > 120:
            print("🗣️ Gaming site detected - speech feedback ENABLED")
            return True
        
        # 3. Multiple interventions in short time (struggling student)
        if self.student_activity.get('intervention_count', 0) >= 2:
            print("🗣️ Multiple interventions - speech feedback ENABLED")
            return True
        
        # 4. Low focus score and declining trend
        focus_score = pattern_analysis.get('focus_score', 10)
        trend = pattern_analysis.get('trend', 'stable')
        if focus_score < 4 and trend == 'declining':
            print("🗣️ Low focus score - speech feedback ENABLED")
            return True
        
        # 5. Educational site with good progress (encouragement) - more frequent
        if recommendation == 'encourage' and any(edu_site in current_url for edu_site in self.educational_sites):
            if self.speech_count < 3:  # Allow more encouragement speeches
                print("🗣️ Educational site encouragement - speech feedback ENABLED")
                return True
        
        return False
    
    def generate_speech_message(self, analysis: Dict[str, Any]) -> str:
        """Generate contextual speech message using AI"""
        try:
            recommendation = analysis.get('recommendation', '')
            current_url = analysis.get('current_url', '').lower()
            time_on_site = analysis.get('time_on_site', 0)
            pattern_analysis = analysis.get('pattern_analysis', {})
            reasoning = analysis.get('reasoning', '')
            urgency = analysis.get('urgency', 'medium')
            emotion = analysis.get('emotion', False)
            message = analysis.get('message', '')
            
            # Determine what specific issue we're addressing
            issue_type = "general"
            if 'tinder' in current_url or 'tinder' in reasoning.lower():
                issue_type = "dating_app"
            elif 'inappropriate domain' in reasoning.lower():
                issue_type = "inappropriate_site"
            elif 'inappropriate keyword' in reasoning.lower():
                issue_type = "inappropriate_search"
            elif 'youtube' in current_url and time_on_site > 300:
                issue_type = "youtube_distraction"
            elif 'youtube' in current_url:
                issue_type = "youtube_general"
            elif any(dist_site in current_url for dist_site in ['facebook', 'instagram', 'twitter', 'reddit']):
                issue_type = "social_media"
            
            # For serious interventions, create detailed explanatory messages
            if recommendation == 'intervene' and (urgency == 'high' or 'inappropriate' in reasoning.lower()):
                if issue_type == "dating_app":
                    context = f"""
                    Generate a caring but clear speech message for a student who is on a dating app during study time.
                    
                    The student is on: {current_url}
                    Time spent: {time_on_site/60:.1f} minutes
                    
                    Create a message that:
                    1. Acknowledges they're on a dating app without being judgmental
                    2. Explains why this isn't appropriate during study time
                    3. Mentions we're redirecting to educational content like TED talks or Khan Academy
                    4. Encourages them to focus on their academic goals
                    
                    Keep it under 35 words but make it personal and caring.
                    Example: "I see you're on a dating app. During study time, let's focus on your education. I'm taking you to some inspiring TED talks that can help you grow."
                    """
                
                elif issue_type == "inappropriate_search":
                    context = f"""
                    Generate a caring speech message for a student who searched for inappropriate content.
                    
                    The search was related to: {reasoning}
                    Current site: {current_url}
                    
                    Create a message that:
                    1. Acknowledges the search without repeating inappropriate terms
                    2. Explains why we're redirecting to better content
                    3. Mentions specific educational alternatives we're providing
                    4. Stays positive and encouraging
                    
                    Keep it under 30 words.
                    Example: "I noticed your search wasn't appropriate for study time. Let me take you to some educational content that will help you learn something valuable instead."
                    """
                
                else:
                    context = f"""
                    Generate a caring but firm speech message for inappropriate content during study time.
                    
                    Current situation: {reasoning}
                    Website: {current_url}
                    
                    Create a message that:
                    1. Acknowledges the issue without being harsh
                    2. Explains why we're redirecting
                    3. Mentions the educational alternative we're providing
                    4. Encourages focus on learning goals
                    
                    Keep it under 30 words and sound supportive.
                    """
            
            elif recommendation == 'intervene':
                if issue_type == "youtube_distraction":
                    context = f"""
                    Generate an encouraging speech message for a student who has been on YouTube too long.
                    
                    Time on YouTube: {time_on_site/60:.1f} minutes
                    Current page: {current_url}
                    
                    Create a message that:
                    1. Acknowledges they've been watching for a while
                    2. Suggests it's time to switch to educational content
                    3. Mentions we're taking them to Khan Academy or similar
                    4. Sounds encouraging, not punitive
                    
                    Keep it under 25 words.
                    Example: "You've been on YouTube for {time_on_site/60:.0f} minutes. Time for some learning! I'm taking you to Khan Academy to explore something educational."
                    """
                
                elif issue_type == "social_media":
                    context = f"""
                    Generate a gentle redirection message for social media during study time.
                    
                    Current site: {current_url}
                    Time spent: {time_on_site/60:.1f} minutes
                    
                    Create a message that:
                    1. Acknowledges they're on social media
                    2. Suggests focusing on educational goals instead
                    3. Mentions the educational site we're redirecting to
                    
                    Keep it under 25 words and sound friendly.
                    """
                
                else:
                    context = f"""
                    Generate an encouraging but redirective speech message for a student who needs to refocus.
                    
                    Current situation:
                    - Website: {current_url}
                    - Time on site: {time_on_site/60:.1f} minutes
                    - AI reasoning: {reasoning}
                    - Focus score: {pattern_analysis.get('focus_score', 5)}/10
                    
                    Create a message that:
                    1. Gently acknowledges their current activity
                    2. Suggests the better alternative we're providing
                    3. Motivates them to stay on track
                    
                    Keep it under 25 words and sound encouraging.
                    """
            
            else:
                # Original context for encouragement and warnings
                context = f"""
                Generate a brief, encouraging speech message for a student.
                
                Current situation:
                - Website: {current_url}
                - Time on site: {time_on_site/60:.1f} minutes
                - AI recommendation: {recommendation}
                - Reasoning: {reasoning}
                - Focus score: {pattern_analysis.get('focus_score', 5)}/10
                
                Keep it under 20 words, warm and supportive.
                """
            
            response = self.fast_llm.invoke([HumanMessage(content=context)])
            speech_message = response.content.strip().replace('"', '').replace("'", "")
            
            # Ensure message isn't too long
            max_length = 250 if recommendation == 'intervene' else 150
            if len(speech_message) > max_length:
                speech_message = speech_message[:max_length-3] + "..."
            
            return speech_message
            
        except Exception as e:
            print(f"⚠️ Error generating speech message: {e}")
            # Enhanced fallback messages based on specific issues
            if recommendation == 'intervene':
                if 'tinder' in current_url.lower() or 'dating' in reasoning.lower():
                    return "I see you're on a dating app. During study time, let's focus on your education. I'm taking you to some inspiring educational content instead."
                elif 'inappropriate' in reasoning.lower():
                    return "I noticed inappropriate content. Let me redirect you to educational resources that will help you learn and grow."
                elif 'youtube' in current_url and time_on_site > 300:
                    return f"You've been on YouTube for {time_on_site/60:.0f} minutes. Time for some learning! I'm taking you to educational content."
                elif 'distraction' in reasoning.lower():
                    return "You've been on this distracting site for a while. Let me help you find some engaging educational content instead."
                else:
                    return "Let's redirect to some productive learning activities that will help you reach your goals."
            elif recommendation == 'encourage':
                return "You're doing great! Keep up the excellent work with your studies."
            else:
                return "Remember to stay focused on your learning goals. You've got this!"
    
    async def give_speech_feedback(self, analysis: Dict[str, Any]) -> bool:
        """Give verbal feedback to the student"""
        print("🎤 Checking if speech feedback should be given...")
        
        if not self.should_give_speech_feedback(analysis):
            print("❌ Speech feedback not triggered")
            return False
        
        try:
            print("🎤 Generating speech feedback...")
            
            # Generate contextual message
            speech_text = self.generate_speech_message(analysis)
            print(f"🗣️ Speech message generated: \"{speech_text}\"")
            
            # Store text for fallback use
            self._last_speech_text = speech_text
            
            # Synthesize speech
            print("🎵 Attempting speech synthesis...")
            audio_data = await self.synthesize_speech(speech_text)
            if not audio_data:
                print("⚠️ Speech synthesis failed, trying fallback...")
                # If synthesis fails, try direct 'say' command on macOS
                if platform.system().lower() == "darwin":
                    try:
                        print("🍎 Using macOS 'say' command as fallback...")
                        # Use a male voice for macOS say command
                        subprocess.run(["say", "-v", "Daniel", speech_text], check=True, timeout=10)
                        print("✅ Speech feedback delivered via macOS 'say' command")
                        self.last_speech_time = datetime.now()
                        self.speech_count += 1
                        return True
                    except Exception as e:
                        print(f"⚠️ Fallback 'say' command failed: {e}")
                        # Try without voice specification
                        try:
                            subprocess.run(["say", speech_text], check=True, timeout=10)
                            print("✅ Speech feedback delivered via macOS 'say' command (default voice)")
                            self.last_speech_time = datetime.now()
                            self.speech_count += 1
                            return True
                        except Exception as e2:
                            print(f"⚠️ Default 'say' command also failed: {e2}")
                return False
            
            # Play speech
            print("🔊 Attempting audio playback...")
            success = self.play_speech(audio_data)
            
            if success:
                self.last_speech_time = datetime.now()
                self.speech_count += 1
                print("✅ Speech feedback delivered successfully")
                return True
            else:
                print("❌ Audio playback failed, trying macOS fallback...")
                # Try macOS 'say' as final fallback
                if platform.system().lower() == "darwin":
                    try:
                        subprocess.run(["say", "-v", "Daniel", speech_text], check=True, timeout=10)
                        print("✅ Speech feedback delivered via macOS 'say' fallback")
                        self.last_speech_time = datetime.now()
                        self.speech_count += 1
                        return True
                    except Exception as e:
                        print(f"⚠️ Final fallback failed: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Speech feedback error: {e}")
            return False

    def generate_emotion_based_message(self, emotions: Dict, recommendation: str, context_type: str, recent_activity: List[Dict]) -> str:
        """Generates a dynamic, supportive message based on detected emotions and context."""
        
        primary_emotion = "neutral"
        if emotions:
            active_emotions = {k: v for k, v in emotions.items() if k != 'neutral' and v > 0}
            if active_emotions:
                primary_emotion = max(active_emotions, key=active_emotions.get)

        intent_map = {
            'encourage': f"give positive reinforcement. The student seems happy and is on a '{context_type}' page.",
            'intervene': f"gently redirect the student to a productive task. They seem happy but are on an '{context_type}' page, and we want to channel that energy.",
            'warn': {
                'educational': f"suggest a different educational resource. The student seems to be feeling '{primary_emotion}' with the current one.",
                'entertainment': f"gently suggest taking a break. The student seems to be feeling '{primary_emotion}' while on an '{context_type}' page.",
                'general': f"provide a gentle, encouraging nudge. The student seems to be feeling '{primary_emotion}'."
            }
        }
        
        if recommendation == 'warn':
            intent = intent_map['warn'][context_type]
        else:
            intent = intent_map.get(recommendation, "provide a general notification.")

        current_activity = recent_activity[-1] if recent_activity else {}
        current_url = current_activity.get('url', 'an unknown page')
        current_title = current_activity.get('page_title', 'an unknown page')

        history_summary = "The user has just started their session."
        if len(recent_activity) > 1:
            previous_sites = list(set(urlparse(act['url']).netloc for act in recent_activity[:-1]))
            if previous_sites:
                history_summary = f"They were previously looking at sites like: {', '.join(previous_sites[:2])}."

        prompt = f"""
        You are an AI study assistant. Your goal is to support a student by providing a gentle, positive, and helpful message based on their emotional state and browsing activity.

        CONTEXT:
        - Student's primary emotion: '{primary_emotion}'
        - Current page title: "{current_title}"
        - Current URL: {current_url}
        - Recent history: {history_summary}
        - Your goal is to: {intent}

        INSTRUCTIONS:
        Generate a single, brief, and supportive sentence. The message must clearly and kindly state that you're taking an action *because* of the emotion you've detected, while also referencing their current activity. Do not use quotes in your response.

        Example for 'happy' on an educational page: "It's great to see you're so happy while working on '{current_title}'! Keep up the fantastic work."
        Example for 'angry' on an educational page: "I sense some frustration while you're on '{current_title}'. Because of that, I'm finding a different resource that might explain this in a new way."
        Example for 'sad' on an entertainment page: "You seem a bit down right now. Because of this, I'm suggesting a short break from '{current_title}' to relax for a moment."

        Generate the message now.
        """

        try:
            response = self.text_llm.invoke([HumanMessage(content=prompt)])
            message = response.content.strip().replace('"', '')
            return message
        except Exception as e:
            print(f"Error generating emotion-based message: {e}")
            return "Let's make sure we're staying on track!"


def main():
    parser = argparse.ArgumentParser(description="Smart AI Agent for Student Browser Monitoring")
    parser.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY env var)")
    parser.add_argument("--interval", "-i", type=int, default=10, 
                       help="Analysis interval in seconds (default: 10)")
    parser.add_argument("--test", action="store_true", 
                       help="Run in test mode (analyze recent logs)")
    
    args = parser.parse_args()
    
    try:
        # Initialize agent
        agent = SmartStudentAIAgent(openai_api_key=args.api_key)
        print("🧠 Smart AI Agent initialized successfully!")
        print("🔍 Using computer vision and intelligent analysis")
        print("⚡ Dynamic timeouts and contextual messaging enabled")
        
        if args.test:
            print("\n📊 Running test analysis on recent activity...")
            recent_activity = agent.get_recent_activity(minutes=30)
            
            if recent_activity:
                print(f"Found {len(recent_activity)} recent activities")
                analysis = agent.analyze_student_behavior(recent_activity)
                
                print("\n🎯 AI Analysis Results:")
                print(f"Current URL: {analysis.get('current_url', 'N/A')}")
                print(f"Recommendation: {analysis.get('recommendation', 'N/A')}")
                print(f"Timeout: {analysis.get('timeout', 0)} seconds")
                print(f"Message: {analysis.get('message', 'N/A')}")
                print(f"Reasoning: {analysis.get('reasoning', 'N/A')}")
                print(f"Urgency: {analysis.get('urgency', 'N/A')}")
                print(f"Emotion: {analysis.get('emotion', 'N/A')}")
                
                # Show screenshot analysis if available
                screenshot_analysis = analysis.get('screenshot_analysis', {})
                if screenshot_analysis:
                    print(f"\n📸 Screenshot Analysis:")
                    print(f"Content type: {screenshot_analysis.get('content_type', 'N/A')}")
                    print(f"Educational value: {screenshot_analysis.get('educational_value', 0)}/10")
                    print(f"Distraction level: {screenshot_analysis.get('distraction_level', 0)}/10")
                    print(f"Description: {screenshot_analysis.get('description', 'N/A')}")
                
                # Show pattern analysis
                pattern_analysis = analysis.get('pattern_analysis', {})
                if pattern_analysis:
                    print(f"\n📈 Pattern Analysis:")
                    print(f"Browsing pattern: {pattern_analysis.get('pattern', 'N/A')}")
                    print(f"Focus score: {pattern_analysis.get('focus_score', 0)}/10")
                    print(f"Educational ratio: {pattern_analysis.get('educational_ratio', 0):.2f}")
                
                # Generate progress report
                print(f"\n📋 Progress Report:")
                report = agent.generate_progress_report()
                print(report)
                
                # Save analysis
                agent.save_analysis_log(analysis)
                print(f"\n💾 Analysis saved to ai_analysis.csv")
                
            else:
                print("No recent activity found to analyze")
        else:
            print(f"\n🔄 Starting continuous monitoring (interval: {args.interval}s)")
            print("The AI will analyze screenshots, patterns, and make intelligent decisions")
            print("Press Ctrl+C to stop")
            
            while True:
                try:
                    recent_activity = agent.get_recent_activity()
                    if recent_activity:
                        analysis = agent.analyze_student_behavior(recent_activity)
                        agent.save_analysis_log(analysis)
                        
                        if analysis.get('recommendation') != 'continue_monitoring':
                            print(f"\n🎯 AI Decision: {analysis.get('recommendation').upper()}")
                            print(f"Message: {analysis.get('message', 'N/A')}")
                            print(f"Timeout: {analysis.get('timeout', 0)}s")
                            agent.perform_action(analysis)
                    
                    time.sleep(args.interval)
                    
                except KeyboardInterrupt:
                    print("\n👋 AI Agent stopped by user")
                    break
                except Exception as e:
                    print(f"❌ Error in monitoring loop: {e}")
                    time.sleep(args.interval)
                    
    except Exception as e:
        print(f"❌ Error initializing AI Agent: {e}")
        print("Make sure you have set your OpenAI API key!")


if __name__ == "__main__":
    main() 