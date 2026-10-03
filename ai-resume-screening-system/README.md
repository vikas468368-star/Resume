# AI Resume Screening System

An enterprise-grade, full-stack recruitment intelligence SaaS platform powered by NLP, TF-IDF cosine similarity, and explainable ATS audits. Automatically ingests candidate resumes in PDF and DOCX formats (with automated OCR fallback), extracts candidate metadata and competencies using a 350+ canonical skill taxonomy, computes multi-factor match scores against job requisitions, calculates explainable ATS compatibility, and ranks candidate pipelines in real-time.

---

## 🌟 Key Features

- **Multi-Engine Document Parsing**: Native layout and table text extraction from `.pdf` and `.docx` documents with automated OCR fallback for scanned images using PyPDF2, pdfminer.six, python-docx, and pytesseract.
- **NLP Information Extraction**: spaCy entity recognition, regex contact parsers (email, phone, location, links), section segmenter (Summary, Experience, Education, Skills, Projects, Certifications), and experience years calculator.
- **350+ Canonical Skill Taxonomy**: Intelligent normalization mapping synonyms, abbreviations, and variations (e.g. `py` &rarr; `Python`, `k8s` &rarr; `Kubernetes`, `react.js` &rarr; `React`, `psql` &rarr; `PostgreSQL`).
- **Multi-Factor Match Scoring**:
  - **40%** TF-IDF Text Similarity (Sublinear term frequency + cosine similarity)
  - **35%** Required & Preferred Skill Overlap (Jaccard / weighted coverage)
  - **15%** Experience Match (Candidate years vs. minimum requisition requirement)
  - **10%** Education Level Match (Degree hierarchy evaluation)
- **Explainable ATS Scoring Rubric**:
  - **Contact Information (15 pts)**: Validates email, phone, and geographic location / profile links.
  - **Section Completeness (25 pts)**: Audits presence of summary, experience, education, and skills sections.
  - **Keyword Relevance (25 pts)**: Evaluates density of high-value domain keywords.
  - **Skill Relevance (25 pts)**: Measures proportion of core mandatory technical competencies.
  - **Formatting Hygiene (10 pts)**: Analyzes word count length and character cleanliness.
- **Automated Candidate Ranking**: Dynamic composite scoring (`Match Score × 0.70 + ATS Score × 0.30`) with automatic 1-indexed rank assignment (`#1, #2, #3...`).
- **Modern Dark Glassmorphism UI**: High-contrast recruiter dashboard with KPI metric cards, Chart.js match distribution donut and submission trend charts, candidate directory filters, and explainable audit checklists.
- **Role-Based Access Control (RBAC)**:
  - **Admin**: Complete administrative control over all jobs, resumes, candidate pools, and analytics.
  - **Recruiter**: Isolated workspace managing their own job postings, candidate screenings, and shortlists.

---

## 🏗 Architecture

```
[Candidate Resumes] (.PDF / .DOCX / Scanned)
        │
        ▼
[app/services/extractor.py]
  ├─ Native PDF / DOCX Extractor
  └─ OCR Fallback (pytesseract + pdf2image)
        │
        ▼
[app/services/nlp_processor.py]
  ├─ Contact & Header Parser (Email, Phone, Location)
  ├─ Section Segmenter (Summary, Experience, Education, Skills)
  └─ 350+ Canonical Skill Taxonomy Normalizer
        │
        ▼
[app/services/scorer.py & ats_scorer.py]
  ├─ TF-IDF Cosine Similarity Engine (40%)
  ├─ Skill Gap & Match Calculator (35%)
  ├─ Experience & Education Alignment (25%)
  └─ 5-Part Explainable ATS Audit Rubric
        │
        ▼
[app/services/ranking.py]
  └─ Composite Score = (Match × 0.70) + (ATS × 0.30) ──► Rank Assignment (#1..N)
        │
        ▼
[Recruiter Dashboard & Analytics] (Glassmorphic UI + Chart.js)
```

---

## 💻 Tech Stack

- **Backend**: Python 3.11 / 3.13, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF, Flask-Migrate, Werkzeug
- **NLP & Machine Learning**: spaCy (`en_core_web_sm`), scikit-learn, TF-IDF Vectorizer, Cosine Similarity, Regex
- **Document Processing**: `pdfminer.six`, `PyPDF2`, `python-docx`, `pytesseract`, `pdf2image`, `Pillow`
- **Database**: PostgreSQL (Production) / SQLite (Zero-config local development)
- **Frontend**: HTML5, Vanilla CSS3 (Custom Glassmorphic design system), Vanilla JavaScript (ES6+), Jinja2, Chart.js 4.4
- **Testing**: Python `unittest`, `pytest`

---

## 📁 Folder Structure

