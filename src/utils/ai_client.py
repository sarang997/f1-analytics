import os
import threading
import google.generativeai as genai
import logging
import json
from typing import List, Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.model = None
        self.chat_session = None
        self.is_ready = False
        
        # Conversation Memory
        self.conversation_history: List[Tuple[str, str, float, int]] = []  # (user_msg, ai_response, timestamp, lap)
        self.session_insights: List[str] = []  # Key facts AI should remember
        self.max_history = 10  # Keep last 10 exchanges
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # Use gemini-flash-latest (Aliases to available Flash model, likely 1.5)
                # 2.0-flash had quota issues (limit 0).
                self.model = genai.GenerativeModel("gemini-flash-latest")
                # Don't use chat history - we'll manage it ourselves for more control
                self.chat_session = self.model.start_chat(history=[])
                self.is_ready = True
                logger.info("AIClient initialized successfully with conversation memory.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini AI: {e}")
        else:
            logger.warning("GEMINI_API_KEY not found. AI features disabled.")

    def ask_engineer(self, user_question, context_json, callback, selected_driver=None):
        """
        Sends a query to the AI in a separate thread.
        callback(response_str) will be called when done.
        """
        if not self.is_ready:
            callback("System: AI is not configured. Please set GEMINI_API_KEY.")
            return

        def run_query():
            try:
                # Parse context to get current lap
                try:
                    context = json.loads(context_json)
                    current_lap = context.get("current_state", {}).get("lap", 0)
                    driver_name = selected_driver or context.get("current_state", {}).get("selected_driver", "the driver")
                except:
                    current_lap = 0
                    driver_name = "the driver"
                
                # Build enhanced prompt with memory
                prompt = self._build_engineer_prompt(user_question, context_json, driver_name)
                
                response = self.chat_session.send_message(prompt)
                response_text = response.text
                
                # Store in conversation history
                self._add_to_history(user_question, response_text, current_lap)
                
                callback(response_text)
            except Exception as e:
                logger.error(f"AI Query failed: {e}")
                callback(f"System: Error connecting to AI - {str(e)}")

        thread = threading.Thread(target=run_query)
        thread.start()
    
    def _build_engineer_prompt(self, user_question: str, context_json: str, driver_name: str) -> str:
        """Build comprehensive prompt with role-playing and memory"""
        
        # System instructions
        system_prompt = f"""You are the RACE ENGINEER for {driver_name} in an F1 race.

ROLE:
- You are a world-class strategist with 20 years of F1 experience
- You have access to live telemetry, historical data, and race analytics
- Your PRIMARY job is to help {driver_name} WIN the race
- Be concise (radio brevity), urgent when needed, calm under pressure
- Use F1 terminology naturally (box, deg, delta, undercut, etc.)

RESPONSE RULES:
- Keep messages under 100 words unless detailed analysis is requested
- Start urgent messages with "⚠️" or "URGENT:"
- Use bullet points (•) for multi-part answers
- Always provide ACTIONABLE advice, not just facts
- If you don't have enough data, say "Insufficient data" - never guess
- Format numbers clearly: gaps in seconds (4.2s), speeds in km/h (287), percentages for throttle/brake (100%, 0%)

PERSONALITY:
- Professional but supportive (like a real engineer)
- Celebrate good performance ("Great lap!")
- Warn about risks calmly but firmly
- Make strategic recommendations confidently"""

        # Conversation history summary
        history_text = ""
        if self.conversation_history:
            recent = self.conversation_history[-3:]  # Last 3 exchanges
            history_text = "\n\nRECENT RADIO CONVERSATION:\n"
            for user_msg, ai_resp, _, lap in recent:
                history_text += f"[Lap {lap}] Driver: {user_msg}\n"
                history_text += f"[Lap {lap}] You: {ai_resp[:80]}...\n"
        
        # Session insights
        insights_text = ""
        if self.session_insights:
            insights_text = "\n\nKEY SESSION FACTS (remember these):\n"
            insights_text += "\n".join(f"• {insight}" for insight in self.session_insights[-5:])
        
        # Full prompt
        full_prompt = f"""{system_prompt}

CURRENT RACE DATA:
{context_json}
{history_text}
{insights_text}

DRIVER QUESTION: {user_question}

YOUR RESPONSE (as race engineer):"""
        
        return full_prompt
    
    def _add_to_history(self, user_msg: str, ai_response: str, lap: int):
        """Add Q&A to conversation history"""
        timestamp = datetime.now().timestamp()
        self.conversation_history.append((user_msg, ai_response, timestamp, lap))
        
        # Trim to max size
        if len(self.conversation_history) > self.max_history:
            self.conversation_history.pop(0)
    
    def add_insight(self, insight: str):
        """Store a key fact for the AI to remember (e.g., 'Strategy is 2-stop Medium-Hard')"""
        if insight not in self.session_insights:
            self.session_insights.append(insight)
            logger.info(f"AI insight added: {insight}")
    
    def clear_session(self):
        """Clear conversation memory (e.g., when starting new race)"""
        self.conversation_history.clear()
        self.session_insights.clear()
        logger.info("AI conversation memory cleared.")
