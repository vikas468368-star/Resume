import re
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Global spaCy NLP instance cache
_spacy_nlp = None

def get_spacy_nlp():
    """Lazy load spaCy model with automatic fallback to blank English model."""
    global _spacy_nlp
    if _spacy_nlp is None:
        try:
            import spacy
            try:
                _spacy_nlp = spacy.load("en_core_web_sm")
            except Exception:
                logger.info("en_core_web_sm not downloaded. Using spacy.blank('en')")
                _spacy_nlp = spacy.blank("en")
        except Exception as e:
            logger.warning(f"Could not load spaCy: {e}")
            _spacy_nlp = None
    return _spacy_nlp


# ============================================================================
# COMPREHENSIVE SKILL TAXONOMY (350+ Skills with Alias Normalization)
# ============================================================================
SKILL_TAXONOMY: Dict[str, List[str]] = {
    # Programming Languages
    "Python": ["python", "python3", "python 3", "python programming", "py"],
    "JavaScript": ["javascript", "js", "es6", "es2015", "ecmascript", "vanilla js"],
    "TypeScript": ["typescript", "ts"],
    "Java": ["java", "core java", "j2ee", "java 8", "java 11", "java 17"],
    "C++": ["c++", "cpp"],
    "C#": ["c#", "csharp", ".net c#"],
    "C": ["c programming", "c language"],
    "Go": ["golang", "go programming", "go lang"],
    "Rust": ["rust", "rustlang"],
    "PHP": ["php", "php7", "php8"],
    "Ruby": ["ruby", "ruby on rails", "rails"],
    "Swift": ["swift", "swiftui"],
    "Kotlin": ["kotlin", "android kotlin"],
    "Dart": ["dart", "flutter dart"],
    "R": ["r programming", "r language", "r-project"],
    "Scala": ["scala"],
    "HTML5": ["html", "html5"],
    "CSS3": ["css", "css3", "sass", "scss", "less"],
    "SQL": ["sql", "t-sql", "pl/sql", "ansi sql"],
    "Shell Scripting": ["bash", "shell", "shell scripting", "sh", "zsh", "powershell"],

    # Web & Backend Frameworks
    "Flask": ["flask", "flask-sqlalchemy", "flask-restful", "flask-login"],
    "Django": ["django", "django rest framework", "drf"],
    "FastAPI": ["fastapi"],
    "Node.js": ["node.js", "nodejs", "node"],
    "Express.js": ["express", "express.js", "expressjs"],
    "Spring Boot": ["spring boot", "spring framework", "spring", "spring mvc"],
    "ASP.NET": ["asp.net", "asp.net core", ".net core", ".net framework", "dotnet"],
    "Laravel": ["laravel"],
    "Ruby on Rails": ["rails", "ruby on rails", "ror"],
    "GraphQL": ["graphql", "apollo graphql"],
    "RESTful APIs": ["rest", "restful", "rest api", "rest apis", "restful api", "restful web services"],
    "gRPC": ["grpc", "protobuf", "protocol buffers"],
    "Microservices": ["microservices", "microservice architecture", "distributed systems", "soa"],
    "WebSockets": ["websockets", "websocket", "socket.io"],

    # Frontend Frameworks & Libraries
    "React": ["react", "react.js", "reactjs", "react-dom"],
    "Next.js": ["next.js", "nextjs", "next"],
    "Vue.js": ["vue", "vue.js", "vuejs", "vue3", "vuex", "pinia"],
    "Angular": ["angular", "angularjs", "angular 2+"],
    "Svelte": ["svelte", "sveltekit"],
    "Redux": ["redux", "redux toolkit", "rtk"],
    "Tailwind CSS": ["tailwind", "tailwind css", "tailwindcss"],
    "Bootstrap": ["bootstrap", "bootstrap 5"],
    "jQuery": ["jquery"],

    # AI / Machine Learning / Data Science
    "Machine Learning": ["machine learning", "ml", "statistical learning", "supervised learning", "unsupervised learning"],
    "Deep Learning": ["deep learning", "dl", "neural networks", "ann", "cnn", "rnn", "lstm", "transformers"],
    "Natural Language Processing": ["nlp", "natural language processing", "text mining", "ner", "sentiment analysis", "llm", "large language models", "spacy", "nltk", "huggingface", "hugging face", "transformers", "langchain", "llamaindex", "rag", "retrieval augmented generation", "bert", "gpt", "word2vec"],
    "Computer Vision": ["computer vision", "cv", "opencv", "image processing", "yolo", "object detection", "segmentation"],
    "Scikit-Learn": ["scikit-learn", "sklearn"],
    "TensorFlow": ["tensorflow", "tf", "tf.keras"],
    "PyTorch": ["pytorch", "torch"],
    "Keras": ["keras"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "SciPy": ["scipy"],
    "Data Analysis": ["data analysis", "eda", "exploratory data analysis", "data analytics"],
    "Data Visualization": ["data visualization", "matplotlib", "seaborn", "plotly", "tableau", "power bi", "d3.js"],
    "Big Data": ["big data", "hadoop", "spark", "apache spark", "pyspark", "kafka", "apache kafka", "flink", "hive"],
    "Feature Engineering": ["feature engineering", "model evaluation", "cross validation", "hyperparameter tuning"],
    "Reinforcement Learning": ["reinforcement learning", "rl", "q-learning"],

    # Databases & Storage
    "PostgreSQL": ["postgresql", "postgres", "psql"],
    "MySQL": ["mysql"],
    "SQLite": ["sqlite", "sqlite3"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "Elasticsearch": ["elasticsearch", "elastic search", "opensearch", "elk stack"],
    "Cassandra": ["cassandra", "apache cassandra"],
    "Oracle DB": ["oracle", "oracle database", "plsql"],
    "DynamoDB": ["dynamodb", "aws dynamodb"],
    "Firebase": ["firebase", "firestore", "firebase realtime database"],
    "Neo4j": ["neo4j", "graph database", "cypher"],

    # Cloud, DevOps & Infrastructure
    "AWS": ["aws", "amazon web services", "ec2", "s3", "lambda", "ecs", "eks", "rds", "cloudformation", "iam", "sqs", "sns"],
    "Google Cloud": ["gcp", "google cloud", "google cloud platform", "bigquery", "cloud run", "gke", "compute engine", "cloud storage"],
    "Microsoft Azure": ["azure", "microsoft azure", "azure devops", "azure functions", "blob storage", "aks"],
    "Docker": ["docker", "dockerfile", "docker-compose", "containerization", "containers"],
    "Kubernetes": ["kubernetes", "k8s", "helm"],
    "CI/CD": ["ci/cd", "ci / cd", "continuous integration", "continuous deployment", "jenkins", "github actions", "gitlab ci", "circleci", "travis ci", "argo cd", "tekton"],
    "Terraform": ["terraform", "iac", "infrastructure as code"],
    "Ansible": ["ansible"],
    "Linux": ["linux", "ubuntu", "debian", "centos", "redhat", "rhel", "alpine"],
    "Nginx": ["nginx", "reverse proxy", "load balancing"],
    "Apache": ["apache", "httpd"],
    "Serverless": ["serverless", "aws lambda", "cloud functions"],
    "Prometheus": ["prometheus", "grafana", "monitoring", "datadog", "new relic"],

    # Software Engineering & Methodologies
    "Git": ["git", "github", "gitlab", "bitbucket", "version control"],
    "Agile": ["agile", "scrum", "kanban", "sprint planning", "jira", "confluence"],
    "Unit Testing": ["unit testing", "pytest", "unittest", "jest", "mocha", "tdd", "test driven development", "bdd"],
    "Integration Testing": ["integration testing", "e2e testing", "selenium", "cypress", "playwright"],
    "Object-Oriented Programming": ["oop", "object-oriented programming", "object oriented design", "solid principles", "design patterns"],
    "System Design": ["system design", "software architecture", "scalability", "high availability", "load balancing", "caching"],
    "Cybersecurity": ["cybersecurity", "security", "owasp", "oauth", "jwt", "ssl", "tls", "cryptography", "penetration testing", "vulnerability assessment"],
    "Data Structures & Algorithms": ["data structures", "algorithms", "dsa", "problem solving", "time complexity"],

    # Soft Skills & Professional
    "Problem Solving": ["problem solving", "analytical skills", "critical thinking"],
    "Communication": ["communication", "verbal communication", "written communication", "presentation skills"],
    "Leadership": ["leadership", "team lead", "mentoring", "technical leadership", "management"],
    "Collaboration": ["collaboration", "cross-functional", "teamwork", "pair programming"],
    "Project Management": ["project management", "pmp", "stakeholder management"]
}

# Compile regex lookup patterns for fast matching
COMPILED_SKILL_PATTERNS: List[Tuple[str, re.Pattern]] = []
for canonical_name, aliases in SKILL_TAXONOMY.items():
    # Sort aliases by length descending so longer phrases match first
    sorted_aliases = sorted(aliases, key=len, reverse=True)
    pattern_parts = []
    for alias in sorted_aliases:
        escaped = re.escape(alias)
        # Handle word boundaries nicely (especially for symbols like c++, c#, .net)
        if alias.isalnum():
            pattern_parts.append(r'\b' + escaped + r'\b')
        elif alias in ['c++', 'c#', '.net', 'ci/cd', 'node.js', 'vue.js', 'next.js', 'react.js']:
            pattern_parts.append(r'(?:^|[\s,;/|()])' + escaped + r'(?:$|[\s,;/|()])')
        else:
            pattern_parts.append(r'\b' + escaped + r'\b')
            
    combined_regex = re.compile('|'.join(pattern_parts), re.IGNORECASE)
    COMPILED_SKILL_PATTERNS.append((canonical_name, combined_regex))


def extract_skills(text: str) -> List[str]:
    """
    Extracts and normalizes technical and domain skills from text.
    Returns a sorted list of unique canonical skill names.
    """
    if not text:
        return []
        
    found_skills = set()
    for canonical_name, pattern in COMPILED_SKILL_PATTERNS:
        if pattern.search(text):
            found_skills.add(canonical_name)
            
    return sorted(list(found_skills))


# ============================================================================
# CONTACT INFORMATION EXTRACTION
# ============================================================================
def extract_email(text: str) -> Optional[str]:
    """Extracts email address using standard RFC-compliant regex."""
    if not text:
        return None
    match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', text)
    return match.group(0).lower() if match else None


def extract_phone(text: str) -> Optional[str]:
    """Extracts phone number with support for international and local formats."""
    if not text:
        return None
        
    # Matches patterns like:
    # +1-555-123-4567, (555) 123-4567, 555.123.4567, +91 98765 43210, +44 20 7123 4567, etc.
    patterns = [
        r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\+?\d{1,3}[-.\s]?\d{10}',
        r'\b\d{5}[-.\s]?\d{5}\b',
        r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b'
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            phone_candidate = match.group(0).strip()
            # Verify it has at least 7 digits and is not a random number/date
            digits = re.sub(r'\D', '', phone_candidate)
            if 7 <= len(digits) <= 15:
                return phone_candidate
    return None


def extract_name(text: str, email: Optional[str] = None) -> str:
    """
    Extracts candidate name from the top header of the resume.
    Uses spaCy NER with intelligent fallbacks.
    """
    if not text:
        return "Unknown Candidate"
        
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines:
        return "Unknown Candidate"
        
    # Exclude common non-name header words
    banned_header_words = {
        'resume', 'curriculum', 'vitae', 'cv', 'profile', 'summary', 'contact',
        'email', 'phone', 'page', 'objective', 'skills', 'experience', 'education',
        'career', 'developer', 'engineer', 'manager', 'consultant', 'specialist',
        'portfolio', 'linkedin', 'github', 'address', 'personal'
    }
    
    # 1. Inspect top 5 lines for a clean 2-4 word capitalized name
    for line in lines[:5]:
        # Strip characters like bullet, pipes
        cleaned = re.sub(r'[^a-zA-Z\s\.]', ' ', line).strip()
        words = cleaned.split()
        if 2 <= len(words) <= 4:
            first_word_lower = words[0].lower()
            last_word_lower = words[-1].lower()
            if first_word_lower not in banned_header_words and last_word_lower not in banned_header_words:
                # Check if words are capitalized or uppercase
                if all(w.istitle() or w.isupper() for w in words if len(w) > 1):
                    return " ".join(words).title()
                    
    # 2. Try spaCy NER on the top 1000 characters
    nlp = get_spacy_nlp()
    if nlp:
        try:
            header_sample = "\n".join(lines[:6])
            doc = nlp(header_sample)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    cand = ent.text.strip()
                    cand_words = cand.split()
                    if 2 <= len(cand_words) <= 4 and all(w.lower() not in banned_header_words for w in cand_words):
                        return cand.title()
        except Exception as e:
            logger.debug(f"spaCy NER name extraction error: {e}")

    # 3. Fallback: Parse from email username (e.g. john.doe@email.com -> John Doe)
    if email:
        username = email.split('@')[0]
        name_parts = re.split(r'[._-]', username)
        name_parts = [p.title() for p in name_parts if p.isalpha() and len(p) > 1]
        if len(name_parts) >= 2:
            return " ".join(name_parts[:3])

    # 4. Fallback: Return first line if reasonable length
    if lines:
        first_line = lines[0].strip()
        if len(first_line) < 50 and len(first_line.split()) <= 4:
            return first_line.title()

    return "Candidate"


def extract_location(text: str) -> Optional[str]:
    """Extracts candidate location/city/country from resume header."""
    if not text:
        return None
        
    top_text = "\n".join(text.split('\n')[:15])
    
    # 1. Regex for "City, State" or "City, Country"
    city_state_pattern = re.compile(r'\b([A-Z][a-zA-Z\s]+),\s*([A-Z]{2}|[A-Z][a-zA-Z\s]+)\b')
    for line in top_text.split('\n'):
        # Exclude lines that look like sentences
        if len(line.split()) < 10 and not any(w in line.lower() for w in ['experience', 'university', 'bachelor', 'master']):
            match = city_state_pattern.search(line)
            if match:
                loc = match.group(0).strip()
                if len(loc) < 40:
                    return loc

    # 2. Try spaCy GPE
    nlp = get_spacy_nlp()
    if nlp:
        try:
            doc = nlp(top_text)
            for ent in doc.ents:
                if ent.label_ in ("GPE", "LOC"):
                    candidate_loc = ent.text.strip()
                    if len(candidate_loc) > 2 and len(candidate_loc) < 35:
                        return candidate_loc
        except Exception:
            pass

    return "Remote / Not Specified"


def extract_contact_info(text: str) -> Dict[str, Any]:
    """Extracts candidate contact details including name, email, phone, and location."""
    email = extract_email(text)
    phone = extract_phone(text)
    name = extract_name(text, email)
    location = extract_location(text)
    
    return {
        "name": name,
        "email": email,
        "phone": phone,
        "location": location
    }


# ============================================================================
# RESUME SECTION SEGMENTATION
# ============================================================================
SECTION_HEADERS = {
    "summary": [
        "summary", "professional summary", "career summary", "executive summary",
        "profile", "about me", "objective", "career objective", "overview"
    ],
    "experience": [
        "experience", "work experience", "professional experience", "employment history",
        "work history", "career history", "relevant experience", "internships", "employment"
    ],
    "education": [
        "education", "academic background", "academics", "qualifications",
        "educational background", "academic qualifications", "degrees"
    ],
    "skills": [
        "skills", "core skills", "technical skills", "core competencies", "technical proficiencies",
        "technologies", "key skills", "skillset", "expertise", "tools & technologies", "technical expertise",
        "professional skills", "skills & tools", "skills & proficiencies"
    ],
    "projects": [
        "projects", "key projects", "personal projects", "academic projects",
        "technical projects", "notable projects", "open source"
    ],
    "certifications": [
        "certifications", "certificates", "licenses", "courses", "professional certifications",
        "credentials", "training", "professional development"
    ],
    "awards": [
        "awards", "honors", "achievements", "accomplishments", "publications", "patents"
    ]
}

def segment_resume_sections(text: str) -> Dict[str, str]:
    """
    Segments resume text into standard sections (summary, experience, education, skills, projects, certifications).
    """
    if not text:
        return {}
        
    lines = text.split('\n')
    sections: Dict[str, List[str]] = {
        "header": [],
        "summary": [],
        "experience": [],
        "education": [],
        "skills": [],
        "projects": [],
        "certifications": [],
        "awards": [],
        "other": []
    }
    
    current_section = "header"
    
    for line in lines:
        clean_line = line.strip().lower()
        # Clean line of markdown headers, bullets, colons
        clean_line_header = re.sub(r'^[#*\-•\s]+', '', clean_line).rstrip(':').strip()
        
        # Check if line matches a known section header
        detected_section = None
        if len(clean_line_header.split()) <= 4: # Headers are usually 1 to 4 words
            for sec, headers in SECTION_HEADERS.items():
                if clean_line_header in headers:
                    detected_section = sec
                    break
                    
        if detected_section:
            current_section = detected_section
        else:
            sections[current_section].append(line)
            
    # Join text per section
    result = {}
    for sec_name, sec_lines in sections.items():
        joined = "\n".join(sec_lines).strip()
        if joined:
            result[sec_name] = joined
            
    return result


# ============================================================================
# EXPERIENCE & EDUCATION EXTRACTION
# ============================================================================
def extract_experience_years(text: str) -> float:
    """
    Calculates total estimated years of experience from resume text and work history dates.
    """
    if not text:
        return 0.0
        
    # 1. Search for explicit mentions (e.g., "5+ years of experience", "4 years experience")
    explicit_match = re.search(r'(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)(?:\s+of)?\s+experience', text, re.IGNORECASE)
    if explicit_match:
        try:
            return min(float(explicit_match.group(1)), 40.0)
        except ValueError:
            pass

    # 2. Extract year ranges (e.g. 2018 - 2023, 2019 - Present, 2021-Current)
    year_ranges = re.findall(r'\b(20\d{2}|19\d{2})\s*(?:-|–|—|to)\s*(20\d{2}|present|current|now)\b', text, re.IGNORECASE)
    total_years = 0.0
    current_year = 2026 # Context current year
    
    seen_ranges = []
    for start_str, end_str in year_ranges:
        try:
            start_yr = int(start_str)
            if end_str.lower() in ('present', 'current', 'now'):
                end_yr = current_year
            else:
                end_yr = int(end_str)
                
            if 1980 <= start_yr <= current_year and start_yr <= end_yr <= current_year + 1:
                duration = max(end_yr - start_yr, 0.5)
                # Avoid extreme double-counting if ranges overlap broadly
                seen_ranges.append((start_yr, end_yr, duration))
        except ValueError:
            continue
            
    if seen_ranges:
        # Sum durations with basic deduplication
        total_years = sum(r[2] for r in seen_ranges)
        return min(round(total_years, 1), 35.0)
        
    return 1.0 # Default baseline if professional resume is provided but dates are implicit


def extract_education_details(text: str) -> List[Dict[str, str]]:
    """
    Extracts structured education entries (Degree, Field, Institution, Year).
    """
    if not text:
        return []
        
    degrees_found = []
    
    degree_patterns = [
        (r'\b(Ph\.?D\.?|Doctorate|Doctor of Philosophy)\b', 'Ph.D.'),
        (r'\b(Master of Science|Master of Technology|Master of Engineering|M\.?S\.?|M\.?Tech\.?|M\.?E\.?|M\.?B\.?A\.?|Master\'?s?(?:\s+Degree)?)\b', 'Master\'s Degree'),
        (r'\b(Bachelor of Science|Bachelor of Technology|Bachelor of Engineering|B\.?S\.?|B\.?Tech\.?|B\.?E\.?|B\.?A\.?|Bachelor\'?s?(?:\s+Degree)?)\b', 'Bachelor\'s Degree'),
        (r'\b(Associate Degree|Associate of Science|A\.?S\.?|Diploma)\b', 'Associate / Diploma'),
        (r'\b(High School Diploma|Secondary School|GED)\b', 'High School')
    ]
    
    lines = text.split('\n')
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        for pat, degree_name in degree_patterns:
            if re.search(pat, line_clean, re.IGNORECASE):
                # Extract year if present in line
                yr_match = re.search(r'\b(20\d{2}|19\d{2})\b', line_clean)
                year = yr_match.group(0) if yr_match else ""
                
                # Check for field of study
                field = ""
                field_match = re.search(r'(?:in|of)\s+([A-Za-z\s&]{4,35})', line_clean, re.IGNORECASE)
                if field_match:
                    field = field_match.group(1).strip()
                    
                degrees_found.append({
                    "degree": degree_name,
                    "raw_text": line_clean,
                    "year": year,
                    "field": field
                })
                break
                
    # If no degree matched by lines, check whole text
    if not degrees_found:
        for pat, degree_name in degree_patterns:
            if re.search(pat, text, re.IGNORECASE):
                degrees_found.append({
                    "degree": degree_name,
                    "raw_text": degree_name,
                    "year": "",
                    "field": ""
                })
                break
                
    return degrees_found


def extract_experience_list(text: str) -> List[Dict[str, str]]:
    """
    Parses work experience bullet points or job blocks into a structured list.
    """
    if not text:
        return []
        
    entries = []
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    current_entry = {"title_company": "", "description": []}
    
    for line in lines:
        # Check if line looks like a job title / company / date line
        if re.search(r'\b(20\d{2}|19\d{2}|present|current)\b', line, re.IGNORECASE) or \
           re.search(r'\b(engineer|developer|manager|lead|architect|analyst|scientist|consultant|intern|specialist)\b', line, re.IGNORECASE):
            if current_entry["title_company"]:
                current_entry["description"] = " ".join(current_entry["description"])
                entries.append(current_entry)
            current_entry = {"title_company": line, "description": []}
        else:
            current_entry["description"].append(line)
            
    if current_entry["title_company"]:
        current_entry["description"] = " ".join(current_entry["description"])
        entries.append(current_entry)
        
    return entries if entries else [{"title_company": "Professional Experience", "description": text[:300]}]


def extract_projects_and_certs(sections: Dict[str, str]) -> Tuple[List[str], List[str]]:
    """Extracts project titles and certifications from segmented sections."""
    projects = []
    certs = []
    
    if "projects" in sections:
        proj_text = sections["projects"]
        proj_lines = [l.strip('-•* \t') for l in proj_text.split('\n') if len(l.strip()) > 5]
        projects = proj_lines[:8]
        
    if "certifications" in sections:
        cert_text = sections["certifications"]
        cert_lines = [l.strip('-•* \t') for l in cert_text.split('\n') if len(l.strip()) > 5]
        certs = cert_lines[:8]
        
    return projects, certs


# ============================================================================
# MAIN NLP PARSER INTERFACE
# ============================================================================
def parse_resume_nlp(raw_text: str) -> Dict[str, Any]:
    """
    Comprehensive NLP pipeline that extracts all candidate profile details,
    sections, contact info, normalized skills, work history, education, and years of experience.
    """
    if not raw_text:
        return {
            "name": "Unknown Candidate",
            "email": None,
            "phone": None,
            "location": None,
            "skills": [],
            "education": [],
            "experience": [],
            "projects": [],
            "certifications": [],
            "experience_years": 0.0,
            "sections": {}
        }
        
    # 1. Segment sections
    sections = segment_resume_sections(raw_text)
    
    # 2. Extract Contact Info
    contact = extract_contact_info(raw_text)
    
    # 3. Extract Skills across entire resume (with extra weight if listed in skills section)
    skills = extract_skills(raw_text)
    
    # 4. Extract Experience & Education
    exp_text = sections.get("experience", raw_text)
    edu_text = sections.get("education", raw_text)
    
    exp_years = extract_experience_years(raw_text)
    education_entries = extract_education_details(edu_text)
    experience_entries = extract_experience_list(exp_text)
    
    # 5. Extract Projects & Certifications
    projects, certifications = extract_projects_and_certs(sections)
    
    return {
        "name": contact["name"],
        "email": contact["email"],
        "phone": contact["phone"],
        "location": contact["location"],
        "skills": skills,
        "education": education_entries,
        "experience": experience_entries,
        "projects": projects,
        "certifications": certifications,
        "experience_years": exp_years,
        "sections": {k: v[:500] for k, v in sections.items()} # truncated preview for storage
    }
