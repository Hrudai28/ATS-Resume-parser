ATS resume_parser – Gemini Version
AI-Powered Resume-to-JD Matching API using Google Gemini 1.5 + FastAPI

This project is an Applicant Tracking System (ATS) matcher that analyzes resumes and job descriptions, extracting skills, experience, similarity scores, and match recommendations using Google Gemini 1.5 Flash.
It supports PDF / DOCX / TXT files and produces structured results for dashboards or automated screening workflows.

✨ Features
🔍 AI-Driven Parsing
Automatically extracts structure from resumes:
Name, email, phone
Roles, companies, dates
Technical skills
Sections: summary, skills, experience, education
Job Description (JD) extraction:
Title
Must-have and nice-to-have skills
Experience range
Domain and location
🤖 LLM-Enhanced Skill Extraction
Normalizes skills using predefined canonical dictionary
Merges LLM and rule-based skill detection
Handles synonyms (e.g., T-SQL → SQL)
📊 Matching Engine
Combines:

Rule-based scoring
Experience relevance
Recency-based scoring
Semantic similarity using Gemini embeddings
📝 API Output
Match score
Semantic similarity
Skill coverage
Missing skills
Flags like AUTO_RECOMMEND, LOW_PRIORITY, BELOW_EXP_RANGE
Explanation summary
🧪 Tech Stack
Component	Usage
FastAPI	API backend
Gemini 1.5 Flash	Resume & JD parsing
text-embedding-004	Semantic similarity
pdfplumber	PDF extraction
python-docx	DOCX extraction
Uvicorn	ASGI server
📦 Installation
1️⃣ Clone repo
git clone https://github.com/your-org/way2hire-ats-gemini.git
cd way2hire-ats-gemini

2️⃣ Create environment
python -3.10 -m venv resume
source venv/bin/activate

3️⃣ Install dependencies
pip install -r requirements.txt

4️⃣ Add environment variable

Create .env file:

GEMINI_API_KEY=YOUR_API_KEY

🚀 Run the Server
uvicorn resume_final:app --reload --port 8000
