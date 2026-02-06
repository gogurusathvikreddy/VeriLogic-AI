import os
import google.generativeai as genai
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# --- CONFIGURATION ---
# We load these from Render Environment Variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")

# --- GEMINI SETUP ---
genai.configure(api_key=GEMINI_API_KEY)

# FIX: This is the correct modern tool configuration for Google Search
tools_config = [
    {"google_search": {}}
]

# NOTE: There is no "Gemini 2.5" yet. The latest fast model is "gemini-1.5-flash" 
# or "gemini-2.0-flash-exp". We will use 1.5-flash as it is the most stable.
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash', 
    tools=tools_config
)

def fact_check(text):
    """Uses Gemini + Google Search to verify the claim"""
    try:
        prompt = (
            f"Fact check this WhatsApp rumor: '{text}'. "
            "Search Google. Reply with one emoji: ✅ (True), ❌ (False), or ⚠️ (Unverified). "
            "Then give a 2-sentence explanation with a source link."
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "⚠️ I couldn't verify this right now. Please try again later."

@app.route("/", methods=["GET"])
def home():
    return "Factify Bot is Alive!", 200

@app.route("/webhook", methods=["POST"])
def whatsapp_reply():
    """Receives message from Twilio, checks facts, and replies"""
    
    # 1. Get the message text from the user
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')
    
    print(f"Message from {sender}: {incoming_msg}")

    # 2. Fact Check
    if incoming_msg:
        fact_check_result = fact_check(incoming_msg)
    else:
        fact_check_result = "Please send a text to fact-check."

    # 3. Create the Twilio response
    resp = MessagingResponse()
    msg = resp.message()
    msg.body(fact_check_result)

    return str(resp)

if __name__ == "__main__":
    app.run(port=5000)
