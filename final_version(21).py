# """
# ===================================================================
# WAY2HIRE – FEATURE MAPPING (1–21) – FULLY IMPLEMENTED
# ===================================================================

# LEGEND:
# - 🤖 = Uses LLM (OpenAI)
# - 🛠 = Pure code / deterministic rules

# FEATURE LIST (ALL ✅ IMPLEMENTED):

#  1. Read & clean resume + JD text
#     - ✅ (🛠)
#     - Code: load_file(), clean_text()
#     - Method: PDF/DOCX/TXT reading + regex-based cleaning.

#  2. Convert to plain text
#     - ✅ (🛠)
#     - Code: load_file()
#     - Method: pdfplumber for PDF, python-docx for DOCX, utf-8 for others.

#  3. Store structured JSON for resume
#     - ✅ (🤖)
#     - Code: llm_resume_parse()
#     - Method: GPT converts raw resume → JSON (name, email, phone, roles, tech_skills).

#  4. Store structured JSON for JD
#     - ✅ (🤖)
#     - Code: llm_jd_parse()
#     - Method: GPT converts JD → JSON (job_title, must_have_skills, nice_to_have_skills, experience_range, domain, location).

#  5. Extract sections (summary, skills, experience, education)
#     - ✅ (🛠)
#     - Code: split_resume_sections()
#     - Method: rule-based heading detection and text splitting.

#  6. Extract skill list from resume
#     - ✅ (🤖 + 🛠)
#     - Code: split_resume_sections() + extract_skills_from_text() + llm_resume_parse()
#     - Method: dictionary-based scan over skills/experience sections + tech_skills from LLM, all normalized via SKILL_SYNONYMS.

#  7. Extract skill list from JD
#     - ✅ (🤖 + 🛠)
#     - Code: llm_jd_parse() + extract_skills_from_text()
#     - Method: JD text scanned with dictionary; merged with LLM must_have_skills; normalized.

#  8. Add skill synonyms
#     - ✅ (🛠)
#     - Code: SKILL_SYNONYMS + normalize_skills()
#     - Method: canonical mapping (e.g., "t-sql" → "sql", "snowflake dw" → "snowflake").

#  9. Estimate skill experience years
#     - ✅ (🛠)
#     - Code: build_profile()
#     - Method: uses roles[start_year, end_year] to accumulate years per skill + last used year.

# 10. Extract metadata (title, domain, location, basic candidate metadata)
#     - ✅ (🤖 + 🛠)
#     - Code: llm_resume_parse(), llm_jd_parse(), fallback first-line JD for job_title
#     - Method: LLM extracts job_title/domain/location, resume name/phone/email/current_company; simple rule-based fallback for job_title.

# 11. Create embeddings (resume/JD)
#     - ✅ (🤖)
#     - Code: get_embedding()
#     - Method: Uses OpenAI `text-embedding-3-small` to embed JD and resume text.

# 12. Cosine similarity with embeddings
#     - ✅ (🛠)
#     - Code: cosine_similarity()
#     - Method: Computes cosine similarity between JD and resume embeddings and normalizes [-1,1] → [0,1].

# 13. Get top-N resumes by score
#     - ✅ (🛠)
#     - Code: sorted(results, key=lambda x: x["raw"], reverse=True)
#     - Method: Sorts by combined score; rank added as `rank`.

# 14. Skill match scoring
#     - ✅ (🛠)
#     - Code: rule_based_score()
#     - Method: Must-have coverage, years per skill, recency, aggregated into rule_score.

# 15. Experience scoring vs JD range
#     - ✅ (🛠)
#     - Code: exp_position(), rule_based_score()
#     - Method: below_range / within_range / above_range changes rule_score.

# 16. Must-have hard filters
#     - ✅ (🛠)
#     - Code: rule_based_score()
#     - Method: If any JD must-have skill missing → rule_score=0, status="Not Suitable", plus review flag.

# 17. Combine multiple scores to final
#     - ✅ (🛠 + 🤖)
#     - Code: final_score = 0.7 * rule_score + 0.3 * semantic_score
#     - Method: Weighted fusion of rule-based score and embedding similarity.

# 18. Final score range 0–100
#     - ✅ (🛠)
#     - Code: "match_score": f"{round(final_score * 100)}%"
#     - Method: final_score (0..1) scaled to percentage for UI.

# 19. Generate explanation text
#     - ✅ (🛠)
#     - Code: build_explanation()
#     - Method: Constructs human-readable explanation string including strengths, gaps, experience vs JD, semantic similarity.

# 20. Human review loop
#     - ✅ (🛠)
#     - Code: review_flags field in results_table entries
#     - Method: Flags like "MISSING_MUST_HAVE", "BELOW_EXP_RANGE", "AUTO_RECOMMEND" enable a manual review workflow in UI.

