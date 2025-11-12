from flask import Flask, request, jsonify
import os
import logging
from quiz_solver import QuizSolver

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
EMAIL = "23f3004253@ds.study.iitm.ac.in"
SECRET = "quiz_secret_2025_tds"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "running",
        "message": "LLM Analysis Quiz Solver API",
        "email": EMAIL
    })

@app.route("/quiz", methods=["POST"])
def handle_quiz():
    try:
        # Parse request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
        
        # Verify secret
        if data.get("secret") != SECRET:
            return jsonify({"error": "Invalid secret"}), 403
        
        # Verify email
        if data.get("email") != EMAIL:
            return jsonify({"error": "Email mismatch"}), 403
        
        # Get quiz URL
        quiz_url = data.get("url")
        if not quiz_url:
            return jsonify({"error": "Missing quiz URL"}), 400
        
        logger.info(f"Received quiz request for URL: {quiz_url}")
        
        # Solve the quiz
        solver = QuizSolver(OPENAI_API_KEY)
        result = solver.solve_quiz(quiz_url, EMAIL, SECRET)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error handling quiz: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
