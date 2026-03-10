import os
import time
import re
import pandas as pd
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ---------------- CONFIGURATION ---------------- #
GEMINI_API_KEY = "YOUR-NEW-API-KEY-HERE"
RESUME_PATH = r"C:\Users\angel\Downloads\Ajmal_Johnson.pdf"
PROMPT_FILE = "prompt.md"
JOBS_EXCEL_FILE = "naukri_jobs.xlsx"
SKIP_EXCEL_FILE = "skip.xlsx"
BASE_SEARCH_URL = "https://www.naukri.com/data-engineer-kafka-big-data-engineer-machine-learning-engineer-ai-product-engineer-analytics-engineer-platform-engineer-data-python-iiot-opc-ua-industry-consultant-data-analyst-business-analytics-predictive-modeling-statistical-modeling-jobs-{}?k=data+engineer+%28kafka%29+big+data+engineer+machine+learning+engineer+ai+product+engineer+analytics+engineer+platform+engineer+%E2%80%93+data%2C+python%2C+iiot%2C+opc+ua%2C+industry+consultant%2C+data+analyst%2C+business+analytics%2C+predictive+modeling%2C+statistical+modeling&experience=3&cityTypeGid=97&cityTypeGid=110&ctcFilter=10to15&ctcFilter=15to25&ctcFilter=25to50&ctcFilter=50to75&ctcFilter=75to100&ctcFilter=100to500&jobAge=3"
MIN_MATCH_SCORE = 70
PAGES_TO_SEARCH = 30
# ----------------------------------------------- #

# Configure Gemini model with API key
genai.configure(api_key=GEMINI_API_KEY)
# Initialize the model as used in openapi_jobprofile_match.py
model = genai.GenerativeModel('models/gemma-3-27b-it')

def get_match_score(job_description, prompt_template):
    """
    Combines the job description with the prompt template and calls Gemini
    to get the percentage match score.
    """
    # Replace the placeholder with the actual job description
    prompt = prompt_template.replace("<< Paste Job Description Here >>", str(job_description))
    
    # Prepend the system instruction to the prompt context
    full_prompt = "You are an expert HR assistant evaluating job fit.\n\n" + prompt
    
    try:
        # Generate the content with a low temperature for more deterministic output
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.0)
        )
        
        result_text = response.text.strip()
        print(f"        Raw API Response: {result_text}")
        
        # Extract the integer number from the response (e.g., 'Match Score: 68%' -> '68')
        match = re.search(r'(\d+)', result_text)
        if match:
            return int(match.group(1))
        else:
            print("        Could not find a number in the Gemini response.")
            return None
            
    except Exception as e:
        print(f"        Gemini API Error: {e}")
        return None

def save_to_excel(jobs_list, skipped_list):
    """
    Saves processed job statuses and skipped ones to Excel to avoid losing data mid-way.
    """
    if jobs_list:
        pd.DataFrame(jobs_list).to_excel(JOBS_EXCEL_FILE, index=False)
    if skipped_list:
        pd.DataFrame(skipped_list).to_excel(SKIP_EXCEL_FILE, index=False)