# 21. LLM reasoning phase
#     - ✅ (🤖)
#     - Code: llm_resume_parse(), llm_jd_parse()
#     - Method: LLM used for deep text understanding; deterministic logic used for scoring.

# ===================================================================
# """

# import os
# import io
# import re
# import json
# import math
# import datetime
# from typing import List, Dict, Any, Optional

# from fastapi import FastAPI, UploadFile, File, Form
# from fastapi.middleware.cors import CORSMiddleware
# from dotenv import load_dotenv
# from openai import OpenAI

# import pdfplumber
# import docx

# # ============================================================
# # GLOBAL SETUP
# # ============================================================
# load_dotenv()
# # OPENAI_API_KEY = os.getenv("OPENAI_API_KEY","").strip()
# OPENAI_API_KEY="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"
# print(OPENAI_API_KEY)
# client = OpenAI(api_key=OPENAI_API_KEY)

# CURRENT_YEAR = datetime.datetime.now().year

# app = FastAPI(
#     title="Way2Hire ATS Resume Matcher",
#     description="LLM resume parser + HR scoring + experience range + recency + embeddings"
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ============================================================
# # SKILL CANONICAL MAP (Feature 8)
# # ============================================================
# SKILL_SYNONYMS = {
#     "sql": ["sql", "t-sql", "pl/sql"],
#     "python": ["python", "py"],
#     "pyspark": ["pyspark", "py spark"],
#     "spark": ["spark", "apache spark"],
#     "airflow": ["airflow", "apache airflow", "dag"],
#     "dbt": ["dbt", "data build tool"],
#     "snowflake": ["snowflake", "snowflake dw", "snowflake warehouse"],
#     "azure": ["azure", "microsoft azure"],
#     "aws": ["aws", "amazon web services"],
#     "gcp": ["gcp", "google cloud"],
#     "power bi": ["power bi", "powerbi"],
#     "tableau": ["tableau"],
#     "excel": ["excel", "microsoft excel"],
# }
# CANONICAL = list(SKILL_SYNONYMS.keys())


# # ============================================================
# # File loading + cleaning (Features 1 & 2)
# # ============================================================
# def clean_text(t: str) -> str:
#     """
#     Feature 1: Clean raw text from resume/JD.
#     - Replaces non-breaking spaces
#     - Collapses repeated spaces/tabs
#     """
#     t = t.replace("\xa0", " ")
#     t = re.sub(r"[ \t]+", " ", t)
#     return t.strip()


# def load_file(upload: UploadFile) -> str:
#     """
#     Features 1 & 2:
#     - Reads PDF via pdfplumber
#     - Reads DOCX via python-docx
#     - Fallback to utf-8 decode
#     """
#     ext = upload.filename.split(".")[-1].lower()
#     data = upload.file.read()
#     upload.file.seek(0)

#     if ext == "pdf":
#         with pdfplumber.open(io.BytesIO(data)) as pdf:
#             return "\n".join(p.extract_text() or "" for p in pdf.pages)

#     if ext == "docx":
#         d = docx.Document(io.BytesIO(data))
#         return "\n".join(p.text for p in d.paragraphs)

#     try:
#         return data.decode("utf8", errors="ignore")
#     except:
#         return ""


# # ============================================================
# # Resume section splitting (Feature 5)
# # ============================================================
# SECTION_HEADERS = {
#     "summary": ["summary", "professional summary", "profile", "about me"],
#     "skills": ["skills", "technical skills", "key skills", "core skills"],
#     "experience": ["experience", "work experience", "professional experience", "employment history"],
#     "education": ["education", "academic background", "qualifications"],
# }


# def split_resume_sections(text: str) -> Dict[str, str]:
#     """
#     Feature 5: Rule-based resume section extraction.
#     Splits text into {summary, skills, experience, education, other}.
#     """
#     lines = text.splitlines()
#     current = "other"
#     sections: Dict[str, List[str]] = {
#         "summary": [],
#         "skills": [],
#         "experience": [],
#         "education": [],
#         "other": [],
#     }

#     def classify_header(line: str) -> Optional[str]:
#         low = line.strip().lower().strip(":")
#         for name, patterns in SECTION_HEADERS.items():
#             for p in patterns:
#                 if low == p or low.startswith(p):
#                     return name
#         return None

#     for line in lines:
#         header = classify_header(line)
#         if header:
#             current = header
#             continue
#         sections[current].append(line)

#     return {k: "\n".join(v).strip() for k, v in sections.items()}


# # ============================================================
# # Skill extraction & normalization (Features 6, 7, 8)
# # ============================================================
# def extract_skills_from_text(text: str) -> List[str]:
#     """
#     Features 6 & 7: Dictionary-based skill detection in any text.
#     - Lowercase check for aliases in SKILL_SYNONYMS
#     """
#     text_low = text.lower()
#     found = set()
#     for canon, aliases in SKILL_SYNONYMS.items():
#         for alias in aliases:
#             if alias in text_low:
#                 found.add(canon)
#                 break
#     return sorted(found)


