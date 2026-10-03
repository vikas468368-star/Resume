import os
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app import create_app, db
from app.models import User, JobDescription, Resume, Screening
from app.services.ranking import process_and_screen_resume, rank_candidates_for_job

def seed_database():
    app = create_app('development')
    with app.app_context():
        print("[INFO] Recreating database tables...")
        db.drop_all()
        db.create_all()

        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)

        # 1. Create Users
        print("[INFO] Creating Admin and Recruiter users...")
        admin = User(
            name="Alex Sterling (Admin)",
            email="admin@resumescreen.ai",
            role="admin"
        )
        admin.set_password("Admin@123")

        recruiter = User(
            name="Sarah Jenkins (Lead Recruiter)",
            email="recruiter@resumescreen.ai",
            role="recruiter"
        )
        recruiter.set_password("Recruiter@123")

        db.session.add_all([admin, recruiter])
        db.session.commit()

        # 2. Create Job Descriptions
        print("[INFO] Creating realistic Job Descriptions...")
        job1 = JobDescription(
            title="Senior Full-Stack Python Engineer",
            department="Engineering",
            location="Remote",
            experience_level="Senior",
            min_experience_years=4.0,
            min_education="Bachelor",
            description_text="""We are seeking a high-performing Senior Full-Stack Python Engineer to design, scale, and maintain our enterprise SaaS platforms.

Key Responsibilities:
- Architect high-throughput backend services using Python, Flask, and PostgreSQL.
- Build clean, responsive frontend web user interfaces with JavaScript and modern component patterns.
- Design and integrate robust RESTful APIs, OpenAPI specifications, and third-party webhooks.
- Containerize microservices with Docker and deploy to AWS cloud infrastructure.
- Implement automated testing with pytest and integrate into CI/CD pipelines.

Requirements:
- 4+ years of professional backend engineering experience with Python and Flask or Django.
- Strong proficiency with PostgreSQL, complex SQL query tuning, and database modeling.
- Solid understanding of Docker, Git version control, and RESTful APIs.
- Bachelor's degree in Computer Science, Software Engineering, or related technical discipline.

Nice to have / Preferred:
- Experience with AWS (EC2, S3, RDS, Lambda), Redis caching, and Celery task queues.
- Familiarity with React, TypeScript, and CI/CD pipelines (GitHub Actions).""",
            required_skills=["Python", "Flask", "PostgreSQL", "Docker", "RESTful APIs", "Git"],
            preferred_skills=["AWS", "Redis", "React", "CI/CD", "TypeScript"],
            created_by_user_id=recruiter.id,
            status="active"
        )

        job2 = JobDescription(
            title="Lead AI / NLP Research Engineer",
            department="Artificial Intelligence",
            location="San Francisco, CA / Hybrid",
            experience_level="Lead / Principal",
            min_experience_years=5.0,
            min_education="Master",
            description_text="""We are looking for a Lead AI / NLP Research Engineer to spearhead our machine learning and natural language processing roadmap.

Key Responsibilities:
- Develop production-grade NLP models for information extraction, named entity recognition (NER), and semantic document similarity.
- Fine-tune modern transformers, large language models (LLMs), and embeddings using PyTorch and Hugging Face.
- Build statistical machine learning pipelines with Scikit-Learn, Pandas, and NumPy.
- Deploy scalable low-latency model inference microservices in Docker and AWS.

Requirements:
- 5+ years of hands-on Machine Learning and Natural Language Processing experience.
- Deep expertise in Python, PyTorch or TensorFlow, Scikit-Learn, spaCy, and Pandas.
- Master's or Ph.D. degree in Computer Science, Data Science, or AI/ML.
- Experience with text mining, tokenization, TF-IDF, embeddings, and vector similarity search.

Preferred / Bonus:
- Experience with LangChain, RAG architectures, transformers (BERT/GPT), and AWS SageMaker.""",
            required_skills=["Python", "Machine Learning", "Natural Language Processing", "PyTorch", "Scikit-Learn", "Pandas", "NumPy"],
            preferred_skills=["Deep Learning", "TensorFlow", "AWS", "Docker", "Git"],
            created_by_user_id=recruiter.id,
            status="active"
        )

        job3 = JobDescription(
            title="Senior Frontend React Developer",
            department="Product Design & UI",
            location="New York, NY / Remote",
            experience_level="Senior",
            min_experience_years=3.5,
            min_education="Bachelor",
            description_text="""We are looking for a creative, detail-oriented Senior Frontend React Developer to build responsive, accessible, and stunning user interfaces.

Responsibilities:
- Build state-of-the-art web dashboards using React, TypeScript, HTML5, and modern CSS3 design systems.
- Manage complex clientside state with Redux Toolkit and optimize rendering performance.
- Collaborate closely with UI/UX designers to implement pixel-perfect glassmorphism and animations.
- Integrate with backend RESTful APIs and real-time WebSockets.

Requirements:
- 3+ years of frontend development experience with JavaScript (ES6+), TypeScript, and React.
- Mastery of HTML5, CSS3, responsive layouts, flexbox, and grid.
- Experience with RESTful APIs, Git, and unit testing with Jest.
- Bachelor's degree in Computer Science or equivalent practical experience.

Nice to have:
- Experience with Next.js, Tailwind CSS, Chart.js, and WebSockets.""",
            required_skills=["JavaScript", "TypeScript", "React", "HTML5", "CSS3", "Redux", "RESTful APIs"],
            preferred_skills=["Next.js", "Tailwind CSS", "WebSockets", "Git", "Unit Testing"],
            created_by_user_id=recruiter.id,
            status="active"
        )

        job4 = JobDescription(
            title="Cloud DevOps & Infrastructure Architect",
            department="Infrastructure & Reliability",
            location="Austin, TX / Remote",
            experience_level="Senior",
            min_experience_years=5.0,
            min_education="Bachelor",
            description_text="""Join our infrastructure team as a Cloud DevOps Architect to oversee cloud reliability, automated deployments, and security posture.

Responsibilities:
- Design and maintain highly available Kubernetes clusters and Dockerized workloads on AWS.
- Automate cloud infrastructure using Terraform (Infrastructure as Code) and Ansible.
- Build reliable CI/CD pipelines with GitHub Actions, Jenkins, and automated testing gates.
- Monitor system performance, alerts, and logs with Prometheus and Grafana.

Requirements:
- 5+ years of experience in DevOps, Cloud Engineering, or SRE roles.
- Expert-level knowledge of AWS, Docker, Kubernetes, and Terraform.
- Strong Linux systems administration and Bash / Shell Scripting skills.
- Hands-on experience with CI/CD and Git.

Preferred:
- Experience with Prometheus, Grafana, Python automation scripting, and Google Cloud Platform.""",
            required_skills=["AWS", "Docker", "Kubernetes", "Terraform", "CI/CD", "Linux", "Shell Scripting"],
            preferred_skills=["Prometheus", "Ansible", "Python", "Google Cloud", "Git"],
            created_by_user_id=admin.id,
            status="active"
        )

        db.session.add_all([job1, job2, job3, job4])
        db.session.commit()

        # 3. Create Sample Resumes with Rich Content
        print("[INFO] Creating candidate resume files and executing real screening algorithms...")
        
        sample_candidates = [
            # Job 1: Python Full-Stack (High match)
            {
                "job": job1,
                "file_name": "Marcus_Vance_Python_Lead.docx",
                "text": """Marcus Vance
Email: marcus.vance@techlead.io | Phone: (415) 890-2341 | Location: San Francisco, CA | LinkedIn: linkedin.com/in/marcusvance

PROFESSIONAL SUMMARY
Results-driven Senior Full-Stack Python Engineer with 6 years of experience architecting cloud-native microservices, RESTful APIs, and responsive web applications. Demonstrated track record in database optimization with PostgreSQL and container orchestration with Docker.

TECHNICAL SKILLS
- Programming Languages: Python, JavaScript, TypeScript, SQL, Bash
- Frameworks: Flask, Django, FastAPI, React, Node.js
- Databases: PostgreSQL, Redis, SQLite, MongoDB
- Cloud & DevOps: Docker, AWS (EC2, S3, RDS, Lambda), CI/CD, Git, GitHub Actions
- Methodologies: Agile, Scrum, Unit Testing (pytest), RESTful APIs, Microservices

WORK EXPERIENCE
Senior Backend Engineer | CloudScale Technologies (2021 - Present)
- Engineered scalable backend microservices using Python and Flask serving 2.5M daily requests.
- Optimized complex PostgreSQL queries and indexing strategies, reducing latency by 42%.
- Designed and documented 30+ RESTful APIs with OpenAPI/Swagger.
- Built automated CI/CD deployment pipelines using Docker and AWS ECS.

Full-Stack Developer | Nexus Innovations (2018 - 2021)
- Developed customer-facing web portals with Python, Flask, and React.
- Managed relational schema migrations and database reliability with PostgreSQL.
- Implemented unit testing suite with pytest achieving 94% code coverage.

EDUCATION
Bachelor of Science in Computer Science
University of California, Berkeley (2014 - 2018)

PROJECTS & CERTIFICATIONS
- Distributed Task Orchestrator: Open-source task queue built in Python with Redis.
- AWS Certified Solutions Architect - Associate (2022)"""
            },
            # Job 1: Python Full-Stack (Good match, minor missing skills)
            {
                "job": job1,
                "file_name": "Elena_Rostova_Python_Dev.pdf",
                "text": """Elena Rostova
Email: elena.rostova@developer.net | Phone: +1-206-555-0192 | Location: Seattle, WA | GitHub: github.com/erostova

CAREER OBJECTIVE
Passionate Software Engineer with 4 years of experience specializing in Python backend systems, database modeling, and automated workflows.

CORE COMPETENCIES
- Core Skills: Python, Flask, PostgreSQL, RESTful APIs, Git, Linux
- Databases & Tools: SQL, MySQL, Redis, Postman, pytest
- Concepts: Object-Oriented Programming, MVC, Agile, Unit Testing

EMPLOYMENT HISTORY
Software Engineer | AlphaSoft Corp (2020 - Present)
- Built enterprise RESTful APIs using Python and Flask integrated with PostgreSQL databases.
- Implemented secure JWT authentication and role-based access control.
- Authored comprehensive test suites using pytest and unittest.

Junior Python Developer | DataFlow Systems (2019 - 2020)
- Developed backend data extraction scripts and database integrations.
- Collaborated in an Agile Scrum team using Git for version control.

EDUCATION
Bachelor of Science in Software Engineering
University of Washington (2015 - 2019)"""
            },
            # Job 1: Moderate Match (Missing PostgreSQL & Docker)
            {
                "job": job1,
                "file_name": "David_Kim_Backend.docx",
                "text": """David Kim
Email: dkim@codelabs.org | Phone: (312) 555-7821 | Location: Chicago, IL

SUMMARY
Backend Developer with 3 years of experience writing web APIs in Python and Django.

SKILLS
Python, Django, MySQL, SQLite, JavaScript, HTML5, CSS3, Git, RESTful APIs

EXPERIENCE
Django Developer | Prairie Software (2021 - Present)
- Built web applications and internal tools using Python and Django.
- Interfaced with MySQL databases and wrote custom ORM queries.
- Created REST APIs for mobile applications.

EDUCATION
Bachelor of Arts in Computer Science
University of Illinois (2017 - 2021)"""
            },
            # Job 2: AI / NLP Specialist (Exceptional Match)
            {
                "job": job2,
                "file_name": "Dr_Aria_Montgomery_AI_NLP.pdf",
                "text": """Dr. Aria Montgomery
Email: aria.montgomery@ai-research.org | Phone: (650) 442-9918 | Location: Palo Alto, CA | LinkedIn: linkedin.com/in/ariamontgomery

PROFESSIONAL SUMMARY
Lead AI & NLP Scientist with 7 years of post-graduate experience building state-of-the-art machine learning models, transformer architectures, and semantic information extraction systems. Published researcher in natural language processing and computer vision.

CORE EXPERTISE
- AI & NLP: Natural Language Processing, Machine Learning, Deep Learning, Transformers, BERT, spaCy, NLTK, NER, LLM, RAG
- Frameworks & Libraries: PyTorch, Scikit-Learn, TensorFlow, Pandas, NumPy, SciPy
- Programming: Python, C++, SQL, Shell Scripting
- Cloud & Engineering: AWS, Docker, Git, RESTful APIs, MLflow

PROFESSIONAL EXPERIENCE
Lead NLP Research Scientist | DeepMind Innovations (2021 - Present)
- Led a team of 6 ML engineers developing proprietary NLP document classification and entity extraction engines.
- Fine-tuned transformer models using PyTorch, improving domain extraction accuracy by 28%.
- Built end-to-end Machine Learning data pipelines using Pandas, NumPy, and Scikit-Learn.
- Deployed real-time inference microservices with Docker and AWS SageMaker.

Senior Machine Learning Engineer | Vector AI Labs (2018 - 2021)
- Developed text summarization and TF-IDF similarity algorithms for enterprise knowledge bases.
- Conducted deep learning experiments with PyTorch and Scikit-Learn.

EDUCATION
Ph.D. in Computer Science (Artificial Intelligence & NLP)
Stanford University (2014 - 2018)

Master of Science in Data Science
Carnegie Mellon University (2012 - 2014)

SELECTED PUBLICATIONS & AWARDS
- Montgomery et al., "Hierarchical Attention Transformers for Clinical Entity Resolution", ACL 2020.
- Best Paper Award, EMNLP 2019."""
            },
            # Job 2: AI / NLP (Good Match)
            {
                "job": job2,
                "file_name": "Julian_Cross_ML_Engineer.docx",
                "text": """Julian Cross
Email: julian.cross@mlhub.io | Phone: (512) 670-3341 | Location: Austin, TX

SUMMARY
Senior Machine Learning Engineer with 5 years of experience building predictive models, data analysis pipelines, and NLP applications.

SKILLS
Python, Machine Learning, Scikit-Learn, Pandas, NumPy, Natural Language Processing, PyTorch, SQL, Docker, Git, Data Visualization

WORK HISTORY
Machine Learning Engineer | Cognitive Solutions (2020 - Present)
- Trained classification and regression models with Scikit-Learn and PyTorch.
- Analyzed large unstructured datasets using Pandas and NumPy.
- Built NLP text parsing pipelines with spaCy for resume and contract screening.

Data Scientist | Apex Analytics (2018 - 2020)
- Executed exploratory data analysis and feature engineering.
- Deployed ML models into production using Docker and Flask APIs.

EDUCATION
Master of Science in Computer Science
University of Texas at Austin (2016 - 2018)

Bachelor of Science in Mathematics
Texas A&M University (2012 - 2016)"""
            },
            # Job 3: Senior Frontend React (Exceptional Match)
            {
                "job": job3,
                "file_name": "Chloe_Zhang_Frontend_Lead.pdf",
                "text": """Chloe Zhang
Email: chloe.zhang@reactui.dev | Phone: (917) 555-8821 | Location: New York, NY | Portfolio: chloezhang.dev

PROFESSIONAL SUMMARY
Senior Frontend React Engineer with 5 years of experience crafting high-performance, accessible web applications. Expert in TypeScript, React, modern state management with Redux, and responsive CSS3 architecture.

TECHNICAL SKILLS
- Frontend Core: JavaScript (ES6+), TypeScript, React, HTML5, CSS3, Next.js
- State & Data: Redux, Redux Toolkit, Context API, RESTful APIs, WebSockets, GraphQL
- Styling: Tailwind CSS, CSS Modules, Styled Components, Bootstrap, Figma to Code
- Quality & Testing: Jest, React Testing Library, Cypress, Unit Testing, Git

WORK EXPERIENCE
Lead Frontend Engineer | FinTech UI Studio (2021 - Present)
- Architected enterprise trading dashboard using React, TypeScript, and Redux Toolkit.
- Integrated real-time WebSockets feeds for streaming financial data.
- Built reusable modern design system component library in TypeScript.
- Ensured 100% responsive design across desktop, tablet, and mobile form factors.

Frontend Developer | PixelCraft Media (2019 - 2021)
- Developed responsive single-page web applications with React, JavaScript, and HTML5/CSS3.
- Integrated RESTful APIs and managed asynchronous data flows.
- Authored unit tests with Jest achieving 90%+ branch coverage.

EDUCATION
Bachelor of Science in Computer Science & Interactive Media
New York University (2015 - 2019)"""
            },
            # Job 3: Frontend (Moderate match - mostly HTML/JS, less TypeScript/Redux)
            {
                "job": job3,
                "file_name": "Liam_O_Connor_WebDev.docx",
                "text": """Liam O'Connor
Email: liam.oconnor@webdev.ie | Phone: (617) 555-4019 | Location: Boston, MA

SUMMARY
Web Developer with 3 years of experience building websites and user interfaces.

SKILLS
JavaScript, React, HTML5, CSS3, Bootstrap, jQuery, Git, RESTful APIs

EXPERIENCE
Frontend Developer | Beacon Web Design (2021 - Present)
- Created responsive websites and landing pages with HTML5, CSS3, and React.
- Connected UI with backend REST APIs.
- Maintained source code with Git.

EDUCATION
Bachelor of Arts in Digital Arts
Boston University (2017 - 2021)"""
            },
            # Job 4: DevOps & Cloud Architect (Exceptional Match)
            {
                "job": job4,
                "file_name": "Rohan_Patel_DevOps_Architect.pdf",
                "text": """Rohan Patel
Email: rohan.patel@cloudops.tech | Phone: (408) 555-9128 | Location: San Jose, CA | GitHub: github.com/rohancloud

EXECUTIVE SUMMARY
Senior Cloud DevOps & Infrastructure Architect with 6+ years of experience leading cloud migrations, Kubernetes container orchestration, and Infrastructure as Code (Terraform) across AWS enterprise environments.

TECHNICAL SKILLS
- Cloud Platforms: AWS (EKS, EC2, S3, RDS, IAM, CloudFront, VPC), Google Cloud
- Containers & Orchestration: Kubernetes, Docker, Helm, Docker Compose
- Infrastructure as Code: Terraform, Ansible
- CI/CD & Automation: GitHub Actions, Jenkins, GitLab CI, CI/CD pipelines
- Systems & Scripting: Linux (Ubuntu/RHEL), Shell Scripting, Bash, Python, Git
- Observability: Prometheus, Grafana, ELK Stack

PROFESSIONAL EXPERIENCE
Senior DevOps Architect | CloudNative Labs (2021 - Present)
- Designed and automated AWS cloud infrastructure using Terraform and Ansible.
- Managed 12 multi-tenant production Kubernetes (EKS) clusters hosting 200+ microservices.
- Constructed automated zero-downtime CI/CD deployment pipelines with GitHub Actions.
- Set up system monitoring, dashboards, and automated alerts with Prometheus and Grafana.

DevOps Engineer | Scalable Systems (2018 - 2021)
- Containerized legacy backend monoliths into lightweight Docker containers.
- Wrote Bash shell scripts and Python automation tools for infrastructure maintenance.
- Administered Linux server fleets ensuring 99.99% uptime SLA.

EDUCATION
Bachelor of Science in Computer Engineering
San Jose State University (2014 - 2018)

CERTIFICATIONS
- AWS Certified DevOps Engineer - Professional
- Certified Kubernetes Administrator (CKA)
- HashiCorp Certified: Terraform Associate"""
            },
            # Job 4: DevOps (Moderate match)
            {
                "job": job4,
                "file_name": "Ethan_Hunt_SysAdmin.docx",
                "text": """Ethan Hunt
Email: ethan.hunt@missionops.net | Phone: (202) 555-0144 | Location: Washington, DC

SUMMARY
Systems Administrator with 4 years of experience managing Linux infrastructure and Docker containers.

SKILLS
Linux, Docker, AWS, Shell Scripting, Bash, Git, Python, CI/CD, Nginx

EXPERIENCE
Systems Administrator | Capital Tech (2020 - Present)
- Administered Ubuntu and CentOS Linux servers.
- Automated daily backup scripts using Bash and Python.
- Deployed containerized applications using Docker.

EDUCATION
Bachelor of Science in Information Technology
George Mason University (2016 - 2020)"""
            }
        ]

        # Write dummy files to disk and execute real processing pipeline
        for cand_data in sample_candidates:
            job = cand_data["job"]
            fname = cand_data["file_name"]
            raw_text = cand_data["text"]
            file_path = os.path.join(upload_dir, fname)

            # Write text representation to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(raw_text)

            resume = Resume(
                candidate_name=os.path.splitext(fname)[0].replace('_', ' ').title(),
                file_name=fname,
                file_path=file_path,
                file_type=fname.split('.')[-1],
                raw_text=raw_text,
                uploaded_by_user_id=recruiter.id,
                processing_status='pending'
            )
            db.session.add(resume)
            db.session.flush()

            # Execute full real screening & ranking
            screening = process_and_screen_resume(resume, job, auto_commit=False)
            
            # Set initial statuses based on score quality
            if screening.match_score >= 80:
                screening.status = 'shortlisted'
            elif screening.match_score >= 60:
                screening.status = 'in_review'
            else:
                screening.status = 'new'

        db.session.commit()

        # Re-rank all candidates for all jobs
        for job in [job1, job2, job3, job4]:
            rank_candidates_for_job(job.id)

        print("\n[SUCCESS] Database seeding complete!")
        print(f"   * Users created: {User.query.count()}")
        print(f"   * Job Descriptions: {JobDescription.query.count()}")
        print(f"   * Resumes processed: {Resume.query.count()}")
        print(f"   * Screenings scored & ranked: {Screening.query.count()}")
        print("\n[INFO] Login Credentials:")
        print("   Admin:     admin@resumescreen.ai / Admin@123")
        print("   Recruiter: recruiter@resumescreen.ai / Recruiter@123")

if __name__ == '__main__':
    seed_database()
