# Design Reference: Multi-Source Classification and Reporting System

## Document Status

- Status: Draft v2
- Purpose: Implementation reference for end-to-end delivery
- Audience: Project owner, future contributors, reviewers
- Source references:
  - `docs/system-design.md`
  - `docs/AI_Capability_Build_Spec_Pack.md`
  - `docs/AI_Capability_Case_Study_Pack.md`
- External design reference:
  - Oppia design-doc guidance: https://github.com/oppia/oppia/wiki/Writing-design-docs

## 1. Executive Summary

This document defines the implementation design for a local-first system that ingests messy business data from multiple source types, classifies and structures that data using LLM-assisted processing, validates the results, stores traceable records, and produces reporting outputs for business users.

The build is intentionally designed as a system of modules rather than a single script. The end state for v1 is a working pipeline with:

- source adapters for multiple input types
- canonical intake normalization
- LLM-based classification and extraction
- schema and business-rule validation
- SQLite persistence
- review queue routing
- Streamlit reporting and CSV export
- prompt versioning and run logging

The design optimizes for implementation clarity. It describes what to build, how the components should interact, what contracts they should honor, what data should be stored, and what constitutes success.

## 2. Problem Statement

Operational teams receive requests from emails, spreadsheets, notes, brief documents, and copied free text. These inputs are inconsistent and often incomplete. Manual classification and triage are slow, error-prone, and difficult to audit.

The system must convert those inputs into structured outputs that can be:

- classified consistently
- reviewed by humans
- persisted for traceability
- summarized for reporting
- extended to new source types without redesigning the pipeline

## 3. Goals and Non-Goals

### 3.1 Goals

- Support multiple text-based and semi-structured source types through a common ingestion contract.
- Produce a validated classification output with summary, extracted entities, risk flags, and recommended next action.
- Persist both raw and processed records with timestamps, status, prompt version, and run history.
- Route invalid or uncertain cases into a review queue.
- Provide a simple reporting interface and export path.
- Keep the implementation modular enough to evolve into a cloud-aligned architecture later.

### 3.2 Non-Goals

- OCR-heavy document pipelines in v1
- production authentication and authorization
- direct integration into live enterprise systems
- custom model training or fine-tuning
- event-driven distributed infrastructure

## 4. v1 Scope

### 4.1 In Scope

- pasted text input
- `.txt` ingestion
- `.csv` ingestion
- `.json` ingestion
- email-style free text
- synthetic and representative sample data
- single-user local execution
- batch and single-item processing

### 4.2 Out of Scope

- scanned PDFs
- Word document parsing
- shared mailbox polling
- multi-user workflow approvals
- production hosting

## 5. Success Criteria

The implementation is successful when:

- at least three source types can be processed through the same pipeline
- the system classifies requests into a fixed taxonomy
- outputs conform to a defined schema
- invalid outputs are prevented from being silently accepted
- raw input and run history can be traced for any processed item
- a Streamlit view can display processed records and flagged items
- CSV export can be generated from validated outputs

## 6. System Context

### 6.1 Example Business Domains

The initial system should be demonstrated against two business contexts:

- architecture firm workflows
- hospitality operations workflows

These domains are useful because they include:

- scheduling and allocation changes
- customer or client requests
- updates to operational instructions
- ambiguous free-text inputs
- deadlines and priority cues

### 6.2 Example Source Types

- copied email content
- CSV export of requests or work items
- text file containing an operations brief
- JSON export from a simulated system

## 7. Canonical Processing Contract

Every adapter must transform input data into a shared canonical object before any model call occurs.

### 7.1 Canonical Intake Schema

```json
{
  "request_id": "REQ-2026-000001",
  "source_type": "email_text",
  "source_name": "manual_upload",
  "business_domain_hint": "hospitality",
  "raw_content": "Customer has requested a room allocation update by Friday.",
  "normalized_content": "Customer has requested a room allocation update by Friday.",
  "metadata": {
    "file_name": "request_001.txt",
    "submitted_by": "demo_user",
    "received_channel": "manual"
  },
  "received_at": "2026-03-25T09:00:00Z"
}
```