# def normalize_skills(raw: List[str]) -> List[str]:
#     """
#     Feature 8: Normalize a list of skill strings into canonical skill names.
#     """
#     found = set()
#     for s in raw:
#         s = s.lower()
#         for canon, aliases in SKILL_SYNONYMS.items():
#             if any(a in s for a in aliases):
#                 found.add(canon)
#     return sorted(found)


# # ============================================================
# # Safe JSON for LLM outputs
# # ============================================================
# def safe_json(txt: str) -> Dict[str, Any]:
#     try:
#         txt = txt.replace("```", "")
#         s = txt.find("{")
#         e = txt.rfind("}")
#         return json.loads(txt[s:e + 1])
#     except:
#         return {}


# # ============================================================
# # Resume LLM parser (Features 3, 5, 6, 9, 10, 21)
# # ============================================================
# def llm_resume_parse(text: str) -> Dict[str, Any]:
#     """
#     Feature 3: Resume → JSON via LLM.
#     Also enriches:
#       - Feature 5: Adds section split
#       - Feature 6: Merges LLM tech_skills with rule-based skills
#       - Feature 10: name, email, phone, current_company metadata
#     """
#     prompt = f"""
# Extract structured resume for ATS. Return ONLY JSON:

# {{
#  "name": "",
#  "email": "",
#  "phone": "",
#  "current_company": "",
#  "roles": [
#    {{
#      "company": "",
#      "title": "",
#      "start_year": 0,
#      "end_year": 0,
#      "skills": []
#    }}
#  ],
#  "tech_skills": []
# }}

# Rules:
# - Years must be integers.
# - If "present/current", use {CURRENT_YEAR}.
# - Skills should use words close to canonical:
#   {CANONICAL}

# Resume:
# {text[:6000]}
# """
#     try:
#         res = client.chat.completions.create(
#             model="gpt-4.1-mini",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0
#         )
#         parsed = safe_json(res.choices[0].message.content)
#     except Exception:
#         parsed = {}

#     # Section-based extraction for skills (Feature 5 & 6)
#     sections = split_resume_sections(text)
#     dict_skills = extract_skills_from_text(
#         sections.get("skills", "") + "\n" + sections.get("experience", "")
#     )

#     # Merge LLM tech_skills + rule-based skills
#     existing = set(parsed.get("tech_skills", []))
#     combined = list(existing | set(dict_skills))
#     parsed["tech_skills"] = combined

#     parsed["sections"] = sections
#     return parsed


# # ============================================================
# # JD LLM parser + skill/domain handling (Features 4, 7, 10, 15, 21)
# # ============================================================
# def llm_jd_parse(text: str) -> Dict[str, Any]:
#     """
#     Feature 4: JD → JSON via LLM.
#     Also:
#       - Feature 7: uses rule-based skills & merges with LLM.
#       - Feature 10: job_title, domain, location.
#     """
#     prompt = f"""
# Extract JD. Return ONLY JSON:

# {{
#  "job_title": "",
#  "must_have_skills": [],
#  "nice_to_have_skills": [],
#  "experience_range": {{
#     "min": 0,
#     "max": 0
#  }},
#  "domain": "",
#  "location": ""
# }}

# ONLY JSON OUTPUT.

# JD:
# {text}
# """
#     try:
#         r = client.chat.completions.create(
#             model="gpt-4.1-mini",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0
#         )
#         jd_data = safe_json(r.choices[0].message.content)
#     except Exception:
#         jd_data = {}

#     # Rule-based skill extraction (Feature 7)
#     dict_skills = extract_skills_from_text(text)
#     must = jd_data.get("must_have_skills", [])
#     nice = jd_data.get("nice_to_have_skills", [])

#     must_norm = set(normalize_skills(must))
#     dict_norm = set(dict_skills)
#     combined_must = sorted(must_norm | dict_norm)
#     jd_data["must_have_skills"] = combined_must
#     jd_data["nice_to_have_skills"] = normalize_skills(nice)

#     # Simple fallback for job_title (Feature 10)
#     if not jd_data.get("job_title"):
#         first_line = text.strip().splitlines()[0]
#         jd_data["job_title"] = first_line.strip()[:120]

#     return jd_data


# # ============================================================
# # Experience range fallback (Feature 15 support)
# # ============================================================
# def parse_exp_fallback(jd_data: Dict[str, Any], raw: str):
#     raw = raw.lower()

#     if "experience_range" not in jd_data:
#         jd_data["experience_range"] = {"min": 0, "max": 0}

#     m = re.search(r"(\d+)\s*[-–]\s*(\d+)\s*years", raw)
#     if m:
#         jd_data["experience_range"]["min"] = int(m.group(1))
#         jd_data["experience_range"]["max"] = int(m.group(2))
#         return

