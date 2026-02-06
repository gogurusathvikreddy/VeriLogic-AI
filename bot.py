import os
import google.generativeai as genai
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from serpapi import GoogleSearch

app = Flask(__name__)

# --- CONFIGURATION ---
# We load ALL keys from Render Environment Variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")

# --- GEMINI SETUP ---
genai.configure(api_key=GEMINI_API_KEY)

# Use Gemini 2.0 Flash (Fast & Reliable)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_google_search_results(query):
    """Searches Google via SerpApi and returns a summary text"""
    try:
        params = {
            "engine": "google",
            "q": query,
            "api_key": SERPAPI_API_KEY,
            "num": 3  # Get top 3 results
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Extract snippets from the results
        snippets = []
        if "organic_results" in results:
            for result in results["organic_results"]:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                link = result.get("link", "")
                snippets.append(f"- {title}: {snippet} ({link})")
        
        return "\n".join(snippets)
    except Exception as e:
        print(f"SerpApi Error: {e}")
        return None

def fact_check(user_claim):
    """1. Search Google. 2. Ask Gemini to analyze results."""
    
    # Step 1: Search
    search_data = get_google_search_results(user_claim)
    
    if not search_data:
        return "⚠️ Error: I couldn't search the web right now. Please check your SerpApi key."

    # Step 2: Ask Gemini
    try:
        prompt = (
            f"Analyze this claim based on the search results below.\n\n"
            f"CLAIM: {user_claim}\n\n"
            f"SEARCH RESULTS:\n{search_data}\n\n"
            "INSTRUCTIONS:\n"
            "1. Start with one emoji: ✅ (True), ❌ (False), or ⚠️ (Unverified/Debated).\n"
            "2. Write a 2-sentence explanation based ONLY on the search results.\n"
            "3. Cite the best source link from the results."
        )
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "⚠️ Error: I couldn't analyze the data."

@app.route("/", methods=["GET"])
def home():
    return "Factify Bot (SerpApi Version) is Alive!", 200

@app.route("/webhook", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')
    
    print(f"Message from {sender}: {incoming_msg}")
    
    if incoming_msg:
        reply = fact_check(incoming_msg)
    else:
        reply = "Please send a text to fact-check."

    resp = MessagingResponse()
    resp.message(reply)
    return str(resp)

if __name__ == "__main__":
    app.run(port=5000)