### 7.2 Design Rule

All downstream services must operate on this canonical schema, not on source-specific payloads.

This keeps:

- preprocessing reusable
- classifier inputs consistent
- validation logic centralized
- reporting independent of source format

## 8. Target Output Contract

The classifier must return a single structured output object that is validated before persistence.

### 8.1 Classification Output Schema

```json
{
  "request_id": "REQ-2026-000001",
  "request_type": "booking_change",
  "business_domain": "hospitality",
  "priority": "high",
  "summary": "Customer requests an urgent booking allocation update before Friday.",
  "entities": {
    "deadline": "2026-03-28",
    "customer_name": "Example Pty Ltd",
    "location": "Brisbane"
  },
  "risk_flags": [
    "deadline_near",
    "missing_capacity_confirmation"
  ],
  "recommended_next_action": "Review room availability and confirm updated allocation options.",
  "confidence": 0.82,
  "status": "validated",
  "processed_at": "2026-03-25T09:01:15Z",
  "prompt_version": "classification_v1"
}
```

### 8.2 Allowed Core Enums

#### `priority`

- `low`
- `medium`
- `high`
- `urgent`

#### `status`

- `validated`
- `review_required`
- `failed`

### 8.3 Initial Request Taxonomy

The first implementation should lock a finite taxonomy:

- `client_instruction`
- `operational_request`
- `booking_change`
- `schedule_change`
- `issue_or_incident`
- `data_update`
- `information_request`
- `risk_or_escalation`
- `unknown`

This taxonomy should be configurable as code constants and referenced by both prompts and validators.

## 9. High-Level Architecture

```text
[Input Source]
    |
    v
[Adapter Registry]
    |
    v
[Canonical Intake Builder]
    |
    v
[Preprocessor]
    |
    v
[Workflow Orchestrator]
    |
    v
[Classifier Client]
    |
    v
[Validator + Business Rules]
   |                  |
   | valid            | invalid or uncertain
   v                  v
[Persistence]      [Review Queue]
   |
   v
[Reporting Service]
   |
   v
[Streamlit App / CSV Export]
```

## 10. Runtime Execution Model

### 10.1 Supported Execution Paths

- single request via CLI or script
- batch processing over a directory of files
- reporting-only mode for viewing persisted outputs
- Streamlit UI for review and reporting

### 10.2 Suggested Entry Points

```text
src/main.py
app/streamlit_app.py
```

### 10.3 Main Processing Sequence

```text
1. Load config
2. Initialize logger
3. Initialize DB session
4. Resolve source adapter
5. Build canonical intake object
6. Preprocess content
7. Select prompt version
8. Call classifier
9. Parse model response
10. Validate schema
11. Apply business rules
12. Persist results
13. Route to review queue if needed
14. Emit logs and summary result
```

## 11. Repository Layout

```text
/app
  streamlit_app.py
/data
  /raw
  /processed
  /synthetic
/docs
  design-reference.md
/src
  /adapters
    base.py
    text_adapter.py
    csv_adapter.py
    json_adapter.py
    email_text_adapter.py
  /config
    settings.py
  /models
    schemas.py
    db_models.py
    enums.py
  /prompts
    classification_v1.md
  /services
    preprocessing.py
    classifier.py
    validator.py
    business_rules.py
    storage.py
    reporting.py
    review.py
    logging_service.py
    prompt_manager.py
  /utils
    ids.py
    timestamps.py
  main.py
/tests
  test_adapters.py
  test_schemas.py
  test_validator.py
  test_business_rules.py
  test_storage.py
  test_pipeline_smoke.py
```

## 12. Module-Level Design

### 12.1 `src/config/settings.py`

Purpose:

- centralize environment and runtime configuration

Recommended contents:

- OpenAI or Azure model settings
- database path
- logging level
- review threshold
- prompt version default
- supported source types

Suggested implementation:

```python
from pydantic import BaseModel


class Settings(BaseModel):
    provider: str
    model_name: str
    database_url: str
    log_level: str = "INFO"
    prompt_version: str = "classification_v1"
    confidence_threshold: float = 0.75
```

### 12.2 `src/models/enums.py`

Purpose:

- define shared enums used by prompts, validation, persistence, and reporting

Suggested enums:

- `SourceType`
- `RequestType`
- `Priority`
- `ProcessingStatus`
- `ReviewStatus`

### 12.3 `src/models/schemas.py`

Purpose:

- define Pydantic contracts for canonical intake, classifier output, validation result, and reporting projections

Suggested classes:

- `CanonicalIntake`
- `ClassificationOutput`
- `ValidationResult`
- `ReviewDecision`
- `ProcessingResult`

Suggested implementation sketch:

```python
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CanonicalIntake(BaseModel):
    request_id: str
    source_type: str
    source_name: str
    business_domain_hint: str | None = None
    raw_content: str
    normalized_content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    received_at: datetime


class ClassificationOutput(BaseModel):
    request_id: str
    request_type: str
    business_domain: str
    priority: str
    summary: str
    entities: dict[str, Any]
    risk_flags: list[str]
    recommended_next_action: str
    confidence: float | None = None
    status: str
    processed_at: datetime
    prompt_version: str
```

### 12.4 `src/models/db_models.py`

Purpose:

- define SQLAlchemy persistence models

Required tables:

- `requests`
- `processed_outputs`
- `run_logs`
- `review_queue`

### 12.5 `src/adapters/base.py`

Purpose:

- define a common interface for all source adapters

Suggested interface:

```python
from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    source_type: str

    @abstractmethod
    def can_handle(self, input_ref: str) -> bool:
        ...

    @abstractmethod
    def load(self, input_ref: str) -> dict:
        ...
```

### 12.6 `src/adapters/text_adapter.py`

Handles:

- plain text files
- copied text passed through the CLI or UI

Responsibilities:

- read text safely
- normalize line endings
- preserve original content

### 12.7 `src/adapters/csv_adapter.py`

Handles:

- CSV rows representing requests

Responsibilities:

- parse rows with pandas
- map row fields into text blocks or structured metadata
- emit one canonical intake per row

Design choice:

- treat each row as a separate request

### 12.8 `src/adapters/json_adapter.py`

Handles:

- JSON input with either raw text fields or semi-structured request records

Responsibilities:

- validate minimal expected keys
- flatten useful fields into `normalized_content`
- preserve original JSON in metadata if needed

### 12.9 `src/services/preprocessing.py`

Purpose:

- normalize content before prompt submission

Required functions:

- `clean_text(raw_text: str) -> str`
- `build_normalized_content(intake: CanonicalIntake) -> str`

Rules:

- remove duplicated whitespace
- normalize newline patterns
- preserve meaning-bearing tokens
- avoid aggressive deletion of domain content

### 12.10 `src/services/prompt_manager.py`

Purpose:

- load prompt assets by version

Required behavior:

- read prompt file from `src/prompts/`
- attach taxonomy and output contract instructions
- return a final prompt string or message structure

Suggested methods:

- `load_prompt(version: str) -> str`
- `build_messages(intake: CanonicalIntake, prompt_version: str) -> list[dict]`

### 12.11 `src/services/classifier.py`

Purpose:

- encapsulate model client behavior and response parsing

Required behavior:

- receive canonical input
- call model provider
- request strict JSON output
- parse the response into `ClassificationOutput`
- return raw response text for logging if parsing fails

Suggested public methods:

- `classify(intake: CanonicalIntake, prompt_version: str) -> ClassificationOutput`

Suggested internal methods:

- `_build_messages(...)`
- `_call_model(...)`
- `_parse_response(...)`

### 12.12 `src/services/validator.py`

Purpose:

- validate schema correctness and required fields

Validation layers:

- Pydantic schema validation
- allowed enum validation
- empty summary check
- missing next-action check
- missing request type fallback

Suggested signature:

```python
def validate_output(output: ClassificationOutput) -> ValidationResult:
    ...
```

### 12.13 `src/services/business_rules.py`

Purpose:

- apply deterministic control logic after schema validation

Example rules:

- if `request_type == "unknown"` then review required
- if `priority == "urgent"` and no deadline exists then add risk flag
- if `confidence` exists and is below threshold then review required
- if `summary` length is below a threshold then review required

Suggested signature:

```python
def apply_rules(output: ClassificationOutput, threshold: float) -> ReviewDecision:
    ...
```

### 12.14 `src/services/storage.py`

Purpose:

- isolate all database interaction

Required methods:

- `init_db()`
- `save_request(intake: CanonicalIntake)`
- `save_processed_output(output: ClassificationOutput)`
- `save_run_log(...)`
- `enqueue_review(...)`
- `list_processed_records(...)`
- `list_review_queue(...)`

### 12.15 `src/services/review.py`

Purpose:

- centralize logic for manual-review routing

Required responsibilities:

- build review reason payloads
- insert review queue entries
- update processing status to `review_required`

### 12.16 `src/services/reporting.py`

Purpose:

- provide query methods used by Streamlit and CSV export

Required outputs:

- list of processed requests
- list of review queue entries
- aggregate metrics by category
- aggregate metrics by source type
- aggregate metrics by status

### 12.17 `src/services/logging_service.py`

Purpose:

- create structured logs for local debugging and audit

Required fields:

- request ID
- stage
- status
- prompt version
- processing time
- error details

## 13. Database Design

### 13.1 Table: `requests`

```sql
CREATE TABLE requests (
    request_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_name TEXT NOT NULL,
    business_domain_hint TEXT,
    raw_content TEXT NOT NULL,
    normalized_content TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    received_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

### 13.2 Table: `processed_outputs`

```sql
CREATE TABLE processed_outputs (
    output_id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    request_type TEXT NOT NULL,
    business_domain TEXT NOT NULL,
    priority TEXT NOT NULL,
    summary TEXT NOT NULL,
    entities_json TEXT NOT NULL,
    risk_flags_json TEXT NOT NULL,
    recommended_next_action TEXT NOT NULL,
    confidence REAL,
    status TEXT NOT NULL,
    processed_at TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (request_id) REFERENCES requests(request_id)
);
```

### 13.3 Table: `run_logs`

```sql
CREATE TABLE run_logs (
    run_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    processing_time_ms INTEGER,
    error_message TEXT,
    prompt_version TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (request_id) REFERENCES requests(request_id)
);
```

### 13.4 Table: `review_queue`

```sql
CREATE TABLE review_queue (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    review_reason TEXT NOT NULL,
    review_status TEXT NOT NULL,
    reviewer_notes TEXT,
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    FOREIGN KEY (request_id) REFERENCES requests(request_id)
);
```

### 13.5 Indexing

Add indexes on:

- `processed_outputs.request_type`
- `processed_outputs.status`
- `processed_outputs.priority`
- `requests.source_type`
- `run_logs.request_id`
- `review_queue.review_status`

## 14. Prompt Design

### 14.1 Prompt Asset Strategy

Prompts must be stored as versioned files, not inline strings buried in code.

Example asset:

```text
src/prompts/classification_v1.md
```

### 14.2 Prompt Requirements

The prompt must:

- define the system role clearly
- describe the taxonomy
- define the output JSON schema
- instruct the model to avoid fabricated fields
- tell the model to return only valid JSON
- reinforce that uncertain data should be reflected as risk flags or omitted

### 14.3 Prompt Skeleton

```text
You are a business workflow classification engine.

Classify the following request into one of the allowed request types:
[taxonomy list]

Return JSON only using this schema:
[schema block]

