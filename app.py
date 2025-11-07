import os
import re
import traceback
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import google.generativeai as genai

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ GEMINI_API_KEY not found in .env file.") 
else:
    print("✅ API key loaded successfully.")

# --- CONFIGURE GEMINI ---
if api_key:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"❌ Error configuring Gemini client: {e}")

# --- INITIALIZE FLASK APP ---
app = Flask(__name__, template_folder="templates")

# --- HELPER FUNCTION: SMALL TALK AND META QUESTIONS ---
def get_small_talk_response(message):
    """
    Handles simple greetings, thank yous, and core meta-questions 
    using precise checks to avoid confusion with math queries.
    """
    message = message.lower().strip()
    
    
    greetings = ["hi", "hello", "hey", "hola", "sup", "good day"]
    if message in greetings or message.rstrip('!') in greetings or message.rstrip('.') in greetings or message.rstrip('?') in greetings:
        return "Hello! I'm DiscBot, your discrete math tutor. How can I help you with sets, logic, or graphs today?"
    
    
    if "what is discrete math" in message or "define discrete math" in message or "explain discrete math" in message:
        return "That's my favorite subject! **Discrete mathematics** is the study of mathematical structures that are fundamentally **separate** or distinct, rather than continuous. It includes topics like **logic**, **sets**, **combinatorics**, and **graph theory**. What specific area interests you?"
        
    if "what is math" in message or "what is mathematics" in message:
        return "Mathematics is the language of science! It's the study of quantity, structure, space, and change. I focus on the **discrete** parts of math, like proofs and algorithms. Got any questions on those?"

    
    if "thank you" in message or "thanks" in message:
        return "You're very welcome! Feel free to ask any more discrete math questions."
        
    
    if message == "how are you" or message == "how are you?":
        return "I'm a bot, but I'm ready to compute! What discrete math topic is on your mind?"

    return None 


def get_system_instruction():
    """Defines the specialized, friendly persona and strict formatting rules for the model."""
    return (
        "You are DiscBot —a friendly, enthusiastic, and highly knowledgeable tutor specializing exclusively in Discrete Mathematics. "
        "Your answers must be clear, well-structured, and follow these rules:"
        "1. Tone: Maintain a warm, encouraging, and human-like tone, using short contractions (like 'I\'m', 'it\'s'). "
        "2. Formatting: For complex or multi-step questions (like proofs, graph drawing descriptions, or logic evaluations), always use **numbered lists** or **bullet points** and double newlines for clear paragraph breaks. "
        "3. Keywords & Concepts:** Use **bolding** (double asterisks) for keywords and concepts."
        "4. Visualization:When a question requires a drawing or visualization (like a graph or truth table), **describe the result clearly in a detailed step-by-step manner** since you cannot draw directly. Use list formatting to describe vertices and edges."
        "5. Math Notation:Use standard LaTeX formatting within dollar signs ($...$) for all mathematical symbols (e.g., $p \land q$ or $G=(V, E)$). "
        "6. Redirection:If a question is clearly outside the scope of discrete mathematics, gently redirect the user back to your specialization."
    )

# --- ROUTES ---
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    user_input = (data.get("message") or "").strip()

    if not user_input:
        return jsonify({"reply": "Please type a question!"})

    # 1. Small Talk Check: Handle greetings/meta-questions first
    small_talk_reply = get_small_talk_response(user_input)
    if small_talk_reply:
        return jsonify({"reply": small_talk_reply})

    # 2. API Call: Send all other requests directly to the model.
    try:
        if not api_key:
             return jsonify({"reply": "API Key is missing or failed to load. Please check your .env file."})

        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=get_system_instruction()
        )
        
        response = model.generate_content(f"User Question: {user_input}")
        
        reply = response.text.strip()
        return jsonify({"reply": reply})
        
    except Exception as e:
        print("❌ Error generating response:", e)
        traceback.print_exc()
        
        # Friendly, human-like error message
        return jsonify({
            "reply": (
                "Oops! I hit a snag while trying to compute that. "
                "The server might be busy or your API quota may be exceeded. "
                "Could you please try rephrasing your discrete math question?"
            )
        })

# --- RUN SERVER ---
if __name__ == "__main__":
    app.run(debug=True)