def main():
    # 1. Check dependencies
    if not os.path.exists(PROMPT_FILE):
        print(f"Error: Prompt file '{PROMPT_FILE}' not found. Please ensure it is in the same directory.")
        return
        
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    # Initialize Chrome options
    options = webdriver.ChromeOptions()
    print("Launching Chrome browser...")
    driver = webdriver.Chrome(options=options)
    
    # Tracking lists
    all_jobs_processed = []
    skipped_jobs = []

    try:
        # 2. Login to platform
        print("Navigating to https://www.naukri.com/")
        driver.get("https://www.naukri.com/")
        WebDriverWait(driver, 10).until(EC.title_contains("Jobs - Recruitment"))
        
        print("Please log in manually. Waiting up to 60 seconds for redirection to homepage...")
        try:
            WebDriverWait(driver, 60).until(EC.url_contains("naukri.com/mnjuser/homepage"))
            print("Successfully logged in.")
        except TimeoutException:
            print("Timeout waiting for login redirect. Proceeding anyway, but application may fail if not logged in.")

        # 3. Update the Resume
        print("Updating resume...")
        try:
            profile_element = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/mnjuser/profile') or contains(@class, 'view-profile') or contains(text(), 'View profile')]"))
            )
            profile_element.click()
            upload_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='file' and contains(@id, 'attachCV')]"))
            )
            upload_input.send_keys(RESUME_PATH)
            print("Resume uploaded successfully. Waiting 20 seconds...")
            time.sleep(20)
        except Exception as e:
            print(f"Error updating resume: {e}")

        # 4. Search and iterate through roles
        for page_no in range(1, PAGES_TO_SEARCH + 1):
            print(f"\n=== Navigating to Job Search Page {page_no} ===")
            search_url = BASE_SEARCH_URL.format(page_no)
            driver.get(search_url)

            # Wait for job cards to load
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@id, 'listContainer')]//div[contains(@class, 'srp-jobtuple-wrapper')]"))
                )
            except Exception:
                print(f"Timeout waiting for job cards on page {page_no}. Possibly no more pages.")
                break
            
            # Pause briefly to allow dynamic content to populate
            time.sleep(5)
            
            # Find all job cards on the page and extract URLs
            job_cards = driver.find_elements(By.XPATH, "//div[contains(@id, 'listContainer')]//div[contains(@class, 'srp-jobtuple-wrapper')]")
            print(f"Found {len(job_cards)} jobs on page {page_no}.")
            
            page_jobs = []
            for card in job_cards:
                try:
                    title_elem = card.find_element(By.XPATH, ".//a[@class='title ']")
                    page_jobs.append({
                        "title": title_elem.text,
                        "link": title_elem.get_attribute("href")
                    })
                except Exception:
                    continue
            
            # Process each job found on the current page
            for index, job in enumerate(page_jobs, start=1):
                title = job["title"]
                link = job["link"]
                print(f"\n--- Processing Job {index} of Page {page_no}: {title} ---")
                
                job_record = {
                    "Job Title": title,
                    "Job Link": link,
                    "Job Description": "",
                    "Match Score (%)": None,
                    "Application Status": "Failed/Error"
                }

                try:
                    driver.get(link)
                    time.sleep(3)
                    
                    # Check if Already Applied
                    already_applied = driver.find_elements(By.XPATH, "//span[contains(@id, 'already-applied') or contains(@class, 'already-applied') and contains(text(), 'Applied')]")
                    if already_applied:
                        print("    Already applied to this job. Skipping.")
                        job_record['Application Status'] = "Already Applied"
                        all_jobs_processed.append(job_record)
                        continue

                    # Extract the entire Job Description
                    desc_elem = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'styles_JDC__dang-inner-html')] | //section[contains(@class, 'job-desc-container') or contains(@class, 'job-desc')]"))
                    )
                    job_desc = desc_elem.text
                    job_record["Job Description"] = job_desc
                    print("    Description extracted successfully.")
                    
                    # 5. Check Job profile matching directly via API
                    print("    Checking job profile match via API...")
                    score = get_match_score(job_desc, prompt_template)
                    job_record["Match Score (%)"] = score
                    
                    # 6 & 7. Apply if Score >= Minimum criteria
                    if score is not None and score >= MIN_MATCH_SCORE:
                        print(f"    Match Score is {score}%. Attempting to apply...")
                        
                        # Apply logic
                        company_site_btn = driver.find_elements(By.XPATH, "//*[contains(text(), 'Apply on company site') or contains(text(), 'Company Site')]")
                        if company_site_btn:
                            # 8. Add to skipped file if external
                            print("    Found 'Apply on company site'. Marking as skipped.")
                            job_record["Application Status"] = "External Site / Skipped"
                            skipped_jobs.append(job_record)
                        else:
                            try:
                                apply_button = WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Apply') and not(contains(text(), 'site'))] | //a[contains(text(), 'Apply') and not(contains(text(), 'site'))] | //button[@id='apply-button']"))
                                )
                                print("    Clicking Apply button...")
                                apply_button.click()
                                
                                # Verify Application Success vs Questionannaires
                                WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'job-title-text') and contains(text(), 'Applied to')] | //div[contains(@class, 'applied-job-content')]//*[contains(text(), 'Applied')] | //*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'successfully applied')] | //span[contains(@class, 'green-tick') or contains(@class, 'success')]"))
                                )
                                print("    SUCCESS: Applied successfully!")
                                job_record["Application Status"] = "Successfully Applied"
                                
                            except TimeoutException:
                                print("    Did not detect successful apply text. Possible questionnaire modal. Marking as skipped.")
                                job_record["Application Status"] = "Questionnaire Modal / Skipped"
                                skipped_jobs.append(job_record)
                            except Exception as ex:
                                print(f"    Apply button issue: {ex}")
                                job_record["Application Status"] = f"Apply error: {ex}"
                                skipped_jobs.append(job_record)
                                
                    elif score is not None:
                        print(f"    Match Score is {score}%, which is < {MIN_MATCH_SCORE}%. Skipping application.")
                        job_record['Application Status'] = "Score too low"
                    else:
                        print("    Failed to calculate match score. Skipping.")
                        job_record['Application Status'] = "Failed to calculate score"

                except Exception as e:
                    print(f"    Error processing job: {e}")
                    job_record["Job Description"] = "Error getting description"
                    
                all_jobs_processed.append(job_record)
                
                # Save progress incrementally to avoid data loss
                save_to_excel(all_jobs_processed, skipped_jobs)
                
                print("    Waiting 10 seconds before next job...")
                time.sleep(10)

    except Exception as e:
        print(f"A critical error occurred: {e}")
    finally:
        print("Closing the Chrome browser.")
        driver.quit()
        save_to_excel(all_jobs_processed, skipped_jobs)
        print("Workflow Complete. Jobs saved to excel files.")

if __name__ == "__main__":
    main()