Rules:
- Do not invent information not present in the request.
- If a field is uncertain, leave it null or add an appropriate risk flag.
- Use one of the allowed priority values only.
```

## 15. Detailed Processing Sequence

### 15.1 Sequence Diagram Source

```text
participant main
participant adapter
participant preprocess
participant prompt_manager
participant classifier
participant validator
participant rules
participant storage
participant review

main->adapter: load(input_ref)
adapter->main: CanonicalIntake
main->preprocess: build_normalized_content(intake)
preprocess->main: CanonicalIntake
main->prompt_manager: load_prompt(version)
prompt_manager->main: prompt
main->classifier: classify(intake, version)
classifier->main: ClassificationOutput
main->validator: validate_output(output)
validator->main: ValidationResult
main->rules: apply_rules(output, threshold)
rules->main: ReviewDecision
main->storage: save_request(intake)
main->storage: save_processed_output(output)
main->review: enqueue_if_required(decision)
main->storage: save_run_log(...)
```

### 15.2 Orchestrator Pseudocode

```python
def process_input(input_ref: str, source_type: str | None = None) -> ProcessingResult:
    run_id = generate_run_id()
    start_time = utc_now()

    adapter = adapter_registry.resolve(input_ref, source_type=source_type)
    intake = adapter.load(input_ref)
    intake = preprocessing_service.normalize(intake)

    storage_service.save_request(intake)

    try:
        output = classifier_service.classify(intake, settings.prompt_version)
        validation = validator.validate_output(output)

        if not validation.is_valid:
            review_decision = review_service.from_validation(validation)
            storage_service.save_run_log(...)
            review_service.enqueue(intake.request_id, review_decision)
            return ProcessingResult(status="review_required", request_id=intake.request_id)

        review_decision = business_rules.apply_rules(output, settings.confidence_threshold)

        if review_decision.review_required:
            output.status = "review_required"
            storage_service.save_processed_output(output)
            review_service.enqueue(intake.request_id, review_decision)
        else:
            output.status = "validated"
            storage_service.save_processed_output(output)

        storage_service.save_run_log(...)
        return ProcessingResult(status=output.status, request_id=intake.request_id)

    except Exception as exc:
        storage_service.save_run_log(...)
        review_service.enqueue_system_failure(intake.request_id, str(exc))
        return ProcessingResult(status="failed", request_id=intake.request_id)
