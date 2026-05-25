> **Note:** : This is a provisional beta version of the document. The project's architecture, specifications, and technologies are currently under active development.

# Project Summary: RegTech Platform for Regulatory Surveillance

The project consists of developing an intelligent Regulatory Technology (RegTech) platform designed to automate regulatory surveillance in the pharmaceutical sector. The system will periodically extract information from the EMA (in English) and AEMPS (in Spanish) agencies, storing a historical record of the publications.

Using Natural Language Processing (NLP) techniques, the engine will compare the historical data to detect and isolate exclusively the actual regulatory changes, discarding irrelevant website modifications. Subsequently, Generative Artificial Intelligence will translate, unify, and summarize these changes into an executive report in Spanish. Finally, the platform will distribute these alerts via email to segmented user groups. The entire ecosystem will be orchestrated through a web interface, from which recipients can be managed and custom regulatory reports filtered by dates can be requested on demand.

## Task List (End-to-End Pipeline)

To build a robust, modular, and fault-tolerant architecture, we will tackle the project covering the following 7 key points:

### 1. Data Ingestion and Extraction (Data Collection)
**Explanation:** Creation of the modules responsible for visiting the EMA and AEMPS websites to extract regulatory texts. It will be designed with an object-oriented approach, creating independent extractors for each agency that handle exceptions and network failures gracefully.

### 2. Historical Storage and Versioning (Database)
**Explanation:** Design of a centralized repository to store the raw extracted texts along with their metadata (agency, extraction date, link). This layer will ensure the temporal traceability needed to compare the "before" and "after" in on-demand queries.

### 3. Change Detection Engine (NLP / Machine Learning)
**Explanation:** Instead of performing an exact text comparison (which would fail if a simple period or comma changes), paragraphs will be transformed into numerical vectors. By calculating the mathematical distance between last month's text and the current one, the model will detect if there has been a real change in meaning in the regulation, isolating only the important fragments.

### 4. Synthesis and Translation (Generative AI)
**Explanation:** Processing of the regulatory fragments isolated in the previous step. Structured system prompts will be designed so the LLM acts as a regulatory analyst, receives texts in English (EMA) or Spanish (AEMPS), and always returns a standardized executive summary in Spanish, organized in bullet points.

### 5. Backend Development and Business Logic (API)
**Explanation:** Construction of the core engine that connects the database, NLP models, and the LLM. This is where the endpoints that will execute on-demand reports and manage the CRUD (Create, Read, Update, Delete) operations of the user database are defined. Solid data validation and unit testing strategies will be applied to guarantee service stability.

### 6. Management Interface and Frontend (UI)
**Explanation:** Creation of the visual control panel. It will have two main sections: a manager to add or remove emails from the distribution groups, and an analytical dashboard with date and agency selectors so a user can instantly generate custom regulatory reports.

### 7. Automation and Notification System (Distribution)
**Explanation:** Implementation of the email delivery system and the scheduling of automated tasks. It ensures that the workflow of extraction, analysis, and mass emailing runs strictly on a biweekly or monthly basis without human intervention.
