import requests
import logging
import time
import json
import re
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuizSolver:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
    
    def fetch_quiz_content(self, url):
        """Fetch quiz content from URL using requests"""
        try:
            logger.info(f"Fetching content from: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text
            logger.info(f"Page content length: {len(content)}")
            return content
        except Exception as e:
            logger.error(f"Error fetching quiz content: {str(e)}")
            raise
    
    def analyze_and_solve_with_llm(self, question_text):
        """Use LLM to analyze and solve the task"""
        try:
            prompt = f"""You are a data analysis expert. Analyze this quiz task and provide the answer.

Task:
{question_text}

IMPORTANT Instructions:
- Read the task carefully
- If it asks for a number, respond with just the number
- If it asks for text, provide just the text
- If it requires calculation, calculate and provide the result
- Be precise and direct
- Extract any URLs, instructions, or data mentioned

Provide your answer in this format:
ANSWER: <your_answer>
SUBMIT_URL: <submission_url_if_mentioned>"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            logger.info(f"LLM Response: {result}")
            
            # Parse the response
            answer_match = re.search(r'ANSWER:\s*(.+?)(?=\nSUBMIT_URL:|$)', result, re.DOTALL)
            url_match = re.search(r'SUBMIT_URL:\s*(.+?)(?=\n|$)', result)
            
            answer = answer_match.group(1).strip() if answer_match else None
            submit_url = url_match.group(1).strip() if url_match else None
            
            return answer, submit_url
        except Exception as e:
            logger.error(f"Error with LLM: {str(e)}")
            return None, None
    
    def extract_submit_info(self, text):
        """Extract submission URL from text"""
        url_pattern = r'https?://[^\s<>"]+/submit[^\s<>"]*'
        urls = re.findall(url_pattern, text)
        return urls[0] if urls else None
    
    def submit_answer(self, submit_url, email, secret, quiz_url, answer):
        """Submit answer to the endpoint"""
        try:
            # Try to parse answer as number if possible
            try:
                if answer and isinstance(answer, str):
                    if '.' in answer:
                        answer = float(answer)
                    elif answer.isdigit() or (answer.startswith('-') and answer[1:].isdigit()):
                        answer = int(answer)
            except:
                pass
            
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
    
    def solve_quiz(self, quiz_url, email, secret, max_retries=3):
        """Main method to solve quiz"""
        try:
            start_time = time.time()
            attempt = 0
            
            while attempt < max_retries and (time.time() - start_time) < 170:
                attempt += 1
                logger.info(f"Attempt {attempt} for {quiz_url}")
                
                # Fetch quiz content
                question_text = self.fetch_quiz_content(quiz_url)
                
                # Analyze and solve with LLM
                answer, llm_submit_url = self.analyze_and_solve_with_llm(question_text)
                
                # Extract submission URL from page if not found by LLM
                submit_url = llm_submit_url or self.extract_submit_info(question_text)
                
                if not submit_url:
                    logger.error("Could not find submit URL")
                    return {"error": "No submit URL found"}
                
                if not answer:
                    logger.error("Could not determine answer")
                    return {"error": "Could not determine answer"}
                
                # Submit answer
                result = self.submit_answer(submit_url, email, secret, quiz_url, answer)
                
                # Check if we got a new quiz URL
                if result.get("url") and not result.get("correct"):
                    logger.info(f"Got new quiz URL: {result['url']}")
                    quiz_url = result["url"]
                    continue
                
                return result
            
            return {"error": "Max retries exceeded or timeout"}
            
        except Exception as e:
            logger.error(f"Error in solve_quiz: {str(e)}")
            raise