```

## 16. Error Handling Strategy

### 16.1 Error Categories

- adapter failure
- unsupported input
- model call failure
- response parsing failure
- schema validation failure
- business-rule review escalation
- persistence failure

### 16.2 Error Handling Rules

- log all failures with request ID and stage
- do not discard raw content on downstream failure
- distinguish `failed` from `review_required`
- preserve raw model response when JSON parsing fails if practical

## 17. Configuration and Environment Variables

### 17.1 Required Environment Variables

```text
OPENAI_API_KEY=
OPENAI_MODEL=
DATABASE_URL=sqlite:///data/app.db
LOG_LEVEL=INFO
PROMPT_VERSION=classification_v1
CONFIDENCE_THRESHOLD=0.75
```

### 17.2 Optional Azure-Oriented Variables

```text
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT=
```

### 17.3 `.env.example`

The repository should include a `.env.example` matching the keys above.

## 18. Reporting and Streamlit Design

### 18.1 Initial Screens

- Dashboard
- Processed Requests
- Request Detail
- Review Queue
- Export

### 18.2 Dashboard Metrics

- total requests
- validated requests
- review-required requests
- failed requests
- requests by type
- requests by source type
- urgent requests
- average processing time

### 18.3 Streamlit Data Requirements

The app should call reporting-service functions rather than querying SQLite inline from UI code.

Suggested functions:

- `get_dashboard_metrics()`
- `get_processed_requests(filters)`
- `get_request_detail(request_id)`
- `get_review_queue(filters)`
- `export_validated_records()`

## 19. Testing Strategy

### 19.1 Unit Tests

- adapter parsing
- schema validation
- business rules
- prompt loading
- storage methods

### 19.2 Contract Tests

- classifier output must map into `ClassificationOutput`
- invalid enum values must fail validation
- empty summaries must not pass acceptance

### 19.3 Integration Tests

- text file to validated output
- CSV row to review queue
- model mock response to persistence

### 19.4 Smoke Tests

- batch process a small synthetic folder
- launch Streamlit against the local database

### 19.5 Test Fixtures

Create messy fixtures that include:

- missing dates
- duplicate phrases
- contradictory priority language
- inconsistent formatting
- unclear category signals

## 20. Build Order

### 20.1 Phase 1: Skeleton

- create folder structure
- add shared enums and schemas
- add settings loader
- add database initialization

### 20.2 Phase 2: Input Pipeline

- implement adapters
- implement preprocessing
- implement request ID generation

### 20.3 Phase 3: Classification Pipeline

- implement prompt loading
- implement model wrapper
- implement response parsing
- implement validation
- implement business rules

### 20.4 Phase 4: Persistence and Review

- store requests and outputs
- add run logs
- add review queue

### 20.5 Phase 5: Reporting

- add reporting queries
- add Streamlit views
- add CSV export

### 20.6 Phase 6: Hardening

- add tests
- add sample data
- add screenshots and documentation polish

## 21. Concrete Task Breakdown

1. Create `src/models/enums.py`.
2. Create `src/models/schemas.py`.
3. Create `src/models/db_models.py`.
4. Create `src/config/settings.py`.
5. Create `src/adapters/base.py`.
6. Implement `text_adapter.py`.
7. Implement `csv_adapter.py`.
8. Implement `json_adapter.py`.
9. Implement `preprocessing.py`.
10. Implement `prompt_manager.py`.
11. Add `src/prompts/classification_v1.md`.
12. Implement `classifier.py`.
13. Implement `validator.py`.
14. Implement `business_rules.py`.
15. Implement `storage.py`.
16. Implement `review.py`.
17. Implement `reporting.py`.
18. Implement `main.py`.
19. Implement `app/streamlit_app.py`.
20. Add synthetic datasets under `data/synthetic/`.
21. Add tests and fixtures.

## 22. Risks and Mitigations

| Risk | Implementation Impact | Mitigation |
|---|---|---|
| Too many source types too early | Delays the first working slice | Start with text, csv, and json only |
| LLM returns malformed JSON | Breaks downstream pipeline | Use strict prompt instructions and parser fallback logging |
| Taxonomy is too vague | Reporting becomes weak | Lock a first finite taxonomy in code and docs |
| Review logic is unclear | Invalid outputs may slip through | Implement explicit rule functions and review reasons |
| UI queries bypass services | Logic becomes duplicated | Keep reporting queries in `reporting.py` |
| SQLite schema churn | Slows feature work | Keep v1 schema minimal and append-only where practical |

## 23. Open Questions

- Should confidence be generated by the model, inferred by rules, or both?
- Should taxonomy differ by business domain or remain global for v1?
- Should raw model responses be stored for debugging in v1?
- What is the minimum review UX needed beyond a table of flagged items?

## 24. Future Work

- PDF and OCR ingestion
- multi-prompt routing by domain
- scheduled batch jobs
- reviewer feedback loop
- cloud migration to Azure services
- Power BI or richer dashboarding

## 25. Acceptance Checklist

- Canonical intake schema is implemented and used everywhere downstream.
- At least three adapters exist and pass tests.
- Classification output validates against a Pydantic schema.
- Business rules can route records to review.
- Requests, outputs, logs, and reviews are stored in SQLite.
- Streamlit can show processed records and review queue items.
- CSV export works from persisted validated records.
- Prompt versions are stored and traceable.

## 26. Recommended First Build Slice

The first narrow slice should be:

- source types: pasted text, `.txt`, `.csv`
- taxonomy: fixed global list
- provider: OpenAI API
- storage: SQLite
- interface: single-page Streamlit table plus detail view
- controls: schema validation, confidence threshold, review queue, run logs

This slice is small enough to ship quickly and complete enough to prove the core system design.
