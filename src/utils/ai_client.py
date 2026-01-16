import os
import threading
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.model = None
        self.chat_session = None
        self.is_ready = False
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # Use gemini-flash-latest (Aliases to available Flash model, likely 1.5)
                # 2.0-flash had quota issues (limit 0).
                self.model = genai.GenerativeModel("gemini-flash-latest")
                self.chat_session = self.model.start_chat(history=[])
                self.is_ready = True
                logger.info("AIClient initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini AI: {e}")
        else:
            logger.warning("GEMINI_API_KEY not found. AI features disabled.")

    def ask_engineer(self, user_question, context_json, callback):
        """
        Sends a query to the AI in a separate thread.
        callback(response_str) will be called when done.
        """
        if not self.is_ready:
            callback("System: AI is not configured. Please set GEMINI_API_KEY.")
            return

        def run_query():
            try:
                # System prompt injection
                prompt = (
                    f"You are a Race Engineer for an F1 team. "
                    f"Here is the current race status in JSON format: {context_json}\n\n"
                    f"User: {user_question}\n"
                    f"Answer succinctly and like a professional race engineer."
                )
                
                response = self.chat_session.send_message(prompt)
                callback(response.text)
            except Exception as e:
                logger.error(f"AI Query failed: {e}")
                callback(f"System: Error connecting to AI - {str(e)}")

        thread = threading.Thread(target=run_query)
        thread.start()
