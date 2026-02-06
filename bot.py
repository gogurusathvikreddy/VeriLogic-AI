import os
import google.generativeai as genai
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# --- CONFIGURATION ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- GEMINI 2.5 SETUP ---
genai.configure(api_key=GEMINI_API_KEY)

# FIX 1: The correct tool config for Gemini 2.5 is a LIST with a DICTIONARY.
# Do not use the string 'google_search_retrieval' (that was for old models).
tools_config = [
    {"google_search": {}}
]

# FIX 2: Use the specific "gemini-2.5-flash" model name.
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash', 
    tools=tools_config
)

def fact_check(text):
    """Uses Gemini 2.5 + Google Search to verify the claim"""
    try:
        prompt = (
            f"Fact check this WhatsApp rumor: '{text}'. "
            "Search Google. Reply with one emoji: ✅ (True), ❌ (False), or ⚠️ (Unverified). "
            "Then give a 2-sentence explanation with a source link."
        )
        # The tool is automatically applied here
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "⚠️ I couldn't verify this. Please try again later."

@app.route("/", methods=["GET"])
def home():
    return "Factify Bot (Gemini 2.5) is Alive!", 200

@app.route("/webhook", methods=["POST"])
def whatsapp_reply():
    """Receives message from Twilio, checks facts, and replies"""
    # 1. Get the message
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')
    
    print(f"Message from {sender}: {incoming_msg}")

    # 2. Fact Check
    if incoming_msg:
        fact_check_result = fact_check(incoming_msg)
    else:
        fact_check_result = "Please send a text message to verify."

    # 3. Reply
    resp = MessagingResponse()
    msg = resp.message()
    msg.body(fact_check_result)

    return str(resp)

if __name__ == "__main__":
    app.run(port=5000)
