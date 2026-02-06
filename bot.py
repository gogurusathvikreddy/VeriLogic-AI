import os
import google.generativeai as genai
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client

app = Flask(__name__)

# --- CONFIGURATION ---
# Load keys from environment variables (set these in Render later)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")

# --- GEMINI SETUP ---
genai.configure(api_key=GEMINI_API_KEY)
tools_config = [{"google_search": {}}]
model = genai.GenerativeModel(model_name='gemini-1.5-flash', tools=tools_config)

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
    return "Factify Bot (Twilio Version) is Alive!", 200

@app.route("/webhook", methods=["POST"])
def whatsapp_reply():
    """Receives message from Twilio, checks facts, and replies"""
    
    # 1. Get the message text from the user
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')
    
    print(f"Message from {sender}: {incoming_msg}")

    # 2. Get the fact-check result
    fact_check_result = fact_check(incoming_msg)

    # 3. Create the Twilio response
    resp = MessagingResponse()
    msg = resp.message()
    msg.body(fact_check_result)

    return str(resp)

if __name__ == "__main__":

    app.run(port=5000)