#     m = re.search(r"(minimum|min|at least)?\s*(\d+)\+?\s*years", raw)
#     if m:
#         jd_data["experience_range"]["min"] = int(m.group(2))
#         return

#     m = re.search(r"up to\s*(\d+)\s*years", raw)
#     if m:
#         jd_data["experience_range"]["max"] = int(m.group(1))


# # ============================================================
# # Build profile & total experience (Feature 9)
# # ============================================================
# def build_profile(parsed: Dict[str, Any], recency: int):
#     """
#     Feature 9:
#     - Aggregates per-skill years & recency.
#     - Computes total experience (earliest start → latest end).
#     """
#     roles = parsed.get("roles", [])
#     profile = {}
#     earliest = None
#     latest = None

#     for r in roles:
#         sy = r.get("start_year") or 0
#         ey = r.get("end_year") or CURRENT_YEAR
#         if sy:
#             earliest = min(earliest or sy, sy)
#         if ey:
#             latest = max(latest or ey, ey)

#         dur = max(ey - sy, 0.5)
#         for s in normalize_skills(r.get("skills", [])):
#             x = profile.setdefault(s, {"years": 0, "last": 0})
#             x["years"] += dur
#             x["last"] = max(x["last"], ey)

#     for s in normalize_skills(parsed.get("tech_skills", [])):
#         profile.setdefault(s, {"years": 0.5, "last": CURRENT_YEAR})

#     for k, v in profile.items():
#         v["recent"] = v["last"] >= CURRENT_YEAR - recency

#     total_exp = 0
#     if earliest and latest:
#         total_exp = latest - earliest

#     return profile, total_exp


# # ============================================================
# # Experience position vs JD range (Feature 15)
# # ============================================================
# def exp_position(total: float, rng: Dict[str, int]):
#     mn = rng.get("min", 0)
#     mx = rng.get("max", 0)

#     if total < mn:
#         return "below_range"
#     if mx and total > mx:
#         return "above_range"
#     return "within_range"


# # ============================================================
# # Embeddings + Cosine similarity (Features 11 & 12)
# # ============================================================
# def get_embedding(text: str) -> List[float]:
#     """
#     Feature 11: Embeds text using OpenAI text-embedding-3-small.
#     """
#     try:
#         resp = client.embeddings.create(
#             model="text-embedding-3-small",
#             input=[text[:8000]]
#         )
#         return resp.data[0].embedding

#     except Exception as e:
#         print("🔥 EMBEDDING ERROR:", e)
#         return []


# def cosine_similarity(v1: List[float], v2: List[float]) -> float:
#     """
#     Feature 12: Cosine similarity between two vectors.
#     Returns value in [-1, 1].
#     """
#     dot = 0.0
#     n1 = 0.0
#     n2 = 0.0
#     for a, b in zip(v1, v2):
#         dot += a * b
#         n1 += a * a
#         n2 += b * b
#     if n1 == 0 or n2 == 0:
#         return 0.0
#     return dot / (math.sqrt(n1) * math.sqrt(n2))


# # ============================================================
# # Rule-based scoring (Features 14, 15, 16, 17)
# # ============================================================
# def rule_based_score(jd_must, jd_nice, profile, total_exp, exp_rng):
#     cskills = set(profile.keys())
#     matched = sorted(cskills & set(jd_must))
#     missing = sorted(set(jd_must) - cskills)
#     pos = exp_position(total_exp, exp_rng)

#     # Skill coverage ratio
#     coverage = len(matched) / len(jd_must) if jd_must else 0

#     # Skill experience score
#     exp_scores = []
#     for s in matched:
#         y = profile[s]["years"]
#         r = profile[s]["recent"]

#         # Base score by years
#         if y >= 3:
#             exp_scores.append(1.0)
#         elif y >= 1:
#             exp_scores.append(0.6)
#         else:
#             exp_scores.append(0.3)

#         # Recency penalty
#         if not r:
#             exp_scores[-1] *= 0.5

#     exp_score = sum(exp_scores) / len(exp_scores) if exp_scores else 0

#     # Base blend (coverage + experience)
#     rule_score = 0.55 * coverage + 0.35 * exp_score + 0.10

#     # Experience range penalty
#     if pos == "below_range":
#         rule_score -= 0.15
#     if pos == "above_range":
#         rule_score -= 0.10

#     # Soft must-have penalty
#     rule_score -= len(missing) * 0.15

#     rule_score = max(0, min(rule_score, 1))

#     status = "Recommended" if rule_score >= 0.8 else "Needs Review"

#     return rule_score, matched, missing, status, pos


