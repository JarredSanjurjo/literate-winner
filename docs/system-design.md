  
## 1. Executive Summary

The system is designed to process unstructured business requests such as client instructions, operational briefs, or workflow intake emails, then convert them into structured, validated, and actionable outputs.

The aim is not to build a novelty demo. The aim is to design a system that demonstrates business relevance, architectural clarity, repeatable processing, governance thinking, and a practical path to operational use.

In this example, two personas are going to be used to validate the performance of this system, a small Architecture firm and a hospitality organisation. Both located in Brisbane

---

## 2. Business Problem

Operations teams often receive requests in messy formats:
- email-style instructions
- free-text briefs
- uploaded documents
- CSV records with inconsistent fields

Manual handling creates four recurring issues:
1. **slow turnaround**
2. **inconsistent interpretation**
3. **poor traceability**
4. **governance risk**

The system must reduce manual effort by converting unstructured requests into structured records that downstream users can review and act on.

### Problem Statement
Design an AI-enabled workflow that ingests messy business requests, extracts key information, classifies the work, validates the result, stores it, and presents a usable output for operations teams.

---

## 3. Users and Stakeholders

### Primary Users
- Operations teams
- Ownership
- Customer service managers

### Secondary Stakeholders
- - Future downstream system owners

### User Need
Users need a system that:
- reduces manual triage effort
- creates structured, consistent outputs
- flags risk or ambiguity
- provides an audit trail
- supports business action
- supports customer service

---

## 4. Scope

### In Scope
- Intake of raw text or file-based requests
- LLM-based extraction and classification
- Structured JSON outputs
- Schema validation
- Persistent storage
- Reporting or dashboard view
- Logging and operational controls
- Architecture and business documentation

### Out of Scope
- Production-scale security engineering
- Live enterprise integrations
- Fine-tuning models
- Full-scale distributed infrastructure

---

## 5. Functional Requirements

The system must:

1. accept messy input in text or file format  
2. preprocess and normalise content  
3. send relevant content to an LLM  
4. extract structured fields from the response  
5. classify the request type  
6. generate a summary and recommended next action  
7. validate output structure against a schema  
8. store the raw input and processed output  
9. display results through a simple interface or export  
10. log processing events and failures  

---

## 6. Non-Functional Requirements

The system should demonstrate:

- **reliability** — repeatable outputs and stable processing  
- **maintainability** — modular components, not one giant script  
- **auditability** — raw input, output, and run history saved  
- **traceability** — prompt version and timestamp recorded  
- **scalability path** — clear route from local build to cloud-aligned target state  
- **usability** — outputs easy for business users to review  

---

## 7. Assumptions

- Initial build uses synthetic and representative data only
- Initial delivery is local-first with optional Azure alignment
- Batch processing is acceptable for v1
- Streamlit is sufficient for v1 output interface
- SQLite is sufficient for v1 persistence
- OpenAI or Azure OpenAI provides inference capability

---

## 8. High-Level Architecture

## 8.1 Architecture Overview

```text
[User / File Upload / Request Source]
                |
                v
        [Ingestion Layer]
                |
                v
      [Preprocessing / Cleaning]
                |
                v
       [LLM Processing Layer]
                |
                v
       [Validation / Schema Check]
                |
        -----------------------
        |                     |
        v                     v
 [Persistence Layer]    [Error / Review Queue]
        |
        v
   [Reporting / UI Layer]
        |
        v
   [User Review / Action]
```

## 8.2 Component Summary

### 1. Ingestion Layer
Receives raw business requests from:
- text inputs, i.e transcripts of recorded conversations or messages
- uploaded files
- CSV records
- emails

### 2. Preprocessing Layer
Cleans and normalises the content before inference:
- remove junk formatting
- standardise field layout
- create request ID
- attach metadata

### 3. LLM Processing Layer
Uses prompt templates, skills and business logic to:
- extract fields
- classify request type
- generate summary
- identify missing information
- suggest next step

### 4. Validation Layer
Checks outputs against the required schema:
- required fields present
- field types match
- invalid outputs rejected or flagged

### 5. Persistence Layer
Stores:
- raw input
- structured output
- metadata
- prompt version
- processing status
- timestamp
- error details

### 6. Output Layer
Surfaces results via:
- Streamlit dashboard
- CSV export
- report-ready data view
- alerts of new requests
- 

### 7. Monitoring and Controls Layer
Provides:
- logging
- run history
- traceability
- basic review path for failed or uncertain outputs

---

## 9. Input Design

## 9.1 Input Types
The system accepts:
- `.txt` files
- `.csv` files
- direct text entry
- simulated email requests

## 9.2 Example Raw Input

```text
Subject: Portfolio instruction update

Client has requested a rebalance of the portfolio to reduce exposure to fossil fuels and align with updated ESG mandate requirements.
Please review holdings, flag affected positions, and prepare a summary for implementation.
Priority is medium but would prefer this completed before Friday.
```

## 9.3 Input Challenges
The system must assume:
- inconsistent wording
- missing fields
- mixed instructions
- duplicate content
- ambiguous priority
- uneven formatting


---

## 10. Output Design

## 10.1 Required Output Schema

```json
{
  "request_id": "REQ-0001",
  "request_type": "portfolio_rebalance",
  "priority": "medium",
  "summary": "Client requests portfolio rebalance aligned to revised ESG mandate.",
  "entities": {
    "deadline": "Friday",
    "theme": "ESG",
    "action_area": "holdings review"
  },
  "risk_flags": [
    "mandate_change",
    "potential compliance review"
  ],
  "recommended_next_action": "Review holdings impacted by ESG exclusion criteria and prepare implementation summary.",
  "status": "validated",
  "processed_at": "2026-03-23T10:00:00Z",
  "prompt_version": "v1.0"
}
```

