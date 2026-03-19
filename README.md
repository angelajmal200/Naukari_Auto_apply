# Naukari_Auto_apply
Intelligent job application automation script using Python, Selenium, and Google Gemini AI. Automatically scrapes listings, evaluates profile fit via LLM prompting, and submits applications for high-matching roles.

**Note:** Although the repository is named `Linkidin_Auto_apply`, this specific workflow is designed to automate job searching, profile matching, and applying on **Naukri.com**.

## Description

This project automates the job application process using Selenium and the Gemini AI API. The main script, `combined_naukri_workflow.py`, logs into Naukri, updates your resume, scrapes job listings based on a specific search URL, evaluates each job description against your profile using Google's Gemini AI, and automatically applies to jobs that score 70% or higher.

It uses two primary files:
1. **`combined_naukri_workflow.py`**: The main execution script containing all automation and API interaction logic.
2. **`prompt.md`**: A text file containing your profile details and instructions for the Gemini AI on how to evaluate job descriptions.

---

## Configuration Guide

Before running the workflow, you will need to update a few details within the codebase to match your needs.

### How to update `prompt.md` with your job criteria

The `prompt.md` file serves as the strict persona and grading criteria for the AI. 
1. Open `prompt.md` in any text editor.
2. Update the top sections (Experience, Target Roles, Location Preference) with your most up-to-date resume details.
3. **Do not modify or remove** the `<< Paste Job Description Here >>` text. The script automatically replaces this placeholder with the scraped job description from each Naukri posting during execution.

### How to update the Gemini API Key

If your Gemini API key expires or you want to use a different one:
1. Open `combined_naukri_workflow.py`.
2. Locate the configuration section at the top of the file (around Line 13).
3. Update the `GEMINI_API_KEY` variable:
   ```python
   GEMINI_API_KEY = "YOUR-NEW-API-KEY-HERE"
   ```

### How to update the Search URL

To search for a different role, location, or experience level:
1. Go to [Naukri.com](https://www.naukri.com) manually in your browser.
2. Perform your desired job search (e.g., search for "Data Scientist" in "Bangalore" with "3 years experience").
3. Once the first page of results loads, copy the entire URL from your browser's address bar.
4. Open `combined_naukri_workflow.py`.
5. Locate the configuration section at the top of the file.
6. Replace the `BASE_SEARCH_URL` value with your copied URL. 
   **Important:** Replace the page number in your copied URL (e.g., `-1?` or `-2?`) with `{}` so the script can paginate automatically.
   ```python
   BASE_SEARCH_URL = "https://www.naukri.com/your-new-search-url-{}?k=..."
   ```

---

## How to Run the Script

If you haven't yet generated a `.exe` file, you can run the script directly using Python.

### Prerequisites
Ensure your environment has Python installed. Then, install the required packages using the provided `requirements.txt` file:
```bash
pip install -r requirements.txt
```

### Execution
1. Open your terminal or command prompt.
2. Navigate to the directory containing the script.
3. Run the script:
   ```bash
   python combined_naukri_workflow.py
   ```
4. **Manual Login Step:** The Chrome browser will launch automatically. It will pause for up to 60 seconds on the Naukri homepage. During this time, you MUST manually log into your Naukri account. Once logged in, the script will detect the redirect to the homepage and automatically resume its process. 

### Outputs
- **`naukri_jobs.xlsx`**: A log of every job the script scanned, including its Match Score and Application Status.
- **`skip.xlsx`**: A log containing jobs that were skipped (e.g., because they routed to an external company site, required questionnaire modals, or resulted tied to an error).
