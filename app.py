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

# Validate API key at startup
if not OPENAI_API_KEY:
    raise ValueError(
        "FATAL ERROR: OPENAI_API_KEY environment variable is not set. "
        "Please set it before running the application."
    )

logger.info("OPENAI_API_KEY successfully validated")


@app.route("/", methods=["GET"])
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "message": "LLM Analysis Quiz Solver API",
        "email": EMAIL
    })


@app.route("/quiz", methods=["POST"])
def handle_quiz():
    """Handle quiz requests and solve them using LLM"""
    try:
        # Parse request
        data = request.get_json()
        
        if not data:
            logger.error("Invalid JSON received")
            return jsonify({"error": "Invalid JSON"}), 400
        
        # Verify secret
        if data.get("secret") != SECRET:
            logger.warning(f"Invalid secret attempt from {data.get('email')}")
            return jsonify({"error": "Invalid secret"}), 403
        
        # Verify email
        if data.get("email") != EMAIL:
            logger.warning(f"Email mismatch: got {data.get('email')}, expected {EMAIL}")
            return jsonify({"error": "Email mismatch"}), 403
        
        # Get quiz URL
        quiz_url = data.get("url")
        if not quiz_url:
            logger.error("Missing quiz URL in request")
            return jsonify({"error": "Missing quiz URL"}), 400
        
        logger.info(f"Received quiz request for URL: {quiz_url}")
        
        # Solve the quiz
        try:
            solver = QuizSolver(OPENAI_API_KEY)
            result = solver.solve_quiz(quiz_url, EMAIL, SECRET)
            return jsonify(result), 200
        except Exception as e:
            logger.error(f"Error solving quiz: {str(e)}", exc_info=True)
            return jsonify({"error": f"Failed to solve quiz: {str(e)}"}), 500
        
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error(f"Unexpected error handling quiz: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    # Use debug=False for production
    app.run(host="0.0.0.0", port=port, debug=False)