```
ai-resume-screening-system/
├── app/
│   ├── __init__.py                # Flask application factory & Jinja filters
│   ├── models.py                  # User, JobDescription, Resume, Screening models
│   ├── routes/
│   │   ├── __init__.py            # RBAC decorators (@admin_required)
│   │   ├── auth.py                # Login, Register, Logout
│   │   ├── dashboard.py           # Overview, KPI statistics, Analytics JSON API
│   │   ├── jobs.py                # Job CRUD & auto-skill extraction API
│   │   ├── resumes.py             # Drag & drop upload portal & file streaming
│   │   └── candidates.py          # Candidate directory, profile, status switcher
│   ├── services/
│   │   ├── __init__.py            # Service package exports
│   │   ├── extractor.py           # Multi-engine PDF/DOCX & OCR extraction
│   │   ├── nlp_processor.py       # spaCy NER, sections & 350+ skill taxonomy
│   │   ├── job_processor.py       # JD parser, requirements & keyword extractor
│   │   ├── scorer.py              # TF-IDF & 4-factor match scoring engine
│   │   ├── ats_scorer.py          # 5-part explainable ATS audit engine
│   │   └── ranking.py             # Composite ranking & pipeline orchestrator
│   ├── templates/
│   │   ├── base.html              # Master layout with sidebar & header
│   │   ├── auth/                  # login.html, register.html
│   │   ├── dashboard/             # index.html, analytics.html
│   │   ├── jobs/                  # list.html, create.html, detail.html, edit.html
│   │   ├── screening/             # index.html (Drag & Drop Portal)
│   │   ├── candidates/            # list.html, detail.html (Explainable Profile)
│   │   └── errors/                # 400.html, 403.html, 404.html, 413.html, 500.html
│   └── static/
│       ├── css/
│       │   └── style.css          # Modern dark glassmorphism design system
│       └── js/
│           ├── main.js            # UI utilities & modal handlers
│           ├── dashboard.js       # Chart.js dynamic initialization
│           └── screening.js       # Drag & drop upload & progress tracker
├── uploads/                       # Uploaded resumes storage
├── tests/
│   ├── test_auth.py               # Auth & RBAC unit tests
│   ├── test_extractor.py          # Document parsing & text cleaner tests
│   ├── test_nlp.py                # Contact extraction & skill taxonomy tests
│   ├── test_scorer.py             # TF-IDF, Match Score & ATS Rubric tests
│   └── test_routes.py             # Route integration & pipeline tests
├── seed.py                        # Database seeder with realistic test data
├── config.py                      # Development, Testing, Production configs
├── run.py                         # Application entrypoint
├── requirements.txt               # Pinned dependencies
├── Procfile                       # Production process declaration
├── render.yaml                    # Cloud deployment specification
├── .env.example                   # Environment variable template
└── README.md                      # Documentation
```

---

## 🚀 Installation & Local Setup

### 1. Clone & Navigate
```bash
cd scratch/ai-resume-screening-system
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install spaCy NLP Model
```bash
python -m spacy download en_core_web_sm
```

### 5. Environment Variables
Create a `.env` file in the root directory:
```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-change-this

# For SQLite (default zero-config local development):
DATABASE_URL=sqlite:///app.db

# For PostgreSQL:
# DATABASE_URL=postgresql://postgres:password@localhost:5432/resume_screener

UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
```

### 6. Seed Database with Realistic Demo Data
```bash
python seed.py
```

### 7. Run the Application
```bash
python run.py
```
Open your browser at `http://localhost:5000`.

---

## 🔑 Demo Credentials

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@resumescreen.ai` | `Admin@123` | Full access across all jobs and candidate pools |
| **Lead Recruiter** | `recruiter@resumescreen.ai` | `Recruiter@123` | Manage own jobs, upload & screen candidates, shortlist |

---

## 📊 Scoring Methodology

### 1. Multi-Factor Match Score (0–100)
$$\text{Match Score} = (0.40 \times \text{TextSim}) + (0.35 \times \text{SkillScore}) + (0.15 \times \text{ExpScore}) + (0.10 \times \text{EduScore})$$

- **Text Similarity (40%)**: Sublinear TF-IDF word & bi-gram vectors evaluated via Cosine Similarity against the raw job description.
- **Skill Score (35%)**: Exact canonical match against required skills (80% weight) and preferred skills (20% weight).
- **Experience Score (15%)**: Ratio of candidate's verified experience years against the minimum requisition requirement.
- **Education Score (10%)**: Hierarchical qualification matching (Ph.D. &gt; Master's &gt; Bachelor's &gt; Associate/Diploma).

### 2. ATS Compatibility Score (0–100)
$$\text{ATS Score} = \text{Contact (15)} + \text{Sections (25)} + \text{Keywords (25)} + \text{Skills (25)} + \text{Formatting (10)}$$

---

## 🧪 Running Automated Tests

Run the comprehensive unit and integration test suite:
```bash
python -m unittest discover -s tests -p "test_*.py"
```

All 22 test suites cover authentication, PDF/DOCX extraction, NLP skill parsing, TF-IDF matching, ATS audits, and route interactions.

---

## 🌐 Production Deployment (Render / Railway / Heroku)

1. Connect your repository to **Render** or **Railway**.
2. Set Environment Variables:
   - `SECRET_KEY`: `<secure-random-string>`
   - `DATABASE_URL`: `postgresql://<user>:<pass>@<host>:<port>/<dbname>`
   - `FLASK_ENV`: `production`
3. Build Command:
   ```bash
   pip install -r requirements.txt && python -m spacy download en_core_web_sm && python seed.py
   ```
4. Start Command:
   ```bash
   gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```

---

## 📄 Resume-Ready Project Description

> **AI Resume Screening & Talent Intelligence SaaS Platform**
> *Developed a full-stack automated recruitment platform utilizing Flask, PostgreSQL, and spaCy NLP that parses multi-format resumes (.pdf, .docx, OCR scanned fallback), extracts competencies across a 350+ canonical skill taxonomy, computes explainable ATS compatibility scores, and ranks candidates using a hybrid multi-factor TF-IDF cosine similarity engine. Built a responsive dark glassmorphic UI featuring interactive Chart.js analytics, candidate directory filters, and role-based access control.*