## 10.2 Output Consumers
Outputs should be usable by:
- operations staff
- implementation analysts
- managers reviewing flagged cases
- downstream systems in a future-state design

---

## 11. Data Model

A minimal v1 data model should include the following entities:

### Request
- request_id
- raw_input
- source_type
- received_at

### ProcessedOutput
- request_id
- request_type
- priority
- summary
- structured_json
- status
- processed_at

### RunLog
- run_id
- request_id
- prompt_version
- processing_time
- success_flag
- error_message

### ReviewQueue
- review_id
- request_id
- reason_flagged
- review_status
- reviewer_notes


---

## 12. Data Flow

## 12.1 End-to-End Flow

1. User uploads or enters a raw request  
2. Ingestion module assigns request ID and captures metadata  
3. Preprocessing module cleans and normalises the input  
4. Processing module sends the request to the LLM using a controlled prompt  
5. LLM returns structured content  
6. Validator checks schema and required fields  
7. If valid, output is stored in SQLite  
8. If invalid, request is routed to a review/error state  
9. Output is displayed in dashboard or export layer  
10. Logging module records the run result  

## 12.2 Sequence View

```text
User -> Ingestion -> Preprocessing -> LLM Processor -> Validator -> Database -> Dashboard
                                                |
                                                v
                                         Error / Review Queue
```

---

## 13. Core Design Decisions

## 13.1 Batch First, Not Real-Time
### Decision
Process requests in batch for v1.

### Why
- faster to build
- easier to test
- suits portfolio delivery timeline
- sufficient for demonstrating repeatable workflow design

### Trade-off
Less immediate than event-driven real-time processing, but cleaner for initial implementation.

---

## 13.2 SQLite First, Not Managed Cloud Database
### Decision
Use SQLite in the first version.

### Why
- simple setup
- enough for demonstrating persistence
- low friction for local build
- easy to inspect during development

### Trade-off
Not suitable for enterprise scale, but perfectly acceptable for a proof-of-capability build.

---

## 13.3 Streamlit First, Not Full Web App
### Decision
Use Streamlit as the user-facing output layer.

### Why
- quick to deploy
- enough to prove usability
- better than backend-only demo
- supports dashboard and review workflow

### Trade-off
Less flexible than a custom frontend, but significantly faster to ship.

---

## 13.4 LLM Plus Validation, Not Blind Trust in Model Output
### Decision
Never accept model output without schema validation.

### Why
- LLMs are probabilistic
- enterprise workflows need consistency
- validation introduces control and trust

### Trade-off
Adds build complexity, but materially improves credibility and auditability.

---

## 14. Risks and Controls

| Risk                 | Description                                    | Control                                             |
| -------------------- | ---------------------------------------------- | --------------------------------------------------- |
| Bad input quality    | Raw requests may be incomplete or inconsistent | Preprocessing, required fields, manual review flags |
| Model inconsistency  | LLM may return malformed or vague outputs      | Schema validation using Pydantic                    |
| Hallucinated fields  | Model invents unsupported details              | Restrictive prompt design and validation rules      |
| No audit trail       | Users cannot trace what happened               | Store raw input, timestamps, prompt version, status |
| Silent failures      | Processing errors go unnoticed                 | Logging and explicit failure states                 |
| Over-clean demo data | Portfolio looks unrealistic                    | Use noisy synthetic and semi-structured inputs      |

This table is one of the fastest signals of mature system design thinking.

---

## 15. Governance and Operational Controls

The system should include the following controls:

### Control 1: Raw Input Retention
Retain original request text alongside processed output.

### Control 2: Prompt Version Tracking
Record which prompt version generated each output.

### Control 3: Schema Validation
Reject or flag outputs that do not meet the expected structure.

### Control 4: Review Queue
Route failed or low-confidence cases for manual review.

### Control 5: Run Logging
Record run ID, timestamp, status, processing time, and errors.

### Control 6: Versioned Outputs
Keep output history where reprocessing occurs.

These controls are what make the design sound operational rather than experimental.

---

## 16. Target-State Enterprise Mapping

The local-first design can be translated into a more enterprise-ready Microsoft-aligned stack.

| v1 Component | Enterprise-Aligned Equivalent |
|---|---|
| OpenAI API | Azure OpenAI |
| SQLite | Azure SQL or Cosmos DB |
| Local files | Azure Blob Storage |
| Python scripts | Azure Functions or containerised services |
| Streamlit | Internal web app or Power BI front-end |
| Local logs | Azure Monitor / App Insights |


---

## 17. Implementation Modules

A clean repository should separate responsibilities into modules like this:

```text
/src
  ingestion.py
  preprocessing.py
  processor.py
  validator.py
  storage.py
  reporting.py
  logger.py
  main.py
/app
  streamlit_app.py
/docs
  system-design.md
  operational-controls.md
  enterprise-case-study.md
```

### Why this matters
This structure shows:
- maintainability
- separation of concerns
- easier testing
- easier extension later

A single 500-line script does not send that signal.

---

## 18. Example Technology Stack

### Development
- Python 3.10+
- VS Code
- GitHub

### AI and Processing
- OpenAI SDK or Azure OpenAI SDK
- pandas
- pydantic

### Persistence
- SQLite
- SQLAlchemy

### Interface
- Streamlit

### Documentation and Design
- Markdown
- draw.io or Miro