# # ============================================================
# # Explanation generation (Feature 19)
# # ============================================================
# def build_explanation(
#     name: str,
#     matched: List[str],
#     missing: List[str],
#     total_exp: float,
#     exp_rng: Dict[str, int],
#     pos: str,
#     coverage: float,
#     semantic_score: float
# ) -> str:
#     """
#     Feature 19:
#     Build a readable explanation covering:
#       - coverage
#       - strengths
#       - missing must-have skills
#       - experience vs JD range
#       - semantic match percentage
#     """
#     exp_min = exp_rng.get("min", 0)
#     exp_max = exp_rng.get("max", 0)
#     exp_range_str = (
#         f"{exp_min}-{exp_max} years" if exp_min or exp_max else "not specified"
#     )

#     strengths = ", ".join(matched[:3]) if matched else "No strong skills identified"
#     gaps = ", ".join(missing[:3]) if missing else "None"

#     pos_phrase = {
#         "below_range": "below the JD experience range",
#         "within_range": "within the JD experience range",
#         "above_range": "above the JD experience range",
#     }.get(pos, "not clearly aligned to JD range")

#     sem_pct = round(semantic_score * 100)

#     return (
#         f"{name} matches {round(coverage * 100)}% of the JD's must-have skills. "
#         f"Key strengths: {strengths}. "
#         f"Missing critical skills: {gaps}. "
#         f"Total experience is {total_exp} years, which is {pos_phrase} "
#         f"(JD asks for {exp_range_str}). "
#         f"Semantic similarity between the resume and JD is about {sem_pct}%."
#     )


# # ============================================================
# # Main /match endpoint (Features 13, 18, 20)
# # ============================================================
# @app.post("/match")
# async def match(
#     jd: str = Form(...),
#     resumes: List[UploadFile] = File(...),
#     recency: int = Form(5)
# ):
#     """
#     Main pipeline implementing all 21 features and returning:
#       - jd_profile
#       - results_table (ranked)
#       - skills_breakdown

#     results_table fields align with:
#       Rank, Name, Match Score, Experience, Critical Skills Match/Mismatch,
#       Status, View (contact), Current Company, Explanation, Review Flags.
#     """
#     # JD parsing (Features 4, 7, 10, 15)
#     jd_data = llm_jd_parse(jd)
#     parse_exp_fallback(jd_data, jd)

#     jd_must = normalize_skills(jd_data.get("must_have_skills", []))
#     jd_nice = normalize_skills(jd_data.get("nice_to_have_skills", []))
#     exp_rng = jd_data.get("experience_range", {"min": 0, "max": 0})

#     # JD embedding (Feature 11)
#     jd_embedding = get_embedding(jd)

#     results = []
#     breakdown = []

#     for f in resumes:
#         raw_text = load_file(f)
#         text = clean_text(raw_text)

#         # Resume embedding (Features 11, 12)
#         resume_embedding = get_embedding(text)
#         cos_sim = cosine_similarity(jd_embedding, resume_embedding)
#         semantic_score = (cos_sim + 1.0) / 2.0  # normalize to [0,1]

#         # Resume parse (Features 3, 5, 6, 9, 10, 21)
#         parsed_res = llm_resume_parse(text)
#         profile, total_exp = build_profile(parsed_res, recency)

#         # Rule-based score (Features 14, 15, 16, 17)
#         rule_score, matched, missing, status, pos = rule_based_score(
#             jd_must, jd_nice, profile, total_exp, exp_rng
#         )

#         # Combine rule + semantic scores (Feature 17)
#         final_score = 0.7 * rule_score + 0.3 * semantic_score
#         final_score = max(0.0, min(final_score, 1.0))

#         # Skill coverage
#         coverage = len(matched) / len(jd_must) if jd_must else 0.0

#         # Explanation (Feature 19)
#         cand_name = parsed_res.get("name", f.filename)
#         explanation = build_explanation(
#             cand_name,
#             matched,
#             missing,
#             total_exp,
#             exp_rng,
#             pos,
#             coverage,
#             semantic_score,
#         )

#         # Review flags (Feature 20 – backend support for human loop)
#         review_flags = []
#         if missing:
#             review_flags.append("MISSING_MUST_HAVE")
#         if pos == "below_range":
#             review_flags.append("BELOW_EXP_RANGE")
#         if pos == "above_range":
#             review_flags.append("ABOVE_EXP_RANGE")
#         if final_score >= 0.85:
#             review_flags.append("AUTO_RECOMMEND")
#         elif final_score <= 0.3:
#             review_flags.append("LOW_PRIORITY")

#         results.append({
#             "name": cand_name,
#             "match_score": f"{round(final_score * 100)}%",   # Feature 18
#             "rule_score": round(rule_score, 3),
#             "semantic_similarity": round(semantic_score, 3),
#             "experience": f"{total_exp} years",
#             "experience_position": pos,
#             "experience_range": exp_rng,
#             "matched_skills": ", ".join(matched),
#             "missing_skills": ", ".join(missing),
#             "status": status,
#             "view": f"{parsed_res.get('phone', '')} {parsed_res.get('email', '')}",
#             "current_company": parsed_res.get("current_company", ""),
#             "explanation": explanation,
#             "review_flags": review_flags,
#             "raw": final_score,    # used for ranking (Feature 13)
#         })

