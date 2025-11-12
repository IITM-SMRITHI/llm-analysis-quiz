import requests
import logging
import time
import json
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openai import OpenAI
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuizSolver:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        self.browser = None
    
    def setup_browser(self):
        """Setup headless Chrome browser"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.browser = webdriver.Chrome(options=chrome_options)
    
    def close_browser(self):
        """Close browser"""
        if self.browser:
            self.browser.quit()
    
    def fetch_quiz_content(self, url):
        """Fetch quiz content from URL with JavaScript execution"""
        try:
            if not self.browser:
                self.setup_browser()
            
            logger.info(f"Fetching content from: {url}")
            self.browser.get(url)
            time.sleep(3)  # Wait for JavaScript to execute
            
            # Get page content
            page_text = self.browser.find_element(By.TAG_NAME, "body").text
            logger.info(f"Page content: {page_text[:500]}...")
            
            return page_text
        except Exception as e:
            logger.error(f"Error fetching quiz content: {str(e)}")
            raise
    
    def analyze_question_with_llm(self, question_text):
        """Use LLM to analyze question and generate solution strategy"""
        try:
            prompt = f"""You are a data analysis expert. Analyze this quiz question and provide:
1. What type of task is this (data sourcing, analysis, visualization, etc.)?
2. What steps are needed to solve it?
3. What tools/methods should be used?
4. What is the expected format of the answer?

Question:
{question_text}

Provide a structured analysis."""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            analysis = response.choices[0].message.content
            logger.info(f"LLM Analysis: {analysis}")
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing with LLM: {str(e)}")
            return None
    
    def solve_task_with_llm(self, question_text):
        """Use LLM to solve the task and generate answer"""
        try:
            prompt = f"""You are a data analysis expert solving quiz tasks. 
Analyze this question and provide the direct answer.

Question:
{question_text}

IMPORTANT: 
- If the question asks for a number, respond with just the number
- If it asks for text, provide just the text
- If it asks for a calculation, calculate and provide the result
- Be precise and direct

Answer:"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            answer = response.choices[0].message.content.strip()
            logger.info(f"LLM Answer: {answer}")
            return answer
        except Exception as e:
            logger.error(f"Error solving with LLM: {str(e)}")
            return None
    
    def extract_submit_info(self, question_text):
        """Extract submission URL and answer format from question"""
        # Look for submit URL
        url_pattern = r'https?://[^\s]+/submit'
        urls = re.findall(url_pattern, question_text)
        submit_url = urls[0] if urls else None
        
        # Look for JSON payload example
        json_pattern = r'\{[^}]+"answer"[^}]+\}'
        jsons = re.findall(json_pattern, question_text, re.DOTALL)
        
        return submit_url, jsons
    
    def submit_answer(self, submit_url, email, secret, quiz_url, answer):
        """Submit answer to the endpoint"""
        try:
            payload = {
                "email": email,
                "secret": secret,
                "url": quiz_url,
                "answer": answer
            }
            
            logger.info(f"Submitting to {submit_url}: {payload}")
            response = requests.post(submit_url, json=payload, timeout=30)
            result = response.json()
            logger.info(f"Submit response: {result}")
            
            return result
        except Exception as e:
            logger.error(f"Error submitting answer: {str(e)}")
            raise
    
    def solve_quiz(self, quiz_url, email, secret, max_attempts=3):
        """Main method to solve quiz"""
        try:
            start_time = time.time()
            
            # Fetch quiz content
            question_text = self.fetch_quiz_content(quiz_url)
            
            # Analyze with LLM
            analysis = self.analyze_question_with_llm(question_text)
            
            # Extract submission info
            submit_url, _ = self.extract_submit_info(question_text)
            
            if not submit_url:
                logger.error("Could not find submit URL in question")
                return {"error": "No submit URL found"}
            
            # Solve task
            answer = self.solve_task_with_llm(question_text)
            
            # Try to parse answer as number if it looks like one
            try:
                if answer and answer.replace(".", "").replace("-", "").isdigit():
                    answer = float(answer) if "." in answer else int(answer)
            except:
                pass
            
            # Submit answer
            result = self.submit_answer(submit_url, email, secret, quiz_url, answer)
            
            # Handle chained quizzes
            if result.get("url") and not result.get("correct"):
                logger.info("Moving to next quiz...")
                # Check if we have time
                if time.time() - start_time < 170:  # Leave 10s buffer
                    return self.solve_quiz(result["url"], email, secret)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in solve_quiz: {str(e)}")
            raise
        finally:
            self.close_browser()
