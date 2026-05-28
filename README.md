# 🛡️ RegTech Platform for Regulatory Surveillance
### **Automated Regulatory Intelligence Dashboard & Pipeline**

---

## 📑 Project Overview & Executive Summary

In the highly strict pharmaceutical sector, compliance officers and quality assurance (QA) teams face an overwhelming volume of daily updates published across public health agency portals. Manually tracking these changes is time-consuming, highly prone to human error, and heavily saturated with digital "noise"—such as structural web layout modifications, minor typo corrections, or formatting updates that hold zero legal or regulatory weight.

This project delivers an enterprise-grade **RegTech (Regulatory Technology)** platform that fully automates the lifecycle of regulatory surveillance. The system continuously monitors the digital infrastructure of the **European Medicines Agency (EMA)** and the **Agencia Española de Medicamentos y Productos Sanitarios (AEMPS)**.

Through an end-to-end data pipeline, the platform extracts raw digital content, maintains an immutable historical database of web snapshots, applies advanced **Natural Language Processing (NLP)** techniques to filter out aesthetic noise, leverages cloud-based **Generative Artificial Intelligence** to synthesize the true regulatory impact in a bilingual format, and seamlessly distributes consolidated alerts to stakeholders via automated communication channels.

---

## 🛠️ System Architecture & Data Lifecycle (The 5-Step Pipeline)

The platform is engineered using a modular, fault-tolerant architecture divided into 5 logical, sequential stages executed entirely in memory:

### 1. Data Ingestion & Extraction
* **Objective:** Connect in real-time to the indexed compliance sections of the EMA and AEMPS to natively capture raw textual data.
* **Engineering Approach:** Designed following Object-Oriented Programming (OOP) paradigms. It implements a **Polite Scraping** loop configured with scheduled delays (`time.sleep`) and customized browser session headers. This effectively simulates authentic human browsing behavior, mitigating the risk of rate-limiting, IP throttling, or server-side blocks (HTTP 403/503 errors).
* **Technologies:** Python, BeautifulSoup, Requests.

### 2. Historical Storage & Auditable Versioning
* **Objective:** Build a centralized data repository to safeguard the historical baseline of regulatory documents and attached tracked links.
* **Engineering Approach:** Managed via the SQLAlchemy ORM connected to a local SQLite relational engine. This setup provides strict transaction consistency (full ACID compliance) and data integrity without the operational complexity of heavy container deployments. Web layout structural changes are isolated into independent metadata columns, preventing text degradation of the baseline regulatory text.
* **Technologies:** SQLite, SQLAlchemy ORM.

### 3. Smart Change Detection Engine (NLP Core)
* **Objective:** Surgically isolate substantial regulatory modifications, completely eliminating false positives caused by stylistic rewriting or web template rendering.
* **Engineering Approach:** Rather than running absolute string comparisons or character-based diffs (which critically break over a misplaced comma), paragraphs are encoded into dense high-dimensional numerical vectors. The engine builds a complete mathematical distance matrix applying cosine similarity metrics.
* **Key Algorithmic Safeguards:**
  * **Greedy Matching Algorithm:** Executes an exclusive 1-to-1 paragraph mapping to eliminate "shadow matching," ensuring that absolute text deletions (`DELETED`) sharing common jargon with adjacent paragraphs are properly isolated.
  * **Hybrid Decision Tree:** Merges semantic embedding scores with targeted Regular Expression (`Regex`) filters. This forces the system to escalate an alert when single-word shifts occur in critical regulatory modalities (e.g., swapping a non-binding `"may"` to a mandatory `"must"`) or updates to compliance deadlines.
  * **Length-Ratio Filtering:** Evaluates the volumetric size ratio between candidate paired paragraphs to silently discard semantic traps (active vs. passive voice shifts with identical meaning).
* **Technologies:** SentenceTransformers (`all-MiniLM-L6-v2`), PyTorch, HuggingFace Hub.

### 4. Semantic Synthesis & Localization (Generative AI)
* **Objective:** Interpret isolated textual anomalies, deduce their real compliance impact on the biopharmaceutical sector, and compile a structured executive summary.
* **Engineering Approach:** Orchestrates low-latency asynchronous inferences via cloud infrastructure. Using advanced system prompt engineering with specialized persona parameters, the large language model functions as an expert regulatory consultant. It extracts abstract compliance concepts (such as identifying an implicit license revocation within a newly inserted text block) and renders standardized outputs in both English and Spanish.
* **Technologies:** Groq API Cloud, Llama 3.1 Model Core.