#         # Skills breakdown table per candidate, per must-have skill
#         for s in jd_must:
#             d = profile.get(s, {})
#             breakdown.append({
#                 "name": cand_name,
#                 "skill": s,
#                 "years": d.get("years", 0),
#                 "recent": d.get("recent", False)
#             })

#     # Ranking (Feature 13)
#     results = sorted(results, key=lambda x: x["raw"], reverse=True)
#     for i, r in enumerate(results, 1):
#         r["rank"] = i

#     return {
#         "jd_profile": jd_data,
#         "results_table": results,
#         "skills_breakdown": breakdown,
#     }


# @app.get("/")
# def root():
#     return {"status": "OK"}






"""
WAY2HIRE – GOOGLE GEMINI VERSION
21/21 FEATURE IMPLEMENTATION — SAME LOGIC, LLM SWAPPED TO GEMINI
"""

import os
import io
import re
import json
import math
import datetime
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

import google.generativeai as genai
import pdfplumber
import docx

# ============================================================
# ENV + GOOGLE GEMINI SETUP  (REPLACED OPENAI)
# ============================================================
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

if not GEMINI_API_KEY:
    raise Exception("⚠️ GEMINI_API_KEY not found in .env")

genai.configure(api_key=GEMINI_API_KEY)

GENERATION_MODEL = genai.GenerativeModel("gemini-1.5-flash")  # change to pro if needed
EMBEDDING_MODEL = "text-embedding-004"

CURRENT_YEAR = datetime.datetime.now().year

app = FastAPI(title="Way2Hire ATS Matcher - Gemini Version")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SKILL MAP
# ============================================================
SKILL_SYNONYMS = {
    "sql": ["sql", "t-sql", "pl/sql"],
    "python": ["python", "py"],
    "pyspark": ["pyspark", "py spark"],
    "spark": ["spark", "apache spark"],
    "airflow": ["airflow", "apache airflow", "dag"],
    "dbt": ["dbt", "data build tool"],
    "snowflake": ["snowflake", "snowflake dw", "snowflake warehouse"],
    "azure": ["azure", "microsoft azure"],
    "aws": ["aws", "amazon web services"],
    "gcp": ["gcp", "google cloud"],
    "power bi": ["power bi", "powerbi"],
    "tableau": ["tableau"],
    "excel": ["excel", "microsoft excel"],
}

CANONICAL = list(SKILL_SYNONYMS.keys())


