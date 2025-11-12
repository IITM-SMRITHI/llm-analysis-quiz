# LLM Analysis Quiz Solver

Automated quiz solver using Large Language Models for data sourcing, analysis, and visualization tasks.

## Description

This project implements an automated system that can solve complex quiz tasks involving:
- Data sourcing from web pages and APIs
- Data preparation and cleansing
- Statistical and analytical processing
- Data visualization
- Multi-step problem solving with LLMs

## Features

- 🤖 **LLM-Powered Analysis**: Uses OpenAI GPT models to understand and solve quiz questions
- 🌐 **Web Scraping**: Supports JavaScript-rendered pages with Selenium
- 📊 **Data Processing**: Handles various data formats (PDF, Excel, CSV, JSON)
- 🔄 **Chained Quiz Support**: Automatically solves sequential quiz questions
- ⚡ **Fast Response**: Optimized to complete within 3-minute time limit
- 🔒 **Secure**: Secret-based authentication for API endpoints

## Project Structure

```
llm-analysis-quiz/
├── app.py              # Flask API endpoint
├── quiz_solver.py      # Core quiz solving logic
├── requirements.txt    # Python dependencies
├── Procfile           # Deployment configuration
├── .env.example       # Environment variables template
├── .gitignore         # Git ignore rules
├── LICENSE            # MIT License
└── README.md          # This file
```

## Setup

### Prerequisites

- Python 3.9+
- OpenAI API Key
- Chrome/Chromium (for Selenium)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/IITM-SMRITHI/llm-analysis-quiz.git
cd llm-analysis-quiz
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
cp .env.example .env
```

4. Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=your_actual_api_key_here
PORT=5000
```

### Running Locally

```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### GET `/`
Health check endpoint

**Response:**
```json
{
  "status": "running",
  "message": "LLM Analysis Quiz Solver API",
  "email": "23f3004253@ds.study.iitm.ac.in"
}
```

### POST `/quiz`
Solve a quiz task

**Request Body:**
```json
{
  "email": "23f3004253@ds.study.iitm.ac.in",
  "secret": "quiz_secret_2025_tds",
  "url": "https://example.com/quiz-123"
}
```

**Response:**
```json
{
  "correct": true,
  "url": "https://example.com/quiz-456"
}
```

## Deployment

### Deploy to Render

1. Fork this repository
2. Go to [Render](https://render.com)
3. Create a new Web Service
4. Connect your GitHub repository
5. Set environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
6. Deploy!

### Deploy to Railway

1. Fork this repository
2. Go to [Railway](https://railway.app)
3. Create new project from GitHub
4. Add environment variables
5. Deploy!

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `PORT`: Port number (default: 5000)

### Email and Secret

Update these in `app.py`:
```python
EMAIL = "23f3004253@ds.study.iitm.ac.in"
SECRET = "quiz_secret_2025_tds"
```

## Project Requirements (TDS Course)

### Google Form Submission

Submit the following to the [Google Form](https://forms.gle/V3vW2QeHGPF9BTrB7):

1. ✅ Email: 23f3004253@ds.study.iitm.ac.in
2. ✅ Secret: quiz_secret_2025_tds
3. ⚠️ System prompt (defensive): *To be added*
4. ⚠️ User prompt (offensive): *To be added*
5. ⚠️ API Endpoint URL: *Your deployed URL*
6. ✅ GitHub Repo: https://github.com/IITM-SMRITHI/llm-analysis-quiz

### Evaluation Timeline

- **Prompt Testing**: Throughout the course
- **Quiz Evaluation**: Saturday, 29 Nov 2025, 3:00-4:00 PM IST
- **Viva**: To be announced

## Tech Stack

- **Backend**: Flask
- **LLM**: OpenAI GPT-4o-mini
- **Web Automation**: Selenium WebDriver
- **Data Processing**: Pandas, NumPy
- **Deployment**: Render/Railway/Heroku

## License

MIT License - see [LICENSE](LICENSE) file for details

## Author

**IITM Student**
- Email: 23f3004253@ds.study.iitm.ac.in
- GitHub: [@IITM-SMRITHI](https://github.com/IITM-SMRITHI)

## Acknowledgments

- Course: Tools in Data Science (TDS)
- Institution: IIT Madras
- Instructor: S Anand
