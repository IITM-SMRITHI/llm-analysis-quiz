import requests
import logging
import time
import json
import re
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuizSolver:
    """Solves quiz tasks using LLM with Selenium support for JS-rendered pages."""
    
    def __init__(self, api_key):
        """Initialize the QuizSolver with OpenAI API key."""
        if not api_key:
            raise ValueError("API key is required to initialize QuizSolver")
        self.client = OpenAI(api_key=api_key)
        self.driver = None
    
    def _init_selenium(self):
        """Initialize Selenium WebDriver for JavaScript rendering."""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            self.driver = webdriver.Chrome(options=options)
            logger.info("Selenium WebDriver initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Selenium: {str(e)}. Falling back to requests.")
            self.driver = None
    
    def fetch_quiz_content(self, url):
        """Fetch quiz content from URL, using Selenium for JS-rendered pages."""
        try:
            logger.info(f"Fetching content from: {url}")
            
            # Try with requests first (faster)
            try:
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                content = response.text
                logger.info(f"Page content fetched via requests ({len(content)} chars)")
                return content
            except requests.RequestException as req_err:
                logger.warning(f"requests failed: {str(req_err)}. Trying Selenium...")
                
                # Fallback to Selenium for JS-rendered content
                if self.driver is None:
                    self._init_selenium()
                
                if self.driver:
                    self.driver.get(url)
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "body"))
                    )
                    content = self.driver.page_source
                    logger.info(f"Page content fetched via Selenium ({len(content)} chars)")
                    return content
                else:
                    raise
        except Exception as e:
            logger.error(f"Error fetching quiz content: {str(e)}")
            raise
    
    def analyze_and_solve_with_llm(self, question_text):
        """Use LLM to analyze and solve the task with robust parsing."""
        try:
            prompt = f"""You are a data analysis expert. Analyze this quiz task and provide the answer.

Task:
{question_text}

IMPORTANT Instructions:
- Read the task carefully and extract what is being asked
- If it asks for a number, respond with just the number (no units)
- If it asks for text, provide just the text
- If it requires calculation, calculate accurately and provide the result
- Be precise and direct
- Extract any URLs, instructions, or data mentioned
- Format your response clearly with labels

Provide your answer in this format:
ANSWER: [your answer here]
SUBMIT_URL: [the URL where to submit the answer, if found]"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            result = response.choices[0].message.content
            logger.info(f"LLM Response length: {len(result)} chars")
            
            # Parse the response with more robust extraction
            answer, submit_url = self._parse_llm_response(result, question_text)
            return answer, submit_url
        except Exception as e:
            logger.error(f"Error with LLM: {str(e)}", exc_info=True)
            return None, None
    
    def _parse_llm_response(self, response, fallback_text):
        """Parse LLM response with improved robustness."""
        try:
            # Split response into sections
            sections = response.split('\n')
            
            answer = None
            submit_url = None
            
            # Look for ANSWER and SUBMIT_URL in response
            for i, line in enumerate(sections):
                if line.strip().startswith("ANSWER:"):
                    answer = line.split("ANSWER:", 1)[1].strip()
                elif line.strip().startswith("SUBMIT_URL:"):
                    url_candidate = line.split("SUBMIT_URL:", 1)[1].strip()
                    if url_candidate.startswith("http"):
                        submit_url = url_candidate
            
            # If no ANSWER found, use last meaningful line
            if not answer and sections:
                for line in reversed(sections):
                    if line.strip() and not line.startswith("SUBMIT_URL"):
                        answer = line.strip()
                        break
            
            # If no URL found in response, try to extract from fallback text
            if not submit_url:
                submit_url = self.extract_submit_info(fallback_text)
            
            logger.info(f"Parsed answer: {answer[:50] if answer else 'None'}...")
            logger.info(f"Parsed URL: {submit_url}")
            
            return answer, submit_url
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return None, None
    
    def extract_submit_info(self, text):
        """Extract submission URL from text with multiple patterns."""
        try:
            # Pattern for submit URLs
            url_patterns = [
                r'https?://[^\s<>"]+/submit[^\s<>"]*',
                r'https?://[^\s<>"]+/api/submit[^\s<>"]*',
                r'(https?://[^\s<>"]+)',  # Fallback to any URL
            ]
            
            for pattern in url_patterns:
                urls = re.findall(pattern, text)
                if urls:
                    logger.info(f"Found submit URL: {urls[0]}")
                    return urls[0]
            
            logger.warning("No submit URL found in text")
            return None
        except Exception as e:
            logger.error(f"Error extracting submit info: {str(e)}")
            return None
    
    def submit_answer(self, submit_url, email, secret, quiz_url, answer):
        """Submit answer to the endpoint with type conversion."""
        try:
            # Try to parse answer as number if possible
            parsed_answer = answer
            if answer and isinstance(answer, str):
                try:
                    if '.' in answer:
                        parsed_answer = float(answer)
                    elif answer.lstrip('-').isdigit():
                        parsed_answer = int(answer)
                except (ValueError, AttributeError):
                    pass  # Keep as string if conversion fails
            
            payload = {
                "email": email,
                "secret": secret,
                "url": quiz_url,
                "answer": parsed_answer
            }
            
            logger.info(f"Submitting to {submit_url}")
            logger.debug(f"Payload: {json.dumps(payload, default=str)}")
            
            response = requests.post(submit_url, json=payload, timeout=15)
            
            if response.status_code != 200:
                logger.warning(f"Submit returned status {response.status_code}")
            
            result = response.json()
            logger.info(f"Submit response: correct={result.get('correct')}, has_url={bool(result.get('url'))}")
            
            return result
        except requests.Timeout:
            logger.error(f"Timeout submitting answer to {submit_url}")
            raise
        except requests.RequestException as e:
            logger.error(f"Request error submitting answer: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in submit response: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error submitting answer: {str(e)}", exc_info=True)
            raise
    
    def solve_quiz(self, quiz_url, email, secret, max_retries=3):
        """Main method to solve quiz with improved multi-step handling."""
        try:
            start_time = time.time()
            attempt = 0
            current_url = quiz_url
            
            while attempt < max_retries and (time.time() - start_time) < 170:
                attempt += 1
                logger.info(f"Attempt {attempt}/{max_retries} for {current_url}")
                
                try:
                    # Fetch quiz content
                    question_text = self.fetch_quiz_content(current_url)
                    
                    # Analyze and solve with LLM
                    answer, llm_submit_url = self.analyze_and_solve_with_llm(question_text)
                    
                    # Extract submission URL
                    submit_url = llm_submit_url or self.extract_submit_info(question_text)
                    
                    if not submit_url:
                        logger.error("Could not find submit URL")
                        return {"error": "No submit URL found"}
                    
                    if not answer:
                        logger.error("Could not determine answer")
                        return {"error": "Could not determine answer"}
                    
                    # Submit answer
                    result = self.submit_answer(submit_url, email, secret, current_url, answer)
                    
                    # Check if we got a new quiz URL (regardless of correctness)
                    if result.get("url"):
                        current_url = result["url"]
                        logger.info(f"Got new quiz URL: {current_url}")
                        if result.get("correct"):
                            logger.info("Answer was correct. Proceeding to next quiz.")
                        else:
                            logger.info("Answer was incorrect. Retrying with new URL.")
                        continue
                    
                    # No new URL, return final result
                    logger.info(f"Quiz complete. Correct: {result.get('correct')}")
                    return result
                
                except (requests.Timeout, requests.RequestException) as req_err:
                    logger.warning(f"Network error on attempt {attempt}: {str(req_err)}")
                    if attempt < max_retries:
                        logger.info(f"Retrying... ({attempt}/{max_retries})")
                        time.sleep(2 ** attempt)
                        continue
                    return {"error": f"Network error: {str(req_err)}"}
                
                except Exception as task_err:
                    logger.error(f"Error on attempt {attempt}: {str(task_err)}", exc_info=True)
                    if attempt >= max_retries:
                        return {"error": str(task_err)}
                    continue
            
            logger.error("Max retries exceeded or timeout")
            return {"error": "Max retries exceeded or timeout"}
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("Selenium driver closed")
                except Exception as e:
                    logger.warning(f"Error closing Selenium driver: {str(e)}")