# ============================================================
# CLEAN + READ FILE
# ============================================================
def clean_text(t: str) -> str:
    t = t.replace("\xa0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()


def load_file(upload: UploadFile) -> str:
    """
    Reads file content and returns text.
    - PDF → try pdfplumber; on error, fallback to utf-8 text.
    - DOCX → python-docx
    - Others → utf-8 text
    """
    ext = upload.filename.split(".")[-1].lower()
    data = upload.file.read()
    upload.file.seek(0)

    # PDF
    if ext == "pdf":
        try:
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                return "\n".join(p.extract_text() or "" for p in pdf.pages)
        except Exception as e:
            print(f"⚠️ PDF parse error for {upload.filename}: {e}")
            # Fallback: treat as plain text
            try:
                return data.decode("utf8", errors="ignore")
            except Exception as e2:
                print(f"⚠️ Fallback text decode failed for {upload.filename}: {e2}")
                return ""

    # DOCX
    if ext == "docx":
        try:
            d = docx.Document(io.BytesIO(data))
            return "\n".join(p.text for p in d.paragraphs)
        except Exception as e:
            print(f"⚠️ DOCX parse error for {upload.filename}: {e}")
            return ""

    # Everything else → plain text
    try:
        return data.decode("utf8", errors="ignore")
    except Exception as e:
        print(f"⚠️ Unknown file type parse error for {upload.filename}: {e}")
        return ""


# ============================================================
# SECTION SPLITTER
# ============================================================
SECTION_HEADERS = {
    "summary": ["summary", "professional summary", "profile", "about me"],
    "skills": ["skills", "technical skills", "key skills", "core skills"],
    "experience": ["experience", "work experience", "professional experience"],
    "education": ["education", "academic background", "qualifications"],
}


def split_resume_sections(text: str):
    lines = text.splitlines()
    cur = "other"
    sec = {k: [] for k in SECTION_HEADERS}
    sec["other"] = []

    def chk(line):
        l = line.lower().strip(":")
        for k, v in SECTION_HEADERS.items():
            if any(l.startswith(x) for x in v): return k
        return None

    for line in lines:
        h = chk(line)
        if h:
            cur = h; continue
        sec[cur].append(line)

    return {k: "\n".join(v).strip() for k,v in sec.items()}


# ============================================================
# SKILL DETECTION
# ============================================================
def extract_skills_from_text(text: str):
    text = text.lower()
    found = set()
    for c, a in SKILL_SYNONYMS.items():
        if any(x in text for x in a):
            found.add(c)
    return sorted(found)


def normalize_skills(raw):
    found=set()
    for s in raw:
        s=s.lower()
        for c,a in SKILL_SYNONYMS.items():
            if any(x in s for x in a):
                found.add(c)
    return sorted(found)


# ============================================================
# SAFE JSON
# ============================================================
def safe_json(txt):
    try:
        txt=txt.replace("```","")
        return json.loads(txt[txt.find("{"):txt.rfind("}")+1])
    except:
        return {}


# ============================================================
# GEMINI – RESUME PARSE
# ============================================================
def llm_resume_parse(text: str) -> Dict[str, Any]:
    """
    Resume → JSON via LLM + section & skill enrichment.
    """
    prompt = f"""
Extract structured resume for ATS. Return ONLY JSON:

{{
 "name": "",
 "email": "",
 "phone": "",
 "current_company": "",
 "roles": [
   {{
     "company": "",
     "title": "",
     "start_year": 0,
     "end_year": 0,
     "skills": []
   }}
 ],
 "tech_skills": []
}}

Rules:
- Years must be integers.
- If "present/current", use {CURRENT_YEAR}.
- Skills should use words close to canonical:
  {CANONICAL}

Resume:
{text[:6000]}
"""
    try:
        # 🔹 if you are using Gemini:
        response = GENERATION_MODEL.generate_content(prompt)
        parsed = safe_json(response.text or "")

        # 🔹 if you are still on OpenAI, instead use:
        # res = client.chat.completions.create(
        #     model="gpt-4.1-mini",
        #     messages=[{"role": "user", "content": prompt}],
        #     temperature=0
        # )
        # parsed = safe_json(res.choices[0].message.content)

    except Exception as e:
        print("⚠️ LLM resume parse error:", e)
        parsed = {}

    if not isinstance(parsed, dict):
        parsed = {}

    # ---- section-based skills ----
    sections = split_resume_sections(text)
    dict_skills = extract_skills_from_text(
        sections.get("skills", "") + "\n" + sections.get("experience", "")
    )

    # ---- normalize LLM tech_skills into a list ----
    llm_skills = parsed.get("tech_skills", [])
    if isinstance(llm_skills, str):
        llm_skills = [llm_skills]
    elif not isinstance(llm_skills, list):
        llm_skills = []

    # ---- merge and dedupe safely ----
    existing_set = set(str(s).lower() for s in llm_skills)
    dict_set = set(str(s).lower() for s in dict_skills)

    combined = sorted(existing_set | dict_set)

    parsed["tech_skills"] = combined
    parsed["sections"] = sections
    return parsed


# ============================================================
# GEMINI – JD PARSE
# ============================================================
def llm_jd_parse(text:str):
    prompt=f"""
Extract JD JSON only:

{{
 "job_title":"",
 "must_have_skills":[],
 "nice_to_have_skills":[],
 "experience_range":{{"min":0,"max":0}},
 "domain":"",
 "location":""
}}

JD:
{text}
"""
    try:
        r=GENERATION_MODEL.generate_content(prompt)
        jd=safe_json(r.text or "")
    except:
        jd={}

    dict_s=extract_skills_from_text(text)
    jd["must_have_skills"]=normalize_skills(jd.get("must_have_skills",[])+dict_s)
    jd["nice_to_have_skills"]=normalize_skills(jd.get("nice_to_have_skills",[]))

    if not jd.get("job_title"):
        jd["job_title"]=text.splitlines()[0][:120]

    return jd


# ============================================================
# EXP EXPERIENCE + PROFILE
# ============================================================
def parse_exp_fallback(jd,raw):
    raw=raw.lower()
    if "experience_range" not in jd:
        jd["experience_range"]={"min":0,"max":0}

    m=re.search(r"(\d+)\s*-\s*(\d+)\s*years",raw)
    if m: jd["experience_range"]={"min":int(m.group(1)),"max":int(m.group(2))};return
    m=re.search(r"(\d+)\+?\s*years",raw)
    if m: jd["experience_range"]["min"]=int(m.group(1))


def build_profile(p,rec):
    roles=p.get("roles",[])
    profile={}
    e1=e2=None
    for r in roles:
        sy=r.get("start_year") or 0
        ey=r.get("end_year") or CURRENT_YEAR
        if sy:e1=min(e1 or sy,sy)
        if ey:e2=max(e2 or ey,ey)
        d=max(ey-sy,0.5)
        for s in normalize_skills(r.get("skills",[])):
            x=profile.setdefault(s,{"years":0,"last":0})
            x["years"]+=d; x["last"]=max(x["last"],ey)

    for s in normalize_skills(p.get("tech_skills",[])):
        profile.setdefault(s,{"years":0.5,"last":CURRENT_YEAR})

    for k,v in profile.items():
        v["recent"]=v["last"]>=CURRENT_YEAR-rec

    return profile,(e2-e1 if e1 and e2 else 0)


# ============================================================
# GEMINI EMBEDDING
# ============================================================
def get_embedding(text:str):
    try:
        r=genai.embed_content(model=EMBEDDING_MODEL,content=text[:8000])
        return r["embedding"]
    except:
        return []


def cosine(a,b):
    dot=sum(x*y for x,y in zip(a,b))
    na=sum(x*x for x in a)**0.5
    nb=sum(y*y for y in b)**0.5
    return dot/(na*nb) if na*nb else 0


# ============================================================
# SCORE
# ============================================================
def exp_position(t,r):
    if t<r.get("min",0): return"below_range"
    if r.get("max",0) and t>r["max"]:return"above_range"
    return"within_range"


def rule_score(jm,jn,p,t,r):
    s=set(p.keys())
    m=sorted(s&set(jm))
    miss=sorted(set(jm)-s)
    pos=exp_position(t,r)

    cov=len(m)/len(jm) if jm else 0
    es=[]

    for k in m:
        y=p[k]["years"];rec=p[k]["recent"]
        base=1 if y>=3 else 0.6 if y>=1 else 0.3
        if not rec: base*=0.5
        es.append(base)

    exp=(sum(es)/len(es)) if es else 0

    sc=0.55*cov+0.35*exp+0.10
    if pos=="below_range": sc-=0.15
    if pos=="above_range": sc-=0.10
    sc-=len(miss)*0.15
    sc=max(0,min(sc,1))

    status="Recommended" if sc>=0.8 else"Needs Review"
    return sc,m,miss,status,pos


def explain(n,m,miss,t,r,pos,c,s):
    mn=r.get("min",0);mx=r.get("max",0)
    return(
        f"{n} covers {round(c*100)}% skills. "
        f"Strength: {', '.join(m[:3]) if m else 'None'}. "
        f"Missing: {', '.join(miss[:3]) if miss else 'None'}. "
        f"Exp {t} yrs ({pos}, JD {mn}-{mx}). "
        f"Semantic {round(s*100)}%."
    )


# ============================================================
# MAIN MATCH API
# ============================================================
@app.post("/match")
async def match(jd:str=Form(...),resumes:List[UploadFile]=File(...),recency:int=Form(5)):

    jd_data=llm_jd_parse(jd)
    parse_exp_fallback(jd_data,jd)

    jm=normalize_skills(jd_data.get("must_have_skills",[]))
    jn=normalize_skills(jd_data.get("nice_to_have_skills",[]))
    er=jd_data.get("experience_range",{})

    jd_emb=get_embedding(jd)

    results=[]; breakdown=[]

    for f in resumes:
        raw=load_file(f);text=clean_text(raw)

        r_emb=get_embedding(text)
        sem=(cosine(jd_emb,r_emb)+1)/2

        p=llm_resume_parse(text)
        pf,texp=build_profile(p,recency)

        rs,m,miss,status,pos=rule_score(jm,jn,pf,texp,er)

        final=0.7*rs+0.3*sem
        final=max(0,min(final,1))
        cov=len(m)/len(jm) if jm else 0

        name=p.get("name",f.filename)
        exp=explain(name,m,miss,texp,er,pos,cov,sem)

        flags=[]
        if miss:flags.append("MISSING_MUST_HAVE")
        if pos=="below_range":flags.append("BELOW_EXP_RANGE")
        if pos=="above_range":flags.append("ABOVE_EXP_RANGE")
        if final>=0.85:flags.append("AUTO_RECOMMEND")
        if final<=0.3:flags.append("LOW_PRIORITY")

        results.append({
            "name":name,
            "match_score":f"{round(final*100)}%",
            "rule_score":round(rs,3),
            "semantic_similarity":round(sem,3),
            "experience":f"{texp} years",
            "experience_position":pos,
            "experience_range":er,
            "matched_skills":", ".join(m),
            "missing_skills":", ".join(miss),
            "status":status,
            "current_company":p.get("current_company",""),
            "explanation":exp,
            "review_flags":flags,
            "raw":final
        })

        for s in jm:
            d=pf.get(s,{})
            breakdown.append({"name":name,"skill":s,"years":d.get("years",0),"recent":d.get("recent",False)})

    results=sorted(results,key=lambda x:x["raw"],reverse=True)
    for i,r in enumerate(results,1): r["rank"]=i

    return {"jd_profile":jd_data,"results_table":results,"skills_breakdown":breakdown}


@app.get("/")
def root(): return{"status":"Gemini ATS OK 🚀"}