### 5. Backend Consolidation & Real-Time Direct Pipeline Runner
* **Objective:** Close the transactional lifecycle by updating database baselines, maintaining data persistence persistence safety, and streaming telemetry logs back to the UI.
* **Engineering Approach:** Implemented as a native Python streaming generator (`yield`) that processes all stages sequentially in memory without intermediate file writing. It utilizes efficient data structure lookups (`set()`) to isolate altered URLs, overwrites production snapshots to serve as the baseline for the next cycle, and wraps database transactions safely. If an anomaly occurs, an immediate `.rollback()` triggers, keeping data pristine.
* **Technologies:** Python Generators, Python Logging, SQLAlchemy Session Management.

---

## 🎯 Test Strategy & Empirical Verification Scenarios

To validate the scientific rigor of the NLP engine and certify its behavior under rigorous QA standards, the system was subjected to controlled verification testing using an authentic communication from the EMA as the reference control baseline.

### Scenario 2: Happy Path Verification ("Easy Level")
Validates standard pipeline execution against straightforward text transformations and surface-level manipulation.
* **Irrelevant Change (Visual Noise):** Injected double spacing, randomized UPPERCASE shifts, and minor typographical typos. *Result: Text embeddings registered maximum mathematical similarity, silently discarding the noise without generating false alerts.*
* **Small Relevant Change (Key Data):** Target modification of numerical data metrics (e.g., changing a compliance window from `"30 days"` to `"90 days"`). *Result: Successfully trapped by the number/date Regex engine, triggering a critical alert.*
* **Large Relevant Change (Obvious Structure):** Appended an entirely new textual section titled `"NEW ANNEX: Prohibited Substances"`. *Result: Isolated with a `0.0` similarity score and automatically flagged as an `ADDED` segment.*

### Scenario 3: Corner Cases & Stress Testing ("Hard Level")
Designed to stress-test the semantic context of the core engine and evaluate its legal judgment capabilities over deceptive, matching texts.
* **Semantic Trap (Irrelevant Change):** Complete paragraph rewriting by altering the grammatical voice and swapping heavy terminology with synonyms (e.g., *"The drug was approved by the committee"* $\rightarrow$ *"The committee granted approval for the medication"*). *Result: The engine crossed the embedding distance score with the length ratio check, detecting that the core meaning remained intact, archiving the text in silence, and saving cloud LLM tokens.*
* **Critical Legal Subtlety (Small Relevant Change):** Modification of a single modal verb that completely flips the legal liability of the regulation (e.g., *"Companies may submit the report"* $\rightarrow$ *"Companies must submit the report"*). *Result: Successfully isolated as `MODIFIED (Critical Legal Modality)`. Even though the embedding threw a high geometric similarity of `0.9922`, the hybrid decision tree bypassed the score and escalated the alert with maximum priority.*
* **Injected Contradiction (Large Relevant Change):** Intercalation of a fraudulent paragraph in the middle of a guideline text that explicitly revokes prior regulatory authorizations. *Result: Caught as a semantic change (`0.7566` similarity score). The volumetric check passed, forcing the downstream LLM to analytically extract and synthesize the critical concept of an emergency revocation in the final report.*
* **Paragraph Deletion (Large Relevant Change):** Total removal of an entire sub-paragraph corresponding to the ETF scientific advice guidelines from the source file. *Result: Successfully caught via the reverse tracking validation rule integrated into the detector. When executing the greedy matching algorithm, the engine isolated the missing old paragraph, triggering a definitive `DELETED` alert with `0.0` similarity.*

---

## 🖥️ Enterprise Frontend & Management Dashboard

The user interface abstracts the backend data complexity into an elegant, interactive command panel tailored for compliance officers and regulatory auditors.

### Implementation Highlights:
* **UI/UX Engineering:** Built completely over Streamlit, injecting custom CSS and HTML elements into the layout to enforce an institutional, corporate-colored palette, adaptive status icons, and responsive navigation sidebars.
* **Audit Trail Persistence:** Linked directly to the SQLite live production tables, allowing users to perform chronological deep searches of historical surveillance records.
* **Mailing List Management (CRUD):** A dynamic module for active email distribution group administration. It permits creating new compliance groups and appending or wiping active email lists on the fly, saving data into optimized JSON structures.
* **On-Demand PDF Report Compilation:** Integrates `reportlab` to build automated regulatory alert PDFs on the fly. It applies specialized typography, handles automated page breaks for dense text, and embeds corporate-colored signature signatures into page footers.
* **Automated SMTP Transmission:** Built securely via MIME protocols and SSL encryption using Google App Passwords. It delivers clean HTML-formatted alert messages and attaches compiled PDF reports directly to active mail groups.
* **Trend & Stress Analytics:** Implements `pandas` to crunch historical metrics across surveillance cycles, mapping a chronological line chart that visually traces regulatory alert spikes over time.

---

## 📂 Project Repository Structure
```text
├── BD/
│   └── regtech_data.db        # Relational SQLite Database (Snapshots & Executive Reports)
├── logs/
│   └── pipeline_run_*.log     # Chronological technical logging files
├── Data_test_scenario_2_easy/ # Scenario 2 Local test files (Happy Path verification)
├── Data_test_scenario_3_hard/ # Scenario 3 Local test files (Corner Cases verification)
├── app.py                     # Main Streamlit Executive Frontend & Dashboard UI
├── nlp_change_detector.py     # NLP Core Module (Similarity Matrix & 1-to-1 Greedy Match)
├── mailing_lists.json         # JSON Storage for distribution list CRUD operations**CREATED ON THE FLY**
├── requirements.txt           # Virtual environment dependencies list
├──.env                        # Local environment variables file (GROQ_API_KEY)**NOT INCLUDED IN REPO**
├── .gitignore                       
└── Documentation/
    └── RegTech_Presentation.pptx # Final presentation Project Big Data & Machine Learning MVP
    └── Bitacora.odt              # Summary of the development process, testing strategy and deployment considerations of each step.

```
---

## 🚀 Installation & Local Execution Guide

### Prerequisites
Ensure your workstation environment has **Python 3.10 or higher** installed.

### 1. Clone the Repository and Install Dependencies
Open your command terminal in your workspace directory and execute:
```bash
git clone <repository-url>
cd RegTech-Platform-Regulatory-Surveillance
pip install -r requirements.txt

### 2. Configure Environment Secrets
Create a file named .env in the root directory of the project to protect your keys:
```bash
GROQ_API_KEY=your_actual_groq_cloud_secret_api_key_here
```

### 3. Launch the Platform Server
Execute the following command to deploy your local Streamlit server instance:
```bash
streamlit run app.py  
``` 
The system will automatically open an active tab in your web browser pointing to http://localhost:8501 where you can interact with the dashboard.

### 4. Direct Pipeline Auditing
Navigate to the ▶️ Run Live Surveillance tab, toggle the secure checkpoint modal window, and click "Yes, Confirm and Run Live Pipeline". The UI mini terminal will progressively stream technical state updates for the 5 infrastructure steps, while raw trace files accumulate chronologically under the /logs directory.
##### NOTE: This functionality has not been included in the repository, it has only been included in the presentation

### **🤝 Acknowledgments**
The successful development of this automated regulatory surveillance platform MVP marks the culmination of an intensive specialization journey in data engineering and advanced analytics. I would like to express my deepest gratitude to those who were indispensable parts of this experience:

To my Professors, **Ana Morais** and **Montassar Jeddou**: Thank you for your masterly guidance, your infinite patience, and for constantly pushing my technical limits through every single module of Big Data and Machine Learning. Your unique ability to deconstruct the architectural complexities of data systems and advanced AI models has been the fundamental pillar in building this production-grade RegTech software. Thank you for your dedication, rigor, and daily inspiration.
I will miss the afternoon icebreakers.😜

To my **Ironhack Classmates:** Thank you for the shared hours of code, intense technical debates, late-night debugging sessions, and for building an unmatched collaborative environment. Your constant support and exchange of ideas turned this academic challenge into an unforgettable, shared journey. This final project carries a piece of the great energy of this entire cohort❤️💪.

💊  Developed with pride by Juan Álvaro Romero | Final Project Big Data & Machine Learning MVP | © 2026  💊
